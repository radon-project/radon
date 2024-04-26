from core.parser import RTResult, Context, SymbolTable
from core.tokens import Position
from core.errors import RTError, IndexError as IndexErr

import inspect
from abc import ABC, abstractmethod



class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()

    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context=None):
        self.context = context
        return self

    def added_to(self, other):
        return None, self.illegal_operation(other)

    def subbed_by(self, other):
        return None, self.illegal_operation(other)

    def multed_by(self, other):
        return None, self.illegal_operation(other)

    def dived_by(self, other):
        return None, self.illegal_operation(other)

    def idived_by(self, other):
        return None, self.illegal_operation(other)

    def powed_by(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_eq(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_ne(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gt(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_lte(self, other):
        return None, self.illegal_operation(other)

    def get_comparison_gte(self, other):
        return None, self.illegal_operation(other)

    def anded_by(self, other):
        return None, self.illegal_operation(other)

    def ored_by(self, other):
        return None, self.illegal_operation(other)

    def notted(self, other):
        return None, self.illegal_operation(other)

    def iter(self):
        return Iterator(self.gen)

    def gen(self):
        yield RTResult().failure(self.illegal_operation())

    def get_index(self, index):
        return None, self.illegal_operation(index)

    def set_index(self, index, value):
        return None, self.illegal_operation(index, value)

    def execute(self, args, kwargs):
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception("No copy method defined")

    def is_true(self):
        return False

    def illegal_operation(self, *others):
        if len(others) == 0:
            others = (self,)

        return RTError(self.pos_start, others[-1].pos_end, f"Illegal operation for {(self, ) + others}", self.context)


class Iterator(Value):
    def __init__(self, generator):
        super().__init__()
        self.it = generator()

    def iter(self):
        return self

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.it)

    def __str__(self):
        return "<iterator>"

    def __repr__(self):
        return str(self)

    def copy(self):
        return Iterator(self.it)


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        elif isinstance(other, String):
            return String(str(self.value) + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            try:
                return Number(self.value * other.value).set_context(self.context), None
            except TypeError:
                return Number(self.value.value * other.value.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, "Division by zero", self.context)

            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def idived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, "Division by zero", self.context)

            return Number(self.value // other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def powed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value**other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def modded_by(self, other):
        if isinstance(other, Number):
            return Number(self.value % other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lt(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value < other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value < other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gt(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value > other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value > other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_lte(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value <= other.value)).set_context(self.context), None
        if isinstance(other, String):
            return Boolean(int(self.value <= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_gte(self, other):
        if isinstance(other, Number):
            return Boolean(int(self.value >= other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def plus_equals(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def minus_equals(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def times_equals(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def divide_equals(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(other.pos_start, other.pos_end, "Division by zero", self.context)

            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def mod_equals(self, other):
        if isinstance(other, Number):
            return Number(self.value % other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def power_equals(self, other):
        if isinstance(other, Number):
            return Number(self.value**other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def anded_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def ored_by(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def notted(self):
        return Number(1 if self.value == 0 else 0).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value != 0

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class Boolean(Value):
    def __init__(self, value):
        super().__init__()
        self.__value = value
        self.value = self.__str__()

    def anded_by(self, other):
        return Boolean(self.__value and other.__value).set_context(self.context), None

    def ored_by(self, other):
        return Boolean(self.__value or other.__value).set_context(self.context), None

    def notted(self):
        return Boolean(not self.__value).set_context(self.context), None

    def get_comparison_eq(self, other):
        if isinstance(other, Boolean):
            return Boolean(int(self.__value == other.__value)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.__value == other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.__value == other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.__value == other.elements)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, Boolean):
            return Boolean(int(self.__value != other.__value)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.__value != other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.__value != other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.__value != other.elements)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = Boolean(self.__value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.__value

    def __str__(self):
        return "true" if self.__value else "false"

    def __repr__(self):
        return "true" if self.__value else "false"


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)
Number.one = Number(1)  # used in increment and decrement ops

Boolean.null = Boolean(False)
Boolean.false = Boolean(False)
Boolean.true = Boolean(True)


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def added_to(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        elif isinstance(other, Number):
            return String(self.value + str(other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other):
        if isinstance(other, String):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.value == other.elements)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, String):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.value != other.elements)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def gen(self):
        for char in self.value:
            yield RTResult().success(String(char))

    def get_index(self, index_start, index_end=None, index_step=None):
        if not isinstance(index_start, Number):
            return None, self.illegal_operation(index_start)

        if index_end != None and not isinstance(index_end, Number):
            return None, self.illegal_operation(index_end)

        if index_step != None and not isinstance(index_step, Number):
            return None, self.illegal_operation(index_step)

        if (index_end != None) and (index_step != None):
            try:
                return String(self.value[index_start.value : index_end.value : index_step.value]), None
            except IndexError:
                return None, RTError(
                    index_start.pos_start,
                    index_end.pos_end,
                    f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                    self.context,
                )
        elif index_end != None:
            try:
                return String(self.value[index_start.value : index_end.value]), None
            except IndexError:
                return None, RTError(
                    index_start.pos_start,
                    index_end.pos_end,
                    f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                    self.context,
                )

        try:
            return String(self.value[index_start.value]), None
        except IndexError:
            return None, RTError(
                index_start.pos_start,
                index_start.pos_end,
                f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                self.context,
            )

    def set_index(self, index, value):
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        if not isinstance(value, String):
            return None, self.illegal_operation(value)
        try:
            self.value = self.value[: index.value] + value.value + self.value[index.value + 1 :]
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot set character {index} from string {self!r} to {value!r} because it is out of bounds.",
                self.context,
            )
        return self, None

    def is_true(self):
        return len(self.value) > 0

    def copy(self):
        copy = String(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def to_int(self):
        if self.value.isdigit():
            return int(self.value)
        return None

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'"{self.value}"'

    def __iter__(self):
        return iter(self.value)

    def __getitem__(self, index):
        return self.value[index]

    def __len__(self):
        return len(self.value)


class Array(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements
        self.value = elements  # For matching with other conventions in the code base

    def added_to(self, other):
        new_array = self.copy()
        if isinstance(other, Array):
            new_array.elements.extend(other.elements)
        else:
            new_array.elements.append(other)
        return new_array, None

    def subbed_by(self, other):
        if isinstance(other, Number):
            new_array = self.copy()
            try:
                new_array.elements.pop(other.value)
                return new_array, None
            except:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Element at this index could not be removed from array because index is out of bounds",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, Array):
            new_array = self.copy()
            new_array.elements.extend(other.elements)
            return new_array, None
        elif isinstance(other, Number):
            new_array = self.copy()
            new_array.elements *= other.value
            return new_array, None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, Number):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start,
                    other.pos_end,
                    "Element at this index could not be retrieved from array because index is out of bounds",
                    self.context,
                )
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_eq(self, other):
        if isinstance(other, Array):
            return Boolean(int(self.elements == other.elements)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.elements == other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def get_comparison_ne(self, other):
        if isinstance(other, Array):
            return Boolean(int(self.elements != other.elements)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.elements != other.value)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def gen(self):
        for element in self.elements:
            yield RTResult().success(element)

    def get_index(self, index_start, index_end=None, index_step=None):
        if not isinstance(index_start, Number):
            return None, self.illegal_operation(index_start)

        if index_end != None and not isinstance(index_end, Number):
            return None, self.illegal_operation(index_end)

        if index_step != None and not isinstance(index_step, Number):
            return None, self.illegal_operation(index_step)

        if (index_end != None) and (index_step != None):
            try:
                # return String(self.value[index_start.value:index_end.value:index_step.value]), None
                if isinstance(self.value[index_start.value : index_end.value : index_step.value], str):
                    return String(self.value[index_start.value : index_end.value : index_step.value]), None
                elif isinstance(self.value[index_start.value : index_end.value : index_step.value], int):
                    return Number(self.value[index_start.value : index_end.value : index_step.value]), None
                elif isinstance(self.value[index_start.value : index_end.value : index_step.value], float):
                    return Number(self.value[index_start.value : index_end.value : index_step.value]), None
                elif isinstance(self.value[index_start.value : index_end.value : index_step.value], bool):
                    return Boolean(self.value[index_start.value : index_end.value : index_step.value]), None
                elif isinstance(self.value[index_start.value : index_end.value : index_step.value], list):
                    return Array(self.value[index_start.value : index_end.value : index_step.value]), None
            except (IndexError, TypeError):
                return None, RTError(
                    index_start.pos_start,
                    index_end.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context,
                )
        elif index_end != None:
            try:
                if isinstance(self.value[index_start.value : index_end.value], str):
                    return String(self.value[index_start.value : index_end.value]), None
                elif isinstance(self.value[index_start.value : index_end.value], Number):
                    return Number(self.value[index_start.value : index_end.value]), None
                elif isinstance(self.value[index_start.value : index_end.value], float):
                    return Number(self.value[index_start.value : index_end.value]), None
                elif isinstance(self.value[index_start.value : index_end.value], bool):
                    return Boolean(self.value[index_start.value : index_end.value]), None
                elif isinstance(self.value[index_start.value : index_end.value], list):
                    return Array(self.value[index_start.value : index_end.value]), None
                else:
                    return None, RTError(
                        index_start.pos_start,
                        index_end.pos_end,
                        f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                        self.context,
                    )
            except (IndexError, TypeError):
                return None, RTError(
                    index_start.pos_start,
                    index_end.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context,
                )

        try:
            # return String(self.value[index_start.value]), None
            if isinstance(self.value[index_start.value], str):
                return String(self.value[index_start.value]), None
            elif isinstance(self.value[index_start.value], Number):
                return Number(self.value[index_start.value]), None
            elif isinstance(self.value[index_start.value], float):
                return Number(self.value[index_start.value]), None
            elif isinstance(self.value[index_start.value], bool):
                return Boolean(self.value[index_start.value]), None
            elif isinstance(self.value[index_start.value], list):
                return Array(self.value[index_start.value]), None
            elif isinstance(self.value[index_start.value], String):
                return String(self.value[index_start.value]), None
            else:
                return None, RTError(
                    index_start.pos_start,
                    index_start.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context,
                )
        except (TypeError, IndexError):
            return None, RTError(
                index_start.pos_start,
                index_start.pos_end,
                f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                self.context,
            )

    def set_index(self, index, value):
        if not isinstance(index, Number):
            return None, self.illegal_operation(index)
        try:
            self.elements[index.value] = value
        except IndexError:
            return None, RTError(
                index.pos_start,
                index.pos_end,
                f"Cannot set element {index} from list {self!r} to {value!r} because it is out of bounds.",
                self.context,
            )
        return self, None

    def is_true(self):
        return len(self.elements) > 0

    def copy(self):
        copy = Array(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return ", ".join(str(x) for x in self.elements)

    def __repr__(self):
        return f'[{", ".join(repr(x) for x in self.elements)}]'

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, index):
        return self.elements[index]

    def __len__(self):
        return len(self.elements)


class HashMap(Value):
    def __init__(self, values):
        super().__init__()
        self.values = values
        self.value = values  # For matching with other conventions in the code base

    def added_to(self, other):
        if not isinstance(other, HashMap):
            return None, self.illegal_operation(other)

        new_dict = self.copy()
        for key, value in other.values.items():
            new_dict.values[key] = value

        return new_dict, None

    def gen(self):
        fake_pos = Position(0, 0, 0, "<hashmap key>", "<native code>")
        for key in self.values.keys():
            key_as_value = String(key).set_pos(fake_pos, fake_pos).set_context(self.context)
            yield RTResult().success(key_as_value)

    def get_index(self, index):
        if not isinstance(index, String):
            return None, self.illegal_operation(index)

        try:
            return self.values[index.value], None
        except KeyError:
            return None, RTError(
                self.pos_start, self.pos_end, f"Could not find key {index!r} in dict {self!r}", self.context
            )

    def set_index(self, index, value):
        if not isinstance(index, String):
            return None, self.illegal_operation(index)

        self.values[index.value] = value

        return self, None

    def copy(self):
        copy = HashMap(self.values)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return ", ".join([str(x) for x in self.values])

    def __repr__(self):
        return f'{{{", ".join([repr(x) for x in self.values])}}}'


class Type(Value):
    def __init__(self, variable):
        super().__init__()
        self.variable = variable or "<unknown>"
        self.get_type()

    def get_type(self):
        self.type = None

        if isinstance(self.variable, String):
            self.type = "String"
        elif isinstance(self.variable, Number):
            if isinstance(self.variable.value, int):
                self.type = "Number.Int"
            elif isinstance(self.variable.value, float):
                self.type = "Number.Float"
            else:
                self.type = "Number"
        elif isinstance(self.variable, Boolean):
            self.type = "Boolean"
        elif isinstance(self.variable, Array):
            self.type = "Array"
        elif isinstance(self.variable, Function):
            self.type = "Function"
        elif isinstance(self.variable, Class):
            self.type = "Class"
        elif isinstance(self.variable, Instance):
            self.type = "Instance"
        elif isinstance(self.variable, HashMap):
            self.type = "HashMap"
        elif isinstance(self.variable, PyAPI):
            self.type = "PyAPI"
        elif isinstance(self.variable, Type):
            self.type = "Type"
        elif self.variable.__class__.__name__ == "BuiltInFunction":
            self.type = "BuiltInFunction"
        elif self.variable.__class__.__name__ == "BuiltInClass":
            self.type = "BuiltInClass"
        elif self.variable.__class__.__name__ == "BuiltInInstance":
            self.type = "BuiltInInstance"
        else:
            self.type = "unknown"

    def copy(self):
        copy = Type(self.variable)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return f"<class '{self.type}'>"

    def __repr__(self):
        return f"<class '{self.type}'>"


def radonify(value, pos_start, pos_end, context):
    def _radonify(value):
        match value:
            case dict():
                return HashMap({k: radonify(v, pos_start, pos_end, context) for k, v in value.items()})
            case list():
                return Array([radonify(v, pos_start, pos_end, context) for v in value])
            case str():
                return String(value)
            case int() | float():
                return Number(value)
            case True:
                return Boolean.true
            case False:
                return Boolean.false
            case None:
                return Number.null
            case _ if inspect.isfunction(value):
                from core.builtin_funcs import BuiltInFunction, args # Lazy import

                signature = inspect.signature(value)
                params = list(signature.parameters.keys())

                @args(params)
                def wrapper(ctx):
                    res = RTResult()

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

def deradonify(value):
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
            def ret(*args, **kwargs):
                res = value.execute([radonify(arg, value.pos_start, value.pos_end, value.context) for arg in args], {k: radonify(arg) for k, arg in kwargs.items()})
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
    def __init__(self, value):
        super().__init__()
        self.value = value

    def copy(self): return self

    def __repr__(self): return f"PyObj({self.value!r})"

class PyAPI(Value):
    def __init__(self, code: str):
        super().__init__()
        self.code = code

    def pyapi(self, ns: HashMap):
        """TODO: update docs"""

        locals_dict = deradonify(ns)

        try:
            # Execute the code and store the output in locals_dict
            exec(self.code, {}, locals_dict)
            
            # Update namespace HashMap
            new_ns = radonify(locals_dict, self.pos_start, self.pos_end, self.context)
            for key, value in new_ns.values.items():
                ns.values[key] = value

        except Exception as e:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, f"Python {type(e).__name__} during execution of PyAPI: {e}", self.context))
        return RTResult().success(Number.null)

    def copy(self):
        copy = PyAPI(self.code)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy


class BaseFunction(Value):
    def __init__(self, name, symbol_table):
        super().__init__()
        self.name = name or "<anonymous>"
        self.symbol_table = symbol_table

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(self.symbol_table)
        return new_context

    def check_args(self, arg_names, args, kwargs, defaults):
        res = RTResult()

        args_count = len(args) + len(kwargs)
        if args_count > len(arg_names):
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

    def populate_args(self, arg_names, args, kwargs, defaults, exec_ctx):
        for i in range(len(arg_names)):
            arg_name = arg_names[i]
            if arg_name in kwargs:
                continue
            arg_value = defaults[i] if i >= len(args) else args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)

        for kw, kwarg in kwargs.items():
            kwarg.set_context(exec_ctx)
            exec_ctx.symbol_table.set(kw, kwarg)

    def check_and_populate_args(self, arg_names, args, kwargs, defaults, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args, kwargs, defaults))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, kwargs, defaults, exec_ctx)
        return res.success(None)


class BaseInstance(Value, ABC):
    def __init__(self, parent_class, symbol_table):
        super().__init__()
        self.parent_class = parent_class
        self.symbol_table = SymbolTable(symbol_table)
        self.value = f"<type {self.__class__.__name__}>"

    @abstractmethod
    def operator(self, operator, *args): ...

    def added_to(self, other):
        return self.operator("__add__", other)

    def subbed_by(self, other):
        return self.operator("__sub__", other)

    def multed_by(self, other):
        return self.operator("__mul__", other)

    def dived_by(self, other):
        return self.operator("__div__", other)

    def powed_by(self, other):
        return self.operator("__pow__", other)

    def get_comparison_eq(self, other):
        return self.operator("__eq__", other)

    def get_comparison_ne(self, other):
        return self.operator("__ne__", other)

    def get_comparison_lt(self, other):
        return self.operator("__lt__", other)

    def get_comparison_gt(self, other):
        return self.operator("__gt__", other)

    def get_comparison_lte(self, other):
        return self.operator("__lte__", other)

    def get_comparison_gte(self, other):
        return self.operator("__gte__", other)

    def anded_by(self, other):
        return self.operator("__and__", other)

    def ored_by(self, other):
        return self.operator("__or__", other)

    def notted(self, other):
        return self.operator("__not__", other)

    def gen(self):
        # TODO: change this when we have generator functions
        return self.operator("__iter__", other).gen()

    def get_index(self, index):
        return self.operator("__getitem__", index)

    def set_index(self, index, value):
        return self.operator("__setitem__", index, value)

    def execute(self, args, kwargs):
        return self.operator("__call__", *args, **kwargs)

    def is_true(self):
        return self.operator("__truthy__")

    def copy(self):
        return self


class Instance(BaseInstance):
    def __init__(self, parent_class):
        super().__init__(parent_class, None)

    def operator(self, operator, *args):
        res = RTResult()
        method = self.symbol_table.symbols.get(operator, None)

        if method == None or not isinstance(method, Function):
            return None, RTError(self.pos_start, self.pos_end, f"Function '{operator}' not defined", self.context)
        if method.symbol_table == None:
            method.symbol_table = SymbolTable()
        method.symbol_table.set("this", self)

        value = res.register(method.execute(list(args), {}))
        if res.should_return():
            return None, res.error
        return value, None

    def __repr__(self):
        # TODO: make this overloadable as well
        return f"<instance of class {self.parent_class.name}>"


class BaseClass(Value, ABC):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.value = f"<type {self.__class__.__name__}>"

    @abstractmethod
    def get(self, name): ...

    def dived_by(self, other):
        if not isinstance(other, String):
            return None, self.illegal_operation(other)

        value = self.get(other.value)
        if value == None:
            return None, RTError(self.pos_start, self.pos_end, f"'{other.value}' is not defined", self.context)

        return value, None

    @abstractmethod
    def create(self, args): ...

    @abstractmethod
    def init(self, inst, args, kwargs): ...

    def execute(self, args, kwargs):
        res = RTResult()

        inst = res.register(self.create(args))
        if res.should_return():
            return res

        res.register(self.init(inst, args, kwargs))
        if res.should_return():
            return res
        return res.success(inst)

    def copy(self):
        return self


class Class(BaseClass):
    def __init__(self, name, symbol_table):
        super().__init__(name)
        self.name = name
        self.symbol_table = symbol_table

    def get(self, name):
        method = self.symbol_table.symbols.get(name, None)
        if method == None:
            return None
        return method

    def create(self, args):
        res = RTResult()

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

    def init(self, inst, args, kwargs):
        res = RTResult()
        method = inst.symbol_table.symbols.get("__constructor__", None)

        if method == None or not isinstance(method, Function):
            return res.failure(
                RTError(self.pos_start, self.pos_end, f"Function '{self.name}' not defined", self.context)
            )
        if method.symbol_table == None:
            method.symbol_table = SymbolTable()
        method.symbol_table.set("this", inst)

        res.register(method.execute(args, kwargs))
        if res.should_return():
            return res

        return res.success(None)

    def __repr__(self):
        return f"<class {self.name}>"


class Function(BaseFunction):
    def __init__(self, name, symbol_table, body_node, arg_names, defaults, should_auto_return):
        super().__init__(name, symbol_table)
        self.body_node = body_node
        self.arg_names = arg_names
        self.defaults = defaults
        self.should_auto_return = should_auto_return

    def execute(self, args, kwargs):
        from core.interpreter import Interpreter  # Lazy import

        res = RTResult()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(self.check_and_populate_args(self.arg_names, args, kwargs, self.defaults, exec_ctx))
        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value == None:
            return res

        ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
        return res.success(ret_value)

    def copy(self):
        copy = Function(
            self.name, self.symbol_table, self.body_node, self.arg_names, self.defaults, self.should_auto_return
        )
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"


class Module(Value):
    def __init__(self, name, file_path, symbol_table):
        super().__init__()
        self.name = name
        self.file_path = file_path
        self.symbol_table = symbol_table

    def copy(self):
        return self

    def __repr__(self):
        return f"<module {self.name} @ {self.file_path!r}>"
