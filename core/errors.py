from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from core.tokens import Position
    from core.parser import Context

#######################################
# ERRORS
#######################################


def string_with_arrows(text: str, pos_start: Position, pos_end: Position) -> str:
    """Return string with arrows"""
    result = ""

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

        # Append to result
        result += line + "\n"
        result += " " * col_start + "^" * (col_end - col_start)

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
    details: str

    def as_string(self) -> str:
        """Return error as string"""
        result = f"{self.error_name}: {self.details}\n"
        result += f"File {self.pos_start.fn}, line {self.pos_start.ln + 1}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def set_pos(self, pos_start=None, pos_end=None):
        """Says it's gonna set the position, but actually does NOTHING"""
        return self

    def __repr__(self) -> str:
        return f"{self.error_name}: {self.details}"

    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.error_name, self.details)


class IllegalCharError(Error):
    """Illegal Character Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str) -> None:
        super().__init__(pos_start, pos_end, "Illegal Character", details)


class ExpectedCharError(Error):
    """Expected Character Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str) -> None:
        super().__init__(pos_start, pos_end, "Expected Character", details)


class InvalidSyntaxError(Error):
    """Invalid Syntax Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str = "") -> None:
        super().__init__(pos_start, pos_end, "Invalid Syntax", details)


class IndexError(Error):
    """Index Error class"""

    def __init__(self, pos_start: Position, pos_end: Position, details: str = "") -> None:
        super().__init__(pos_start, pos_end, "Index Error", details)


class RTError(Error):
    """Runtime Error class"""
    context: Context

    def __init__(self, pos_start: Position, pos_end: Position, details: str, context: Context) -> None:
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context

    def as_string(self) -> str:
        """Return error as string"""
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self) -> str:
        """Generate traceback for runtime error"""
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f"  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n" + result
            assert ctx.parent is not None
            assert ctx.parent_entry_pos is not None
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return "Traceback (most recent call last):\n" + result

    def set_context(self, context=None):
        """Says it's gonna set the context, but actually does nothing"""
        return self

    def copy(self) -> RTError:
        return type(self)(self.pos_start, self.pos_end, self.details, self.context)


class TryError(RTError):
    prev_error: RTError

    def __init__(self, pos_start: Position, pos_end: Position, details: str, context: Context, prev_error: RTError) -> None:
        super().__init__(pos_start, pos_end, details, context)
        self.prev_error = prev_error

    def generate_traceback(self) -> str:
        result = ""
        if self.prev_error:
            result += self.prev_error.as_string()
        result += "\nDuring the handling of the above error, another error occurred:\n\n"
        return result + super().generate_traceback()


class VError(RTError):
    """Value Error class"""

    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Value Error", details)
        self.context = context

