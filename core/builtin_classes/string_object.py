from core.errors import *
from core.datatypes import *
from core.parser import RTResult
from core.builtin_funcs import args
from core.builtin_classes.base_classes import BuiltInObject, operator, check, method


class StringObject(BuiltInObject):
    @operator("__constructor__")
    @check([String], [String("")])
    def constructor(self, string: String):
        self.value: str = string.value
        return RTResult().success(None)

    @operator("__add__")
    @check([String])
    def add(self, other):
        res = RTResult()
        return res.success(String(self.value + other.value))

    @args([])
    @method
    def upper(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(String(self.value.upper()))

    @args([])
    @method
    def lower(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(String(self.value.lower()))

    @args([])
    @method
    def title(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(String(self.value.title()))

    @args([])
    @method
    def capitalize(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(String(self.value.capitalize()))

    @args([])
    @method
    def swapcase(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(String(self.value.swapcase()))

    @args([])
    @method
    def length(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(Number(len(self.value)))

    @args(["string"], [String("")])
    @method
    def count(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        if len(string.value) == 0:
            return res.failure(
                RTError(string.pos_start, string.pos_end, "Cannot count an empty string", string.context)
            )
        return res.success(Number(self.value.count(string.value)))
