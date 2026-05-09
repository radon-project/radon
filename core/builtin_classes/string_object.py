from core.builtin_classes.base_classes import BuiltInObject, check, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class StringObject(BuiltInObject):
    """Buili-in String manipulation object."""

    @operator("__constructor__")
    @check([String], [String("")])
    def constructor(self, string: String) -> RTResult[Value]:
        self.value: str = string.value
        return RTResult[Value]().success(Null.null())

    @operator("__add__")
    @check([String])
    def add(self, other: String) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value + other.value))

    def __string_display__(self) -> str:
        """This method helps __repr__ to display as we want."""
        return self.value

    def __len__(self) -> int:
        """Return the length of string."""
        return len(self.value)

    @args([])
    @method
    def upper(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value.upper()))

    @args([])
    @method
    def lower(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value.lower()))

    @args([])
    @method
    def title(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value.title()))

    @args([])
    @method
    def capitalize(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value.capitalize()))

    @args([])
    @method
    def swapcase(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(String(self.value.swapcase()))

    @args([])
    @method
    def length(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(Number(len(self.value)))

    @args(["string"], [String("")])
    @method
    def count(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(RTError(string.pos_start, string.pos_end, "Cannot count a non-string", string.context))
        if len(string.value) == 0:
            return res.failure(
                RTError(string.pos_start, string.pos_end, "Cannot count an empty string", string.context)
            )
        return res.success(Number(self.value.count(string.value)))

    @args(["string", "value"], [String(""), String("")])
    @method
    def replace(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(RTError(string.pos_start, string.pos_end, "Cannot replace a non-string", string.context))
        value = ctx.symbol_table.get("value")
        assert value is not None
        if not isinstance(value, String):
            return res.failure(RTError(value.pos_start, value.pos_end, "Cannot replace a non-string", value.context))
        return res.success(String(self.value.replace(string.value, value.value)))

    @args(["string"], [String("")])
    @method
    def find(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(RTError(string.pos_start, string.pos_end, "Cannot find a non-string", string.context))
        return res.success(Number(self.value.find(string.value)))

    @args(["string"], [String("")])
    @method
    def startswith(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(
                RTError(string.pos_start, string.pos_end, "Cannot startswith a non-string", string.context)
            )
        return res.success(Boolean(self.value.startswith(string.value)))

    @args(["string"], [String("")])
    @method
    def endswith(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(
                RTError(string.pos_start, string.pos_end, "Cannot endswith a non-string", string.context)
            )
        return res.success(Boolean(self.value.endswith(string.value)))

    @args(["separator"], [Null.null()])
    @method
    def split(self, ctx: Context) -> RTResult[Value]:
        """Split the string by separator. If no separator, splits on whitespace."""
        res = RTResult[Value]()
        separator = ctx.symbol_table.get("separator")
        assert separator is not None
        if isinstance(separator, Null):
            # No separator - split on whitespace
            return res.success(Array([String(i) for i in self.value.split()]))
        if not isinstance(separator, String):
            return res.failure(RTError(separator.pos_start, separator.pos_end, "Separator must be a string", separator.context))
        return res.success(Array([String(i) for i in self.value.split(separator.value)]))

    @args(["array"])
    @method
    def join(self, ctx: Context) -> RTResult[Value]:
        """Join an array of strings with this string as separator."""
        res = RTResult[Value]()
        arr = ctx.symbol_table.get("array")
        assert arr is not None
        if not isinstance(arr, Array):
            return res.failure(RTError(arr.pos_start, arr.pos_end, "Argument must be an array", arr.context))
        str_parts = []
        for elem in arr.elements:
            if isinstance(elem, String):
                str_parts.append(elem.value)
            else:
                str_parts.append(str(elem))
        return res.success(String(self.value.join(str_parts)))

    @args(["chars"], [Null.null()])
    @method
    def strip(self, ctx: Context) -> RTResult[Value]:
        """Strip whitespace (or given chars) from both ends."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            # No chars - strip whitespace
            return res.success(String(self.value.strip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", chars.context))
        if chars.value:
            return res.success(String(self.value.strip(chars.value)))
        return res.success(String(self.value.strip()))

    @args(["chars"], [Null.null()])
    @method
    def lstrip(self, ctx: Context) -> RTResult[Value]:
        """Strip whitespace (or given chars) from the left."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            return res.success(String(self.value.lstrip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", chars.context))
        if chars.value:
            return res.success(String(self.value.lstrip(chars.value)))
        return res.success(String(self.value.lstrip()))

    @args(["chars"], [Null.null()])
    @method
    def rstrip(self, ctx: Context) -> RTResult[Value]:
        """Strip whitespace (or given chars) from the right."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            return res.success(String(self.value.rstrip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", chars.context))
        if chars.value:
            return res.success(String(self.value.rstrip(chars.value)))
        return res.success(String(self.value.rstrip()))

    @args([])
    @method
    def is_digit(self, _ctx: Context) -> RTResult[Value]:
        """Check if string contains only digits."""
        return RTResult[Value]().success(Boolean(self.value.isdigit()))

    @args([])
    @method
    def is_alpha(self, _ctx: Context) -> RTResult[Value]:
        """Check if string contains only alphabetic characters."""
        return RTResult[Value]().success(Boolean(self.value.isalpha()))

    @args([])
    @method
    def is_alnum(self, _ctx: Context) -> RTResult[Value]:
        """Check if string contains only alphanumeric characters."""
        return RTResult[Value]().success(Boolean(self.value.isalnum()))

    @args([])
    @method
    def is_space(self, _ctx: Context) -> RTResult[Value]:
        """Check if string contains only whitespace."""
        return RTResult[Value]().success(Boolean(self.value.isspace()))

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Return the string (identity)."""
        return RTResult[Value]().success(String(self.value))
