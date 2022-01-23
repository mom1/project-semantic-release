import pytest

from semantic_release.changelog.handlers import (
    add_mr_link_gitlab,
    add_pr_link,
    add_pr_link_github,
    capitalize,
    demojize,
    drop,
    emojize,
    final_dot,
    indent,
    noop,
    remove_emoji,
    strip,
)
from semantic_release.errors import SemanticReleaseBaseError
from semantic_release.vcs_helpers import get_repository_owner_and_name

owner, name = get_repository_owner_and_name()


@pytest.mark.parametrize(
    "func,param,expect",
    [
        pytest.param(noop, "test", "test", id="noop"),
        pytest.param(strip, " test ", "test", id="strip"),
        pytest.param(drop, "test", "", id="drop"),
        pytest.param(final_dot, "test", "test.", id="final_dot"),
        pytest.param(capitalize, "title", "Title", id="capitalize"),
        pytest.param(capitalize, "Title", "Title", id="capitalize"),
        pytest.param(capitalize, "tiTle", "TiTle", id="capitalize"),
        pytest.param(demojize, "👌", ":ok_hand:", id="demojize"),
        pytest.param(emojize, ":ok_hand:", "👌", id="emojize"),
        pytest.param(remove_emoji, ":ok_hand:", "", id="remove_emoji"),
    ],
)
def test_noop(func, param, expect):
    assert func(param) == expect


@pytest.mark.parametrize(
    "message,first,expected_output",
    [
        ("- Sample text\n\nwithout ident", None, "  - Sample text\n\n  without ident"),
        (
            "- Sample text\n\n  without ident",
            None,
            "  - Sample text\n\n    without ident",
        ),
        ("Sample text\n\nwithout ident", "- ", "- Sample text\n\n  without ident"),
    ],
)
def test_indent(message, first, expected_output):
    assert indent(message, first=first) == expected_output


def test_repr_or():
    proc = strip | add_mr_link_gitlab
    assert repr(proc) == "'strip | add_mr_link_gitlab'"
    assert proc(" test ") == "test"


def test_or_error():
    with pytest.raises(SemanticReleaseBaseError):
        strip | 1


@pytest.mark.parametrize(
    "message,expected_output",
    [
        (
            "test (#123)",
            f"test ([#123](https://gitlab.com/{owner}/{name}/-/issues/123))",
        ),
        ("test without commit", "test without commit"),
    ],
)
def test_add_mr_link_gitlab(message, expected_output, mocker):
    with mocker.patch(
        "semantic_release.vcs_helpers.get_repository_owner_and_name",
        return_value=[owner, name],
    ):

        assert add_mr_link_gitlab(message) == expected_output


@pytest.mark.parametrize(
    "message,expected_output",
    [
        ("test (#123)", f"test ([#123](https://github.com/{owner}/{name}/issues/123))"),
        ("test without commit", "test without commit"),
        ("test (#123) in middle", "test (#123) in middle"),
    ],
)
def test_add_pr_link_github(message, expected_output, mocker):
    with mocker.patch(
        "semantic_release.vcs_helpers.get_repository_owner_and_name",
        return_value=[owner, name],
    ):

        assert add_pr_link_github(message) == expected_output
        assert add_pr_link(message) == expected_output
