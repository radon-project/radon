import json

from core.builtin_classes.base_classes import BuiltInObject, check, method, operator
from core.builtin_funcs import args
from core.datatypes import Null, String, Value, deradonify, radonify
from core.errors import RTError
from core.parser import Context, RTResult


class JSONObject(BuiltInObject):
    """Buili-in json manipulation object."""

    @operator("__constructor__")
    @check([], [])
    def constructor(self) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null())

    @args(["radon_object"])
    @method
    def dumps(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        radon_object = ctx.symbol_table.get("radon_object")
        assert radon_object is not None
        try:
            return res.success(String(json.dumps(deradonify(radon_object))))
        except Exception as e:
            return res.failure(
                RTError(radon_object.pos_start, radon_object.pos_end, f"Error dumping object: {str(e)}", ctx)
            )

    @args(["radon_string"])
    @method
    def loads(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        radon_string = ctx.symbol_table.get("radon_string")
        assert radon_string is not None
        if not isinstance(radon_string, String):
            return res.failure(RTError(radon_string.pos_start, radon_string.pos_end, "Cannot loads a non-string", ctx))
        try:
            return res.success(
                radonify(
                    json.loads(radon_string.value), radon_string.pos_start, radon_string.pos_end, radon_string.context
                )
            )
        except Exception as e:
            return res.failure(
                RTError(radon_string.pos_start, radon_string.pos_end, f"Error loading object: {str(e)}", ctx)
            )
