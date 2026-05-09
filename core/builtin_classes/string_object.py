from core.builtin_classes.base_classes import BuiltInObject, check, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class StringObject(BuiltInObject):
    """Built-in String wrapper for objective method access.

    A String is an immutable sequence of characters.

    Methods:
        upper()             - Convert to uppercase
        lower()             - Convert to lowercase
        title()             - Convert to title case
        capitalize()        - Capitalize first character
        swapcase()          - Swap case of all characters
        length()            - Get string length
        count(substr)       - Count occurrences of substring
        replace(old, new)   - Replace occurrences of old with new
        find(substr)        - Find index of substring (-1 if not found)
        startswith(prefix)  - Check if string starts with prefix
        endswith(suffix)    - Check if string ends with suffix
        split(separator)    - Split string into array
        join(array)         - Join array elements with this string
        strip(chars)        - Remove leading/trailing whitespace (or chars)
        lstrip(chars)       - Remove leading whitespace (or chars)
        rstrip(chars)       - Remove trailing whitespace (or chars)
        is_digit()          - Check if all characters are digits
        is_alpha()          - Check if all characters are alphabetic
        is_alnum()          - Check if all characters are alphanumeric
        is_space()          - Check if all characters are whitespace
        is_upper()          - Check if all characters are uppercase
        is_lower()          - Check if all characters are lowercase
        is_empty()          - Check if string is empty
        to_string()         - Return the string (identity)
        to_int()            - Convert to integer
        to_float()          - Convert to float
        get(index)          - Get character at index
        slice(start, end)   - Get substring from start to end
        reverse()           - Return reversed string
        center(width, char) - Center string in given width
        zfill(width)        - Pad with zeros on the left
        includes(substr)    - Check if string contains substring
        repeat(n)           - Repeat string n times

    Operators:
        str1 + str2         - Concatenate strings
        str * n             - Repeat string n times
        x in str            - Check if substring exists
        str[i]              - Get character at index
        len(str)            - Get length

    Example:
        var s = "hello world"
        s.upper()           # "HELLO WORLD"
        s.split(" ")        # ["hello", "world"]
        s.find("world")     # 6
        s.replace("world", "Radon")  # "hello Radon"
    """

    @operator("__constructor__")
    @check([String], [String("")])
    def constructor(self, string: String) -> RTResult[Value]:
        """Initialize the string object."""
        self.value: str = string.value
        return RTResult[Value]().success(Null.null())

    @operator("__add__")
    @check([String])
    def add(self, other: String) -> RTResult[Value]:
        """Concatenate two strings."""
        res = RTResult[Value]()
        return res.success(String(self.value + other.value))

    def __string_display__(self) -> str:
        """Return the string for display."""
        return self.value

    def __len__(self) -> int:
        """Return the length of the string."""
        return len(self.value)

    @args([])
    @method
    def upper(self, _ctx: Context) -> RTResult[Value]:
        """Convert all characters to uppercase."""
        res = RTResult[Value]()
        return res.success(String(self.value.upper()))

    @args([])
    @method
    def lower(self, _ctx: Context) -> RTResult[Value]:
        """Convert all characters to lowercase."""
        res = RTResult[Value]()
        return res.success(String(self.value.lower()))

    @args([])
    @method
    def title(self, _ctx: Context) -> RTResult[Value]:
        """Convert to title case (first letter of each word capitalized)."""
        res = RTResult[Value]()
        return res.success(String(self.value.title()))

    @args([])
    @method
    def capitalize(self, _ctx: Context) -> RTResult[Value]:
        """Capitalize the first character."""
        res = RTResult[Value]()
        return res.success(String(self.value.capitalize()))

    @args([])
    @method
    def swapcase(self, _ctx: Context) -> RTResult[Value]:
        """Swap uppercase to lowercase and vice versa."""
        res = RTResult[Value]()
        return res.success(String(self.value.swapcase()))

    @args([])
    @method
    def length(self, _ctx: Context) -> RTResult[Value]:
        """Return the number of characters in the string."""
        res = RTResult[Value]()
        return res.success(Number(len(self.value)))

    @args(["string"], [String("")])
    @method
    def count(self, ctx: Context) -> RTResult[Value]:
        """Count the number of non-overlapping occurrences of substring."""
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(RTError(string.pos_start, string.pos_end, "Argument must be a string", ctx))
        if len(string.value) == 0:
            return res.failure(RTError(string.pos_start, string.pos_end, "Cannot count an empty string", ctx))
        return res.success(Number(self.value.count(string.value)))

    @args(["old", "new"])
    @method
    def replace(self, ctx: Context) -> RTResult[Value]:
        """Replace all occurrences of old with new."""
        res = RTResult[Value]()
        old = ctx.symbol_table.get("old")
        new = ctx.symbol_table.get("new")
        assert old is not None and new is not None
        if not isinstance(old, String):
            return res.failure(RTError(old.pos_start, old.pos_end, "First argument must be a string", ctx))
        if not isinstance(new, String):
            return res.failure(RTError(new.pos_start, new.pos_end, "Second argument must be a string", ctx))
        return res.success(String(self.value.replace(old.value, new.value)))

    @args(["string"])
    @method
    def find(self, ctx: Context) -> RTResult[Value]:
        """Find the index of the first occurrence of substring (-1 if not found)."""
        res = RTResult[Value]()
        string = ctx.symbol_table.get("string")
        assert string is not None
        if not isinstance(string, String):
            return res.failure(RTError(string.pos_start, string.pos_end, "Argument must be a string", ctx))
        return res.success(Number(self.value.find(string.value)))

    @args(["prefix"])
    @method
    def startswith(self, ctx: Context) -> RTResult[Value]:
        """Check if the string starts with the given prefix."""
        res = RTResult[Value]()
        prefix = ctx.symbol_table.get("prefix")
        assert prefix is not None
        if not isinstance(prefix, String):
            return res.failure(RTError(prefix.pos_start, prefix.pos_end, "Argument must be a string", ctx))
        return res.success(Boolean(self.value.startswith(prefix.value)))

    @args(["suffix"])
    @method
    def endswith(self, ctx: Context) -> RTResult[Value]:
        """Check if the string ends with the given suffix."""
        res = RTResult[Value]()
        suffix = ctx.symbol_table.get("suffix")
        assert suffix is not None
        if not isinstance(suffix, String):
            return res.failure(RTError(suffix.pos_start, suffix.pos_end, "Argument must be a string", ctx))
        return res.success(Boolean(self.value.endswith(suffix.value)))

    @args(["separator"], [Null.null()])
    @method
    def split(self, ctx: Context) -> RTResult[Value]:
        """Split the string into an array. If no separator, splits on whitespace."""
        res = RTResult[Value]()
        separator = ctx.symbol_table.get("separator")
        assert separator is not None
        if isinstance(separator, Null):
            return res.success(Array([String(i) for i in self.value.split()]))
        if not isinstance(separator, String):
            return res.failure(RTError(separator.pos_start, separator.pos_end, "Separator must be a string", ctx))
        return res.success(Array([String(i) for i in self.value.split(separator.value)]))

    @args(["array"])
    @method
    def join(self, ctx: Context) -> RTResult[Value]:
        """Join an array of elements with this string as separator."""
        res = RTResult[Value]()
        arr = ctx.symbol_table.get("array")
        assert arr is not None
        if not isinstance(arr, Array):
            return res.failure(RTError(arr.pos_start, arr.pos_end, "Argument must be an array", ctx))
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
        """Remove leading and trailing whitespace (or specified characters)."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            return res.success(String(self.value.strip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", ctx))
        if chars.value:
            return res.success(String(self.value.strip(chars.value)))
        return res.success(String(self.value.strip()))

    @args(["chars"], [Null.null()])
    @method
    def lstrip(self, ctx: Context) -> RTResult[Value]:
        """Remove leading whitespace (or specified characters)."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            return res.success(String(self.value.lstrip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", ctx))
        if chars.value:
            return res.success(String(self.value.lstrip(chars.value)))
        return res.success(String(self.value.lstrip()))

    @args(["chars"], [Null.null()])
    @method
    def rstrip(self, ctx: Context) -> RTResult[Value]:
        """Remove trailing whitespace (or specified characters)."""
        res = RTResult[Value]()
        chars = ctx.symbol_table.get("chars")
        assert chars is not None
        if isinstance(chars, Null):
            return res.success(String(self.value.rstrip()))
        if not isinstance(chars, String):
            return res.failure(RTError(chars.pos_start, chars.pos_end, "Argument must be a string", ctx))
        if chars.value:
            return res.success(String(self.value.rstrip(chars.value)))
        return res.success(String(self.value.rstrip()))

    @args([])
    @method
    def is_digit(self, _ctx: Context) -> RTResult[Value]:
        """Check if the string contains only digit characters."""
        return RTResult[Value]().success(Boolean(self.value.isdigit() if self.value else False))

    @args([])
    @method
    def is_alpha(self, _ctx: Context) -> RTResult[Value]:
        """Check if the string contains only alphabetic characters."""
        return RTResult[Value]().success(Boolean(self.value.isalpha() if self.value else False))

    @args([])
    @method
    def is_alnum(self, _ctx: Context) -> RTResult[Value]:
        """Check if the string contains only alphanumeric characters."""
        return RTResult[Value]().success(Boolean(self.value.isalnum() if self.value else False))

    @args([])
    @method
    def is_space(self, _ctx: Context) -> RTResult[Value]:
        """Check if the string contains only whitespace characters."""
        return RTResult[Value]().success(Boolean(self.value.isspace() if self.value else False))

    @args([])
    @method
    def is_upper(self, _ctx: Context) -> RTResult[Value]:
        """Check if all cased characters are uppercase."""
        return RTResult[Value]().success(Boolean(self.value.isupper() if self.value else False))

    @args([])
    @method
    def is_lower(self, _ctx: Context) -> RTResult[Value]:
        """Check if all cased characters are lowercase."""
        return RTResult[Value]().success(Boolean(self.value.islower() if self.value else False))

    @args([])
    @method
    def is_empty(self, _ctx: Context) -> RTResult[Value]:
        """Check if the string is empty."""
        return RTResult[Value]().success(Boolean(len(self.value) == 0))

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Return the string itself (identity operation)."""
        return RTResult[Value]().success(String(self.value))

    @args([])
    @method
    def to_int(self, ctx: Context) -> RTResult[Value]:
        """Convert the string to an integer."""
        res = RTResult[Value]()
        try:
            return res.success(Number(int(self.value)))
        except ValueError:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, f"Cannot convert '{self.value}' to int", ctx)
            )

    @args([])
    @method
    def to_float(self, ctx: Context) -> RTResult[Value]:
        """Convert the string to a float."""
        res = RTResult[Value]()
        try:
            return res.success(Number(float(self.value)))
        except ValueError:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, f"Cannot convert '{self.value}' to float", ctx)
            )

    @args(["index"])
    @method
    def get(self, ctx: Context) -> RTResult[Value]:
        """Get the character at the specified index."""
        res = RTResult[Value]()
        index = ctx.symbol_table.get("index")
        assert index is not None
        if not isinstance(index, Number):
            return res.failure(RTError(index.pos_start, index.pos_end, "Index must be a number", ctx))
        try:
            return res.success(String(self.value[int(index.value)]))
        except IndexError:
            return res.failure(RTError(index.pos_start, index.pos_end, "Index out of range", ctx))

    @args(["start", "end"], [None, Null.null()])
    @method
    def slice(self, ctx: Context) -> RTResult[Value]:
        """Get a substring from start to end index."""
        res = RTResult[Value]()
        start = ctx.symbol_table.get("start")
        end = ctx.symbol_table.get("end")
        assert start is not None
        if not isinstance(start, Number):
            return res.failure(RTError(start.pos_start, start.pos_end, "Start must be a number", ctx))
        start_idx = int(start.value)
        if isinstance(end, Null):
            return res.success(String(self.value[start_idx:]))
        if not isinstance(end, Number):
            assert end is not None
            return res.failure(RTError(end.pos_start, end.pos_end, "End must be a number", ctx))
        end_idx = int(end.value)
        return res.success(String(self.value[start_idx:end_idx]))

    @args([])
    @method
    def reverse(self, _ctx: Context) -> RTResult[Value]:
        """Return the string reversed."""
        return RTResult[Value]().success(String(self.value[::-1]))

    @args(["width", "char"], [None, String(" ")])
    @method
    def center(self, ctx: Context) -> RTResult[Value]:
        """Center the string in a field of the given width."""
        res = RTResult[Value]()
        width = ctx.symbol_table.get("width")
        char = ctx.symbol_table.get("char")
        assert width is not None and char is not None
        if not isinstance(width, Number):
            return res.failure(RTError(width.pos_start, width.pos_end, "Width must be a number", ctx))
        if not isinstance(char, String):
            return res.failure(RTError(char.pos_start, char.pos_end, "Fill character must be a string", ctx))
        if len(char.value) != 1:
            return res.failure(RTError(char.pos_start, char.pos_end, "Fill character must be a single character", ctx))
        return res.success(String(self.value.center(int(width.value), char.value)))

    @args(["width"])
    @method
    def zfill(self, ctx: Context) -> RTResult[Value]:
        """Pad the string on the left with zeros to fill the given width."""
        res = RTResult[Value]()
        width = ctx.symbol_table.get("width")
        assert width is not None
        if not isinstance(width, Number):
            return res.failure(RTError(width.pos_start, width.pos_end, "Width must be a number", ctx))
        return res.success(String(self.value.zfill(int(width.value))))

    @args(["substr"])
    @method
    def includes(self, ctx: Context) -> RTResult[Value]:
        """Check if the string contains the given substring."""
        res = RTResult[Value]()
        substr = ctx.symbol_table.get("substr")
        assert substr is not None
        if not isinstance(substr, String):
            return res.failure(RTError(substr.pos_start, substr.pos_end, "Argument must be a string", ctx))
        return res.success(Boolean(substr.value in self.value))

    @args(["n"])
    @method
    def repeat(self, ctx: Context) -> RTResult[Value]:
        """Repeat the string n times."""
        res = RTResult[Value]()
        n = ctx.symbol_table.get("n")
        assert n is not None
        if not isinstance(n, Number):
            return res.failure(RTError(n.pos_start, n.pos_end, "Argument must be a number", ctx))
        return res.success(String(self.value * int(n.value)))
