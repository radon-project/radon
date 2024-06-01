from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
from core.colortools import Log

if TYPE_CHECKING:
    from core.tokens import Position
    from core.parser import Context

#######################################
# ERRORS
#######################################


def string_with_arrows(text: str, pos_start: Position, pos_end: Position) -> str:
    """Return string with arrows"""
    result = "\n"
    # Calculate indices
    idx_start = max(text.rfind("\n", 0, pos_start.idx), 0)
    idx_end = text.find("\n", idx_start + 1)
    if idx_end < 0:
        idx_end = len(text)

    # Generate each line
    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[idx_start:idx_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        col_start_color = col_start  # + 1
        col_end_color = col_end + 1

        # Append to result
        line_text = f"{line[:col_start_color]}{Log.deep_error(line[col_start_color:col_end_color], bold=True)}{line[col_end_color:]}\n"
        lstripped_len = len(line_text) - len(line_text.lstrip()) - 1
        result += line_text.lstrip()
        result += " " * (col_start - lstripped_len) + Log.deep_error("^" * (col_end - col_start), bold=True)

        # Re-calculate indices
        idx_start = idx_end
        idx_end = text.find("\n", idx_start + 1)
        if idx_end < 0:
            idx_end = len(text)

    return result.replace("\t", "")


@dataclass
class Error:
    """Base Error class"""

    pos_start: Position
    pos_end: Position
    error_name: str
    details: Optional[str]

    def as_string(self) -> str:
        """Return error as string"""
        result = Log.light_purple("Radiation (most recent call last):\n")
        result += f"  File {Log.light_info(self.pos_start.fn)}, line {Log.light_info(str(self.pos_start.ln + 1))}\n"
        result += f"{Log.deep_error(self.error_name, bold=True)}"
        if self.details is not None:
            result += f": {Log.light_error(self.details)}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def set_pos(self, pos_start=None, pos_end=None):
        """Says it's gonna set the position, but actually does NOTHING"""
        return self

    def set_context(self, context=None):
        """Says it's gonna set the context, but actually does NOTHING"""
        return self

    def __repr__(self) -> str:
        if self.details is not None:
            return f"{self.error_name}: {self.details}"
        return self.error_name

    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.error_name, self.details)


class IllegalCharError(Error):
    """Illegal Character Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str) -> None:
        super().__init__(pos_start, pos_end, "IllegalCharacter", details)


class ExpectedCharError(Error):
    """Expected Character Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str) -> None:
        super().__init__(pos_start, pos_end, "ExpectedCharacter", details)


class InvalidSyntaxError(Error):
    """Invalid Syntax Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str = "") -> None:
        super().__init__(pos_start, pos_end, "InvalidSyntax", details)


class RTError(Error):
    """Runtime Error class"""

    context: Context

    def __init__(self, pos_start: Position, pos_end: Position, details: Optional[str], context: Context) -> None:
        super().__init__(pos_start, pos_end, "RuntimeError", details)
        self.context = context

    def as_string(self) -> str:
        """Return error as string"""
        result = self.generate_radiation()
        result += f"{Log.deep_error(self.error_name, bold=True)}"
        if self.details is not None:
            result += f": {Log.light_error(self.details)}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_radiation(self) -> str:
        """Generate traceback for runtime error"""
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = (
                f"  File {Log.light_info(pos.fn)}, line {Log.light_info(str(pos.ln + 1))}, in {Log.light_info(ctx.display_name)}\n"
                + result
            )
            pos = ctx.parent_entry_pos  # type: ignore
            ctx = ctx.parent  # type: ignore

        return Log.light_purple("Radiation (most recent call last):\n") + result

    def set_context(self, context=None):
        """Says it's gonna set the context, but actually does nothing"""
        return self

    def copy(self) -> RTError:
        return type(self)(self.pos_start, self.pos_end, self.details, self.context)


class TryError(RTError):
    prev_error: RTError

    def __init__(
        self, pos_start: Position, pos_end: Position, details: str, context: Context, prev_error: RTError
    ) -> None:
        super().__init__(pos_start, pos_end, details, context)
        self.prev_error = prev_error

    def generate_radiation(self) -> str:
        result = ""
        if self.prev_error:
            result += self.prev_error.as_string()
        result += Log.light_error("\nDuring the handling of the above error, another error occurred:\n\n")
        return result + super().generate_radiation()


class VError(RTError):
    """Value Error class"""

    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "ValueError", details)
        self.context = context
