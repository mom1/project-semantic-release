from collections import defaultdict
from typing import Any, DefaultDict, Dict, List

from ..settings import config

try:
    from .processing import get_handler
except ImportError:
    get_handler = lambda *args, **kwargs: lambda *args: ""


def changelog_grouping(owner: str, repo_name: str, changelog: list, changelog_sections: list, **kwargs):
    """Grouping commits by field.

    It will work only with `commit_analyzer=semantic_release.history.logs.get_commits`
    """
    grouping_field = config.get("grouping_field", "type").strip()
    sections = defaultdict(list)
    handler = get_handler("changelog_section_handlers")
    for commit in changelog[:]:
        changelog.pop()
        sections[commit[grouping_field]].append(commit)

    changelog.extend(
        [
            {"section": handler(section), "commits_section": sections[section]}
            for section in changelog_sections
            if section and sections[section]
        ]
    )


def changelog_composite_grouping(owner: str, repo_name: str, changelog: list, **kwargs):
    """Grouping commits by field.

    It will work only with `commit_analyzer=semantic_release.history.logs.get_commits`
    """
    grouping_field = config.get("grouping_field", "type").strip()
    groups = {}
    composite_groups = tuple(sg for g in config.get("composite_groups", "").split(",") if (sg := g.strip()))
    for group in composite_groups:
        for i in config.get(f"composite_groups_{group}", "").split(","):
            groups[i.strip()] = group

    sections: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    handler = get_handler("changelog_section_handlers")
    ignore_types = set(i.strip() for i in config.get("composite_groups_ignore_types", "").split(","))
    ignore_types.add(None)
    other_group = groups.get("*")

    commit = changelog.pop()
    while changelog and commit:
        type_ = commit[grouping_field]
        if type_ in ignore_types:
            continue
        group = groups.get(type_, other_group)
        sections[group].insert(0, commit)
        commit = changelog.pop()

    changelog.extend(
        [
            {"section": handler(section), "commits_section": section_items}
            for section in composite_groups
            if (section_items := sections.get(section))
        ]
    )
