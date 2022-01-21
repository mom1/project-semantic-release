from ..changelog import handlers
from ..helpers import import_path
from ..settings import config


def get_handler(name: str, default: handlers.TextProc = handlers.noop):
    result_handler = default
    for handler in config.get(name, "").split(","):
        handler = handler.strip()
        if handler:
            result_handler |= getattr(handlers, handler, None) or import_path(handler)
    return result_handler


def get_body_handler():
    return get_handler("changelog_body_handlers")


def get_subject_handler():
    return get_handler("changelog_subject_handlers")


def changelog_processing(owner: str, repo_name: str, changelog: list, changelog_sections: list, **kwargs):
    """Processing subject and body.

    It will work only with `commit_analyzer=semantic_release.history.logs.get_commits`
    """
    subject_handler = get_subject_handler()
    body_handler = get_body_handler()
    for commit in changelog:
        commit["subject"] = subject_handler(commit["subject"])
        commit["body"] = body_handler(commit["body"])
