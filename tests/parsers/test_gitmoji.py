from semantic_release.history import gitmoji_parser


def test_major():
    commit = ":boom: Breaking changes\n\n" "More description\n\n" "Even more description"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 3
    assert parsed_commit.type == ":boom:"
    assert parsed_commit.scope is None
    assert parsed_commit.descriptions == [
        ":boom: Breaking changes",
        "More description",
        "Even more description",
    ]
    assert parsed_commit.breaking_descriptions is None


def test_minor():
    commit = ":sparkles: Add a new feature\n\n" "Some description of the feature"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 2
    assert parsed_commit.type == ":sparkles:"
    assert parsed_commit.scope is None
    assert parsed_commit.descriptions == [
        ":sparkles: Add a new feature",
        "Some description of the feature",
    ]
    assert parsed_commit.breaking_descriptions is None


def test_patch():
    commit = ":bug: Fixing a bug\n\n" "The bug is finally gone!"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 1
    assert parsed_commit.type == ":bug:"
    assert parsed_commit.descriptions == [":bug: Fixing a bug", "The bug is finally gone!"]
    assert parsed_commit.breaking_descriptions is None


def test_other_emoji():
    commit = ":pencil: Documentation changes"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 0
    assert parsed_commit.type is None
    assert parsed_commit.descriptions == [":pencil: Documentation changes"]
    assert parsed_commit.breaking_descriptions is None


def test_multiple_emojis():
    commit = ":sparkles::pencil: Add a feature and document it"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 2
    assert parsed_commit.type == ":sparkles:"
    assert parsed_commit.descriptions == [":sparkles::pencil: Add a feature and document it"]
    assert parsed_commit.breaking_descriptions is None


def test_emoji_in_description():
    commit = ":sparkles: Add a new feature\n\n" ":boom: should not be detected"
    parsed_commit = gitmoji_parser(commit)
    assert parsed_commit.bump == 2
    assert parsed_commit.type == ":sparkles:"
    assert parsed_commit.descriptions == [
        ":sparkles: Add a new feature",
        ":boom: should not be detected",
    ]
    assert parsed_commit.breaking_descriptions is None
