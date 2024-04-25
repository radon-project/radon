from core.errors import *
from core.tokens import *
from core.datatypes import *
from core.parser import Parser
from core.lexer import *

import os


# Decorator for built-in functions
def args(arg_names, defaults=None):
    if defaults is None:
        defaults = [None] * len(arg_names)

    def _args(f):
        f.arg_names = arg_names
        f.defaults = defaults
        return f

    return _args


class BuiltInFunction(BaseFunction):
    def __init__(self, name, func=None):
        super().__init__(name, None)
        self.func = func

    def execute(self, args, kwargs):
        res = RTResult()
        if len(kwargs) > 0:
            return res.failure(
                RTError(
                    list(kwargs.values())[0].pos_start,
                    list(kwargs.values())[-1].pos_end,
                    "Keyword arguments are not yet supported for built-in functions.",
                    list(kwargs.values())[0].context,
                )
            )
        exec_ctx = self.generate_new_context()

        if self.func is None:
            method_name = f"execute_{self.name}"
            method = getattr(self, method_name, self.no_execute_method)
        else:
            method = self.func

        res.register(self.check_and_populate_args(method.arg_names, args, kwargs, method.defaults, exec_ctx))
        if res.should_return():
            return res

        return_value = res.register(method(exec_ctx))
        if res.should_return():
            return res
        return res.success(return_value)

    @args([])
    def no_execute_method(self, context):
        raise Exception(f"No execute_{self.name} method defined")

    def copy(self):
        return self

    def __repr__(self):
        return f"<built-in function {self.name}>"

    #####################################

    @args(["value"])
    def execute_print(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        if isinstance(value, String):
            print(str(value.value))

        elif isinstance(value, Number):
            print(str(value.value))

        elif isinstance(value, Array):
            print(repr(value))

        elif isinstance(value, Instance):
            # print(value.print_to_str())
            print(value)

        elif isinstance(value, Type):
            print(value)

        elif isinstance(value, PyAPI):
            try:
                print(value.value)
            except Exception as exe:
                # print(exe)
                pass

        elif isinstance(value, BuiltInFunction):
            print(value)

        elif isinstance(value, Class):
            print(value)

        elif isinstance(value, Instance):
            print(value)

        else:
            try:
                print(value.value)
            except AttributeError:
                print(repr(value))
        return RTResult().success(Number.null)

    @args(["value"])
    def execute_print_ret(self, exec_ctx):
        return RTResult().success(String(str(exec_ctx.symbol_table.get("value"))))

    @args(["value"])
    def execute_input(self, exec_ctx):
        text = input(str(exec_ctx.symbol_table.get("value")))
        return RTResult().success(String(text))

    @args([])
    def execute_input_int(self, exec_ctx):
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult().success(Number(number))

    @args([])
    def execute_clear(self, exec_ctx):
        os.system("cls" if os.name == "nt" else "clear")
        return RTResult().success(Number.null)

    @args(["value"])
    def execute_is_number(self, exec_ctx):
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult().success(Boolean.true if is_number else Boolean.false)

    @args(["value"])
    def execute_is_int(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        is_int = isinstance(value.value, int)
        return RTResult().success(Boolean.true if is_int else Boolean.false)

    @args(["value"])
    def execute_is_float(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")
        is_float = isinstance(value.value, float)
        return RTResult().success(Boolean.true if is_float else Boolean.false)

    @args(["value"])
    def execute_is_string(self, exec_ctx):
        is_string = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult().success(Boolean.true if is_string else Boolean.false)

    @args(["value"])
    def execute_is_bool(self, exec_ctx):
        is_boolean = isinstance(exec_ctx.symbol_table.get("value"), Boolean)
        return RTResult().success(Boolean.true if is_boolean else Boolean.false)

    @args(["value"])
    def execute_is_array(self, exec_ctx):
        is_arr = isinstance(exec_ctx.symbol_table.get("value"), Array)
        return RTResult().success(Boolean.true if is_arr else Boolean.false)

    @args(["value"])
    def execute_is_function(self, exec_ctx):
        is_func = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult().success(Boolean.true if is_func else Boolean.false)

    @args(["array", "value"])
    def execute_arr_append(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx))

        array_.elements.append(value)
        return RTResult().success(Number.null)

    @args(["array", "index"])
    def execute_arr_pop(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx))

        try:
            element = array_.elements.pop(index.value)
        except:
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Element at this index could not be removed from array because index is out of bounds",
                    exec_ctx,
                )
            )
        return RTResult().success(element)

    @args(["arrayA", "arrayB"])
    def execute_arr_extend(self, exec_ctx):
        arrayA = exec_ctx.symbol_table.get("arrayA")
        arrayB = exec_ctx.symbol_table.get("arrayB")

        if not isinstance(arrayA, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx))

        if not isinstance(arrayB, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be array", exec_ctx))

        arrayA.elements.extend(arrayB.elements)
        return RTResult().success(Number.null)

    @args(["array", "index"])
    def execute_arr_find(self, exec_ctx):
        array = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx))

        try:
            val_ = array.elements[index.value]
            if isinstance(val_, String):
                return RTResult().success(String(val_))
            elif isinstance(val_, Number):
                return RTResult().success(Number(val_))
            return RTResult().success(Array(val_))
        except:
            return RTResult().failure(IndexError(self.pos_start, self.pos_end, "Could't find that index", exec_ctx))

    @args(["array", "value"])
    def execute_arr_chunk(self, exec_ctx):
        array = exec_ctx.symbol_table.get("array")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(array, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx))

        if not isinstance(value, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx))

        try:
            # _list = Array(array.elements[start.value:end.value])
            _list = Array([array[i : i + value] for i in range(0, len(array), value)])
        except:
            return RTResult().failure(IndexError(self.pos_start, self.pos_end, "Could't not complete chunk", exec_ctx))
        return RTResult().success(_list)

    @args(["array", "index"])
    def execute_arr_get(self, exec_ctx):
        array = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array, Array):
            return RTResult().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be an array", exec_ctx)
            )
        if not isinstance(index, Number):
            return RTResult().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be a number", exec_ctx)
            )
        try:
            element = array.elements[int(index.value)]
            return RTResult().success(element)
        except Exception as exe:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, exe, exec_ctx))

    @args(["array"])
    def execute_arr_len(self, exec_ctx):
        array_ = exec_ctx.symbol_table.get("array")

        if not isinstance(array_, Array):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Argument must be array", exec_ctx))

        return RTResult().success(Number(len(array_.elements)))

    @args(["string"])
    def execute_str_len(self, exec_ctx):
        string = exec_ctx.symbol_table.get("string")

        if not isinstance(string, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Argument must be string", exec_ctx))

        return RTResult().success(Number(len(string.value)))

    @args(["string", "value"])
    def execute_str_find(self, exec_ctx):
        string = exec_ctx.symbol_table.get("string")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(string, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be string", exec_ctx))

        if not isinstance(value, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be string", exec_ctx))

        try:
            return RTResult().success(Number(string.value.find(value.value)))
        except:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could't find that index", exec_ctx))

    @args(["string", "index"])
    def execute_str_get(self, exec_ctx):
        string = exec_ctx.symbol_table.get("string")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(string, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "First argument must be string", exec_ctx))

        if not isinstance(index, Number):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx))

        try:
            return RTResult().success(String(string.value[index.value]))
        except:
            return RTResult().failure(IndexError(self.pos_start, self.pos_end, "Could't find that index", exec_ctx))

    @args(["value"])
    def execute_int(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Number(int(value.value)))
        except:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could not convert to int", exec_ctx))

    @args(["value"])
    def execute_float(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Number(float(value.value)))
        except:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could not convert to float", exec_ctx))

    @args(["value"])
    def execute_str(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            if isinstance(value, Array):
                return RTResult().success(String(str(value.elements)))
            return RTResult().success(String(str(value.value)))
        except Exception as e:
            # print(e)
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could not convert to string", exec_ctx))

    @args(["value"])
    def execute_bool(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult().success(Boolean(bool(value.value)))
        except:
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could not convert to boolean", exec_ctx))

    @args(["value"])
    def execute_type(self, exec_ctx):
        value = exec_ctx.symbol_table.get("value")

        return RTResult().success(Type(value))

    @args(["code"])
    def execute_pyapi(self, exec_ctx):
        code = exec_ctx.symbol_table.get("code")

        try:
            return RTResult().success(
                # PyAPI(code.value).pyapi()
                String(PyAPI(code.value).pyapi())
            )
        except Exception as e:
            print(e)
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could't run the code", exec_ctx))

    @args([])
    def execute_sys_args(self, exec_ctx):
        from sys import argv  # Lazy import

        try:
            return RTResult().success(Array(argv))
        except Exception as e:
            print(e)
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Could't run the sys_args", exec_ctx))

    @args([])
    def execute_time_now(self, exec_ctx):
        import time  # Lazy import

        return RTResult().success(Number(time.time()))

    @args(["module"])
    def execute_require(self, exec_ctx):
        module = exec_ctx.symbol_table.get("module")

        if not isinstance(module, String):
            return RTResult().failure(RTError(self.pos_start, self.pos_end, "Second argument must be string", exec_ctx))

        module = module.value

        try:
            if module not in STDLIBS:
                file_extension = module.split("/")[-1].split(".")[-1]
                if file_extension != "rn":
                    return RTResult().failure(
                        RTError(self.pos_start, self.pos_end, "A Radon script must have a .rn extension", exec_ctx)
                    )
                module_file = module.split("/")[-1]
                module_path = os.path.dirname(os.path.realpath(module))

                global CURRENT_DIR
                if CURRENT_DIR is None:
                    CURRENT_DIR = module_path

                module = os.path.join(CURRENT_DIR, module_file)
            else:
                # For STDLIB modules
                module = os.path.join(BASE_DIR, "stdlib", f"{module}.rn")

            with open(module, "r") as f:
                script = f.read()
        except Exception as e:
            if run.hide_paths:
                module = "<stdin>"
            return RTResult().failure(
                RTError(self.pos_start, self.pos_end, f'Failed to load script "{module}"\n' + str(e), exec_ctx)
            )

        _, error, should_exit = run(module, script)

        if error:
            if run.hide_paths:
                module = "<stdin>"
            return RTResult().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f'Failed to finish executing script "{module}"\n' + error.as_string(),
                    exec_ctx,
                )
            )

        if should_exit:
            return RTResult().success_exit(Number.null)
        return RTResult().success(Number.null)

    @args([])
    def execute_exit(self, exec_ctx):
        return RTResult().success_exit(Number.null)


def run(fn, text, context=None, entry_pos=None, return_result=False, hide_paths=False):
    from core.interpreter import Interpreter  # Lazy import

    if hide_paths or run.hide_paths:
        hide_paths = run.hide_paths = True  # Once hidden, forever hidden

    # Generate tokens
    fn = "[REDACTED]" if hide_paths else fn

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
    # context = Context('<program>')
    # context.symbol_table = global_symbol_table
    context = Context("<program>", context, entry_pos)
    if context.parent is None:
        context.symbol_table = global_symbol_table
    else:
        context.symbol_table = context.parent.symbol_table
    result = interpreter.visit(ast.node, context)

    if return_result:
        return result
    return result.value, result.error, result.should_exit


run.hide_paths = False

# Defining builtin functions
# I/O methods
BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.print_ret = BuiltInFunction("print_ret")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
# Datatype validator methods
BuiltInFunction.is_num = BuiltInFunction("is_num")
BuiltInFunction.is_int = BuiltInFunction("is_int")
BuiltInFunction.is_float = BuiltInFunction("is_float")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_bool = BuiltInFunction("is_bool")
BuiltInFunction.is_array = BuiltInFunction("is_array")
BuiltInFunction.is_fun = BuiltInFunction("is_fun")
# Array methods
BuiltInFunction.arr_append = BuiltInFunction("arr_append")
BuiltInFunction.arr_pop = BuiltInFunction("arr_pop")
BuiltInFunction.arr_extend = BuiltInFunction("arr_extend")
BuiltInFunction.arr_find = BuiltInFunction("arr_find")
BuiltInFunction.arr_len = BuiltInFunction("arr_len")
BuiltInFunction.arr_chunk = BuiltInFunction("arr_chunk")
BuiltInFunction.arr_get = BuiltInFunction("arr_get")
# String methods
BuiltInFunction.str_len = BuiltInFunction("str_len")
BuiltInFunction.str_find = BuiltInFunction("str_find")
BuiltInFunction.str_get = BuiltInFunction("str_get")
# Typecase methods
BuiltInFunction.int = BuiltInFunction("int")
BuiltInFunction.float = BuiltInFunction("float")
BuiltInFunction.str = BuiltInFunction("str")
BuiltInFunction.bool = BuiltInFunction("bool")
BuiltInFunction.type = BuiltInFunction("type")
# PyAPI methods (Python API)
BuiltInFunction.pyapi = BuiltInFunction("pyapi")
# System methods
BuiltInFunction.require = BuiltInFunction("require")
BuiltInFunction.exit = BuiltInFunction("exit")
BuiltInFunction.sys_args = BuiltInFunction("sys_args")
BuiltInFunction.time_now = BuiltInFunction("time_now")


# Setting all functions to global symbol table
def create_global_symbol_table():
    ret = SymbolTable()
    ret.set("null", Number.null)
    ret.set("false", Boolean.false)
    ret.set("true", Boolean.true)
    ret.set("print", BuiltInFunction.print)
    ret.set("print_ret", BuiltInFunction.print_ret)
    ret.set("input", BuiltInFunction.input)
    ret.set("input_int", BuiltInFunction.input_int)
    ret.set("clear", BuiltInFunction.clear)
    ret.set("cls", BuiltInFunction.clear)
    ret.set("require", BuiltInFunction.require)
    ret.set("exit", BuiltInFunction.exit)
    # Datatype validator methods
    ret.set("is_num", BuiltInFunction.is_num)
    ret.set("is_int", BuiltInFunction.is_int)
    ret.set("is_float", BuiltInFunction.is_float)
    ret.set("is_str", BuiltInFunction.is_string)
    ret.set("is_bool", BuiltInFunction.is_bool)
    ret.set("is_array", BuiltInFunction.is_array)
    ret.set("is_fun", BuiltInFunction.is_fun)
    # Internal array methods
    ret.set("arr_append", BuiltInFunction.arr_append)
    ret.set("arr_pop", BuiltInFunction.arr_pop)
    ret.set("arr_extend", BuiltInFunction.arr_extend)
    ret.set("arr_find", BuiltInFunction.arr_find)
    ret.set("arr_len", BuiltInFunction.arr_len)
    ret.set("arr_chunk", BuiltInFunction.arr_chunk)
    ret.set("arr_get", BuiltInFunction.arr_get)
    # String methods
    ret.set("str_len", BuiltInFunction.str_len)
    ret.set("str_find", BuiltInFunction.str_find)
    ret.set("str_get", BuiltInFunction.str_get)
    # Typecase methods
    ret.set("int", BuiltInFunction.int)
    ret.set("float", BuiltInFunction.float)
    ret.set("str", BuiltInFunction.str)
    ret.set("bool", BuiltInFunction.bool)
    ret.set("type", BuiltInFunction.type)
    # PyAPI methods (Python API)
    ret.set("pyapi", BuiltInFunction.pyapi)
    # System methods
    ret.set("require", BuiltInFunction.require)
    ret.set("exit", BuiltInFunction.exit)
    ret.set("sys_args", BuiltInFunction.sys_args)
    ret.set("time_now", BuiltInFunction.time_now)
    return ret

global_symbol_table = create_global_symbol_table()
