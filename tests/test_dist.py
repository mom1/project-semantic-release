from semantic_release.dist import build_dists, should_build, should_remove_dist

from . import pytest, wrapped_config_get


@pytest.mark.parametrize(
    "commands",
    ["sdist bdist_wheel", "sdist", "bdist_wheel", "sdist bdist_wheel custom_cmd"],
)
def test_build_command(mocker, commands):
    mocker.patch("semantic_release.dist.config", wrapped_config_get(build_command=commands))
    mock_run = mocker.patch("semantic_release.dist.run")
    build_dists()
    mock_run.assert_called_once_with(commands)


@pytest.mark.parametrize(
    "config,expected",
    [
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "python setup.py build",
            },
            True,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": False,
            },
            False,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": None,
            },
            False,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "",
            },
            False,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "false",
            },
            False,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": False,
                "upload_to_release": True,
                "build_command": "python setup.py build",
            },
            True,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "python setup.py build",
            },
            True,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": False,
                "upload_to_release": True,
                "build_command": "python setup.py build",
            },
            True,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": True,
                "upload_to_release": False,
                "build_command": "python setup.py build",
            },
            False,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": False,
                "upload_to_release": False,
                "build_command": "python setup.py build",
            },
            False,
        ),
    ],
)
def test_should_build(config, expected, mocker):
    settings = wrapped_config_get(**config)
    mocker.patch("semantic_release.cli.config", settings)
    mocker.patch("semantic_release.dist.config", settings)
    mocker.patch("semantic_release.repository.config", settings)
    assert should_build() == expected


@pytest.mark.parametrize(
    "config,expected",
    [
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "python setup.py build",
                "remove_dist": True,
            },
            True,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "python setup.py build",
                "remove_dist": True,
            },
            True,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": False,
                "upload_to_release": True,
                "build_command": "python setup.py build",
                "remove_dist": True,
            },
            True,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": False,
                "upload_to_release": False,
                "build_command": "python setup.py build",
                "remove_dist": True,
            },
            False,
        ),
        (
            {
                "upload_to_pypi": True,
                "upload_to_repository": True,
                "upload_to_release": True,
                "build_command": "python setup.py build",
                "remove_dist": False,
            },
            False,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": False,
                "upload_to_release": False,
                "build_command": False,
                "remove_dist": True,
            },
            False,
        ),
        (
            {
                "upload_to_pypi": False,
                "upload_to_repository": False,
                "upload_to_release": False,
                "build_command": "false",
                "remove_dist": True,
            },
            False,
        ),
    ],
)
def test_should_remove_dist(config, expected, mocker):
    settings = wrapped_config_get(**config)
    mocker.patch("semantic_release.cli.config", settings)
    mocker.patch("semantic_release.dist.config", settings)
    mocker.patch("semantic_release.repository.config", settings)
    assert should_remove_dist() == expected
