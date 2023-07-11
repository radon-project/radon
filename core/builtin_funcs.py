from core.errors import *
# from core.parser import *
from core.tokens import *
from core.datatypes import *
from core.parser import Parser
from core.lexer import *

import os


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, args):
        res = RTResult()
        exec_ctx = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        res.register(self.check_and_populate_args(
            method.arg_names, args, exec_ctx))
        if res.should_return():
            return res

        return_value = res.register(method(exec_ctx))
        if res.should_return():
            return res
        return res.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"

    #####################################

    def execute_print(self, exec_ctx):
        value = exec_ctx.symbol_table.get('value')

        if isinstance(value, String):
            print(str(value.value))

        elif isinstance(value, Number):
            print(str(value.value))

        elif isinstance(value, Array):
            print(repr(value))

        elif isinstance(value, Instance):
            # print(value.print_to_str())
            print(value)

        else:
            print(value.value)
        return RTResult().success(Number.null)
    execute_print.arg_names = ['value']

    def execute_print_ret(self, exec_ctx):
        return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))
    execute_print_ret.arg_names = ['value']

    def execute_input(self, exec_ctx):
        text = input(str(exec_ctx.symbol_table.get('value')))
        return RTResult().success(String(text))
    execute_input.arg_names = ['value']

    def execute_input_int(self, exec_ctx):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult().success(Number(number))
    execute_input_int.arg_names = []

    def execute_clear(self, exec_ctx):
        os.system('cls' if os.name == 'nt' else 'clear')
        return RTResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult().success(Boolean.true if is_number else Boolean.false)
    execute_is_number.arg_names = ["value"]

    def execute_is_int(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        is_int = isinstance(value.value, int)
        return RTResult().success(Boolean.true if is_int else Boolean.false)
    execute_is_int.arg_names = ["value"]

    def execute_is_float(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        is_float = isinstance(value.value, float)
        return RTResult().success(Boolean.true if is_float else Boolean.false)
    execute_is_float.arg_names = ["value"]

    def execute_is_string(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult().success(Boolean.true if is_number else Boolean.false)
    execute_is_string.arg_names = ["value"]

    def execute_is_bool(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Boolean)
        return RTResult().success(Boolean.true if is_number else Boolean.false)
    execute_is_bool.arg_names = ["value"]

    def execute_is_array(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Array)
        return RTResult().success(Boolean.true if is_number else Boolean.false)
    execute_is_array.arg_names = ["value"]

    def execute_is_function(self, exec_ctx):
        is_number = isinstance(
            exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult().success(Boolean.true if is_number else Boolean.false)
    execute_is_function.arg_names = ["value"]

    def execute_arr_append(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be array",
                exec_ctx
            ))

        array_.elements.append(value)
        return RTResult().success(Number.null)
    execute_arr_append.arg_names = ["array", "value"]

    def execute_arr_pop(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be array",
                exec_ctx
            ))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be number",
                exec_ctx
            ))

        try:
            element = array_.elements.pop(index.value)
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                'Element at this index could not be removed from array because index is out of bounds',
                exec_ctx
            ))
        return RTResult().success(element)
    execute_arr_pop.arg_names = ["array", "index"]

    def execute_arr_extend(self, exec_ctx):
        arrayA = exec_ctx.symbol_table.get("arrayA")
        arrayB = exec_ctx.symbol_table.get("arrayB")

        if not isinstance(arrayA, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be array",
                exec_ctx
            ))

        if not isinstance(arrayB, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be array",
                exec_ctx
            ))

        arrayA.elements.extend(arrayB.elements)
        return RTResult().success(Number.null)
    execute_arr_extend.arg_names = ["arrayA", "arrayB"]

    def execute_arr_find(self, exec_ctx):
        array = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be array",
                exec_ctx
            ))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be number",
                exec_ctx
            ))

        try:
            return RTResult().success(
                array.elements[index.value]
            )
        except:
            return RTResult().failure(IndexError(
                self.pos_start, self.pos_end,
                "Could't find that index",
                exec_ctx
            ))
        
    execute_arr_find.arg_names = ["array", "index"]

    def execute_arr_slice(self, exec_ctx):
        array = exec_ctx.symbol_table.get("array")
        start = exec_ctx.symbol_table.get("start")
        end = exec_ctx.symbol_table.get("end")

        if not isinstance(array, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be array",
                exec_ctx
            ))

        if not isinstance(start, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be number",
                exec_ctx
            ))

        if not isinstance(end, Number):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Third argument must be number",
                exec_ctx
            ))

        try:
            _list = Array(array.elements[start.value:end.value])
        except:
            return RTResult().failure(IndexError(
                self.pos_start, self.pos_end,
                "Could't find that index",
                exec_ctx
            ))
        return RTResult().success(_list)
        
    execute_arr_slice.arg_names = ["array", "start", "end"]

    def execute_arr_len(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument must be array",
                exec_ctx
            ))

        return RTResult().success(Number(len(array_.elements)))
    execute_arr_len.arg_names = ["array"]

    def execute_strlen(self, exec_ctx):
        string = exec_ctx.symbol_table.get("string")

        if not isinstance(string, String):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argument must be string",
                exec_ctx
            ))

        return RTResult().success(Number(len(string.value)))
    execute_strlen.arg_names = ["string"]

    def execute_int(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Number(int(value.value)))
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could not convert to int",
                exec_ctx
            ))
    execute_int.arg_names = ["value"]

    def execute_float(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Number(float(value.value)))
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could not convert to float",
                exec_ctx
            ))
    execute_float.arg_names = ["value"]

    def execute_str(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(String(str(value.value)))
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could not convert to string",
                exec_ctx
            ))
    execute_str.arg_names = ["value"]

    def execute_bool(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Boolean(bool(value.value)))
        except:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could not convert to boolean",
                exec_ctx
            ))
    execute_bool.arg_names = ["value"]

    def execute_type(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(
            Type(value)
        )
    execute_type.arg_names = ["value"]

    def execute_pyapi(self, exec_ctx):
        code = exec_ctx.symbol_table.get("code")

        try:
            return RTResult().success(
                PyAPI(code.value)
            )
        except Exception as e:
            print(e)
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could't run the code",
                exec_ctx
            ))
    execute_pyapi.arg_names = ["code"]

    def execute_sys_args(self, exec_ctx):
        from sys import argv  # Lazy import

        try:
            return RTResult().success(
                Array(argv)
            )
        except Exception as e:
            print(e)
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Could't run the sys_args",
                exec_ctx
            ))
    execute_sys_args.arg_names = []

    def execute_require(self, exec_ctx):
        module = exec_ctx.symbol_table.get("module")

        if not isinstance(module, String):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Second argument must be string",
                exec_ctx
            ))

        module = module.value

        try:
            if module not in STDLIBS:
                file_extension = module.split("/")[-1].split('.')[-1]
                if file_extension != "rn":
                    return RTResult().failure(RTError(
                        self.pos_start, self.pos_end,
                        "A Radon script must have a .rn extension",
                        exec_ctx
                    ))
                module_file = module.split("/")[-1]
                module_path = os.path.dirname(os.path.realpath(module))

                global CURRENT_DIR
                if CURRENT_DIR is None:
                    CURRENT_DIR = module_path

                module = os.path.join(CURRENT_DIR, module_file)
            else:
                # For STDLIB modules
                module = os.path.join(BASE_DIR, 'stdlib', f'{module}.rn')

            with open(module, "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                f"Failed to load script \"{module}\"\n" + str(e),
                exec_ctx
            ))

        _, error, should_exit = run(module, script)

        if error:
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                f"Failed to finish executing script \"{module}\"\n" +
                error.as_string(),
                exec_ctx
            ))

        if should_exit:
            return RTResult().success_exit(Number.null)
        return RTResult().success(Number.null)
    execute_require.arg_names = ["module"]

    def execute_exit(self, exec_ctx):
        return RTResult().success_exit(Number.null)
    execute_exit.arg_names = []


def run(fn, text):
    from core.interpreter import Interpreter  # Lazy import

    # Generate tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error:
        return None, error, False

    # Generate AST
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error, False

    # Run program
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error, result.should_exit


# Defining builtin functions
BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")

BuiltInFunction.is_num = BuiltInFunction("is_num")
BuiltInFunction.is_int = BuiltInFunction("is_int")
BuiltInFunction.is_float = BuiltInFunction("is_float")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_bool = BuiltInFunction("is_bool")
BuiltInFunction.is_array = BuiltInFunction("is_array")
BuiltInFunction.is_fun = BuiltInFunction("is_fun")

BuiltInFunction.arr_append = BuiltInFunction("arr_append")
BuiltInFunction.arr_pop = BuiltInFunction("arr_pop")
BuiltInFunction.arr_extend = BuiltInFunction("arr_extend")
BuiltInFunction.arr_find = BuiltInFunction("arr_find")
BuiltInFunction.arr_slice = BuiltInFunction("arr_slice")
BuiltInFunction.arr_len = BuiltInFunction("arr_len")

BuiltInFunction.require = BuiltInFunction("require")
BuiltInFunction.exit = BuiltInFunction("exit")
BuiltInFunction.strlen = BuiltInFunction("strlen")
BuiltInFunction.int = BuiltInFunction("int")
BuiltInFunction.float = BuiltInFunction("float")
BuiltInFunction.str = BuiltInFunction("str")
BuiltInFunction.bool = BuiltInFunction("bool")
BuiltInFunction.type = BuiltInFunction("type")
BuiltInFunction.pyapi = BuiltInFunction("pyapi")
BuiltInFunction.sys_args = BuiltInFunction("sys_args")


# Setting all functions to global symbol table
global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number.null)
global_symbol_table.set("false", Boolean.false)
global_symbol_table.set("true", Boolean.true)
global_symbol_table.set("print", BuiltInFunction.print)
global_symbol_table.set("print_ret", BuiltInFunction.print_ret)
global_symbol_table.set("input", BuiltInFunction.input)
global_symbol_table.set("input_int", BuiltInFunction.input_int)
global_symbol_table.set("clear", BuiltInFunction.clear)
global_symbol_table.set("cls", BuiltInFunction.clear)
global_symbol_table.set("require", BuiltInFunction.require)
global_symbol_table.set("exit", BuiltInFunction.exit)
# Datatype validator methods
global_symbol_table.set("is_num", BuiltInFunction.is_num)
global_symbol_table.set("is_int", BuiltInFunction.is_int)
global_symbol_table.set("is_float", BuiltInFunction.is_float)
global_symbol_table.set("is_str", BuiltInFunction.is_string)
global_symbol_table.set("is_bool", BuiltInFunction.is_bool)
global_symbol_table.set("is_array", BuiltInFunction.is_array)
global_symbol_table.set("is_fun", BuiltInFunction.is_fun)
# Internal array methods
global_symbol_table.set("arr_append", BuiltInFunction.arr_append)
global_symbol_table.set("arr_pop", BuiltInFunction.arr_pop)
global_symbol_table.set("arr_extend", BuiltInFunction.arr_extend)
global_symbol_table.set("arr_find", BuiltInFunction.arr_find)
global_symbol_table.set("arr_slice", BuiltInFunction.arr_slice)
global_symbol_table.set("arr_len", BuiltInFunction.arr_len)
# String methods
global_symbol_table.set("strlen", BuiltInFunction.strlen)
# Typecase methods
global_symbol_table.set("int", BuiltInFunction.int)
global_symbol_table.set("float", BuiltInFunction.float)
global_symbol_table.set("str", BuiltInFunction.str)
global_symbol_table.set("bool", BuiltInFunction.bool)

global_symbol_table.set("type", BuiltInFunction.type)
global_symbol_table.set("pyapi", BuiltInFunction.pyapi)
global_symbol_table.set("sys_args", BuiltInFunction.sys_args)
