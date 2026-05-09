"""Built-in Boolean wrapper class for objective method access."""

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult


class BooleanObject(BuiltInObject):
    """Built-in Boolean wrapper for objective method access.

    A Boolean represents a logical true or false value.

    Methods:
        to_string()         - Convert to "true" or "false"
        to_number()         - Convert to 1 or 0
        toggle()            - Return the opposite boolean value
        and_(other)         - Logical AND with another value
        or_(other)          - Logical OR with another value
        xor(other)          - Logical XOR with another value
        not_()              - Logical NOT (same as toggle)
        implies(other)      - Logical implication (this -> other)
        equals(other)       - Check equality with another boolean

    Operators:
        bool1 && bool2      - Logical AND
        bool1 || bool2      - Logical OR
        !bool               - Logical NOT
        bool1 == bool2      - Equality check

    Example:
        var b = true
        b.to_string()       # "true"
        b.toggle()          # false
        b.and_(false)       # false
        b.or_(false)        # true
    """

    value: bool

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing boolean or convert from any value."""
        if len(args_list) == 1 and isinstance(args_list[0], Boolean):
            self.value = args_list[0].value
        elif len(args_list) == 0:
            self.value = False
        else:
            # Convert to boolean
            self.value = args_list[0].is_true()
        return RTResult[Value]().success(Null.null())

    def __string_display__(self) -> str:
        return "true" if self.value else "false"

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Convert the boolean to its string representation ("true" or "false")."""
        return RTResult[Value]().success(String("true" if self.value else "false"))

    @args([])
    @method
    def to_number(self, _ctx: Context) -> RTResult[Value]:
        """Convert the boolean to a number (1 for true, 0 for false)."""
        return RTResult[Value]().success(Number(1 if self.value else 0))

    @args([])
    @method
    def toggle(self, _ctx: Context) -> RTResult[Value]:
        """Return the opposite boolean value."""
        return RTResult[Value]().success(Boolean(not self.value))

    @args(["other"])
    @method
    def and_(self, ctx: Context) -> RTResult[Value]:
        """Perform logical AND with another value."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        return res.success(Boolean(self.value and other.is_true()))

    @args(["other"])
    @method
    def or_(self, ctx: Context) -> RTResult[Value]:
        """Perform logical OR with another value."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        return res.success(Boolean(self.value or other.is_true()))

    @args(["other"])
    @method
    def xor(self, ctx: Context) -> RTResult[Value]:
        """Perform logical XOR with another value."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        return res.success(Boolean(self.value != other.is_true()))

    @args([])
    @method
    def not_(self, _ctx: Context) -> RTResult[Value]:
        """Return the logical NOT of this boolean."""
        return RTResult[Value]().success(Boolean(not self.value))

    @args(["other"])
    @method
    def implies(self, ctx: Context) -> RTResult[Value]:
        """Perform logical implication (this -> other). True unless this is true and other is false."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        # Implication: P -> Q is equivalent to (not P) or Q
        return res.success(Boolean((not self.value) or other.is_true()))

    @args(["other"])
    @method
    def equals(self, ctx: Context) -> RTResult[Value]:
        """Check if this boolean equals another boolean value."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("other")
        assert other is not None
        if not isinstance(other, Boolean):
            return res.failure(RTError(other.pos_start, other.pos_end, "Can only compare with another boolean", ctx))
        return res.success(Boolean(self.value == other.value))
