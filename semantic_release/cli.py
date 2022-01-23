"""CLI."""
import logging
import os
import sys
from pathlib import Path

import click
import click_log

from semantic_release import ci_checks
from semantic_release.errors import GitError, ImproperConfigurationError

from .changelog import markdown_changelog
from .dist import build_dists, remove_dists, should_build, should_remove_dist
from .history import (
    evaluate_version_bump,
    get_current_version,
    get_new_version,
    get_previous_version,
    set_new_version,
)
from .hvcs import (
    check_build_status,
    check_token,
    get_domain,
    get_token,
    post_changelog,
    post_pull_request,
    upload_to_release,
)
from .repository import ArtifactRepo
from .settings import config, import_from_settings, overload_configuration
from .vcs_helpers import (
    checkout,
    commit_new_version,
    get_current_head_hash,
    get_repository_owner_and_name,
    push_new_version,
    tag_new_version,
    update_changelog_file,
)

logger = logging.getLogger("semantic_release")

TOKEN_VARS = [
    "github_token_var",
    "gitlab_token_var",
    "pypi_pass_var",
    "pypi_token_var",
    "pypi_user_var",
    "repository_user_var",
    "repository_pass_var",
]

COMMON_OPTIONS = [
    click_log.simple_verbosity_option(logger),
    click.option("--major", "force_level", flag_value="major", help="Force major version."),
    click.option("--minor", "force_level", flag_value="minor", help="Force minor version."),
    click.option("--patch", "force_level", flag_value="patch", help="Force patch version."),
    click.option("--post", is_flag=True, help="Post changelog."),
    click.option("--retry", is_flag=True, help="Retry the same release, do not bump."),
    click.option(
        "--noop",
        is_flag=True,
        help="No-operations mode, finds the new version number without changing it.",
    ),
    click.option(
        "--define",
        "-D",
        multiple=True,
        help='setting="value", override a configuration value.',
    ),
    overload_configuration,
]


def common_options(func):
    """Decorator that adds all the options in COMMON_OPTIONS."""
    for option in reversed(COMMON_OPTIONS):
        func = option(func)
    return func


def print_version(*, current=False, force_level=None, **_):
    """Print the current or new version to standard output."""
    try:
        current_version = get_current_version()
    except GitError as e:
        print(str(e), file=sys.stderr)
        return False
    if current:
        print(current_version, end="")
        return True

    # Find what the new version number should be
    level_bump = evaluate_version_bump(current_version, force_level)
    new_version = get_new_version(current_version, level_bump)
    if should_bump_version(current_version=current_version, new_version=new_version):
        print(new_version, end="")
        return True

    print("No release will be made.", file=sys.stderr)
    return False


def version(*, retry=False, noop=False, force_level=None, **_):
    """Detect the new version according to git log and semver.

    Write the new version number and commit it, unless the noop option is True.
    """
    if retry:
        logger.info("Retrying publication of the same version")
    else:
        logger.info("Creating new version")

    # Get the current version number
    try:
        current_version = get_current_version()
        logger.info(f"Current version: {current_version}")
    except GitError as e:
        logger.error(str(e))
        return False
    # Find what the new version number should be
    level_bump = evaluate_version_bump(current_version, force_level)
    new_version = get_new_version(current_version, level_bump)

    if not should_bump_version(current_version=current_version, new_version=new_version, retry=retry, noop=noop):
        return False

    if retry:
        # No need to make changes to the repo, we're just retrying.
        return True

    # Bump the version
    bump_version(new_version, level_bump)
    return True


def should_bump_version(*, current_version, new_version, retry=False, noop=False):
    """Test whether the version should be bumped."""
    if new_version == current_version and not retry:
        logger.info("No release will be made.")
        return False

    if noop:
        logger.warning("No operation mode. Should have bumped " f"from {current_version} to {new_version}")
        return False

    if config.get("check_build_status"):
        logger.info("Checking build status...")
        owner, name = get_repository_owner_and_name()
        if not check_build_status(owner, name, get_current_head_hash()):
            logger.warning("The build failed, cancelling the release")
            return False
        logger.info("The build was a success, continuing the release")

    return True


def bump_version(new_version, level_bump):
    """Set the version to the given `new_version`.

    Edit in the source code, commit and create a git tag.
    """
    set_new_version(new_version)
    if config.get("commit_version_number", config.get("version_source") == "commit"):
        commit_new_version(new_version)
    if config.get("version_source") == "tag" or config.get("tag_commit"):
        tag_new_version(new_version)

    logger.info(f"Bumping with a {level_bump} version to {new_version}")


def changelog(*, unreleased=False, noop=False, post=False, **_):
    """Generate the changelog since the last release.

    :raises ImproperConfigurationError: if there is no current version
    """
    current_version = get_current_version()
    if current_version is None:
        raise ImproperConfigurationError(
            "Unable to get the current version. " "Make sure semantic_release.version_variable " "is setup correctly"
        )

    previous_version = get_previous_version(current_version)
    commit_analyzer = import_from_settings("commit_analyzer")
    # Generate the changelog
    if unreleased:
        log = commit_analyzer(current_version, None)
    else:
        log = commit_analyzer(previous_version, current_version)

    owner, name = get_repository_owner_and_name()
    # print is used to keep the changelog on stdout, separate from log messages
    print(markdown_changelog(owner, name, current_version, log))

    # Post changelog to HVCS if enabled
    if not noop and post:
        if check_token():
            logger.info("Posting changelog to HVCS")
            post_changelog(
                owner,
                name,
                current_version,
                markdown_changelog(owner, name, current_version, log),
            )
        else:
            logger.error("Missing token: cannot post changelog to HVCS")


def publish(retry: bool = False, noop: bool = False, **kwargs):
    """Run the version task, then push to git and upload to an artifact repository / GitHub Releases."""
    current_version = get_current_version()

    verbose = logger.isEnabledFor(logging.DEBUG)
    if retry:
        logger.info("Retry is on")
        # The "new" version will actually be the current version, and the
        # "current" version will be the previous version.
        level_bump = None
        new_version = current_version
        current_version = get_previous_version(current_version)
    else:
        # Calculate the new version
        level_bump = evaluate_version_bump(current_version, kwargs.get("force_level"))
        new_version = get_new_version(current_version, level_bump)

    owner, name = get_repository_owner_and_name()

    branch = config.get("branch")
    logger.debug(f"Running publish on branch {branch}")
    ci_checks.check(branch)
    checkout(branch)

    if should_bump_version(
        current_version=current_version,
        new_version=new_version,
        retry=retry,
        noop=noop,
    ):
        commit_analyzer = import_from_settings("commit_analyzer")
        log = commit_analyzer(current_version)
        changelog_md = markdown_changelog(
            owner,
            name,
            new_version,
            log,
            previous_version=current_version,
        )

        if not retry:
            update_changelog_file(new_version, changelog_md)
            bump_version(new_version, level_bump)
        # A new version was released
        logger.info("Pushing new version")
        push_new_version(
            auth_token=get_token(),
            owner=owner,
            name=name,
            branch=branch,
            domain=get_domain(),
        )

        # Get config options for uploads
        dist_path = config.get("dist_path")
        upload_release = config.get("upload_to_release")

        if should_build():
            # We need to run the command to build wheels for releasing
            logger.info("Building distributions")
            if should_remove_dist():
                # Remove old distributions before building
                remove_dists(dist_path)
            build_dists()

        if ArtifactRepo.upload_enabled():
            logger.info("Uploading to artifact Repository")
            ArtifactRepo(Path(dist_path)).upload(noop=noop, verbose=verbose, skip_existing=retry)

        if check_token():
            # Update changelog on HVCS
            logger.info("Posting changelog to HVCS")
            try:
                post_changelog(owner, name, new_version, changelog_md)
            except GitError:
                logger.error("Posting changelog failed")
        else:
            logger.warning("Missing token: cannot post changelog to HVCS")

        # Upload to GitHub Releases
        if upload_release:
            if check_token():
                logger.info("Uploading to HVCS release")
                upload_to_release(owner, name, new_version, dist_path)
                logger.info("Upload to HVCS is complete")
            else:
                logger.warning("Missing token: cannot upload to HVCS")

        # Remove distribution files as they are no longer needed
        if should_remove_dist():
            logger.info("Removing distribution files")
            remove_dists(dist_path)

        logger.info("Publish has finished")

    # else: Since version shows a message on failure, we do not need to print another.


def merge_request(
    title: str = "",
    commit_prefix: str = "",
    source_branch: str = "",
    target_branch: str = "",
    **kwargs,
):
    """Creates a pull request with a changes between branches.

    Now works only with `semantic_release.history.logs.get_commits`
    """
    target_branch = target_branch or config.get("branch")
    mr_title = title or source_branch
    if commit_prefix:
        mr_title = f"{commit_prefix}: {mr_title}"

    owner, name = get_repository_owner_and_name()
    commit_analyzer = import_from_settings("commit_analyzer")
    log = commit_analyzer(None, None, f"{source_branch}...{target_branch or ''}")

    return post_pull_request(
        owner=owner,
        repository=name,
        changelog=markdown_changelog(owner, name, get_current_version(), log),
        title=mr_title,
        source_branch=source_branch,
        target_branch=target_branch,
        **kwargs,
    )


def filter_output_for_secrets(message):
    """Remove secrets from cli output."""
    output = message
    for token_var in TOKEN_VARS:
        secret_name = config.get(token_var)
        secret = os.environ.get(secret_name)
        if secret != "" and secret is not None:
            output = output.replace(secret, f"${secret_name}")

    return output


def entry():
    # Move flags to after the command
    args = sorted(sys.argv[1:], key=lambda x: 1 if x.startswith("--") else -1)

    if args and not args[0].startswith("print-"):
        # print-* command output should not be polluted with logging.
        click_log.basic_config()

    main(args=args)


#
# Making the CLI commands.
# We have a level of indirection to the logical commands
# so we can successfully mock them during testing
#


@click.group()
@common_options
def main(**kwargs):
    logger.debug(f"Main args: {kwargs}")
    message = ""
    for token_var in TOKEN_VARS:
        secret_name = config.get(token_var)
        message += f'{secret_name}="{os.environ.get(secret_name)}",'
    logger.debug(f"Environment: {filter_output_for_secrets(message)}")

    obj = {}
    for key in [
        "check_build_status",
        "commit_subject",
        "commit_message",
        "commit_parser",
        "patch_without_tag",
        "major_on_zero",
        "upload_to_pypi",
        "upload_to_repository",
        "version_source",
        "no_git_tag",
    ]:
        obj[key] = config.get(key)
    logger.debug(f"Main config: {obj}")


@main.command(name="publish", help=publish.__doc__)
@common_options
def cmd_publish(**kwargs):
    try:
        return publish(**kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(str(error)))
        exit(1)


@main.command(name="changelog", help=changelog.__doc__)
@common_options
@click.option(
    "--unreleased/--released",
    help="Decides whether to show the released or unreleased changelog.",
)
def cmd_changelog(**kwargs):
    try:
        return changelog(**kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(str(error)))
        exit(1)


@main.command(name="version", help=version.__doc__)
@common_options
def cmd_version(**kwargs):
    try:
        return version(**kwargs)
    except Exception as error:
        logger.error(filter_output_for_secrets(str(error)))
        exit(1)


@main.command(name="print-version", help=print_version.__doc__)
@common_options
@click.option(
    "--current/--next",
    default=False,
    help="Choose to output next version (default) or current one.",
)
def cmd_print_version(**kwargs):
    try:
        return print_version(**kwargs)
    except Exception as error:
        print(filter_output_for_secrets(str(error)), file=sys.stderr)
        exit(1)


@main.command(name="merge_request", help=merge_request.__doc__)
@click.option(
    "--source-branch",
    envvar="CI_COMMIT_REF_NAME",
    required=True,
    help="The source branch to merge into.",
)
@click.option(
    "--target-branch",
    "-t",
    envvar="CI_DEFAULT_BRANCH",
    help="The target branch to merge onto.",
)
@click.option(
    "--user-id",
    envvar="GITLAB_USER_ID",
    required=True,
    type=int,
    multiple=True,
    help="The GitLab user ID(s) to assign the created MR to.",
)
@click.option("--commit-prefix", "-c", default="WIP", help="Prefix for the MR title i.e. WIP.")
@click.option(
    "--remove-branch",
    "-r",
    is_flag=True,
    help="If set will remove the source branch after MR.",
)
@click.option("--squash-commits", "-s", is_flag=True, help="If set will squash commits on merge.")
@click.option("--title", type=str, help="Custom tile for the MR.")
@click.option(
    "--allow-collaboration",
    "-a",
    is_flag=True,
    help="If set allow, commits from members who can merge to the target branch.",
)
@click.option("--insecure", "-k", is_flag=True, help="Do not verify server SSL certificate.")
def cmd_merge_request(**kwargs):
    try:
        return merge_request(**kwargs)
    except Exception as error:
        print(filter_output_for_secrets(str(error)), file=sys.stderr)
        exit(1)
