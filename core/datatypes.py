from core.parser import RTResult, Context, SymbolTable
from core.errors import (
    RTError,
    IndexError as IndexErr,
)


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

    def execute(self, args):
        return RTResult().failure(self.illegal_operation())

    def copy(self):
        raise Exception('No copy method defined')

    def is_true(self):
        return False

    def illegal_operation(self, other=None):
        if not other:
            other = self
        return RTError(
            self.pos_start, other.pos_end,
            'Illegal operation',
            self.context
        )


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
        return '<iterator>'

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
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Division by zero',
                    self.context
                )

            return Number(self.value / other.value).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def powed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
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
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Division by zero',
                    self.context
                )

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
            return Number(self.value ** other.value).set_context(self.context), None
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
        self.value = value

    def anded_by(self, other):
        return Boolean(self.value and other.value).set_context(self.context), None

    def ored_by(self, other):
        return Boolean(self.value or other.value).set_context(self.context), None

    def notted(self):
        return Boolean(not self.value).set_context(self.context), None
    
    def get_comparison_eq(self, other):
        if isinstance(other, Boolean):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value == other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.value == other.elements)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)
    
    def get_comparison_ne(self, other):
        if isinstance(other, Boolean):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        elif isinstance(other, Number):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        elif isinstance(other, String):
            return Boolean(int(self.value != other.value)).set_context(self.context), None
        elif isinstance(other, Array):
            return Boolean(int(self.value != other.elements)).set_context(self.context), None
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = Boolean(self.value)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def is_true(self):
        return self.value

    def __str__(self):
        return "true" if self.value else "false"

    def __repr__(self):
        return "true" if self.value else "false"


Number.null = Number(0)
Number.false = Number(0)
Number.true = Number(1)

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
                return String(self.value[index_start.value:index_end.value:index_step.value]), None
            except IndexError:
                return None, RTError(
                    index_start.pos_start, index_end.pos_end,
                    f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                    self.context
                )
        elif index_end != None:
            try:
                return String(self.value[index_start.value:index_end.value]), None
            except IndexError:
                return None, RTError(
                    index_start.pos_start, index_end.pos_end,
                    f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                    self.context
                )
            
        try:
            return String(self.value[index_start.value]), None
        except IndexError:
            return None, RTError(
                index_start.pos_start, index_start.pos_end,
                f"Cannot retrieve character {index_start} from string {self!r} because it is out of bounds.",
                self.context
            )

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
        self.value = elements # For matching with other conventions in the code base

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
                    other.pos_start, other.pos_end,
                    'Element at this index could not be removed from array because index is out of bounds',
                    self.context
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
                    other.pos_start, other.pos_end,
                    'Element at this index could not be retrieved from array because index is out of bounds',
                    self.context
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

    # def get_index(self, index):
    #     if not isinstance(index, Number):
    #         return None, self.illegal_operation(index)
    #     try:
    #         return self.elements[index.value], None
    #     except IndexError:
    #         return None, RTError(
    #             index.pos_start, index.pos_end,
    #             f"Cannot retrieve element {index} from list {self!r} because it is out of bounds.",
    #             self.context
    #         )

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
                if isinstance(self.value[index_start.value:index_end.value:index_step.value], str):
                    return String(self.value[index_start.value:index_end.value:index_step.value]), None
                elif isinstance(self.value[index_start.value:index_end.value:index_step.value], int):
                    return Number(self.value[index_start.value:index_end.value:index_step.value]), None
                elif isinstance(self.value[index_start.value:index_end.value:index_step.value], float):
                    return Number(self.value[index_start.value:index_end.value:index_step.value]), None
                elif isinstance(self.value[index_start.value:index_end.value:index_step.value], bool):
                    return Boolean(self.value[index_start.value:index_end.value:index_step.value]), None
                elif isinstance(self.value[index_start.value:index_end.value:index_step.value], list):
                    return Array(self.value[index_start.value:index_end.value:index_step.value]), None
            except (IndexError, TypeError):
                return None, RTError(
                    index_start.pos_start, index_end.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context
                )
        elif index_end != None:
            try:
                if isinstance(self.value[index_start.value:index_end.value], str):
                    return String(self.value[index_start.value:index_end.value]), None
                elif isinstance(self.value[index_start.value:index_end.value], Number):
                    return Number(self.value[index_start.value:index_end.value]), None
                elif isinstance(self.value[index_start.value:index_end.value], float):
                    return Number(self.value[index_start.value:index_end.value]), None
                elif isinstance(self.value[index_start.value:index_end.value], bool):
                    return Boolean(self.value[index_start.value:index_end.value]), None
                elif isinstance(self.value[index_start.value:index_end.value], list):
                    return Array(self.value[index_start.value:index_end.value]), None
                else:
                    return None, RTError(
                        index_start.pos_start, index_end.pos_end,
                        f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                        self.context
                    )
            except (IndexError, TypeError):
                return None, RTError(
                    index_start.pos_start, index_end.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context
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
                    index_start.pos_start, index_start.pos_end,
                    f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                    self.context
                )
        except (TypeError, IndexError):
            return None, RTError(
                index_start.pos_start, index_start.pos_end,
                f"Cannot retrieve character {index_start} from list {self!r} because it is out of bounds.",
                self.context
            )

    def is_true(self):
        return len(self.elements) > 0

    def copy(self):
        copy = Array(self.elements.copy())
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return ", ".join([str(x) for x in self.elements])

    def __repr__(self):
        return f'[{", ".join([repr(x) for x in self.elements])}]'

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, index):
        return self.elements[index]

    def __len__(self):
        return len(self.elements)


class ObjectNode(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements

    def added_to(self, other):
        new_object = self.copy()
        new_object.elements.append(other)
        return new_object, None

    def subbed_by(self, other):
        if isinstance(other, String):
            new_object = self.copy()
            try:
                del new_object.elements[other.value]
                return new_object, None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Element at this index could not be removed from object because index is out of bounds',
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def multed_by(self, other):
        if isinstance(other, ObjectNode):
            new_object = self.copy()
            new_object.elements.extend(other.elements)
            return new_object, None
        else:
            return None, Value.illegal_operation(self, other)

    def dived_by(self, other):
        if isinstance(other, String):
            try:
                return self.elements[other.value], None
            except:
                return None, RTError(
                    other.pos_start, other.pos_end,
                    'Element at this index could not be retrieved from object because index is out of bounds',
                    self.context
                )
        else:
            return None, Value.illegal_operation(self, other)

    def copy(self):
        copy = ObjectNode(self.elements)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return ", ".join([str(x) for x in self.elements])

    def __repr__(self):
        return f'{{{", ".join([repr(x) for x in self.elements])}}}'


class Type(Value):
    def __init__(self, variable):
        super().__init__()
        self.variable = variable or '<unknown>'
        self.get_type()

    def get_type(self):
        self.type = None

        if isinstance(self.variable, String):
            self.type = 'String'
        elif isinstance(self.variable, Number):
            if isinstance(self.variable, int):
                self.type = 'Number.Int'
            elif isinstance(self.variable, float):
                self.type = 'Number.Float'
            else:
                self.type = 'Number'
        elif isinstance(self.variable, Boolean):
            self.type = 'Boolean'
        elif isinstance(self.variable, Array):
            self.type = 'Array'
        elif isinstance(self.variable, Function):
            self.type = 'Function'
        elif isinstance(self.variable, Class):
            self.type = 'Class'
        elif isinstance(self.variable, Instance):
            self.type = 'Instance'
        elif isinstance(self.variable, ObjectNode):
            self.type = 'Object'
        elif isinstance(self.variable, PyAPI):
            self.type = 'PyAPI'
        elif isinstance(self.variable, Type):
            self.type = 'Type'
        elif self.variable.__class__.__name__ == 'BuiltInFunction':
            self.type = 'BuiltInFunction'
        else:
            self.type = 'unknown'

    def copy(self):
        copy = Type(self.variable)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy

    def __str__(self):
        return f'<class \'{self.type}\'>'

    def __repr__(self):
        return f'<class \'{self.type}\'>'

class PyAPI(Value):
    def __init__(self, code: str):
        super().__init__()
        self.code = code
        self.pyapi()

    def pyapi(self):
        '''This will execute python code and return the result. Output will be store in a output variable. To access the output, use output variable in the Python string code.'''

        # Empty dictionary to store the output
        locals_dict = {}

        try:
            # Execute the code and store the output in locals_dict
            exec(self.code, {}, locals_dict)

            if 'output' in locals_dict:
                return str(locals_dict['output'])
            else:
                return "No output produced."

        except Exception as e:
            return f"Error: {str(e)}"
            
    def copy(self):
        copy = PyAPI(self.code)
        copy.set_pos(self.pos_start, self.pos_end)
        copy.set_context(self.context)
        return copy


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args, defaults):
        res = RTResult()

        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)} too many args passed into {self}",
                self.context
            ))

        if len(args) < len(arg_names) - len(list(filter(lambda default: default is not None, defaults))):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{(len(arg_names) - len(list(filter(lambda default: default is not None, defaults)))) - len(args)} too few args passed into {self}",
                self.context
            ))

        return res.success(None)

    def populate_args(self, arg_names, args, defaults, exec_ctx):
        for i in range(len(arg_names)):
            arg_name = arg_names[i]
            arg_value = defaults[i] if i >= len(args) else args[i]
            arg_value.set_context(exec_ctx)
            exec_ctx.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, defaults, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args, defaults))
        if res.should_return():
            return res
        self.populate_args(arg_names, args, defaults, exec_ctx)
        return res.success(None)


class Instance(Value):
    def __init__(self, parent_class):
        super().__init__()
        self.parent_class = parent_class
        self.symbol_table = None

    def copy(self):
        return self

    def __repr__(self):
        return f"<instance of class {self.parent_class.name}>"

    def print_to_str(self):
        res = self.symbol_table.get('to_object').execute('')
        return res.should_return()
        # return res.should_return()
        # get the to_object() from parent_class and return the return value of it
        # return self.symbol_table.get(self.parent_class.name).to_object()


class Class(Value):
    def __init__(self, name, symbol_table):
        super().__init__()
        self.name = name
        self.symbol_table = symbol_table

    def dived_by(self, other):
        if not isinstance(other, String):
            return None, self.illegal_operation(other)

        value = self.symbol_table.get(other.value)
        if not value:
            return None, RTError(
                self.pos_start, self.pos_end,
                f"'{other.value}' is not defined",
                self.context
            )

        return value, None

    def execute(self, args):
        res = RTResult()

        exec_ctx = Context(self.name, self.context, self.pos_start)

        # TODO: Some issue here when direct accessing class methods without instantiation
        inst = Instance(self)
        inst.symbol_table = SymbolTable(self.symbol_table)

        exec_ctx.symbol_table = inst.symbol_table
        for name in self.symbol_table.symbols:
            inst.symbol_table.set(name, self.symbol_table.symbols[name].copy())

        for name in inst.symbol_table.symbols:
            inst.symbol_table.symbols[name].set_context(exec_ctx)

        inst.symbol_table.set('this', inst)

        method = inst.symbol_table.symbols[self.name] if self.name in inst.symbol_table.symbols else None

        if method == None or not isinstance(method, Function):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"Function '{self.name}' not defined",
                self.context
            ))

        res.register(method.execute(args))
        if res.should_return():
            return res

        return res.success(inst.set_context(self.context).set_pos(self.pos_start, self.pos_end))

    def copy(self):
        return self

    def __repr__(self):
        return f"<class {self.name}>"


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, defaults, should_auto_return):
        super().__init__(name)
        self.body_node = body_node
        self.arg_names = arg_names
        self.defaults = defaults
        self.should_auto_return = should_auto_return

    def execute(self, args):
        from core.interpreter import Interpreter  # Lazy import

        res = RTResult()
        interpreter = Interpreter()
        exec_ctx = self.generate_new_context()

        res.register(self.check_and_populate_args(
            self.arg_names, args, self.defaults, exec_ctx))
        if res.should_return():
            return res

        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        if res.should_return() and res.func_return_value == None:
            return res

        ret_value = (
            value if self.should_auto_return else None) or res.func_return_value or Number.null
        return res.success(ret_value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.defaults, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"
