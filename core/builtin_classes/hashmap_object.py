"""Built-in HashMap wrapper class for objective method access."""

from typing import Dict

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, HashMap, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class HashMapObject(BuiltInObject):
    """Built-in HashMap manipulation object.

    Provides objective method syntax for HashMap values.
    Example: hm.keys(), hm.get("key"), hm.set("key", value)
    """

    _data: Dict[str, Value]

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing hashmap or empty."""
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
        """Return array of keys."""
        return RTResult[Value]().success(Array([String(k) for k in self._data.keys()]))

    @args([])
    @method
    def values(self, _ctx: Context) -> RTResult[Value]:
        """Return array of values."""
        return RTResult[Value]().success(Array(list(self._data.values())))

    @args([])
    @method
    def items(self, _ctx: Context) -> RTResult[Value]:
        """Return array of [key, value] pairs."""
        pairs: list[Value] = []
        for k, v in self._data.items():
            pairs.append(Array([String(k), v]))
        return RTResult[Value]().success(Array(pairs))

    @args(["key", "default"], [None, Null.null()])
    @method
    def get(self, ctx: Context) -> RTResult[Value]:
        """Get a value by key with optional default."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        default = ctx.symbol_table.get("default")
        if not isinstance(key, String):
            return res.failure(
                RTError(key.pos_start, key.pos_end, "Key must be a string", ctx)
            )
        value = self._data.get(key.value)
        if value is None:
            assert default is not None
            return res.success(default)
        return res.success(value)

    @args(["key", "value"])
    @method
    def set(self, ctx: Context) -> RTResult[Value]:
        """Set a key-value pair."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        value = ctx.symbol_table.get("value")
        if not isinstance(key, String):
            return res.failure(
                RTError(key.pos_start, key.pos_end, "Key must be a string", ctx)
            )
        assert value is not None
        self._data[key.value] = value
        return res.success(Null.null())

    @args(["key"])
    @method
    def has(self, ctx: Context) -> RTResult[Value]:
        """Check if key exists."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            return res.failure(
                RTError(key.pos_start, key.pos_end, "Key must be a string", ctx)
            )
        return res.success(Boolean(key.value in self._data))

    @args(["key"])
    @method
    def remove(self, ctx: Context) -> RTResult[Value]:
        """Remove a key-value pair."""
        res = RTResult[Value]()
        key = ctx.symbol_table.get("key")
        if not isinstance(key, String):
            return res.failure(
                RTError(key.pos_start, key.pos_end, "Key must be a string", ctx)
            )
        if key.value not in self._data:
            return res.failure(
                RTError(key.pos_start, key.pos_end, f"Key '{key.value}' not found", ctx)
            )
        del self._data[key.value]
        return res.success(Null.null())

    @args([])
    @method
    def length(self, _ctx: Context) -> RTResult[Value]:
        """Return the number of key-value pairs."""
        return RTResult[Value]().success(Number(len(self._data)))

    @args([])
    @method
    def clear(self, _ctx: Context) -> RTResult[Value]:
        """Remove all key-value pairs."""
        self._data.clear()
        return RTResult[Value]().success(Null.null())

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Convert hashmap to string."""
        return RTResult[Value]().success(String(str(HashMap(self._data))))
