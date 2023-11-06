from __future__ import annotations

from typing import TYPE_CHECKING
import dataclasses

from typing import Any, Dict, Optional, Type

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from thoughtspot_tml.types import TMLObject, GUID
    from yaml import error


class TMLError(Exception):
    """
    All errors in thoughtspot_tml derive from this Exception.
    """


class TMLExtensionWarning(UserWarning):
    """
    Alerts when a user saves a TML file without the proper extension.
    """


class MissingGUIDMappedValueWarning(UserWarning):
    """
    Alerts when a GUID mapping is generated, but is missing across environments.
    """


class TMLDecodeError(TMLError):
    """
    Raised when a TML object cannot be instantiated from input data.
    """

    def __init__(
        self,
        tml_cls: Type[TMLObject],
        *,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        path: Optional[Path] = None,
        problem_mark: Optional[error.Mark] = None,
    ):  # pragma: no cover
        self.tml_cls = tml_cls
        self.message = message
        self.data = data
        self.path = path
        self.problem_mark = problem_mark

    def __str__(self) -> str:
        lines = []
        class_name = self.tml_cls.__name__

        if self.message is not None:
            lines.append(self.message)

        if self.data is not None:
            lines.append(f"supplied data does not produce a valid TML ({class_name}) document")
            fields = {f.name for f in dataclasses.fields(self.tml_cls)}
            data = set(self.data)

            if data.difference(fields):
                extra = ", ".join([f"'{arg}'" for arg in data.difference(fields)])
                lines.append(f"\ngot extra data: {extra}")

        if self.path is not None:
            lines.append(f"'{self.path}' is not a valid TML ({class_name}) file")

        if self.problem_mark is not None:
            err_line = self.problem_mark.line + 1
            err_column = self.problem_mark.column + 1
            snippet = self.problem_mark.get_snippet()
            lines.append(f"\nsyntax error on line {err_line}, around column {err_column}")

            if snippet is not None:
                lines.append(snippet)

        return "\n".join(lines)


class TMLDisambiguationError(TMLError):
    """
    Raised when a TML file (or files) does not have the FQN property.
    """

    def __init__(self, tml_guids: Iterable[GUID]):
        self.tml_guids = tml_guids

    def __str__(self) -> str:
        guids = ", ".join(self.tml_guids)
        return f"No FQN found on: {guids}, was metadata/tml/export ran with parameter: export_fqn = true ?"
