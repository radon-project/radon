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
    """Built-in Array wrapper for objective method access.

    An Array is an ordered, mutable collection of elements.

    Methods:
        append(value)       - Add element to end
        pop(index=-1)       - Remove and return element at index
        extend(array)       - Extend with another array
        find(element)       - Find index of element (-1 if not found)
        index_of(element)   - Alias for find
        includes(element)   - Check if element exists in array
        map(func)           - Transform each element with function
        filter(func)        - Filter elements by predicate function
        is_empty()          - Check if array is empty
        to_string()         - Convert to string representation
        length()            - Get number of elements
        copy()              - Create shallow copy
        reverse()           - Reverse in place
        clear()             - Remove all elements
        get(index)          - Get element at index
        set(index, value)   - Set element at index
        insert(index, value)- Insert element at index
        remove(value)       - Remove first occurrence of value
        slice(start, end)   - Get sub-array from start to end
        chunk(size)         - Split into sub-arrays of given size
        join(separator)     - Join elements into string
        first()             - Get first element
        last()              - Get last element
        count(element)      - Count occurrences of element
        sum()               - Sum all numeric elements
        min()               - Get minimum element
        max()               - Get maximum element
        sort(reverse)       - Sort in place
        unique()            - Remove duplicates
        every(func)         - Check if all elements satisfy predicate
        some(func)          - Check if any element satisfies predicate

    Operators:
        arr1 + arr2         - Concatenate arrays
        arr * n             - Repeat array n times
        x in arr            - Check membership
        arr[i]              - Get element at index
        len(arr)            - Get length

    Example:
        var arr = [1, 2, 3]
        arr.append(4)       # [1, 2, 3, 4]
        arr.pop()           # returns 4, arr is [1, 2, 3]
        arr.reverse()       # [3, 2, 1]
        arr.map(fun(x) -> x * 2)  # [6, 4, 2]
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

    @args(["index"])
    @method
    def get(self, ctx: Context) -> RTResult[Value]:
        """Get element at the specified index."""
        res = RTResult[Value]()
        index = ctx.symbol_table.get("index")
        assert index is not None
        if not isinstance(index, Number):
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index must be a number", ctx)
            )
        try:
            element = self.elements[int(index.value)]
            return res.success(element)
        except IndexError:
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index out of range", ctx)
            )

    @args(["index", "value"])
    @method
    def set(self, ctx: Context) -> RTResult[Value]:
        """Set element at the specified index."""
        res = RTResult[Value]()
        index = ctx.symbol_table.get("index")
        value = ctx.symbol_table.get("value")
        assert index is not None and value is not None
        if not isinstance(index, Number):
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index must be a number", ctx)
            )
        try:
            self.elements[int(index.value)] = value
            return res.success(Null.null())
        except IndexError:
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index out of range", ctx)
            )

    @args(["index", "value"])
    @method
    def insert(self, ctx: Context) -> RTResult[Value]:
        """Insert element at the specified index."""
        res = RTResult[Value]()
        index = ctx.symbol_table.get("index")
        value = ctx.symbol_table.get("value")
        assert index is not None and value is not None
        if not isinstance(index, Number):
            return res.failure(
                RTError(index.pos_start, index.pos_end, "Index must be a number", ctx)
            )
        self.elements.insert(int(index.value), value)
        return res.success(Null.null())

    @args(["value"])
    @method
    def remove(self, ctx: Context) -> RTResult[Value]:
        """Remove first occurrence of the specified value."""
        res = RTResult[Value]()
        value = ctx.symbol_table.get("value")
        assert value is not None
        for i, elem in enumerate(self.elements):
            cmp, err = elem.get_comparison_eq(value)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                self.elements.pop(i)
                return res.success(Null.null())
        return res.failure(
            RTError(value.pos_start, value.pos_end, "Value not found in array", ctx)
        )

    @args(["start", "end"], [None, Null.null()])
    @method
    def slice(self, ctx: Context) -> RTResult[Value]:
        """Get a sub-array from start to end index."""
        res = RTResult[Value]()
        start = ctx.symbol_table.get("start")
        end = ctx.symbol_table.get("end")
        assert start is not None
        if not isinstance(start, Number):
            return res.failure(
                RTError(start.pos_start, start.pos_end, "Start must be a number", ctx)
            )
        start_idx = int(start.value)
        if isinstance(end, Null):
            return res.success(Array(self.elements[start_idx:]))
        if not isinstance(end, Number):
            return res.failure(
                RTError(end.pos_start, end.pos_end, "End must be a number", ctx)
            )
        end_idx = int(end.value)
        return res.success(Array(self.elements[start_idx:end_idx]))

    @args(["size"])
    @method
    def chunk(self, ctx: Context) -> RTResult[Value]:
        """Split array into sub-arrays of the specified size."""
        res = RTResult[Value]()
        size = ctx.symbol_table.get("size")
        assert size is not None
        if not isinstance(size, Number):
            return res.failure(
                RTError(size.pos_start, size.pos_end, "Size must be a number", ctx)
            )
        chunk_size = int(size.value)
        if chunk_size <= 0:
            return res.failure(
                RTError(size.pos_start, size.pos_end, "Size must be positive", ctx)
            )
        chunks: list[Value] = []
        for i in range(0, len(self.elements), chunk_size):
            chunks.append(Array(self.elements[i : i + chunk_size]))
        return res.success(Array(chunks))

    @args(["separator"], [String("")])
    @method
    def join(self, ctx: Context) -> RTResult[Value]:
        """Join array elements into a string with separator."""
        res = RTResult[Value]()
        separator = ctx.symbol_table.get("separator")
        assert separator is not None
        if not isinstance(separator, String):
            return res.failure(
                RTError(separator.pos_start, separator.pos_end, "Separator must be a string", ctx)
            )
        parts: list[str] = []
        for elem in self.elements:
            if isinstance(elem, String):
                parts.append(elem.value)
            else:
                parts.append(str(elem))
        return res.success(String(separator.value.join(parts)))

    @args(["element"])
    @method
    def includes(self, ctx: Context) -> RTResult[Value]:
        """Check if the array contains the specified element."""
        res = RTResult[Value]()
        element = ctx.symbol_table.get("element")
        assert element is not None
        for val in self.elements:
            cmp, err = val.get_comparison_eq(element)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                return res.success(Boolean.true())
        return res.success(Boolean.false())

    @args(["element"])
    @method
    def index_of(self, ctx: Context) -> RTResult[Value]:
        """Find the index of an element (alias for find)."""
        return self.find(ctx)

    @args([])
    @method
    def first(self, ctx: Context) -> RTResult[Value]:
        """Get the first element of the array."""
        res = RTResult[Value]()
        if len(self.elements) == 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Array is empty", ctx)
            )
        return res.success(self.elements[0])

    @args([])
    @method
    def last(self, ctx: Context) -> RTResult[Value]:
        """Get the last element of the array."""
        res = RTResult[Value]()
        if len(self.elements) == 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Array is empty", ctx)
            )
        return res.success(self.elements[-1])

    @args(["element"])
    @method
    def count(self, ctx: Context) -> RTResult[Value]:
        """Count occurrences of the specified element."""
        res = RTResult[Value]()
        element = ctx.symbol_table.get("element")
        assert element is not None
        count = 0
        for val in self.elements:
            cmp, err = val.get_comparison_eq(element)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                count += 1
        return res.success(Number(count))

    @args([])
    @method
    def sum(self, ctx: Context) -> RTResult[Value]:
        """Sum all numeric elements in the array."""
        res = RTResult[Value]()
        total = 0.0
        for elem in self.elements:
            if isinstance(elem, Number):
                total += elem.value
            else:
                return res.failure(
                    RTError(elem.pos_start, elem.pos_end, "All elements must be numbers for sum()", ctx)
                )
        return res.success(Number(total))

    @args([])
    @method
    def min(self, ctx: Context) -> RTResult[Value]:
        """Get the minimum element in the array."""
        res = RTResult[Value]()
        if len(self.elements) == 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Array is empty", ctx)
            )
        min_val = self.elements[0]
        for elem in self.elements[1:]:
            cmp, err = elem.get_comparison_lt(min_val)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                min_val = elem
        return res.success(min_val)

    @args([])
    @method
    def max(self, ctx: Context) -> RTResult[Value]:
        """Get the maximum element in the array."""
        res = RTResult[Value]()
        if len(self.elements) == 0:
            return res.failure(
                RTError(self.parent_class.pos_start, self.parent_class.pos_end, "Array is empty", ctx)
            )
        max_val = self.elements[0]
        for elem in self.elements[1:]:
            cmp, err = elem.get_comparison_gt(max_val)
            if err is not None:
                return res.failure(err)
            assert cmp is not None
            if cmp.is_true():
                max_val = elem
        return res.success(max_val)

    @args(["reverse"], [Boolean.false()])
    @method
    def sort(self, ctx: Context) -> RTResult[Value]:
        """Sort the array in place."""
        res = RTResult[Value]()
        reverse = ctx.symbol_table.get("reverse")
        assert reverse is not None

        # Check all elements are comparable (all numbers or all strings)
        if len(self.elements) == 0:
            return res.success(Null.null())

        all_numbers = all(isinstance(e, Number) for e in self.elements)
        all_strings = all(isinstance(e, String) for e in self.elements)

        if not (all_numbers or all_strings):
            return res.failure(
                RTError(
                    self.parent_class.pos_start,
                    self.parent_class.pos_end,
                    "All elements must be of the same comparable type for sort()",
                    ctx,
                )
            )

        if all_numbers:
            self.elements.sort(key=lambda x: x.value, reverse=reverse.is_true())  # type: ignore
        else:
            self.elements.sort(key=lambda x: x.value, reverse=reverse.is_true())  # type: ignore

        return res.success(Null.null())

    @args([])
    @method
    def unique(self, _ctx: Context) -> RTResult[Value]:
        """Return a new array with duplicate elements removed."""
        seen: list[Value] = []
        result: list[Value] = []
        for elem in self.elements:
            is_duplicate = False
            for s in seen:
                cmp, _ = elem.get_comparison_eq(s)
                if cmp is not None and cmp.is_true():
                    is_duplicate = True
                    break
            if not is_duplicate:
                seen.append(elem)
                result.append(elem)
        return RTResult[Value]().success(Array(result))

    @args(["func"])
    @method
    def filter(self, ctx: Context) -> RTResult[Value]:
        """Filter elements by a predicate function."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        filtered: list[Value] = []
        for element in self.elements:
            result = res.register(func.execute([element], {}))
            if res.should_return():
                return res
            assert result is not None
            if result.is_true():
                filtered.append(element)

        return res.success(Array(filtered))

    @args(["func"])
    @method
    def every(self, ctx: Context) -> RTResult[Value]:
        """Check if all elements satisfy the predicate function."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        for element in self.elements:
            result = res.register(func.execute([element], {}))
            if res.should_return():
                return res
            assert result is not None
            if not result.is_true():
                return res.success(Boolean.false())

        return res.success(Boolean.true())

    @args(["func"])
    @method
    def some(self, ctx: Context) -> RTResult[Value]:
        """Check if any element satisfies the predicate function."""
        res = RTResult[Value]()
        func = ctx.symbol_table.get("func")
        assert func is not None

        for element in self.elements:
            result = res.register(func.execute([element], {}))
            if res.should_return():
                return res
            assert result is not None
            if result.is_true():
                return res.success(Boolean.true())

        return res.success(Boolean.false())
