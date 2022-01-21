import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

from ..errors import ImproperConfigurationError
from ..history import get_new_version
from ..history.logs import evaluate_version_bump
from ..hvcs import Github, Gitlab
from ..settings import config
from .compare import compare_url


def add_pr_link(owner: str, repo_name: str, message: str) -> str:
    """
    GitHub release notes automagically link to the PR, but changelog markdown
    doesn't. Replace (#123) at the end of a message with a markdown link.
    """

    pr_pattern = re.compile(r"\s+\(#(\d{1,8})\)$")
    match = re.search(pr_pattern, message)

    if match:
        pr_number = match.group(1)
        url = (
            f"https://{Gitlab.domain()}/{owner}/{repo_name}/-/issues/{pr_number}"
            if config.get("hvcs") == "gitlab"
            else f"https://{Github.domain()}/{owner}/{repo_name}/issues/{pr_number}"
        )

        return re.sub(pr_pattern, f" ([#{pr_number}]({url}))", message)

    return message


def get_changelog_sections(changelog: dict, changelog_sections: list) -> Iterable[str]:
    """Generator which yields each changelog section to be included"""

    included_sections = config.get("changelog_sections")
    included_sections = [s.strip() for s in included_sections.split(",")]

    for section in included_sections:
        if section in changelog and changelog[section]:
            yield section


def get_hash_link(owner: str, repo_name: str, hash_: str) -> str:
    """Generate the link for commit hash"""
    url = (
        f"https://{Gitlab.domain()}/{owner}/{repo_name}/-/commit/{hash_}"
        if config.get("hvcs") == "gitlab"
        else f"https://{Github.domain()}/{owner}/{repo_name}/commit/{hash_}"
    )
    short_hash = hash_[:7]
    return f"[`{short_hash}`]({url})"


def changelog_headers(owner: str, repo_name: str, changelog: dict, changelog_sections: list, **kwargs) -> Optional[str]:
    output = ""

    for section in get_changelog_sections(changelog, changelog_sections):
        # Add a header for this section
        output += f"\n### {section.capitalize()}\n"

        # Add each commit from the section in an unordered list
        for item in changelog[section]:
            message = add_pr_link(owner, repo_name, item[1])
            output += f"* {message} ({get_hash_link(owner, repo_name, item[0])})\n"

    return output


def changelog_table(owner: str, repo_name: str, changelog: dict, changelog_sections: list, **kwargs) -> str:
    output = "| Type | Change |\n| --- | --- |\n"

    for section in get_changelog_sections(changelog, changelog_sections):
        items = "<br>".join(
            [
                f"{add_pr_link(owner, repo_name, item[1])} " f"({get_hash_link(owner, repo_name, item[0])})"
                for item in changelog[section]
            ]
        )
        output += f"| {section.title()} | {items} |\n"

    return output


def changelog_template(
    owner: str,
    repo_name: str,
    changelog: Any,
    changelog_sections: list,
    version: Optional[str] = None,
    previous_version: Optional[str] = None,
) -> Optional[str]:
    try:
        import chevron
    except ImportError:
        raise ImproperConfigurationError("Install `chevron` for use 'changelog_template' component")
    from ..vcs_helpers import get_formatted_tag, repo
    from . import handlers

    last_release = previous_version or version
    last_git_tag = get_formatted_tag(last_release)
    git_head_last = ""

    next_release = previous_version and version or None
    level_bump = ""
    git_head_next = ""
    if not next_release:
        # Calculate the new version
        level_bump = evaluate_version_bump(version, config.get("force_level"))
        next_release = get_new_version(version, level_bump)

    next_git_tag = get_formatted_tag(next_release)

    try:
        tag = repo.tag(last_git_tag)
        git_head_last = tag.commit.hexsha
    except ValueError:
        pass
    try:
        tag = repo.tag(next_git_tag)
        git_head_next = tag.commit.hexsha
    except ValueError:
        pass

    template_path = config.get("changelog_template", Path(__file__).parent.parent / "templates/template.tpl")

    file = Path(template_path)
    template = ""
    if file.exists():
        template = Path(template_path).read_text()
    else:
        template = (Path(__file__).parent.parent / "templates" / template_path).read_text()
    context = {
        "owner": owner,
        "repo_name": repo_name,
        "last_release": {
            "version": last_release,
            "git_tag": last_git_tag,
            "git_head": git_head_last,
        },
        "next_release": {
            "type": level_bump,
            "version": next_release,
            "git_tag": next_git_tag,
            "git_head": git_head_next,
        },
        "commits": changelog,
        "changelog_sections": changelog_sections,
        "version": version,
        "previous_version": previous_version,
        "datetime": lambda fmt, _: datetime.now().strftime(fmt),
        "compare_url": previous_version and compare_url(next_release, last_release) or "",
        "get_hash_link": handlers.get_hash_link,
    }

    return chevron.render(template, context)
