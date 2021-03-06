from unittest import mock

from semantic_release.history import evaluate_version_bump

from .. import wrapped_config_get
from . import (
    ALL_KINDS_OF_COMMIT_MESSAGES,
    MAJOR,
    MAJOR_MENTIONING_LAST_VERSION,
    MINOR,
    MINOR_AND_PATCH_COMMIT_MESSAGES,
    NO_TAG,
    PATCH_COMMIT_MESSAGES,
)


def test_major():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: ALL_KINDS_OF_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump("0.0.0") == "major"


def test_minor():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: MINOR_AND_PATCH_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump("0.0.0") == "minor"


def test_patch():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: PATCH_COMMIT_MESSAGES,
    ):
        assert evaluate_version_bump("0.0.0") == "patch"


def test_nothing_if_no_tag():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: [("", "...")],
    ):
        assert evaluate_version_bump("0.0.0") is None


def test_force():
    assert evaluate_version_bump("0.0.0", "major") == "major"
    assert evaluate_version_bump("0.0.0", "minor") == "minor"
    assert evaluate_version_bump("0.0.0", "patch") == "patch"


def test_should_not_skip_commits_mentioning_other_commits():
    with mock.patch(
        "semantic_release.history.logs.get_commit_log",
        lambda *a, **kw: MAJOR_MENTIONING_LAST_VERSION,
    ):
        assert evaluate_version_bump("1.0.0") == "major"


@mock.patch("semantic_release.history.logs.config", wrapped_config_get(patch_without_tag=True))
@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [MINOR])
def test_should_minor_with_patch_without_tag():
    assert evaluate_version_bump("1.1.0") == "minor"


@mock.patch("semantic_release.history.logs.config", wrapped_config_get(patch_without_tag=True))
@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [NO_TAG])
def test_should_patch_without_tagged_commits():
    assert evaluate_version_bump("1.1.0") == "patch"


@mock.patch("semantic_release.history.logs.config", wrapped_config_get(patch_without_tag=False))
@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [NO_TAG])
def test_should_return_none_without_tagged_commits():
    assert evaluate_version_bump("1.1.0") is None


@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [])
def test_should_return_none_without_commits():
    """Make sure that we do not release if there are no commits since last release."""
    with mock.patch(
        "semantic_release.history.logs.config", wrapped_config_get(patch_without_tag=True, major_on_zero=True)
    ):
        assert evaluate_version_bump("1.1.0") is None

    with mock.patch(
        "semantic_release.history.logs.config", wrapped_config_get(patch_without_tag=False, major_on_zero=False)
    ):
        assert evaluate_version_bump("1.1.0") is None


@mock.patch("semantic_release.history.logs.config", wrapped_config_get(major_on_zero=False))
@mock.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [MAJOR])
def test_should_minor_without_major_on_zero():
    assert evaluate_version_bump("0.1.0") == "minor"
