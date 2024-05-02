from core.errors import *
from core.datatypes import *
from core.parser import RTResult
from core.builtin_funcs import args
from core.builtin_classes.base_classes import BuiltInObject, operator, check, method
from core.datatypes import radonify, deradonify

import json


class JSONObject(BuiltInObject):
    @operator("__constructor__")
    @check([], [])
    def constructor(self):
        return RTResult().success(Null.null())

    @args(["radon_object"])
    @method
    def dumps(ctx):
        res = RTResult()
        radon_object = ctx.symbol_table.get("radon_object")
        try:
            return res.success(String(json.dumps(deradonify(radon_object))))
        except Exception as e:
            return res.failure(
                RTError(radon_object.pos_start, radon_object.pos_end, f"Error dumping object: {str(e)}", ctx)
            )

    @args(["radon_string"])
    @method
    def loads(ctx):
        res = RTResult()
        radon_string = ctx.symbol_table.get("radon_string")
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
