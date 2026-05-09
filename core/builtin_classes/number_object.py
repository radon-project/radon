"""Built-in Number wrapper class for objective method access."""

import math

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class NumberObject(BuiltInObject):
    """Built-in Number wrapper for objective method access.

    A Number represents both integers and floating-point values.

    Methods:
        to_string()         - Convert to string representation
        abs()               - Get absolute value
        round(digits=0)     - Round to decimal places
        floor()             - Round down to nearest integer
        ceil()              - Round up to nearest integer
        is_int()            - Check if value is an integer
        is_float()          - Check if value has decimal part
        is_even()           - Check if integer is even
        is_odd()            - Check if integer is odd
        is_positive()       - Check if value is positive
        is_negative()       - Check if value is negative
        is_zero()           - Check if value is zero
        sqrt()              - Square root
        pow(exp)            - Raise to power
        log(base=e)         - Logarithm (natural by default)
        log10()             - Base-10 logarithm
        log2()              - Base-2 logarithm
        exp()               - e raised to this power
        sin()               - Sine (radians)
        cos()               - Cosine (radians)
        tan()               - Tangent (radians)
        asin()              - Arcsine (returns radians)
        acos()              - Arccosine (returns radians)
        atan()              - Arctangent (returns radians)
        sinh()              - Hyperbolic sine
        cosh()              - Hyperbolic cosine
        tanh()              - Hyperbolic tangent
        to_radians()        - Convert degrees to radians
        to_degrees()        - Convert radians to degrees
        sign()              - Return sign (-1, 0, or 1)
        clamp(min, max)     - Clamp value to range
        mod(divisor)        - Modulo operation
        div(divisor)        - Integer division

    Example:
        var n = 42
        n.to_string()       # "42"
        n.is_even()         # true
        (-5).abs()          # 5
        (3.14159).round(2)  # 3.14
        (16).sqrt()         # 4
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
        """Convert the number to its string representation."""
        if self.value == int(self.value):
            return RTResult[Value]().success(String(str(int(self.value))))
        return RTResult[Value]().success(String(str(self.value)))

    @args([])
    @method
    def abs(self, _ctx: Context) -> RTResult[Value]:
        """Return the absolute value of the number."""
        return RTResult[Value]().success(Number(abs(self.value)))

    @args(["digits"], [Number(0)])
    @method
    def round(self, ctx: Context) -> RTResult[Value]:
        """Round to the given number of decimal places."""
        res = RTResult[Value]()
        digits = ctx.symbol_table.get("digits")
        if not isinstance(digits, Number):
            assert digits is not None
            return res.failure(
                RTError(digits.pos_start, digits.pos_end, "Digits must be a number", ctx)
            )
        return res.success(Number(round(self.value, int(digits.value))))

    @args([])
    @method
    def floor(self, _ctx: Context) -> RTResult[Value]:
        """Return the largest integer less than or equal to the number."""
        return RTResult[Value]().success(Number(math.floor(self.value)))

    @args([])
    @method
    def ceil(self, _ctx: Context) -> RTResult[Value]:
        """Return the smallest integer greater than or equal to the number."""
        return RTResult[Value]().success(Number(math.ceil(self.value)))

    @args([])
    @method
    def is_int(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number is an integer (has no decimal part)."""
        return RTResult[Value]().success(Boolean(self.value == int(self.value)))

    @args([])
    @method
    def is_float(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number has a decimal part."""
        return RTResult[Value]().success(Boolean(self.value != int(self.value)))

    @args([])
    @method
    def is_even(self, ctx: Context) -> RTResult[Value]:
        """Check if the integer is even."""
        res = RTResult[Value]()
        if self.value != int(self.value):
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "is_even() requires an integer", ctx)
            )
        return res.success(Boolean(int(self.value) % 2 == 0))

    @args([])
    @method
    def is_odd(self, ctx: Context) -> RTResult[Value]:
        """Check if the integer is odd."""
        res = RTResult[Value]()
        if self.value != int(self.value):
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "is_odd() requires an integer", ctx)
            )
        return res.success(Boolean(int(self.value) % 2 == 1))

    @args([])
    @method
    def is_positive(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number is positive (greater than zero)."""
        return RTResult[Value]().success(Boolean(self.value > 0))

    @args([])
    @method
    def is_negative(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number is negative (less than zero)."""
        return RTResult[Value]().success(Boolean(self.value < 0))

    @args([])
    @method
    def is_zero(self, _ctx: Context) -> RTResult[Value]:
        """Check if the number is zero."""
        return RTResult[Value]().success(Boolean(self.value == 0))

    @args([])
    @method
    def sqrt(self, ctx: Context) -> RTResult[Value]:
        """Return the square root of the number."""
        res = RTResult[Value]()
        if self.value < 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Cannot take square root of negative number", ctx)
            )
        return res.success(Number(math.sqrt(self.value)))

    @args(["exp"])
    @method
    def pow(self, ctx: Context) -> RTResult[Value]:
        """Raise the number to the given power."""
        res = RTResult[Value]()
        exp = ctx.symbol_table.get("exp")
        assert exp is not None
        if not isinstance(exp, Number):
            return res.failure(
                RTError(exp.pos_start, exp.pos_end, "Exponent must be a number", ctx)
            )
        try:
            return res.success(Number(math.pow(self.value, exp.value)))
        except ValueError as e:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, str(e), ctx)
            )

    @args(["base"], [Null.null()])
    @method
    def log(self, ctx: Context) -> RTResult[Value]:
        """Return the logarithm (natural log by default, or specify base)."""
        res = RTResult[Value]()
        if self.value <= 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Cannot take logarithm of non-positive number", ctx)
            )
        base = ctx.symbol_table.get("base")
        assert base is not None
        if isinstance(base, Null):
            return res.success(Number(math.log(self.value)))
        if not isinstance(base, Number):
            return res.failure(
                RTError(base.pos_start, base.pos_end, "Base must be a number", ctx)
            )
        if base.value <= 0 or base.value == 1:
            return res.failure(
                RTError(base.pos_start, base.pos_end, "Base must be positive and not equal to 1", ctx)
            )
        return res.success(Number(math.log(self.value, base.value)))

    @args([])
    @method
    def log10(self, ctx: Context) -> RTResult[Value]:
        """Return the base-10 logarithm of the number."""
        res = RTResult[Value]()
        if self.value <= 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Cannot take logarithm of non-positive number", ctx)
            )
        return res.success(Number(math.log10(self.value)))

    @args([])
    @method
    def log2(self, ctx: Context) -> RTResult[Value]:
        """Return the base-2 logarithm of the number."""
        res = RTResult[Value]()
        if self.value <= 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Cannot take logarithm of non-positive number", ctx)
            )
        return res.success(Number(math.log2(self.value)))

    @args([])
    @method
    def exp(self, _ctx: Context) -> RTResult[Value]:
        """Return e raised to the power of this number."""
        return RTResult[Value]().success(Number(math.exp(self.value)))

    @args([])
    @method
    def sin(self, _ctx: Context) -> RTResult[Value]:
        """Return the sine of the number (in radians)."""
        return RTResult[Value]().success(Number(math.sin(self.value)))

    @args([])
    @method
    def cos(self, _ctx: Context) -> RTResult[Value]:
        """Return the cosine of the number (in radians)."""
        return RTResult[Value]().success(Number(math.cos(self.value)))

    @args([])
    @method
    def tan(self, _ctx: Context) -> RTResult[Value]:
        """Return the tangent of the number (in radians)."""
        return RTResult[Value]().success(Number(math.tan(self.value)))

    @args([])
    @method
    def asin(self, ctx: Context) -> RTResult[Value]:
        """Return the arcsine of the number (result in radians)."""
        res = RTResult[Value]()
        if self.value < -1 or self.value > 1:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "asin() argument must be in range [-1, 1]", ctx)
            )
        return res.success(Number(math.asin(self.value)))

    @args([])
    @method
    def acos(self, ctx: Context) -> RTResult[Value]:
        """Return the arccosine of the number (result in radians)."""
        res = RTResult[Value]()
        if self.value < -1 or self.value > 1:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "acos() argument must be in range [-1, 1]", ctx)
            )
        return res.success(Number(math.acos(self.value)))

    @args([])
    @method
    def atan(self, _ctx: Context) -> RTResult[Value]:
        """Return the arctangent of the number (result in radians)."""
        return RTResult[Value]().success(Number(math.atan(self.value)))

    @args([])
    @method
    def sinh(self, _ctx: Context) -> RTResult[Value]:
        """Return the hyperbolic sine of the number."""
        return RTResult[Value]().success(Number(math.sinh(self.value)))

    @args([])
    @method
    def cosh(self, _ctx: Context) -> RTResult[Value]:
        """Return the hyperbolic cosine of the number."""
        return RTResult[Value]().success(Number(math.cosh(self.value)))

    @args([])
    @method
    def tanh(self, _ctx: Context) -> RTResult[Value]:
        """Return the hyperbolic tangent of the number."""
        return RTResult[Value]().success(Number(math.tanh(self.value)))

    @args([])
    @method
    def to_radians(self, _ctx: Context) -> RTResult[Value]:
        """Convert degrees to radians."""
        return RTResult[Value]().success(Number(math.radians(self.value)))

    @args([])
    @method
    def to_degrees(self, _ctx: Context) -> RTResult[Value]:
        """Convert radians to degrees."""
        return RTResult[Value]().success(Number(math.degrees(self.value)))

    @args([])
    @method
    def sign(self, _ctx: Context) -> RTResult[Value]:
        """Return the sign of the number: -1, 0, or 1."""
        if self.value > 0:
            return RTResult[Value]().success(Number(1))
        elif self.value < 0:
            return RTResult[Value]().success(Number(-1))
        else:
            return RTResult[Value]().success(Number(0))

    @args(["min_val", "max_val"])
    @method
    def clamp(self, ctx: Context) -> RTResult[Value]:
        """Clamp the number to be within the given range."""
        res = RTResult[Value]()
        min_val = ctx.symbol_table.get("min_val")
        max_val = ctx.symbol_table.get("max_val")
        assert min_val is not None and max_val is not None
        if not isinstance(min_val, Number):
            return res.failure(
                RTError(min_val.pos_start, min_val.pos_end, "Min must be a number", ctx)
            )
        if not isinstance(max_val, Number):
            return res.failure(
                RTError(max_val.pos_start, max_val.pos_end, "Max must be a number", ctx)
            )
        clamped = max(min_val.value, min(self.value, max_val.value))
        return res.success(Number(clamped))

    @args(["divisor"])
    @method
    def mod(self, ctx: Context) -> RTResult[Value]:
        """Return the modulo (remainder) of division by divisor."""
        res = RTResult[Value]()
        divisor = ctx.symbol_table.get("divisor")
        assert divisor is not None
        if not isinstance(divisor, Number):
            return res.failure(
                RTError(divisor.pos_start, divisor.pos_end, "Divisor must be a number", ctx)
            )
        if divisor.value == 0:
            return res.failure(
                RTError(divisor.pos_start, divisor.pos_end, "Division by zero", ctx)
            )
        return res.success(Number(self.value % divisor.value))

    @args(["divisor"])
    @method
    def div(self, ctx: Context) -> RTResult[Value]:
        """Return the integer division result."""
        res = RTResult[Value]()
        divisor = ctx.symbol_table.get("divisor")
        assert divisor is not None
        if not isinstance(divisor, Number):
            return res.failure(
                RTError(divisor.pos_start, divisor.pos_end, "Divisor must be a number", ctx)
            )
        if divisor.value == 0:
            return res.failure(
                RTError(divisor.pos_start, divisor.pos_end, "Division by zero", ctx)
            )
        return res.success(Number(int(self.value // divisor.value)))
