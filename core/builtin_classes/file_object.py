from typing import IO

from core.builtin_classes.base_classes import (BuiltInObject, check, method,
                                               operator)
from core.builtin_funcs import args
from core.datatypes import *
from core.errors import *
from core.parser import RTResult


class FileObject(BuiltInObject):
    file: IO[str]

    @operator("__constructor__")
    @check([String, String], [None, String("r")])
    def constructor(self, path: String, mode: String) -> RTResult[Value]:
        allowed_modes = [None, "r", "w", "a", "r+", "w+", "a+"]  # Allowed modes for opening files
        res = RTResult[Value]()
        if mode.value not in allowed_modes:
            return res.failure(RTError(mode.pos_start, mode.pos_end, f"Invalid mode '{mode.value}'", mode.context))
        try:
            self.file = open(path.value, mode.value)
        except OSError as e:
            return res.failure(
                RTError(path.pos_start, path.pos_end, f"Could not open file {path.value}: {e}", path.context)
            )
        return res.success(Null.null())

    @args(["count"], [Number(-1)])
    @method
    def read(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        count = ctx.symbol_table.get("count")
        assert count is not None
        if not isinstance(count, Number):
            return res.failure(RTError(count.pos_start, count.pos_end, "Count must be a number", count.context))

        try:
            if count.value == -1:
                value = self.file.read()
            else:
                value = self.file.read(int(count.value))
            return res.success(String(value))
        except OSError as e:
            return res.failure(
                RTError(count.pos_start, count.pos_end, f"Could not read from file: {e.strerror}", count.context)
            )

    @args([])
    @method
    def readline(self, ctx: Context):
        res = RTResult[Value]()
        try:
            value = self.file.readline()
            return res.success(String(value))
        except OSError as e:
            pos = Position(-1, -1, -1, "<idk>", "<idk>")
            return res.failure(RTError(pos, pos, f"Could not read from file: {e.strerror}", ctx))

    @args([])
    @method
    def readlines(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        try:
            value = self.file.readlines()
            return res.success(Array([String(line) for line in value]))
        except OSError as e:
            pos = Position(-1, -1, -1, "<idk>", "<idk>")
            return res.failure(RTError(pos, pos, f"Could not read from file: {e.strerror}", ctx))

    @args(["data"])
    @method
    def write(self, ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        data = ctx.symbol_table.get("data")
        assert data is not None
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
    def close(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        self.file.close()
        return res.success(Null.null())

    @args([])
    @method
    def is_closed(self, _ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        return res.success(Boolean(self.file.closed))
