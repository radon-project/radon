from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generator
from typing import Iterator as PyIterator
from typing import Optional, TypeAlias, TypeVar

from core.errors import Error, RTError
from core.parser import Context, RTResult, SymbolTable
from core.tokens import Position

if TYPE_CHECKING:
    from core.nodes import Node

    Self = TypeVar("Self", bound="Value")

# ResultTuple: TypeAlias = "tuple[None, Error] | tuple[Value, None]"
ResultTuple: TypeAlias = tuple[Optional["Value"], Optional[Error]]


class Value:
    pos_start: Position
    pos_end: Position
    context: Context

    def __init__(self) -> None:
        self.set_pos()
        self.set_context()

    def set_pos(self: Self, pos_start: Optional[Position] = None, pos_end: Optional[Position] = None) -> Self:
        self.pos_start = pos_start if pos_start is not None else Position(0, 0, 0, "<unset>", "<unset>")
        self.pos_end = pos_end if pos_end is not None else Position(0, 0, 0, "<unset>", "<unset>")
        return self

    def set_context(self: Self, context: Optional[Context] = None) -> Self:
        self.context = context if context is not None else Context("<unset>")
        return self

    def added_to(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def subbed_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def multed_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def dived_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def modded_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def idived_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def powed_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def anded_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def ored_by(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def notted(self) -> ResultTuple:
        return None, self.illegal_operation()

    def iter(self) -> Iterator:
        return Iterator(self.gen())

    def gen(self) -> Generator[RTResult[Value], None, None]:
        yield RTResult[Value]().failure(self.illegal_operation())

    def get_index(self, index: Value) -> ResultTuple:
        return None, self.illegal_operation(index)

    def get_slice(self, start: Optional[Value], end: Optional[Value], step: Optional[Value]) -> ResultTuple:
        return None, self.illegal_operation()

    def set_index(self, index: Value, value: Value) -> ResultTuple:
        return None, self.illegal_operation(index, value)

    def execute(self, args: list[Value], kwargs: dict[str, Value]) -> RTResult[Value]:
        return RTResult[Value]().failure(self.illegal_operation())

    def contains(self, other: Value) -> ResultTuple:
        return None, self.illegal_operation(other)

    def copy(self: Self) -> Self:
        raise Exception("No copy method defined")

    def is_true(self) -> bool:
        return False

    # Help text for help() in radon
    def __help_repr__(self) -> str:
        return """
This data type help is not implemented yet
"""

    def illegal_operation(self, *others: Value) -> RTError:
        if len(others) == 0:
            others = (self,)

        assert self.pos_start is not None
        assert self.pos_end is not None
        assert others[-1].pos_end is not None
        assert self.context is not None
        try:
            return RTError(
                self.pos_start, others[-1].pos_end, f"Illegal operation for {(self, ) + others}", self.context
            )
        except AttributeError:
            return RTError(self.pos_start, self.pos_end, f"Illegal operation for {self}", self.context)


class Iterator(Value):
    it: Generator[RTResult[Value], None, None]

    def __init__(self, generator: Generator[RTResult[Value], None, None]) -> None:
        super().__init__()
        self.it = generator

    def __len__(self) -> int:
        return len(list(self.it))

    def iter(self) -> Iterator:
        return self

    def __iter__(self) -> Iterator:
        return self

    def __next__(self) -> RTResult[Value]:
        return next(self.it)

    def __str__(self) -> str:
        return "<iterator>"

    def __help_repr__(self) -> str:
        return """
Iterator

An Iterator is an object that enables traversal over a collection, one element at a time.
"""

    def __repr__(self) -> str:
        return str(self)

    def copy(self) -> Iterator:
        return Iterator(self.it)


class Number(Value):
    value: int | float

    def __init__(self, value: int | float) -> None:
        super().__init__()
        self.value = value

    def added_to(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        elif isinstance(other, String):
            return String(str(self.value) + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, "Division by zero", self.context)

            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def idived_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, "Division by zero", self.context)
            return Number(int(self.value // other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def powed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(self.value**other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def modded_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(self.value % other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value == other.value).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(False).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value != other.value).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(True).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lt(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value < other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gt(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value > other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lte(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value <= other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gte(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Boolean(self.value >= other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def anded_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def ored_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self) -> ResultTuple:
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self) -> Number:
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self) -> bool:
        return self.value != 0

    def __str__(self) -> str:
        return str(self.value)

    def __help_repr__(self) -> str:
        return """
Number

A Number represents a numeric value. It can be an integer, float, or other numeric type.

Operations:
    +, -, *, /    -> Basic arithmetic operations.
    //, %         -> Integer division and modulus.
    ^            -> Exponentiation.
    math.factorial() -> Gets the factorial of a number (standard math library)
    str()    -> Converts the number to its string representation.

Example: 25
"""

    def __repr__(self) -> str:
        return str(self.value)

    @classmethod
    def one(cls) -> Number:
        return cls(1)


class Boolean(Value):
    value: bool

    def __init__(self, value: bool) -> None:
        super().__init__()
        self.value = value

    def anded_by(self, other: Value) -> ResultTuple:
        return Boolean(self.value and other.is_true()).set_context(self.context), None

    def ored_by(self, other: Value) -> ResultTuple:
        return Boolean(self.value or other.is_true()).set_context(self.context), None

    def notted(self) -> ResultTuple:
        return Boolean(not self.value).set_context(self.context), None

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, Boolean):
            return Boolean(self.value == other.value).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(self.value == other.value).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(False).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(False).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if isinstance(other, Boolean):
            return Boolean(self.value != other.value).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(self.value != other.value).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(True).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(True).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self) -> Boolean:
        copy = Boolean(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self) -> bool:
        return self.value

    def __len__(self) -> int:
        return 1 if self.value else 0

    def __str__(self) -> str:
        return "true" if self.value else "false"

    def __repr__(self) -> str:
        return "true" if self.value else "false"

    def __help_repr__(self) -> str:
        return """
Boolean

A Boolean represents a truth value: True or False.

Operations:
    and, or, not   -> Logical operations.
    ==, !=         -> Equality and inequality checks.

Example: true
"""

    @classmethod
    def true(cls) -> Boolean:
        return cls(True)

    @classmethod
    def false(cls) -> Boolean:
        return cls(False)


class String(Value):
    value: str

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def added_to(self, other: Value) -> ResultTuple:
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        elif isinstance(other, Number):
            return String(self.value + str(other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            return String(self.value * int(other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, String):
            return Boolean(self.value == other.value).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(False).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(False).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if isinstance(other, String):
            return Boolean(self.value != other.value).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(True).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(True).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def gen(self) -> Generator[RTResult[Value], None, None]:
        for char in self.value:
            yield RTResult[Value]().success(String(char))

    def get_index(self, index: Value) -> ResultTuple:
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        try:
            return String(self.value[int(index.value)]), None
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot get char {index} from string {self!r} because it is out of bounds.",
                self.context,
            )

    def get_slice(self, start: Optional[Value], end: Optional[Value], step: Optional[Value]) -> ResultTuple:
        if start is not None and not isinstance(start, Number):
            return None, self.illegal_operation(start)
        if end is not None and not isinstance(end, Number):
            return None, self.illegal_operation(end)
        if step is not None and not isinstance(step, Number):
            return None, self.illegal_operation(step)

        istart: int | None
        iend: int | None
        istep: int | None
        if start is not None:
            istart = int(start.value)
        else:
            istart = start
        if end is not None:
            iend = int(end.value)
        else:
            iend = end
        if step is not None:
            if step.value == 0:
                return None, RTError(step.pos_start, step.pos_end, "Step cannot be zero.", self.context)
            istep = int(step.value)
        else:
            istep = None
        return String(self.value[istart:iend:istep]), None

    def set_index(self, index: Value, value: Value) -> ResultTuple:
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        if not isinstance(value, String):
            return None, self.illegal_operation(value)
        try:
            self.value = self.value[: int(index.value)] + value.value + self.value[int(index.value + 1) :]
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot set character {index} from string {self!r} to {value!r} because it is out of bounds.",
                self.context,
            )
        return self, None

    def contains(self, other: Value) -> ResultTuple:
        if not isinstance(other, String):
            return None, self.illegal_operation(other)
        return Boolean(other.value in self.value), None

    def is_true(self) -> bool:
        return len(self.value) > 0

    def copy(self) -> String:
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def to_int(self) -> Optional[int]:
        if self.value.isdigit():
            return int(self.value)
        return None

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f'"{self.value}"'

    def __help_repr__(self) -> str:
        return """
String

A String is a sequence of characters.

Methods:
    len(str)       -> Returns the length of the string.

String standard library methods:
    find(str)   -> Find a character in a string and return its index (-1 if not found)
    to_int()    -> Magic method to convert string to int if possible

Example: "Hello World!"
"""

    def __iter__(self) -> PyIterator[str]:
        return iter(self.value)

    def __getitem__(self, index: int) -> str:
        return self.value[index]

    def __len__(self) -> int:
        return len(self.value)


class Array(Value):
    elements: list[Value]

    def __init__(self, elements: list[Value]) -> None:
        super().__init__()
        self.elements = elements

    def added_to(self, other: Value) -> ResultTuple:
        new_array = self.copy()
        if isinstance(other, Array):
            new_array.elements.extend(other.elements)
        else:
            new_array.elements.append(other)
        return new_array, None

    def subbed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            new_array = self.copy()
            try:
                new_array.elements.pop(int(other.value))
                return new_array, None
            except Exception:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Element at this index could not be removed from array because index is out of bounds",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Array):
            new_array = self.copy()
            new_array.elements.extend(other.elements)
            return new_array, None
        elif isinstance(other, Number):
            new_array = self.copy()
            new_array.elements *= int(other.value)
            return new_array, None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other: Value) -> ResultTuple:
        if isinstance(other, Number):
            try:
                return self.elements[int(other.value)], None
            except IndexError:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Element at this index could not be retrieved from array because index is out of bounds",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, Array):
            if len(self.elements) != len(other.elements):
                return Boolean.false(), None

            for a, b in zip(self.elements, other.elements):
                ret, error = a.get_comparison_eq(b)
                if error is not None:
                    return None, error
                assert ret is not None
                if not ret.is_true():
                    return Boolean.false(), None
            return Boolean.true(), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        ret, error = self.get_comparison_eq(other)
        if error is not None:
            return None, error
        assert ret is not None
        return Boolean.false() if ret.is_true() else Boolean.true(), None

    def gen(self) -> Generator[RTResult[Value], None, None]:
        for element in self.elements:
            yield RTResult[Value]().success(element)

    def get_index(self, index: Value) -> ResultTuple:
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        try:
            return self.elements[int(index.value)], None
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot get element {index} from list {self!r} because it is out of bounds.",
                self.context,
            )
        return self, None

    def get_slice(self, start: Optional[Value], end: Optional[Value], step: Optional[Value]) -> ResultTuple:
        if start is not None and not isinstance(start, Number):
            return None, self.illegal_operation(start)
        if end is not None and not isinstance(end, Number):
            return None, self.illegal_operation(end)
        if step is not None and not isinstance(step, Number):
            return None, self.illegal_operation(step)

        istart: Optional[int]
        iend: Optional[int]
        istep: Optional[int]
        if start is not None:
            istart = int(start.value)
        else:
            istart = None
        if end is not None:
            iend = int(end.value)
        else:
            iend = None
        if step is not None:
            if step.value == 0:
                return None, RTError(step.pos_start, step.pos_end, "Step cannot be zero.", self.context)
            istep = int(step.value)
        else:
            istep = None
        return Array(self.elements[istart:iend:istep]), None

    def set_index(self, index: Value, value: Value) -> ResultTuple:
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        try:
            self.elements[int(index.value)] = value
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot set element {index} from list {self!r} to {value!r} because it is out of bounds.",
                self.context,
            )
        return self, None

    def contains(self, other: Value) -> ResultTuple:
        ret: Boolean = Boolean.false()
        for val in self.elements:
            cmp, err = val.get_comparison_eq(other)
            if err is not None:
                return None, err
            assert cmp is not None
            if cmp.is_true():
                ret = Boolean.true()
                break
        return ret, None

    def is_true(self) -> bool:
        return len(self.elements) > 0

    def copy(self) -> Array:
        copy: Array = Array(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'[{", ".join(repr(x) for x in self.elements)}]'

    def __help_repr__(self) -> str:
        return """
Array

An Array is an ordered collection of elements.

Methods:
    len(arr)       -> Returns the number of elements in the array.

Array standard library methods:
    map(func)      -> Map an array with a function
    append(item)   -> Append an element from the right
    pop(index)     -> Removes and returns the last element of the array.
    extend(arr)    -> Extend by another array
    find(element)  -> Get the index of an element in the array (-1 if not found)

    is_empty()     -> Returns boolean indicating if the array is empty or not
    to_string()    -> Convert to string
    is_array()     -> returns true

Example: [1,2,3,true,"Hello World!"]
"""

    def __iter__(self) -> PyIterator[Value]:
        return iter(self.elements)

    def __getitem__(self, index: int) -> Value:
        return self.elements[index]

    def __len__(self) -> int:
        return len(self.elements)


class HashMap(Value):
    values: dict[str, Value]

    def __init__(self, values: dict[str, Value]) -> None:
        super().__init__()
        self.values = values

    def added_to(self, other: Value) -> ResultTuple:
        if not isinstance(other, HashMap):
            return None, self.illegal_operation(other)

        new_dict = self.copy()
        for key, value in other.values.items():
            new_dict.values[key] = value

        return new_dict, None

    def gen(self) -> Generator[RTResult[Value], None, None]:
        fake_pos = Position(0, 0, 0, "<hashmap key>", "<native code>")
        for key in self.values.keys():
            key_as_value = String(key).set_pos(fake_pos, fake_pos).set_context(self.context)
            yield RTResult[Value]().success(key_as_value)

    def get_index(self, index: Value) -> ResultTuple:
        if not isinstance(index, String):
            return None, self.illegal_operation(index)

        try:
            return self.values[index.value], None
        except KeyError:
            return None, RTError(
                self.pos_start, self.pos_end, f"Could not find key {index!r} in dict {self!r}", self.context
            )

    def set_index(self, index: Value, value: Value) -> ResultTuple:
        if not isinstance(index, String):
            return None, self.illegal_operation(index)

        self.values[index.value] = value

        return self, None

    def contains(self, other: Value) -> ResultTuple:
        ret = Boolean.false()
        for val in self.values.keys():
            cmp, err = other.get_comparison_eq(String(val))
            if err:
                return None, err
            assert cmp is not None
            if cmp.is_true():
                ret = Boolean.true()
                break
        return ret, None

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if not isinstance(other, HashMap):
            return None, self.illegal_operation(other)

        if len(self.values) != len(other.values):
            return Boolean.false(), None

        for key, value in self.values.items():
            if key not in other.values:
                return Boolean.false(), None

            cmp, err = value.get_comparison_eq(other.values[key])
            if err:
                return None, err
            assert cmp is not None
            if not cmp.is_true():
                return Boolean.false(), None

        return Boolean.true(), None

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if not isinstance(other, HashMap):
            return None, self.illegal_operation(other)

        if len(self.values) != len(other.values):
            return Boolean.true(), None

        for key, value in self.values.items():
            if key not in other.values:
                return Boolean.true(), None

            cmp, err = value.get_comparison_ne(other.values[key])
            if err:
                return None, err
            assert cmp is not None
            if cmp.is_true():
                return Boolean.true(), None

        return Boolean.false(), None

    def __len__(self) -> int:
        return len(self.values)

    def copy(self) -> HashMap:
        copy = HashMap(self.values)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self) -> str:
        return self.__repr__()

    def __help_repr__(self) -> str:
        return """
HashMap

A HashMap is a collection of key-value pairs.

Example: {"key":"value"}
"""

    def __repr__(self) -> str:
        __val = ", ".join([f"{repr(k)}: {repr(v)}" for k, v in self.values.items()])
        return f"{{{__val}}}"


class Type(Value):
    variable: Value
    type: str

    def __init__(self, variable: Value) -> None:
        super().__init__()
        self.variable = variable
        self.get_type()

    def get_type(self) -> None:
        self.type = self.variable.__class__.__name__

    def copy(self) -> Type:
        copy = Type(self.variable)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self) -> str:
        return f"<class '{self.type}'>"

    def __repr__(self) -> str:
        return f"<class '{self.type}'>"

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, Type):
            return Boolean(self.type == other.type).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if isinstance(other, Type):
            return Boolean(self.type != other.type).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)


def radonify(value: object, pos_start: Position, pos_end: Position, context: Context) -> Value:
    def _radonify(value: object) -> Value:
        match value:
            case True:
                return Boolean.true()
            case False:
                return Boolean.false()
            case dict():
                _value1: dict[str, Value] = value
                return HashMap({k: radonify(v, pos_start, pos_end, context) for k, v in _value1.items()})
            case list():
                _value2: list[Value] = value
                return Array([radonify(v, pos_start, pos_end, context) for v in _value2])
            case str():
                return String(value)
            case int() | float():
                return Number(value)
            case None:
                return Null.null()
            case _ if inspect.isfunction(value):
                from core.builtin_funcs import BuiltInFunction  # Lazy import
                from core.builtin_funcs import args

                signature = inspect.signature(value)
                params = list(signature.parameters.keys())

                @args(params)
                def wrapper(ctx: Context) -> RTResult[Value]:
                    res = RTResult[Value]()

                    deradonified_params = (deradonify(ctx.symbol_table.get(param)) for param in params)

                    try:
                        return_value = radonify(value(*deradonified_params), pos_start, pos_end, ctx)
                    except Exception as e:
                        return res.failure(RTError(pos_start, pos_end, str(e), ctx))
                    return res.success(return_value)

                return BuiltInFunction(value.__name__, wrapper)
            case _:
                return PyObj(value)

    return _radonify(value).set_pos(pos_start, pos_end).set_context(context)


def deradonify(value: Optional[Value]) -> str | dict[str, Any] | int | float | list[object] | object:
    match value:
        case PyObj():
            return value.value
        case String():
            return str(value.value)
        case HashMap():
            return {k: deradonify(v) for k, v in value.values.items()}
        case Number():
            return value.value
        case Array():
            return [deradonify(v) for v in value.elements]
        case BaseFunction():
            def ret(*args: list[Value], **kwargs: dict[str, Value]) -> object:
                res = value.execute(
                    [radonify(arg, value.pos_start, value.pos_end, value.context) for arg in args],
                    {k: radonify(arg, value.pos_start, value.pos_end, value.context) for k, arg in kwargs.items()},
                )
                if res.error:
                    raise RuntimeError(f"Radon exception: {res.error.as_string()}")
                elif res.should_return():
                    assert False, "unreachable!"
                return deradonify(res.value)

            ret.__name__ = value.name
            return ret
        case _:
            assert False, f"no deradonification procedure for type {type(value)}"


class PyObj(Value):
    """Thin wrapper around a Python object"""

    value: object

    def __init__(self, value: object) -> None:
        super().__init__()
        self.value = value

    def copy(self) -> PyObj:
        return self

    def __repr__(self) -> str:
        return f"PyObj({self.value!r})"


class PyAPI(Value):
    code: str

    def __init__(self, code: str) -> None:
        super().__init__()
        self.code = code

    def pyapi(self, ns: HashMap) -> RTResult[Value]:
        """TODO: update docs"""

        try:
            locals_dict: dict[str, Any] = deradonify(ns) # type: ignore
            assert isinstance(locals_dict, dict)
            # Execute the code and store the output in locals_dict
            exec(self.code, {}, locals_dict)

            # Update namespace HashMap
            new_ns = radonify(locals_dict, self.pos_start, self.pos_end, self.context)
            assert isinstance(new_ns, HashMap)
            for key, value in new_ns.values.items():
                ns.values[key] = value

        except Exception as e:
            return RTResult[Value]().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"Python {type(e).__name__} during execution of PyAPI: {e}",
                    self.context,
                )
            )
        return RTResult[Value]().success(Null.null())

    def copy(self) -> PyAPI:
        copy = PyAPI(self.code)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy


class BaseFunction(Value):
    name: str
    symbol_table: Optional[SymbolTable]
    desc: str
    arg_names: list[str]
    va_name: Optional[str]

    def __init__(self, name: Optional[str], symbol_table: Optional[SymbolTable]) -> None:
        super().__init__()
        self.name = name if name is not None else "<anonymous>"
        self.symbol_table = symbol_table

    def generate_new_context(self) -> Context:
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(self.symbol_table)
        return new_context

    def check_args(
        self,
        arg_names: list[str],
        args: list[Value],
        kwargs: dict[str, Value],
        defaults: list[Optional[Value]],
        max_pos_args: int,
    ) -> RTResult[None]:
        res = RTResult[None]()

        args_count = len(args) + len(kwargs)
        if self.va_name is None and (args_count > len(arg_names) or len(args) > max_pos_args):
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"{len(args) - len(arg_names)} too many args passed into {self}",
                    self.context,
                )
            )

        defaults_count = sum(1 for default in defaults if default is not None)
        if args_count < len(arg_names) - defaults_count:
            return res.failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f"{args_count - defaults_count} too few args passed into {self}",
                    self.context,
                )
            )

        for kw in kwargs.keys():
            if kw not in arg_names:
                return res.failure(
                    RTError(
                        self.pos_start,
                        self.pos_end,
                        f"{kw} is not a valid keyword arg passed into {self}",
                        self.context,
                    )
                )

        return res.success(None)

    def populate_args(self, arg_names: list[str], args: list[Value], kwargs: dict[str, Value], defaults: list[Optional[Value]], max_pos_args: int, exec_ctx: Context) -> None:
        for i, (arg_name, default) in enumerate(zip(arg_names, defaults)):
            if default is not None:
                exec_ctx.symbol_table.set(arg_name, default)

        populated = 0
        for i in range(len(arg_names)):
            arg_name = arg_names[i]
            if i >= max_pos_args or arg_name in kwargs or i >= len(args):
                continue
            arg_value = args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)
            populated += 1

        if self.va_name is not None:
            va_list: list[Value] = []
            for i in range(populated, len(args)):
                arg = args[i]
                arg.set_context(exec_ctx)
                va_list.append(arg)
            exec_ctx.symbol_table.set(self.va_name, Array(va_list))

        for kw, kwarg in kwargs.items():
            kwarg.set_context(exec_ctx)
            exec_ctx.symbol_table.set(kw, kwarg)

    def check_and_populate_args(self, arg_names: list[str], args: list[Value], kwargs: dict[str, Value], defaults: list[Optional[Value]], max_pos_args: int, exec_ctx: Context) -> RTResult[None]:
        res = RTResult[None]()
        res.register(self.check_args(arg_names, args, kwargs, defaults, max_pos_args))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, kwargs, defaults, max_pos_args, exec_ctx)
        return res.success(None)


class BaseInstance(Value, ABC):
    def __init__(self, parent_class: BaseClass, symbol_table: Optional[SymbolTable]):
        super().__init__()
        self.parent_class = parent_class
        self.symbol_table = SymbolTable(symbol_table)

    @abstractmethod
    def operator(self, operator: str, *args: Value) -> ResultTuple: ...

    @abstractmethod
    def bind_method(self, method: BaseFunction) -> RTResult[BaseFunction]: ...

    def added_to(self, other: Value) -> ResultTuple:
        return self.operator("__add__", other)

    def subbed_by(self, other: Value) -> ResultTuple:
        return self.operator("__sub__", other)

    def multed_by(self, other: Value) -> ResultTuple:
        return self.operator("__mul__", other)

    def dived_by(self, other: Value) -> ResultTuple:
        return self.operator("__div__", other)

    def powed_by(self, other: Value) -> ResultTuple:
        return self.operator("__pow__", other)

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        return self.operator("__eq__", other)

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        return self.operator("__ne__", other)

    def get_comparison_lt(self, other: Value) -> ResultTuple:
        return self.operator("__lt__", other)

    def get_comparison_gt(self, other: Value) -> ResultTuple:
        return self.operator("__gt__", other)

    def get_comparison_lte(self, other: Value) -> ResultTuple:
        return self.operator("__lte__", other)

    def get_comparison_gte(self, other: Value) -> ResultTuple:
        return self.operator("__gte__", other)

    def anded_by(self, other: Value) -> ResultTuple:
        return self.operator("__and__", other)

    def ored_by(self, other: Value) -> ResultTuple:
        return self.operator("__or__", other)

    def notted(self) -> ResultTuple:
        return self.operator("__not__")

    def get_index(self, index: Value) -> ResultTuple:
        return self.operator("__getitem__", index)

    def set_index(self, index: Value, value: Value) -> ResultTuple:
        return self.operator("__setitem__", index, value)

    def execute(self, args: list[Value], kwargs: dict[str, Value]) -> RTResult[Value]:
        res, err = self.operator("__call__", *args)
        if err is not None:
            return RTResult[Value]().failure(err)
        assert res is not None
        return RTResult[Value]().success(res)

    def contains(self, other: Value) -> ResultTuple:
        return self.operator("__contains__", other)

    def is_true(self) -> bool:
        res, err = self.operator("__truthy__")
        if err is not None:
            return False
        assert res is not None
        return res.is_true()

    def copy(self: Self) -> Self:
        return self


class Instance(BaseInstance):
    def __init__(self, parent_class: Class) -> None:
        super().__init__(parent_class, None)

    def __exec_len__(self) -> Value | Null:
        try:
            return self.operator("__len__")[0].value # type: ignore
        except AttributeError:
            return Null.null()

    def __help_repr__(self) -> str:
        result: str = f"Help on object {self.parent_class.name}:\n\nclass {self.parent_class.name}\n|\n"
        for k in self.symbol_table.symbols:
            f = self.symbol_table.symbols[k]
            if isinstance(f, Function):
                result += f.__help_repr_method__()
            elif isinstance(f, Value) and k != "this":
                result += f"| {k} = {f!r}\n|\n"
        return result

    def bind_method(self, method: BaseFunction) -> RTResult[BaseFunction]:
        method = method.copy()
        if method.symbol_table is None:
            method.symbol_table = SymbolTable()
        method.symbol_table.set("this", self)
        return RTResult[BaseFunction]().success(method)

    def operator(self, operator: str, *args: Value) -> ResultTuple:
        res = RTResult[Value]()
        method = self.symbol_table.symbols.get(operator, None)

        if method is None or not isinstance(method, Function):
            return None, RTError(self.pos_start, self.pos_end, f"Function '{operator}' not defined", self.context)
        if method.symbol_table is None:
            method.symbol_table = SymbolTable()
        method.symbol_table.set("this", self)

        value = res.register(method.execute(list(args), {}))
        if res.error is not None:
            return None, res.error
        assert value is not None
        return value, None

    def __repr__(self) -> str:
        # TODO: make this overloadable as well
        return f"<instance of class {self.parent_class.name}>"


class BaseClass(Value, ABC):
    name: str
    symbol_table: SymbolTable

    def __init__(self, name: str, symbol_table: SymbolTable) -> None:
        super().__init__()
        self.name = name
        self.symbol_table = symbol_table

    @abstractmethod
    def get(self, name: str) -> Optional[Value]: ...

    def dived_by(self, other: Value) -> ResultTuple:
        if not isinstance(other, String):
            return None, self.illegal_operation(other)

        value = self.get(other.value)
        if value is None:
            return None, RTError(self.pos_start, self.pos_end, f"'{other.value}' is not defined", self.context)

        return value, None

    @abstractmethod
    def create(self, args: list[Value]) -> RTResult[BaseInstance]: ...

    @abstractmethod
    def init(self, inst: BaseInstance, args: list[Value], kwargs: dict[str, Value]) -> RTResult[None]: ...

    def execute(self, args: list[Value], kwargs: dict[str, Value]) -> RTResult[Value]:
        res = RTResult[Value]()

        inst = res.register(self.create(args))
        if res.should_return():
            return res
        assert inst is not None

        res.register(self.init(inst, args, kwargs))
        if res.should_return():
            return res
        return res.success(inst)

    def copy(self: Self) -> Self:
        return self


class Class(BaseClass):
    def get(self, name: str) -> Optional[Value]:
        method = self.symbol_table.symbols.get(name, None)
        if method is None:
            return None
        return method

    def __help_repr__(self) -> str:
        result: str = f"Help on object {self.name}:\n\nclass {self.name}\n|\n"
        for k in self.symbol_table.symbols:
            f = self.symbol_table.symbols[k]
            if isinstance(f, Function):
                result += f.__help_repr_method__()
            elif isinstance(f, Value) and k != "this":
                result += f"| {k} = {f!r}\n|\n"
        return result

    def create(self, args: list[Value]) -> RTResult[BaseInstance]:
        res = RTResult[BaseInstance]()

        # TODO: Some issue here when direct accessing class methods without instantiation
        inst = Instance(self)
        inst.symbol_table = SymbolTable(self.symbol_table)

        for name in self.symbol_table.symbols:
            inst.symbol_table.set(name, self.symbol_table.symbols[name].copy())

        exec_ctx = Context(f"<class {self.name}>", self.context, self.pos_start)
        exec_ctx.symbol_table = inst.symbol_table
        for name in inst.symbol_table.symbols:
            inst.symbol_table.symbols[name].set_context(exec_ctx)

        inst.symbol_table.set("this", inst)
        return res.success(inst.set_context(self.context).set_pos(self.pos_start, self.pos_end))

    def init(self, inst: BaseInstance, args: list[Value], kwargs: dict[str, Value]) -> RTResult[None]:
        res = RTResult[None]()
        method = inst.symbol_table.symbols.get("__constructor__", None)

        if method is None or not isinstance(method, Function):
            return res.failure(
                RTError(self.pos_start, self.pos_end, f"Function '{self.name}' not defined", self.context)
            )
        if method.symbol_table is None:
            method.symbol_table = SymbolTable()
        method.symbol_table.set("this", inst)

        res.register(method.execute(args, kwargs))
        if res.should_return():
            return res

        return res.success(None)

    def __repr__(self) -> str:
        return f"<class {self.name}>"


class Function(BaseFunction):
    body_node: Node
    arg_names: list[str]
    defaults: list[Optional[Value]]
    should_auto_return: bool
    max_pos_args: int

    def __help_repr__(self) -> str:
        return f"Help on function {self.name}:\n\n{self.__help_repr_method__()}"

    def __help_repr_method__(self) -> str:
        arg_strs: list[str] = []
        for i in range(len(self.arg_names)):
            if self.defaults[i] is not None:
                arg_strs.append(f"{self.arg_names[i]} = {self.defaults[i].__repr__()}")
            else:
                arg_strs.append(self.arg_names[i])
        return f"| fun {self.name}({', '.join(arg_strs)})\n|\t{self.desc}\n|\n"

    def __init__(
        self,
        name: Optional[str],
        symbol_table: Optional[SymbolTable],
        body_node: Node,
        arg_names: list[str],
        defaults: list[Optional[Value]],
        should_auto_return: bool,
        desc: str,
        va_name: Optional[str],
        max_pos_args: int,
    ) -> None:
        super().__init__(name, symbol_table)
        self.body_node = body_node
        self.arg_names = arg_names
        self.defaults = defaults
        self.should_auto_return = should_auto_return
        self.desc = desc
        self.va_name = va_name
        self.max_pos_args = max_pos_args

    def execute(self, args: list[Value], kwargs: dict[str, Value]) -> RTResult[Value]:
        from core.interpreter import Interpreter  # Lazy import

        res = RTResult[Value]()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(
            self.check_and_populate_args(self.arg_names, args, kwargs, self.defaults, self.max_pos_args, exec_ctx)
        )
        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value is None:
            return res

        if self.should_auto_return:
            ret_value = value
        else:
            ret_value = res.func_return_value
        if ret_value is None:
            ret_value = Null.null()
        return res.success(ret_value)

    def copy(self) -> Function:
        copy = Function(
            self.name,
            self.symbol_table,
            self.body_node,
            self.arg_names,
            self.defaults,
            self.should_auto_return,
            self.desc,
            self.va_name,
            self.max_pos_args,
        )
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self) -> str:
        return f"<function {self.name}>"


class Module(Value):
    name: str
    file_path: str
    symbol_table: SymbolTable

    def __init__(self, name: str, file_path: str, symbol_table: SymbolTable) -> None:
        super().__init__()
        self.name = name
        self.file_path = file_path
        self.symbol_table = symbol_table

    def copy(self) -> Module:
        return self

    def __repr__(self) -> str:
        return f"<module {self.name} @ {self.file_path!r}>"


class Null(Value):
    def __repr__(self) -> str:
        return "null"

    def copy(self) -> Null:
        return self

    def is_true(self) -> bool:
        return False

    def get_comparison_eq(self, other: Value) -> ResultTuple:
        if isinstance(other, Null):
            return Boolean.true(), None
        else:
            return Boolean.false(), None

    def get_comparison_ne(self, other: Value) -> ResultTuple:
        if isinstance(other, Null):
            return Boolean.false(), None
        else:
            return Boolean.true(), None

    @classmethod
    def null(cls) -> Null:
        return cls()
