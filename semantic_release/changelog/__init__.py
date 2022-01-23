import logging

from ..helpers import LoggedFunction
from ..settings import config, import_from_settings

from .changelog import changelog_headers, changelog_table, changelog_template  # noqa isort:skip
from .compare import compare_url  # noqa isort:skip

__all__ = ("compare_url", "changelog_headers", "changelog_table", "changelog_template")

logger = logging.getLogger(__name__)


@LoggedFunction(logger)
def markdown_changelog(owner: str, repo_name: str, version: str, changelog: dict, previous_version: str = None) -> str:
    """Generate a markdown version of the changelog.

    :param owner: The repo owner.
    :param repo_name: The repo name.
    :param version: A string with the version number.
    :param previous_version: A string with the last version number, to
        use for the comparison URL. If omitted, the URL will not be included.
    :param changelog: A parsed changelog dict from generate_changelog.
    :return: The markdown formatted changelog.
    """
    output = ""

    # Add the output of each component separated by a blank line
    output += "\n\n".join(
        component_output.strip()
        for component_output in (
            component(
                owner=owner,
                repo_name=repo_name,
                version=version,
                previous_version=previous_version,
                changelog=changelog,
                changelog_sections=config.get("changelog_sections"),
            )
            for component in import_from_settings("changelog_components")
        )
        if component_output is not None
    )

    return output
