"""Built-in Boolean wrapper class for objective method access."""

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Boolean, Null, Number, String, Value
from core.parser import Context, RTResult


class BooleanObject(BuiltInObject):
    """Built-in Boolean manipulation object.

    Provides objective method syntax for Boolean values.
    Example: true.to_string(), false.to_number()
    """

    value: bool

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing boolean."""
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
        """Convert boolean to string."""
        return RTResult[Value]().success(String("true" if self.value else "false"))

    @args([])
    @method
    def to_number(self, _ctx: Context) -> RTResult[Value]:
        """Convert boolean to number (1 or 0)."""
        return RTResult[Value]().success(Number(1 if self.value else 0))
