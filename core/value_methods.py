"""Methods for built-in value types (Array, String, Number, Boolean, HashMap).

This module provides method resolution for built-in datatypes, enabling
objective syntax like `arr.append(1)` instead of `arr_append(arr, 1)`.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, Optional, Protocol

if TYPE_CHECKING:
    from core.datatypes import Value

from core.datatypes import Array, Boolean, HashMap, Null, Number, String
from core.errors import RTError
from core.parser import Context, RTResult


class ValueMethod(Protocol):
    """Protocol for value methods with arg_names and defaults."""

    arg_names: list[str]
    defaults: list[Optional["Value"]]

    def __call__(self, value: "Value", ctx: Context) -> RTResult["Value"]: ...


def method(arg_names: list[str], defaults: Optional[list[Optional["Value"]]] = None) -> Callable:
    """Decorator to define method arguments and defaults."""
    if defaults is None:
        defaults = [None] * len(arg_names)

    def decorator(func: Callable) -> Callable:
        func.arg_names = arg_names  # type: ignore
        func.defaults = defaults  # type: ignore
        return func

    return decorator


# =============================================================================
# Array Methods
# =============================================================================


class ArrayMethods:
    """Methods for Array datatype."""

    @staticmethod
    @method(["value"])
    def append(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Append a value to the array."""
        res = RTResult["Value"]()
        value = ctx.symbol_table.get("value")
        assert value is not None
        arr.elements.append(value)
        return res.success(Null.null())

    @staticmethod
    @method(["index"], [Number(-1)])
    def pop(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Remove and return the element at the given index (default: last)."""
        res = RTResult["Value"]()
        index = ctx.symbol_table.get("index")
        if not isinstance(index, Number):
            return res.failure(
                RTError(arr.pos_start, arr.pos_end, "Index must be a number", ctx)
            )
        try:
            element = arr.elements.pop(int(index.value))
        except IndexError:
            return res.failure(
                RTError(
                    arr.pos_start,
                    arr.pos_end,
                    "Pop index out of range",
                    ctx,
                )
            )
        return res.success(element)

    @staticmethod
    @method(["array"])
    def extend(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Extend the array with another array."""
        res = RTResult["Value"]()
        other = ctx.symbol_table.get("array")
        if not isinstance(other, Array):
            return res.failure(
                RTError(arr.pos_start, arr.pos_end, "Argument must be an array", ctx)
            )
        arr.elements.extend(other.elements)
        return res.success(Null.null())

    @staticmethod
    @method(["element"])
    def find(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Find the index of an element in the array (-1 if not found)."""
        res = RTResult["Value"]()
        element = ctx.symbol_table.get("element")
        assert element is not None
        for i, val in enumerate(arr.elements):
            cmp, err = val.get_comparison_eq(element)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                return res.success(Number(i))
        return res.success(Number(-1))

    @staticmethod
    @method(["func"])
    def map(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Map a function over the array elements."""
        res = RTResult["Value"]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        new_elements: list["Value"] = []
        for element in arr.elements:
            result = res.register(func.execute([element], {}))
            if res.should_return():
                return res
            assert result is not None
            new_elements.append(result)

        return res.success(Array(new_elements))

    @staticmethod
    @method([])
    def is_empty(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Check if the array is empty."""
        return RTResult["Value"]().success(
            Boolean.true() if len(arr.elements) == 0 else Boolean.false()
        )

    @staticmethod
    @method([])
    def to_string(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Convert the array to a string."""
        return RTResult["Value"]().success(String(str(arr)))

    @staticmethod
    @method([])
    def length(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Return the length of the array."""
        return RTResult["Value"]().success(Number(len(arr.elements)))

    @staticmethod
    @method([])
    def copy(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Return a shallow copy of the array."""
        return RTResult["Value"]().success(Array(arr.elements[:]))

    @staticmethod
    @method([])
    def reverse(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Reverse the array in place."""
        arr.elements.reverse()
        return RTResult["Value"]().success(Null.null())

    @staticmethod
    @method([])
    def clear(arr: Array, ctx: Context) -> RTResult["Value"]:
        """Remove all elements from the array."""
        arr.elements.clear()
        return RTResult["Value"]().success(Null.null())


# =============================================================================
# String Methods
# =============================================================================


class StringMethods:
    """Methods for String datatype."""

    @staticmethod
    @method([])
    def upper(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string in uppercase."""
        return RTResult["Value"]().success(String(s.value.upper()))

    @staticmethod
    @method([])
    def lower(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string in lowercase."""
        return RTResult["Value"]().success(String(s.value.lower()))

    @staticmethod
    @method([])
    def title(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string in title case."""
        return RTResult["Value"]().success(String(s.value.title()))

    @staticmethod
    @method([])
    def capitalize(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string with first character capitalized."""
        return RTResult["Value"]().success(String(s.value.capitalize()))

    @staticmethod
    @method([])
    def swapcase(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string with swapped case."""
        return RTResult["Value"]().success(String(s.value.swapcase()))

    @staticmethod
    @method([])
    def length(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the length of the string."""
        return RTResult["Value"]().success(Number(len(s.value)))

    @staticmethod
    @method(["separator"], [String(" ")])
    def split(s: String, ctx: Context) -> RTResult["Value"]:
        """Split the string by separator."""
        res = RTResult["Value"]()
        sep = ctx.symbol_table.get("separator")
        if not isinstance(sep, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Separator must be a string", ctx)
            )
        parts = s.value.split(sep.value) if sep.value else list(s.value)
        return res.success(Array([String(p) for p in parts]))

    @staticmethod
    @method(["substring"])
    def find(s: String, ctx: Context) -> RTResult["Value"]:
        """Find the index of a substring (-1 if not found)."""
        res = RTResult["Value"]()
        sub = ctx.symbol_table.get("substring")
        if not isinstance(sub, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        return res.success(Number(s.value.find(sub.value)))

    @staticmethod
    @method(["old", "new"])
    def replace(s: String, ctx: Context) -> RTResult["Value"]:
        """Replace occurrences of old with new."""
        res = RTResult["Value"]()
        old = ctx.symbol_table.get("old")
        new = ctx.symbol_table.get("new")
        if not isinstance(old, String) or not isinstance(new, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Arguments must be strings", ctx)
            )
        return res.success(String(s.value.replace(old.value, new.value)))

    @staticmethod
    @method(["chars"], [String("")])
    def strip(s: String, ctx: Context) -> RTResult["Value"]:
        """Strip whitespace (or given chars) from both ends."""
        res = RTResult["Value"]()
        chars = ctx.symbol_table.get("chars")
        if not isinstance(chars, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        if chars.value:
            return res.success(String(s.value.strip(chars.value)))
        return res.success(String(s.value.strip()))

    @staticmethod
    @method(["chars"], [String("")])
    def lstrip(s: String, ctx: Context) -> RTResult["Value"]:
        """Strip whitespace (or given chars) from the left."""
        res = RTResult["Value"]()
        chars = ctx.symbol_table.get("chars")
        if not isinstance(chars, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        if chars.value:
            return res.success(String(s.value.lstrip(chars.value)))
        return res.success(String(s.value.lstrip()))

    @staticmethod
    @method(["chars"], [String("")])
    def rstrip(s: String, ctx: Context) -> RTResult["Value"]:
        """Strip whitespace (or given chars) from the right."""
        res = RTResult["Value"]()
        chars = ctx.symbol_table.get("chars")
        if not isinstance(chars, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        if chars.value:
            return res.success(String(s.value.rstrip(chars.value)))
        return res.success(String(s.value.rstrip()))

    @staticmethod
    @method(["prefix"])
    def startswith(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string starts with prefix."""
        res = RTResult["Value"]()
        prefix = ctx.symbol_table.get("prefix")
        if not isinstance(prefix, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        return res.success(Boolean(s.value.startswith(prefix.value)))

    @staticmethod
    @method(["suffix"])
    def endswith(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string ends with suffix."""
        res = RTResult["Value"]()
        suffix = ctx.symbol_table.get("suffix")
        if not isinstance(suffix, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        return res.success(Boolean(s.value.endswith(suffix.value)))

    @staticmethod
    @method(["substring"])
    def count(s: String, ctx: Context) -> RTResult["Value"]:
        """Count occurrences of substring."""
        res = RTResult["Value"]()
        sub = ctx.symbol_table.get("substring")
        if not isinstance(sub, String):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be a string", ctx)
            )
        if not sub.value:
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Cannot count empty string", ctx)
            )
        return res.success(Number(s.value.count(sub.value)))

    @staticmethod
    @method(["array"])
    def join(s: String, ctx: Context) -> RTResult["Value"]:
        """Join an array of strings with this string as separator."""
        res = RTResult["Value"]()
        arr = ctx.symbol_table.get("array")
        if not isinstance(arr, Array):
            return res.failure(
                RTError(s.pos_start, s.pos_end, "Argument must be an array", ctx)
            )
        str_parts = []
        for elem in arr.elements:
            if isinstance(elem, String):
                str_parts.append(elem.value)
            else:
                str_parts.append(str(elem))
        return res.success(String(s.value.join(str_parts)))

    @staticmethod
    @method([])
    def to_string(s: String, ctx: Context) -> RTResult["Value"]:
        """Return the string (identity)."""
        return RTResult["Value"]().success(String(s.value))

    @staticmethod
    @method([])
    def is_digit(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string contains only digits."""
        return RTResult["Value"]().success(Boolean(s.value.isdigit()))

    @staticmethod
    @method([])
    def is_alpha(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string contains only alphabetic characters."""
        return RTResult["Value"]().success(Boolean(s.value.isalpha()))

    @staticmethod
    @method([])
    def is_alnum(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string contains only alphanumeric characters."""
        return RTResult["Value"]().success(Boolean(s.value.isalnum()))

    @staticmethod
    @method([])
    def is_space(s: String, ctx: Context) -> RTResult["Value"]:
        """Check if string contains only whitespace."""
        return RTResult["Value"]().success(Boolean(s.value.isspace()))


# =============================================================================
# Number Methods
# =============================================================================


class NumberMethods:
    """Methods for Number datatype."""

    @staticmethod
    @method([])
    def to_string(n: Number, ctx: Context) -> RTResult["Value"]:
        """Convert number to string."""
        if n.value == int(n.value):
            return RTResult["Value"]().success(String(str(int(n.value))))
        return RTResult["Value"]().success(String(str(n.value)))

    @staticmethod
    @method([])
    def abs(n: Number, ctx: Context) -> RTResult["Value"]:
        """Return absolute value."""
        return RTResult["Value"]().success(Number(abs(n.value)))

    @staticmethod
    @method(["digits"], [Number(0)])
    def round(n: Number, ctx: Context) -> RTResult["Value"]:
        """Round to given number of decimal places."""
        res = RTResult["Value"]()
        digits = ctx.symbol_table.get("digits")
        if not isinstance(digits, Number):
            return res.failure(
                RTError(n.pos_start, n.pos_end, "Digits must be a number", ctx)
            )
        return res.success(Number(round(n.value, int(digits.value))))

    @staticmethod
    @method([])
    def floor(n: Number, ctx: Context) -> RTResult["Value"]:
        """Return the floor of the number."""
        return RTResult["Value"]().success(Number(math.floor(n.value)))

    @staticmethod
    @method([])
    def ceil(n: Number, ctx: Context) -> RTResult["Value"]:
        """Return the ceiling of the number."""
        return RTResult["Value"]().success(Number(math.ceil(n.value)))

    @staticmethod
    @method([])
    def is_int(n: Number, ctx: Context) -> RTResult["Value"]:
        """Check if the number is an integer."""
        return RTResult["Value"]().success(Boolean(n.value == int(n.value)))


# =============================================================================
# Boolean Methods
# =============================================================================


class BooleanMethods:
    """Methods for Boolean datatype."""

    @staticmethod
    @method([])
    def to_string(b: Boolean, ctx: Context) -> RTResult["Value"]:
        """Convert boolean to string."""
        return RTResult["Value"]().success(String(str(b)))

    @staticmethod
    @method([])
    def to_number(b: Boolean, ctx: Context) -> RTResult["Value"]:
        """Convert boolean to number (1 or 0)."""
        return RTResult["Value"]().success(Number(1 if b.value else 0))


# =============================================================================
# HashMap Methods
# =============================================================================


class HashMapMethods:
    """Methods for HashMap datatype."""

    @staticmethod
    @method([])
    def keys(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Return array of keys."""
        return RTResult["Value"]().success(
            Array([String(k) for k in hm.values.keys()])
        )

    @staticmethod
    @method([])
    def values(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Return array of values."""
        return RTResult["Value"]().success(Array(list(hm.values.values())))

    @staticmethod
    @method([])
    def items(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Return array of [key, value] pairs."""
        pairs: list[Value] = []
        for k, v in hm.values.items():
            pairs.append(Array([String(k), v]))
        return RTResult["Value"]().success(Array(pairs))

    @staticmethod
    @method(["key", "default"], [None, Null.null()])
    def get(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Get a value by key with optional default."""
        res = RTResult["Value"]()
        key = ctx.symbol_table.get("key")
        default = ctx.symbol_table.get("default")
        if not isinstance(key, String):
            return res.failure(
                RTError(hm.pos_start, hm.pos_end, "Key must be a string", ctx)
            )
        value = hm.values.get(key.value)
        if value is None:
            assert default is not None
            return res.success(default)
        return res.success(value)

    @staticmethod
    @method(["key", "value"])
    def set(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Set a key-value pair."""
        res = RTResult["Value"]()
        key = ctx.symbol_table.get("key")
        value = ctx.symbol_table.get("value")
        if not isinstance(key, String):
            return res.failure(
                RTError(hm.pos_start, hm.pos_end, "Key must be a string", ctx)
            )
        assert value is not None
        hm.values[key.value] = value
        return res.success(Null.null())

    @staticmethod
    @method(["key"])
    def has(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Check if key exists."""
        res = RTResult["Value"]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            return res.failure(
                RTError(hm.pos_start, hm.pos_end, "Key must be a string", ctx)
            )
        return res.success(Boolean(key.value in hm.values))

    @staticmethod
    @method(["key"])
    def remove(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Remove a key-value pair."""
        res = RTResult["Value"]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            return res.failure(
                RTError(hm.pos_start, hm.pos_end, "Key must be a string", ctx)
            )
        if key.value not in hm.values:
            return res.failure(
                RTError(hm.pos_start, hm.pos_end, f"Key '{key.value}' not found", ctx)
            )
        del hm.values[key.value]
        return res.success(Null.null())

    @staticmethod
    @method([])
    def length(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Return the number of key-value pairs."""
        return RTResult["Value"]().success(Number(len(hm.values)))

    @staticmethod
    @method([])
    def clear(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Remove all key-value pairs."""
        hm.values.clear()
        return RTResult["Value"]().success(Null.null())

    @staticmethod
    @method([])
    def to_string(hm: HashMap, ctx: Context) -> RTResult["Value"]:
        """Convert hashmap to string."""
        return RTResult["Value"]().success(String(str(hm)))


# =============================================================================
# Method Registry
# =============================================================================

# Maps type names to their method classes
METHOD_REGISTRY: dict[type, type] = {
    Array: ArrayMethods,
    String: StringMethods,
    Number: NumberMethods,
    Boolean: BooleanMethods,
    HashMap: HashMapMethods,
}


def get_value_method(value: "Value", method_name: str) -> Optional[ValueMethod]:
    """Get a method for a value type by name.

    Returns None if the method doesn't exist.
    """
    value_type = type(value)
    method_class = METHOD_REGISTRY.get(value_type)
    if method_class is None:
        return None
    method_func = getattr(method_class, method_name, None)
    if method_func is None or not hasattr(method_func, "arg_names"):
        return None
    return method_func  # type: ignore[return-value]
