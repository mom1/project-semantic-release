from functools import partial
from textwrap import dedent
from unittest import mock

import pytest

from semantic_release.changelog import markdown_changelog
from semantic_release.changelog.changelog import (
    add_pr_link,
    changelog_table,
    get_changelog_sections,
)
from semantic_release.changelog.compare import compare_url, get_github_compare_url
from semantic_release.changelog.handlers import add_mr_link_gitlab, get_hash_link

from . import wrapped_config_get


def test_markdown_changelog():
    assert markdown_changelog(
        "owner",
        "repo_name",
        "0",
        {
            "refactor": [("12", "Refactor super-feature")],
            "breaking": [("21", "Uses super-feature as default instead of dull-feature.")],
            "feature": [
                ("145", "Add non-breaking super-feature"),
                ("134", "Add super-feature"),
            ],
            "fix": [("234", "Fix bug in super-feature (#15)")],
            "documentation": [("0", "Document super-feature (#189)")],
            "performance": [],
        },
    ) == (
        # Expected output with the default configuration
        "### Feature\n"
        "* Add non-breaking super-feature ([`145`](https://github.com/owner/repo_name/"
        "commit/145))\n"
        "* Add super-feature ([`134`](https://github.com/owner/repo_name/commit/134))\n"
        "\n"
        "### Fix\n"
        "* Fix bug in super-feature ([#15](https://github.com/owner/repo_name/issues/15))"
        " ([`234`](https://github.com/owner/repo_name/"
        "commit/234))\n"
        "\n"
        "### Breaking\n"
        "* Uses super-feature as default instead of dull-feature."
        " ([`21`](https://github.com/owner/repo_name/commit/21))\n"
        "\n"
        "### Documentation\n"
        "* Document super-feature ([#189](https://github.com/owner/repo_name/issues/189))"
        " ([`0`](https://github.com/owner/repo_name/commit/0))"
    )


def test_markdown_changelog_gitlab():
    settings = wrapped_config_get(hvcs="gitlab")
    with mock.patch("semantic_release.changelog.changelog.config", settings), mock.patch(
        "semantic_release.changelog.config", settings
    ), mock.patch("semantic_release.settings.config", settings):
        assert markdown_changelog(
            "owner",
            "repo_name",
            "0",
            {
                "refactor": [("12", "Refactor super-feature")],
                "feature": [
                    ("145", "Add non-breaking super-feature (#1)"),
                    ("134", "Add super-feature"),
                ],
                "documentation": [("0", "Document super-feature (#189)")],
                "performance": [],
            },
        ) == (
            # Expected output with the default configuration
            "### Feature\n"
            "* Add non-breaking super-feature ([#1](https://gitlab.com/owner/"
            "repo_name/-/issues/1)) ([`145`](https://gitlab.com/owner/"
            "repo_name/-/commit/145))\n"
            "* Add super-feature ([`134`](https://gitlab.com/owner/repo_name/-/"
            "commit/134))\n"
            "\n"
            "### Documentation\n"
            "* Document super-feature ([#189](https://gitlab.com/owner/repo_name/"
            "-/issues/189)) ([`0`](https://gitlab.com/owner/repo_name/"
            "-/commit/0))"
        )


def test_markdown_changelog_template_gitlab(mocker):
    settings = wrapped_config_get(
        hvcs="gitlab",
        commit_analyzer="semantic_release.history.logs.get_commits",
        changelog_components=[
            "semantic_release.history.processing.changelog_processing",
            "semantic_release.history.grouping.changelog_grouping",
            "semantic_release.changelog.changelog.changelog_template",
        ],
    )
    mocker.patch("semantic_release.changelog.changelog.config", settings)
    mocker.patch("semantic_release.changelog.config", settings)
    mocker.patch("semantic_release.settings.config", settings)
    mocker.patch("semantic_release.changelog.handlers.config", settings)
    mocker.patch("semantic_release.history.logs.get_commit_log", lambda *a, **kw: [("", "...")])
    mocker.patch(
        "semantic_release.changelog.handlers.get_repository_owner_and_name", return_value=["owner", "repo_name"]
    )
    mocker.patch("semantic_release.vcs_helpers.get_repository_owner_and_name", return_value=["owner", "repo_name"])
    mocker.patch(
        "semantic_release.changelog.handlers.add_mr_link_gitlab",
        side_effect=partial(add_mr_link_gitlab, owner="owner", repo_name="repo_name"),
    )
    mocker.patch(
        "semantic_release.changelog.handlers.get_hash_link",
        side_effect=partial(get_hash_link, owner="owner", repo_name="repo_name"),
    )

    changelog = [
        {
            "commit": {
                "long": "145",
                "short": "145",
            },
            "tree": {
                "long": "",
                "short": "",
            },
            "author": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "committer": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "subject": "Add non-breaking super-feature (#1)",
            "body": "",
            "message": "feature: Add non-breaking super-feature (#1)",
            "committer_date": "2020-12-20",
            "type": "feature",
            "scope": None,
        },
        {
            "commit": {
                "long": "12",
                "short": "12",
            },
            "tree": {
                "long": "",
                "short": "",
            },
            "author": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "committer": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "subject": "Refactor super-feature",
            "body": "",
            "message": "feature: Refactor super-feature",
            "committer_date": "2020-12-20",
            "type": "refactor",
            "scope": None,
        },
        {
            "commit": {
                "long": "134",
                "short": "134",
            },
            "tree": {
                "long": "",
                "short": "",
            },
            "author": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "committer": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "subject": "Add super-feature",
            "body": "",
            "message": "feature: Add super-feature",
            "committer_date": "2020-12-20",
            "type": "feature",
            "scope": None,
        },
        {
            "commit": {
                "long": "0",
                "short": "0",
            },
            "tree": {
                "long": "",
                "short": "",
            },
            "author": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "committer": {
                "name": "test",
                "email": "test@test.test",
                "date": "2020-12-20",
            },
            "subject": "Document super-feature (#189)",
            "body": "",
            "message": "doc: Document super-feature (#189)",
            "committer_date": "2020-12-20",
            "type": "documentation",
            "scope": None,
        },
    ]
    assert markdown_changelog("owner", "repo_name", "0.0.0", changelog) == (
        # Expected output with the default configuration
        dedent(
            """### Feature
* Add non-breaking super-feature ([#1](https://gitlab.com/owner/repo_name/-/issues/1))\
 ([`145`](https://gitlab.com/owner/repo_name/-/commit/145))
* Add super-feature. ([`134`](https://gitlab.com/owner/repo_name/-/commit/134))

### Documentation
* Document super-feature ([#189](https://gitlab.com/owner/repo_name/-/issues/189))\
 ([`0`](https://gitlab.com/owner/repo_name/-/commit/0))"""
        )
    )


def test_changelog_table():
    assert changelog_table(
        "owner",
        "repo_name",
        {
            "feature": [("sha1", "commit1"), ("sha2", "commit2")],
            "fix": [("sha3", "commit3 (#123)")],
        },
        ["section1", "section2"],
    ) == (
        "| Type | Change |\n"
        "| --- | --- |\n"
        "| Feature | commit1 ([`sha1`](https://github.com/owner/repo_name/commit/sha1))"
        "<br>commit2 ([`sha2`](https://github.com/owner/repo_name/commit/sha2)) |\n"
        "| Fix | commit3 ([#123](https://github.com/owner/repo_name/issues/123))"
        " ([`sha3`](https://github.com/owner/repo_name/commit/sha3)) |\n"
    )


def test_should_not_output_heading():
    assert "v1.0.1" not in markdown_changelog(
        "owner",
        "repo_name",
        "1.0.1",
        {},
    )


def test_get_changelog_sections():
    assert (
        len(
            list(
                get_changelog_sections(
                    {
                        "refactor": [0, 1, 2],
                        "breaking": [],
                        "feature": [],
                        "fix": [],
                        "documentation": [],
                        "performance": [],
                    },
                    ["breaking", "feature", "fix", "performance"],
                )
            )
        )
        == 0
    )


@pytest.mark.parametrize(
    "message,hvcs,expected_output",
    [
        (
            "test (#123)",
            "github",
            "test ([#123](https://github.com/owner/name/issues/123))",
        ),
        ("test without commit", "github", "test without commit"),
        ("test (#123) in middle", "github", "test (#123) in middle"),
        (
            "test (#123)",
            "gitlab",
            "test ([#123](https://gitlab.com/owner/name/-/issues/123))",
        ),
        ("test without commit", "gitlab", "test without commit"),
    ],
)
def test_add_pr_link(message, hvcs, expected_output):
    settings = wrapped_config_get(hvcs=hvcs)
    with mock.patch("semantic_release.changelog.changelog.config", settings), mock.patch(
        "semantic_release.changelog.config", settings
    ), mock.patch("semantic_release.settings.config", settings):

        assert add_pr_link("owner", "name", message) == expected_output


def test_github_compare_url():
    with mock.patch(
        "semantic_release.changelog.compare.get_repository_owner_and_name",
        return_value=["owner", "name"],
    ):
        assert get_github_compare_url("1.0.0", "2.0.0") == "https://github.com/owner/name/compare/v1.0.0...v2.0.0"


def test_compare_url():
    with mock.patch(
        "semantic_release.changelog.compare.get_repository_owner_and_name",
        return_value=["owner", "name"],
    ):
        assert (
            compare_url(previous_version="1.0.0", version="2.0.0")
            == "https://github.com/owner/name/compare/v1.0.0...v2.0.0"
        )
