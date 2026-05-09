"""Built-in Array wrapper class for objective method access."""

from typing import TYPE_CHECKING

from core.builtin_classes.base_classes import BuiltInObject, method, operator
from core.builtin_funcs import args
from core.datatypes import Array, Boolean, Null, Number, String, Value
from core.errors import RTError
from core.parser import Context, RTResult

if TYPE_CHECKING:
    pass


class ArrayObject(BuiltInObject):
    """Built-in Array manipulation object.

    Provides objective method syntax for Array values.
    Example: arr.append(1), arr.pop(), arr.find(x)
    """

    # Store reference to the wrapped array
    elements: list[Value]

    @operator("__constructor__")
    def constructor(self, args_list: list[Value]) -> RTResult[Value]:
        """Initialize with an existing array or create empty."""
        if len(args_list) == 1 and isinstance(args_list[0], Array):
            self.elements = args_list[0].elements
        elif len(args_list) == 0:
            self.elements = []
        else:
            self.elements = list(args_list)
        return RTResult[Value]().success(Null.null())

    def __string_display__(self) -> str:
        return str(Array(self.elements))

    def __len__(self) -> int:
        return len(self.elements)

    @args(["value"])
    @method
    def append(self, ctx: Context) -> RTResult[Value]:
        """Append a value to the array."""
        res = RTResult[Value]()
        value = ctx.symbol_table.get("value")
        assert value is not None
        self.elements.append(value)
        return res.success(Null.null())

    @args(["index"], [Number(-1)])
    @method
    def pop(self, ctx: Context) -> RTResult[Value]:
        """Remove and return the element at the given index (default: last)."""
        res = RTResult[Value]()
        index = ctx.symbol_table.get("index")
        assert index is not None
        if not isinstance(index, Number):
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index must be a number", ctx)
            )
        try:
            element = self.elements.pop(int(index.value))
        except IndexError:
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Pop index out of range", ctx)
            )
        return res.success(element)

    @args(["array"])
    @method
    def extend(self, ctx: Context) -> RTResult[Value]:
        """Extend the array with another array."""
        res = RTResult[Value]()
        other = ctx.symbol_table.get("array")
        assert other is not None
        if not isinstance(other, Array):
            return res.failure(
                RTError(other.pos_start, other.pos_end, "Argument must be an array", ctx)
            )
        self.elements.extend(other.elements)
        return res.success(Null.null())

    @args(["element"])
    @method
    def find(self, ctx: Context) -> RTResult[Value]:
        """Find the index of an element in the array (-1 if not found)."""
        res = RTResult[Value]()
        element = ctx.symbol_table.get("element")
        assert element is not None
        for i, val in enumerate(self.elements):
            cmp, err = val.get_comparison_eq(element)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                return res.success(Number(i))
        return res.success(Number(-1))

    @args(["func"])
    @method
    def map(self, ctx: Context) -> RTResult[Value]:
        """Map a function over the array elements."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        new_elements: list[Value] = []
        for element in self.elements:
            result = res.register(func.execute([element], {}))
            if res.should_return():
                return res
            assert result is not None
            new_elements.append(result)

        return res.success(Array(new_elements))

    @args([])
    @method
    def is_empty(self, _ctx: Context) -> RTResult[Value]:
        """Check if the array is empty."""
        return RTResult[Value]().success(
            Boolean.true() if len(self.elements) == 0 else Boolean.false()
        )

    @args([])
    @method
    def to_string(self, _ctx: Context) -> RTResult[Value]:
        """Convert the array to a string."""
        return RTResult[Value]().success(String(str(Array(self.elements))))

    @args([])
    @method
    def length(self, _ctx: Context) -> RTResult[Value]:
        """Return the length of the array."""
        return RTResult[Value]().success(Number(len(self.elements)))

    @args([])
    @method
    def copy(self, _ctx: Context) -> RTResult[Value]:
        """Return a shallow copy of the array."""
        return RTResult[Value]().success(Array(self.elements[:]))

    @args([])
    @method
    def reverse(self, _ctx: Context) -> RTResult[Value]:
        """Reverse the array in place."""
        self.elements.reverse()
        return RTResult[Value]().success(Null.null())

    @args([])
    @method
    def clear(self, _ctx: Context) -> RTResult[Value]:
        """Remove all elements from the array."""
        self.elements.clear()
        return RTResult[Value]().success(Null.null())
