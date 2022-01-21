"""Commit parser which looks for emojis to determine the type of commit."""
import logging

from semantic_release.helpers import LoggedFunction
from semantic_release.history.parser_helpers import ParsedCommit, parse_paragraphs

from .data import GITMOJIS_CODE_DICT, GITMOJIS_DICT, get_emoji_regexp

logger = logging.getLogger(__name__)

LEVEL_BUMPS = {None: 0, "patch": 1, "minor": 2, "major": 3}


@LoggedFunction(logger)
def parse_commit_message(message: str) -> ParsedCommit:
    """Parse a commit using an emoji in the subject line.

    :param message: A string of a commit message.
    :return: A tuple of (level to bump, type of change, scope of change, a tuple with descriptions)
    """
    descriptions = parse_paragraphs(message)

    subject = descriptions[0]

    primary_emoji = next(
        (match.group() for match in get_emoji_regexp().finditer(subject.strip())),
        "other",
    )
    primary_emoji = primary_emoji.lower()

    logger.debug(f"Selected {primary_emoji} as the primary emoji")
    # Find which level this commit was from
    emoji_info = GITMOJIS_DICT.get(primary_emoji) or GITMOJIS_CODE_DICT.get(primary_emoji)
    level_bump = 0
    code = None
    if emoji_info:
        level_bump = LEVEL_BUMPS[emoji_info["semver"]]
        code = emoji_info["code"]

    return ParsedCommit(level_bump, code, None, descriptions, None)
