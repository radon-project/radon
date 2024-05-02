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
        return RTResult[Value]().success(Null.null())

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

    @args(["string", "value"], [String(""), String("")])
    @method
    def replace(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        value = ctx.symbol_table.get("value")
        return res.success(String(self.value.replace(string.value, value.value)))

    @args(["string"], [String("")])
    @method
    def find(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(Number(self.value.find(string.value)))

    @args(["string"], [String("")])
    @method
    def startswith(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(Boolean(self.value.startswith(string.value)))

    @args(["string"], [String("")])
    @method
    def endswith(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(Boolean(self.value.endswith(string.value)))

    @args(["string"], [String("")])
    @method
    def split(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(Array([String(i) for i in self.value.split(string.value)]))

    @args(["string"], [String("")])
    @method
    def join(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(String(string.value.join(self.value)))

    @args(["string"], [String("")])
    @method
    def strip(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(String(self.value.strip(string.value)))

    @args(["string"], [String("")])
    @method
    def lstrip(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(String(self.value.lstrip(string.value)))

    @args(["string"], [String("")])
    @method
    def rstrip(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        string = ctx.symbol_table.get("string")
        return res.success(String(self.value.rstrip(string.value)))
