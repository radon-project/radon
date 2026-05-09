"""Built-in Number wrapper class for objective method access."""

import math

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class NumberObject(BuiltInObject):
    """Built-in Number manipulation object.

    Provides objective method syntax for Number values.
    Example: (42).to_string(), (-5).abs(), (3.14).round(2)
    """

    value: float

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing number."""
        if len(args_list) == 1 and isinstance(args_list[0], Number):
            self.value = args_list[0].value
        elif len(args_list) == 0:
            self.value = 0
        else:
            return RTResult[Value]().failure(
                RTError(
                    args_list[0].pos_start,
                    args_list[0].pos_end,
                    "NumberObject constructor expects a Number",
                    args_list[0].context,
                )
            )
        return RTResult[Value]().success(Null.null())

    def __string_display__(self) -> str:
        if self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Convert number to string."""
        if self.value == int(self.value):
            return RTResult[Value]().success(String(str(int(self.value))))
        return RTResult[Value]().success(String(str(self.value)))

    @args([])
    @method
    def abs(self, _ctx: Context) -> RTResult[Value]:
        """Return absolute value."""
        return RTResult[Value]().success(Number(abs(self.value)))

    @args(["digits"], [Number(0)])
    @method
    def round(self, ctx: Context) -> RTResult[Value]:
        """Round to given number of decimal places."""
        res = RTResult[Value]()
        digits = ctx.symbol_table.get("digits")
        if not isinstance(digits, Number):
            return res.failure(
                RTError(digits.pos_start, digits.pos_end, "Digits must be a number", ctx)
            )
        return res.success(Number(round(self.value, int(digits.value))))

    @args([])
    @method
    def floor(self, _ctx: Context) -> RTResult[Value]:
        """Return the floor of the number."""
        return RTResult[Value]().success(Number(math.floor(self.value)))

    @args([])
    @method
    def ceil(self, _ctx: Context) -> RTResult[Value]:
        """Return the ceiling of the number."""
        return RTResult[Value]().success(Number(math.ceil(self.value)))

    @args([])
    @method
    def is_int(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number is an integer."""
        return RTResult[Value]().success(Boolean(self.value == int(self.value)))
