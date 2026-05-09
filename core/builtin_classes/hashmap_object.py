"""Built-in HashMap wrapper class for objective method access."""

from typing import Dict

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, HashMap, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class HashMapObject(BuiltInObject):
    """Built-in HashMap wrapper for objective method access.

    A HashMap is a collection of key-value pairs with string keys.

    Methods:
        keys()              - Get array of all keys
        values()            - Get array of all values
        items()             - Get array of [key, value] pairs
        get(key, default)   - Get value by key (with optional default)
        set(key, value)     - Set a key-value pair
        has(key)            - Check if key exists
        remove(key)         - Remove a key-value pair
        length()            - Get number of pairs
        clear()             - Remove all pairs
        to_string()         - Convert to string representation
        is_empty()          - Check if hashmap is empty
        copy()              - Create a shallow copy
        merge(other)        - Merge with another hashmap
        pop(key, default)   - Remove and return value
        update(other)       - Update with another hashmap in place
        get_or_set(key, default) - Get value or set default if missing
        filter(func)        - Filter pairs by predicate
        map_values(func)    - Transform values with function

    Operators:
        hm[key]             - Get value by key
        hm[key] = value     - Set value
        key in hm           - Check key existence
        len(hm)             - Get number of pairs

    Example:
        var hm = {"name": "Alice", "age": 30}
        hm.keys()           # ["name", "age"]
        hm.get("name")      # "Alice"
        hm.has("email")     # false
        hm.set("email", "alice@example.com")
    """

    _data: Dict[str, Value]

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing hashmap or create empty."""
        if len(args_list) == 1 and isinstance(args_list[0], HashMap):
            self._data = args_list[0].values
        elif len(args_list) == 0:
            self._data = {}
        else:
            return RTResult[Value]().failure(
                RTError(
                    args_list[0].pos_start,
                    args_list[0].pos_end,
                    "HashMapObject constructor expects a HashMap",
                    args_list[0].context,
                )
            )
        return RTResult[Value]().success(Null.null())

    def __string_display__(self) -> str:
        return str(HashMap(self._data))

    def __len__(self) -> int:
        return len(self._data)

    @args([])
    @method
    def keys(self, _ctx: Context) -> RTResult[Value]:
        """Return an array of all keys in the hashmap."""
        return RTResult[Value]().success(Array([String(k) for k in self._data.keys()]))

    @args([])
    @method
    def values(self, _ctx: Context) -> RTResult[Value]:
        """Return an array of all values in the hashmap."""
        return RTResult[Value]().success(Array(list(self._data.values())))

    @args([])
    @method
    def items(self, _ctx: Context) -> RTResult[Value]:
        """Return an array of [key, value] pairs."""
        pairs: list[Value] = []
        for k, v in self._data.items():
            pairs.append(Array([String(k), v]))
        return RTResult[Value]().success(Array(pairs))

    @args(["key", "default"], [None, Null.null()])
    @method
    def get(self, ctx: Context) -> RTResult[Value]:
        """Get the value for a key, returning default if key doesn't exist."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        default = ctx.symbol_table.get("default")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        value = self._data.get(key.value)
        if value is None:
            assert default is not None
            return res.success(default)
        return res.success(value)

    @args(["key", "value"])
    @method
    def set(self, ctx: Context) -> RTResult[Value]:
        """Set a key-value pair in the hashmap."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        value = ctx.symbol_table.get("value")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        assert value is not None
        self._data[key.value] = value
        return res.success(Null.null())

    @args(["key"])
    @method
    def has(self, ctx: Context) -> RTResult[Value]:
        """Check if a key exists in the hashmap."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        return res.success(Boolean(key.value in self._data))

    @args(["key"])
    @method
    def remove(self, ctx: Context) -> RTResult[Value]:
        """Remove a key-value pair from the hashmap."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        if key.value not in self._data:
            return res.failure(RTError(key.pos_start, key.pos_end, f"Key '{key.value}' not found", ctx))
        del self._data[key.value]
        return res.success(Null.null())

    @args([])
    @method
    def length(self, _ctx: Context) -> RTResult[Value]:
        """Return the number of key-value pairs in the hashmap."""
        return RTResult[Value]().success(Number(len(self._data)))

    @args([])
    @method
    def clear(self, _ctx: Context) -> RTResult[Value]:
        """Remove all key-value pairs from the hashmap."""
        self._data.clear()
        return RTResult[Value]().success(Null.null())

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Convert the hashmap to its string representation."""
        return RTResult[Value]().success(String(str(HashMap(self._data))))

    @args([])
    @method
    def is_empty(self, _ctx: Context) -> RTResult[Value]:
        """Check if the hashmap is empty."""
        return RTResult[Value]().success(Boolean(len(self._data) == 0))

    @args([])
    @method
    def copy(self, _ctx: Context) -> RTResult[Value]:
        """Return a shallow copy of the hashmap."""
        return RTResult[Value]().success(HashMap(dict(self._data)))

    @args(["other"])
    @method
    def merge(self, ctx: Context) -> RTResult[Value]:
        """Return a new hashmap with this hashmap merged with another."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        if not isinstance(other, HashMap):
            return res.failure(RTError(other.pos_start, other.pos_end, "Argument must be a hashmap", ctx))
        merged = dict(self._data)
        merged.update(other.values)
        return res.success(HashMap(merged))

    @args(["key", "default"], [None, Null.null()])
    @method
    def pop(self, ctx: Context) -> RTResult[Value]:
        """Remove and return the value for a key, returning default if not found."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        default = ctx.symbol_table.get("default")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        assert default is not None
        if key.value in self._data:
            value = self._data.pop(key.value)
            return res.success(value)
        return res.success(default)

    @args(["other"])
    @method
    def update(self, ctx: Context) -> RTResult[Value]:
        """Update the hashmap with key-value pairs from another hashmap."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        if not isinstance(other, HashMap):
            assert other is not None
            return res.failure(RTError(other.pos_start, other.pos_end, "Argument must be a hashmap", ctx))
        self._data.update(other.values)
        return res.success(Null.null())

    @args(["key", "default"])
    @method
    def get_or_set(self, ctx: Context) -> RTResult[Value]:
        """Get the value for a key, or set and return the default if missing."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        default = ctx.symbol_table.get("default")
        if not isinstance(key, String):
            assert key is not None
            return res.failure(RTError(key.pos_start, key.pos_end, "Key must be a string", ctx))
        assert default is not None
        if key.value in self._data:
            return res.success(self._data[key.value])
        self._data[key.value] = default
        return res.success(default)

    @args(["func"])
    @method
    def filter(self, ctx: Context) -> RTResult[Value]:
        """Filter key-value pairs by a predicate function that receives (key, value)."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        filtered: Dict[str, Value] = {}
        for k, v in self._data.items():
            result = res.register(func.execute([String(k), v], {}))
            if res.should_return():
                return res
            assert result is not None
            if result.is_true():
                filtered[k] = v

        return res.success(HashMap(filtered))

    @args(["func"])
    @method
    def map_values(self, ctx: Context) -> RTResult[Value]:
        """Transform values with a function that receives (key, value) and returns new value."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        mapped: Dict[str, Value] = {}
        for k, v in self._data.items():
            result = res.register(func.execute([String(k), v], {}))
            if res.should_return():
                return res
            assert result is not None
            mapped[k] = result

        return res.success(HashMap(mapped))
