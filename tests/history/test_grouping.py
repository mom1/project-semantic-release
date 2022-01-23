from semantic_release.history.grouping import changelog_composite_grouping
from tests import wrapped_config_get


def test_changelog_composite_grouping(mocker):
    settings = wrapped_config_get(
        hvcs="gitlab",
        commit_analyzer="semantic_release.history.logs.get_commits",
        composite_groups=["group1", "group2"],
        composite_groups_group1="sub1,sub2",
        composite_groups_group2="sub3",
        changelog_components=[
            "semantic_release.history.processing.changelog_processing",
            "semantic_release.history.grouping.changelog_grouping",
            "semantic_release.changelog.changelog.changelog_template",
        ],
    )
    mocker.patch("semantic_release.history.grouping.config", settings)
    changelog = [{"type": "sub1"}, {"type": "sub2"}, {"type": "sub3"}, {"type": "sub4"}, {"type": "sub3"}]

    changelog_composite_grouping("owner", "repo_name", changelog)
    assert changelog == [
        {"section": "Group1", "commits_section": [{"type": "sub1"}, {"type": "sub2"}]},
        {"section": "Group2", "commits_section": [{"type": "sub3"}, {"type": "sub3"}]},
    ]
