from core.builtin_classes.base_classes import BuiltInObject, check, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, Null, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class BuiltinsObject(BuiltInObject):
    """Buili-in builtins manipulation object."""

    @operator("__constructor__")
    @check([], [])
    def constructor(self) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null())

    @args([])
    @method
    def show(self, ctx: Context) -> RTResult[Value]:
        from core.builtin_funcs import global_symbol_table  # Lazy import

        return RTResult[Value]().success(Array(list(map(String, global_symbol_table.symbols.keys()))))

    @args(["name", "obj"])
    @method
    def set(self, ctx: Context) -> RTResult[Value]:
        from core.builtin_funcs import global_symbol_table  # Lazy import

        res = RTResult[Value]()
        name = ctx.symbol_table.get("name")
        obj = ctx.symbol_table.get("obj")

        assert name is not None
        assert obj is not None

        if not isinstance(name, String):
            return res.failure(RTError(name.pos_start, name.pos_end, "Can't set a non-string", ctx))

        # if not isinstance(obj, Value):
        #     return res.failure(RTError(obj.pos_start, obj.pos_end, "Can't set a non-value", ctx))

        try:
            global_symbol_table.set(str(name), obj)
            return res.success(Boolean(True))
        except Exception as e:
            return res.failure(RTError(name.pos_start, obj.pos_end, f"Error settting builtins: {str(e)}", ctx))

    @args(["name"])
    @method
    def remove(self, ctx: Context) -> RTResult[Value]:
        from core.builtin_funcs import global_symbol_table  # Lazy import

        res = RTResult[Value]()
        name = ctx.symbol_table.get("name")
        assert name is not None

        if not isinstance(name, String):
            return res.failure(RTError(name.pos_start, name.pos_end, "Can't set a non-string", ctx))

        global_symbol_table.remove(str(name))
        try:
            return res.success(Boolean(True))
        except Exception as e:
            return res.failure(RTError(name.pos_start, name.pos_end, f"Error removing builtins: {str(e)}", ctx))
