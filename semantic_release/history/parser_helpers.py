"""Commit parser helpers."""
import collections
import re
from typing import List

re_breaking = re.compile("BREAKING[ -]CHANGE: ?(.*)")


ParsedCommit = collections.namedtuple(
    "ParsedCommit", ["bump", "type", "scope", "descriptions", "breaking_descriptions"]
)


def parse_paragraphs(text: str) -> List[str]:
    """This will take a text block and return a list containing each paragraph.

    :param text: The text string to be divided.
    :return: A list of paragraphs.
    """
    return [paragraph for paragraph in text.split("\n\n") if paragraph]
