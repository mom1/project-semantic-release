"""Logs."""
import logging
from typing import Any, Callable, Dict, List, Optional

from ..errors import UnknownCommitMessageStyleError
from ..helpers import LoggedFunction
from ..settings import config, import_from_settings
from ..vcs_helpers import get_commit_log, get_commits_beetwen
from .parser_helpers import ParsedCommit

logger = logging.getLogger(__name__)

LEVELS = {
    0: None,
    1: "patch",
    2: "minor",
    3: "major",
}


@LoggedFunction(logger)
def evaluate_version_bump(current_version: str, force: str = None) -> Optional[str]:
    """Read git log since the last release to decide if we should make a major, minor or patch release.

    :param current_version: A string with the current version number.
    :param force: A string with the bump level that should be forced.
    :return: A string with either major, minor or patch if there should be a release.
             If no release is necessary, None will be returned.
    """
    if force:
        return force

    bump = None

    changes = []
    commit_count = 0
    commit_parser = import_from_settings("commit_parser")
    for _, commit_message in get_commit_log(current_version):
        if commit_message.startswith(current_version):
            # Stop once we reach the current version
            # (we are looping in the order of newest -> oldest)
            logger.debug(f'"{commit_message}" is commit for {current_version}, breaking loop')
            break

        commit_count += 1  # noqa: SIM113

        # Attempt to parse this commit using the currently-configured parser
        try:
            message = commit_parser(commit_message)
            changes.append(message.bump)
        except UnknownCommitMessageStyleError as err:
            logger.debug(f"Ignoring UnknownCommitMessageStyleError: {err}")
            pass

    logger.debug(f"Commits found since last release: {commit_count}")

    if changes:
        # Select the largest required bump level from the commits we parsed
        level = max(changes)
        if level in LEVELS:
            bump = LEVELS[level]
        else:
            logger.warning(f"Unknown bump level {level}")

    if config.get("patch_without_tag") and commit_count > 0 and bump is None:
        bump = "patch"
        logger.debug("Changing bump level to patch based on config patch_without_tag")

    if not config.get("major_on_zero") and current_version.startswith("0.") and bump == "major":
        bump = "minor"
        logger.debug("Changing bump level to minor based on config major_on_zero")

    return bump


@LoggedFunction(logger)
def generate_changelog(from_version: str, to_version: str = None) -> dict:
    """Parse a changelog dictionary for the given version.

    :param from_version: The version before where the changelog starts.
                         The changelog will be generated from the commit after this one.
    :param to_version: The last version included in the changelog.
    :return: A dict with changelog sections and commits
    """
    # Additional sections will be added as new types are encountered
    changes: dict = {"breaking": []}

    rev = None
    if from_version:
        rev = from_version

    commit_parser = import_from_settings("commit_parser")

    found_the_release = to_version is None
    for _hash, commit_message in get_commit_log(rev):
        if not found_the_release:
            # Skip until we find the last commit in this release
            # (we are looping in the order of newest -> oldest)
            if to_version and to_version not in commit_message:
                continue
            else:
                logger.debug(f"Reached the start of {to_version}, beginning changelog generation")
                found_the_release = True

        if from_version is not None and from_version in commit_message:
            # We reached the previous release
            logger.debug(f"{from_version} reached, ending changelog generation")
            break

        try:
            message = commit_parser(commit_message)
            if message.type not in changes:
                logger.debug(f"Creating new changelog section for {message.type} ")
                changes[message.type] = []

            # Capitalize the first letter of the message, leaving others as they were
            # (using str.capitalize() would make the other letters lowercase)
            formatted_message = message.descriptions[0][0].upper() + message.descriptions[0][1:]
            if config.get("changelog_capitalize") is False:
                formatted_message = message.descriptions[0]

            # By default, feat(x): description shows up in changelog with the
            # scope bolded, like:
            #
            # * **x**: description
            if config.get("changelog_scope") and message.scope:
                formatted_message = f"**{message.scope}:** {formatted_message}"

            changes[message.type].append((_hash, formatted_message))

            if message.breaking_descriptions:
                # Copy breaking change descriptions into changelog
                for paragraph in message.breaking_descriptions:
                    changes["breaking"].append((_hash, paragraph))
            elif message.bump == 3:
                # Major, but no breaking descriptions, use commit subject instead
                changes["breaking"].append((_hash, message.descriptions[0]))

        except UnknownCommitMessageStyleError as err:
            logger.debug(f"Ignoring UnknownCommitMessageStyleError: {err}")

    return changes


@LoggedFunction(logger)
def get_commits(from_version: str, to_version: str = None, rev: str = None) -> List[Dict[str, Any]]:
    results = []
    commit_parser: Callable[[str], ParsedCommit] = import_from_settings("commit_parser")

    for commit in get_commits_beetwen(from_version, to_version, rev):
        message: ParsedCommit = commit_parser(commit.message)
        results.append(
            {
                "commit": {
                    "long": commit.hexsha,
                    "short": commit.hexsha[:7],
                },
                "tree": {
                    "long": commit.tree.hexsha,
                    "short": commit.tree.hexsha[:7],
                },
                "author": {
                    "name": commit.author.name,
                    "email": commit.author.email,
                    "date": str(commit.authored_datetime),
                },
                "committer": {
                    "name": commit.committer.name,
                    "email": commit.committer.email,
                    "date": str(commit.committed_datetime),
                },
                "subject": message.descriptions[0],
                "body": "\n\n".join(message.descriptions[1:]),
                "message": commit.message,
                "committer_date": str(commit.committed_datetime),
                "type": message.type,
                "scope": message.scope,
            }
        )
    return results
