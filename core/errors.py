from core.colortools import Log


def string_with_arrows(text, pos_start, pos_end):
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
        result += f"{line[:col_start]}{Log.deep_error(line[col_start:col_end], bold=True)}{line[col_end:]}\n"
        result += " " * col_start + Log.deep_error("^" * (col_end - col_start), bold=True)

        # Re-calculate indices
        idx_start = idx_end
        idx_end = text.find("\n", idx_start + 1)
        if idx_end < 0:
            idx_end = len(text)

    return result.replace("\t", "")


class Error:
    """Base Error class"""

    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
        self.value = details

    def as_string(self):
        """Return error as string"""
        result = Log.light_purple("Radiation (most recent call last):\n")
        result += f"  File {Log.deep_info(self.pos_start.fn)}, line {Log.deep_info(str(self.pos_start.ln + 1))}\n"
        result += f"{Log.deep_error(self.error_name, bold=True)}: {Log.light_error(self.details)}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def set_pos(self, pos_start=None, pos_end=None):
        return self

    def __repr__(self) -> str:
        return f"{self.error_name}: {self.details}"

    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.error_name, self.details)


class IllegalCharError(Error):
    """Illegal Character Error class"""

    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "IllegalCharacter", details)


class ExpectedCharError(Error):
    """Expected Character Error class"""

    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "ExpectedCharacter", details)


class InvalidSyntaxError(Error):
    """Invalid Syntax Error class"""

    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "InvalidSyntax", details)


class IndexError(Error):
    """Index Error class"""

    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "IndexError", details)


class RTError(Error):
    """Runtime Error class"""

    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "RuntimeError", details)
        self.context = context

    def as_string(self):
        """Return error as string"""
        result = self.generate_radiation()
        result += f"{Log.deep_error(self.error_name, bold=True)}: {Log.light_error(self.details)}"
        result += "\n" + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_radiation(self):
        """Generate traceback for runtime error"""
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f"  File {Log.deep_info(pos.fn)}, line {Log.deep_info(str(pos.ln + 1))}, in {Log.deep_info(ctx.display_name)}\n" + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return Log.light_purple("Radiation (most recent call last):\n") + result

    def set_context(self, context=None):
        return self

    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.details, self.context)


class TryError(RTError):
    def __init__(self, pos_start, pos_end, details, context, prev_error):
        super().__init__(pos_start, pos_end, details, context)
        self.prev_error = prev_error

    def generate_radiation(self):
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
