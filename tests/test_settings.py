import os
import platform
from textwrap import dedent
from unittest import TestCase

from semantic_release.errors import ImproperConfigurationError
from semantic_release.history import parser_angular
from semantic_release.settings import _config, import_from_settings

from . import mock, reset_config, wrapped_config_get

assert reset_config


# Set path to this directory
temp_dir = (
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "tmp") if platform.system() == "Windows" else "/tmp/"
)


class ConfigTests(TestCase):
    def test_config(self):
        config = _config()
        self.assertEqual(
            config.get("version_variable"),
            "semantic_release/__init__.py:__version__",
        )

    def test_defaults(self):
        config = _config()
        self.assertEqual(config.get("minor_tag"), ":sparkles:")
        self.assertEqual(config.get("fix_tag"), ":nut_and_bolt:")
        self.assertFalse(config.get("patch_without_tag"))
        self.assertTrue(config.get("major_on_zero"))
        self.assertFalse(config.get("check_build_status"))
        self.assertEqual(config.get("hvcs"), "github")
        self.assertEqual(config.get("upload_to_repository"), True)
        self.assertEqual(config.get("github_token_var"), "GH_TOKEN")
        self.assertEqual(config.get("gitlab_token_var"), "GL_TOKEN")
        self.assertEqual(config.get("pypi_pass_var"), "PYPI_PASSWORD")
        self.assertEqual(config.get("pypi_token_var"), "PYPI_TOKEN")
        self.assertEqual(config.get("pypi_user_var"), "PYPI_USERNAME")
        self.assertEqual(config.get("repository_user_var"), "REPOSITORY_USERNAME")
        self.assertEqual(config.get("repository_pass_var"), "REPOSITORY_PASSWORD")

    def test_toml_override(self):
        # create temporary toml config file
        dummy_conf_path = os.path.join(temp_dir, "pyproject.toml")
        os.makedirs(os.path.dirname(dummy_conf_path), exist_ok=True)
        toml_conf_content = """
[tool.foo]
bar = "baz"
[tool.semantic_release]
upload_to_repository = false
version_source = "tag"
foo = "bar"
"""
        with open(dummy_conf_path, "w") as dummy_conf_file:
            dummy_conf_file.write(toml_conf_content)

        config = _config(temp_dir)
        self.assertEqual(config.get("hvcs"), "github")
        self.assertEqual(config.get("upload_to_repository"), False)
        self.assertEqual(config.get("version_source"), "tag")
        self.assertEqual(config.get("foo"), "bar")

        # delete temporary toml config file
        os.remove(dummy_conf_path)

    def test_toml_no_psr_section(self):
        # create temporary toml config file
        dummy_conf_path = os.path.join(temp_dir, "pyproject.toml")
        toml_conf_content = dedent(
            """
            [tool.foo]
            bar = "baz"
            """
        )
        os.makedirs(os.path.dirname(dummy_conf_path), exist_ok=True)

        with open(dummy_conf_path, "w") as dummy_conf_file:
            dummy_conf_file.write(toml_conf_content)

        config = _config()
        self.assertEqual(config.get("hvcs"), "github")
        # delete temporary toml config file
        os.remove(dummy_conf_path)

    @mock.patch("semantic_release.settings.config", wrapped_config_get(commit_parser="nonexistent.parser"))
    def test_current_commit_parser_should_raise_error_if_parser_module_do_not_exist(
        self,
    ):
        self.assertRaises(ImproperConfigurationError, lambda: import_from_settings("commit_parser"))

    @mock.patch("semantic_release.settings.config", wrapped_config_get(commit_parser="semantic_release.not_a_parser"))
    def test_current_commit_parser_should_raise_error_if_parser_do_not_exist(self):
        self.assertRaises(ImproperConfigurationError, lambda: import_from_settings("commit_parser"))

    def test_current_commit_parser_should_return_correct_parser(self):
        self.assertEqual(import_from_settings("commit_parser"), parser_angular.parse_commit_message)
