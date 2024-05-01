from core.errors import *
from core.datatypes import *
from core.parser import RTResult
from core.builtin_funcs import args
from core.builtin_classes.base_classes import BuiltInObject, operator, check, method


class FileObject(BuiltInObject):
    @operator("__constructor__")
    @check([String, String], [None, String("r")])
    def constructor(self, path, mode):
        allowed_modes = [None, "r", "w", "a", "r+", "w+", "a+"]  # Allowed modes for opening files
        res = RTResult()
        if mode.value not in allowed_modes:
            return res.failure(RTError(mode.pos_start, mode.pos_end, f"Invalid mode '{mode.value}'", mode.context))
        try:
            self.file = open(path.value, mode.value)
        except OSError as e:
            return res.failure(
                RTError(path.pos_start, path.pos_end, f"Could not open file {path.value}: {e}", path.context)
            )
        return res.success(None)

    @args(["count"], [Number(-1)])
    @method
    def read(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        count = ctx.symbol_table.get("count")
        if not isinstance(count, Number):
            return res.failure(RTError(count.pos_start, count.pos_end, "Count must be a number", count.context))

        try:
            if count.value == -1:
                value = self.file.read()
            else:
                value = self.file.read(count.value)
            return res.success(String(value))
        except OSError as e:
            return res.failure(
                RTError(count.pos_start, count.pos_end, f"Could not read from file: {e.strerror}", count.context)
            )

    @args([])
    @method
    def readline(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        try:
            value = self.file.readline()
            return res.success(String(value))
        except OSError as e:
            return res.failure(RTError(None, None, f"Could not read from file: {e.strerror}", None))

    @args([])
    @method
    def readlines(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        try:
            value = self.file.readlines()
            return res.success(Array([String(line) for line in value]))
        except OSError as e:
            return res.failure(RTError(None, None, f"Could not read from file: {e.strerror}", None))

    @args(["data"])
    @method
    def write(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        data = ctx.symbol_table.get("data")
        if not isinstance(data, String):
            return res.failure(RTError(data.pos_start, data.pos_end, "Data must be a string", data.context))

        try:
            bytes_written = self.file.write(data.value)
            return res.success(Number(bytes_written))
        except OSError as e:
            return res.failure(
                RTError(data.pos_start, data.pos_end, f"Could not read from file: {e.strerror}", data.context)
            )

    @args([])
    @method
    def close(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        self.file.close()
        return res.success(Null.null())

    @args([])
    @method
    def is_closed(ctx):
        res = RTResult()
        self = ctx.symbol_table.get("this")
        return res.success(Boolean(self.file.closed))
