import re
from typing import AnyStr, Callable, Optional, Pattern, Union

from semantic_release.errors import SemanticReleaseBaseError
from semantic_release.hvcs import Github, Gitlab
from semantic_release.vcs_helpers import get_repository_owner_and_name

from ..settings import config


class TextProc:
    __slots__ = ("fun", "__name__")

    def __init__(self, fun: Callable[[str], str]):
        self.fun = fun
        if hasattr(fun, "__name__"):
            self.__name__ = fun.__name__

    def __call__(self, text: str, *args, **kwargs):
        return self.fun(text, *args, **kwargs)

    def __or__(self, value: Union["TextProc", "ReSub"]):
        if not isinstance(value, (TextProc, ReSub)):
            raise SemanticReleaseBaseError(f"Only TextProc type allowed, but get {type(value)}")

        def wrap(msg):
            return value.fun(self.fun(msg))

        wrap.__name__ = f"{self.__name__} | {value.__name__}"
        return TextProc(wrap)

    def __repr__(self) -> str:
        return f"'{self.__name__}'"


class ReSub:
    __slots__ = ("compile_pattern", "func", "__name__", "kwargs")

    def __init__(self, pattern: Union[AnyStr, Pattern[AnyStr]], flags=None, **kwargs):
        self.compile_pattern: Pattern = re.compile(pattern, flags=flags or re.I)
        self.kwargs = kwargs
        self.__name__ = "ReSub"

    def __call__(self, func: Callable, *args, **kwargs):
        self.func = func

        def run(text: str, *run_args, **run_kwargs):
            return self.func(
                text,
                self.compile_pattern,
                *[*args, *run_args],
                **{**self.kwargs, **kwargs, **run_kwargs},
            )

        if hasattr(func, "__name__"):
            run.__name__ = func.__name__

        return TextProc(run)


@ReSub(
    r"\s+\(#(\d{1,8})\)$",
    **dict(zip(("owner", "repo_name"), get_repository_owner_and_name())),
)
def add_mr_link_gitlab(msg: str, pattern: Pattern, owner="", repo_name=""):
    match = pattern.search(msg)
    if match:
        pr_number = match.group(1)
        url = f"https://{Gitlab.domain()}/{owner}/{repo_name}/-/issues/{pr_number}"

        return pattern.sub(f" ([#{pr_number}]({url}))", msg)
    return msg


@ReSub(
    r"\s+\(#(\d{1,8})\)$",
    **dict(zip(("owner", "repo_name"), get_repository_owner_and_name())),
)
def add_pr_link_github(msg: str, pattern: Pattern, owner="", repo_name=""):
    match = pattern.search(msg)
    if match:
        pr_number = match.group(1)
        url = f"https://{Github.domain()}/{owner}/{repo_name}/issues/{pr_number}"

        return pattern.sub(f" ([#{pr_number}]({url}))", msg)
    return msg


@TextProc
def add_pr_link(msg: str):
    if config.get("hvcs") == "gitlab":
        return add_mr_link_gitlab(msg)
    return add_pr_link_github(msg)


@TextProc
def capitalize(msg: str):
    """Capitalize the first letter.

    using str.capitalize() would make the other letters lowercase

    title -> Title
    Title -> Title
    tiTle -> TiTle
    """

    return msg and f"{msg[0].upper()}{msg[1:]}" or msg


@TextProc
def final_dot(msg: str):
    """Add dot at end if need.

    title -> title. title: -> title:
    """
    return msg and msg[-1].isalnum() and f"{msg}." or msg


@TextProc
def indent(text: str, chars: str = "  ", first: Optional[str] = None):
    """Ident text.

    |- Sample text|  - Sample text
    |             |
    |without ident|  without ident
    """
    split_text = text.split("\n")
    if first:
        first_line = split_text[0]
        rest = "\n".join(split_text[1:])
        return "\n".join(((f"{first}{first_line}").rstrip(), indent(rest, chars=chars)))
    return "\n".join((f"{chars}{line}").rstrip() for line in split_text)


@TextProc
def strip(msg: str):
    """strip.

    ' 123 ' -> '123'
    """
    return msg and msg.strip() or msg


@TextProc
def noop(msg: str):
    return msg


@TextProc
def drop(_):
    return ""


try:
    import emoji
except ImportError:
    pass
else:

    @TextProc
    def demojize(msg: str):
        """demojize.

        ♻️ -> :recycle:
        """
        return msg and emoji.demojize(msg, use_aliases=True) or msg

    @TextProc
    def emojize(msg: str):
        """emojize.

        :recycle: -> ♻️
        """
        return msg and emoji.emojize(msg, use_aliases=True) or msg

    @ReSub(r"(:([\w_]+):)\s?")
    def remove_emoji(msg: str, pattern: Pattern[str]):
        """remove_emoji.

        :recycle: -> ''
        """
        return pattern.sub("", msg)


try:
    import chevron  # noqa: F401
except ImportError:
    pass
else:

    @ReSub("", **dict(zip(("owner", "repo_name"), get_repository_owner_and_name())))
    def get_hash_link(msg: str, _, render, owner="", repo_name="") -> str:
        """Generate the link for commit hash.

        Designed to run in a template
        """
        hash_ = render(msg)
        url = (
            f"https://{Gitlab.domain()}/{owner}/{repo_name}/-/commit/{hash_}"
            if config.get("hvcs") == "gitlab"
            else f"https://{Github.domain()}/{owner}/{repo_name}/commit/{hash_}"
        )
        return url
