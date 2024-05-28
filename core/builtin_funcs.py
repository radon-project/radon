from __future__ import annotations

from core.errors import *
from core.tokens import *
from core.datatypes import *
from core.parser import Parser
from core.lexer import *

import os
from sys import stdout

from typing import Optional, Callable, Protocol, cast, Generic, ParamSpec

P = ParamSpec("P")


class RadonCompatibleFunction(Protocol, Generic[P]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RTResult[Value]: ...

    @property
    def arg_names(self) -> list[str]: ...

    @property
    def defaults(self) -> list[Optional[Value]]: ...


# Decorator for built-in functions
def args(
    arg_names: list[str], defaults: Optional[list[Optional[Value]]] = None
) -> Callable[[Callable[P, RTResult[Value]]], RadonCompatibleFunction[P]]:
    if defaults is None:
        defaults = [None] * len(arg_names)

    def _args(f: Callable[P, RTResult[Value]]) -> RadonCompatibleFunction[P]:
        f.arg_names = arg_names  # type: ignore
        f.defaults = defaults  # type: ignore
        return cast(RadonCompatibleFunction, f)

    return _args


class BuiltInFunction(BaseFunction):
    func: Optional[RadonCompatibleFunction]

    def __init__(self, name: str, func: Optional[RadonCompatibleFunction] = None):
        super().__init__(name, None)
        self.func = func

    def execute(self, args: list[Value], kwargs: dict[str, Value]) -> RTResult[Value]:
        res = RTResult[Value]()
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

        return_value = res.register(method(exec_ctx))  # type: ignore
        if res.should_return():
            return res
        assert return_value is not None
        return res.success(return_value)

    @args([])
    def no_execute_method(self, context: Context):
        raise Exception(f"No execute_{self.name} method defined")

    def copy(self) -> BuiltInFunction:
        return self

    def __repr__(self) -> str:
        return f"<built-in function {self.name}>"

    #####################################

    @args(["value"])
    def execute_print(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")

        print(value)
        return RTResult[Value]().success(Null.null())

    @args(["value"])
    def execute_print_ret(self, exec_ctx: Context) -> RTResult[Value]:
        return RTResult[Value]().success(String(str(exec_ctx.symbol_table.get("value"))))

    @args(["value"])
    def execute_len(self, exec_ctx: Context) -> RTResult[Value]:
        val = exec_ctx.symbol_table.get("value")
        try:
            if val is not None and val.__class__ is not Value:
                if hasattr(val, "__len__"):
                    ret = int(val.__len__())
                elif hasattr(val, "__exec_len__"):
                    ret = int(val.__exec_len__())
                else:
                    raise TypeError()
                return RTResult[Value]().success(Number(ret))
            return TypeError()
        except TypeError:
            return RTResult[Value]().failure(Error(self.pos_start, self.pos_end, "TypeError", "Object has no len()"))

    @args(["value"])
    def execute_input(self, exec_ctx: Context) -> RTResult[Value]:
        text = input(str(exec_ctx.symbol_table.get("value")))
        return RTResult[Value]().success(String(text))

    @args([])
    def execute_input_int(self, exec_ctx: Context) -> RTResult[Value]:
        while True:
            text = input()
            try:
                number = int(text)
                break
            except ValueError:
                print(f"'{text}' must be an integer. Try again!")
        return RTResult[Value]().success(Number(number))

    @args([])
    def execute_clear(self, exec_ctx: Context) -> RTResult[Value]:
        os.system("cls" if os.name == "nt" else "clear")
        return RTResult[Value]().success(Null.null())

    @args(["value"])
    def execute_is_number(self, exec_ctx: Context) -> RTResult[Value]:
        is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
        return RTResult[Value]().success(Boolean.true() if is_number else Boolean.false())

    @args(["value"])
    def execute_is_int(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")
        is_int = isinstance(value, Number) and isinstance(value.value, int)
        return RTResult[Value]().success(Boolean.true() if is_int else Boolean.false())

    @args(["value"])
    def execute_is_float(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")
        is_float = isinstance(value, Number) and isinstance(value.value, float)
        return RTResult[Value]().success(Boolean.true() if is_float else Boolean.false())

    @args(["value"])
    def execute_is_string(self, exec_ctx: Context) -> RTResult[Value]:
        is_string = isinstance(exec_ctx.symbol_table.get("value"), String)
        return RTResult[Value]().success(Boolean.true() if is_string else Boolean.false())

    @args(["value"])
    def execute_is_bool(self, exec_ctx: Context) -> RTResult[Value]:
        is_boolean = isinstance(exec_ctx.symbol_table.get("value"), Boolean)
        return RTResult[Value]().success(Boolean.true() if is_boolean else Boolean.false())

    @args(["value"])
    def execute_is_array(self, exec_ctx: Context) -> RTResult[Value]:
        is_arr = isinstance(exec_ctx.symbol_table.get("value"), Array)
        return RTResult[Value]().success(Boolean.true() if is_arr else Boolean.false())

    @args(["value"])
    def execute_is_function(self, exec_ctx: Context) -> RTResult[Value]:
        is_func = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
        return RTResult[Value]().success(Boolean.true() if is_func else Boolean.false())

    @args(["array", "value"])
    def execute_arr_append(self, exec_ctx: Context) -> RTResult[Value]:
        array = exec_ctx.symbol_table.get("array")
        value = exec_ctx.symbol_table.get("value")
        assert value is not None

        if not isinstance(array, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx)
            )

        array.elements.append(value)
        return RTResult[Value]().success(Null.null())

    @args(["array", "index"], [None, Number(-1)])
    def execute_arr_pop(self, exec_ctx: Context) -> RTResult[Value]:
        array = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx)
            )

        if not isinstance(index, Number):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx)
            )

        try:
            element = array.elements.pop(int(index.value))
        except Exception:
            return RTResult[Value]().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    "Element at this index could not be removed from array because index is out of bounds",
                    exec_ctx,
                )
            )
        return RTResult[Value]().success(element)

    @args(["arrayA", "arrayB"])
    def execute_arr_extend(self, exec_ctx: Context) -> RTResult[Value]:
        arrayA = exec_ctx.symbol_table.get("arrayA")
        arrayB = exec_ctx.symbol_table.get("arrayB")

        if not isinstance(arrayA, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx)
            )

        if not isinstance(arrayB, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be array", exec_ctx)
            )

        arrayA.elements.extend(arrayB.elements)
        return RTResult[Value]().success(Null.null())

    @args(["array", "value"])
    def execute_arr_chunk(self, exec_ctx: Context) -> RTResult[Value]:
        array = exec_ctx.symbol_table.get("array")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(array, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be array", exec_ctx)
            )

        if not isinstance(value, Number):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx)
            )

        val = int(value.value)

        try:
            # _list = Array(array.elements[start.value:end.value])
            _list = Array([array[i : i + val] for i in range(0, len(array), val)])
        except IndexError:
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Could't not complete chunk", exec_ctx)
            )
        return RTResult[Value]().success(_list)

    @args(["array", "index"])
    def execute_arr_get(self, exec_ctx: Context) -> RTResult[Value]:
        array = exec_ctx.symbol_table.get("array")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(array, Array):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be an array", exec_ctx)
            )
        if not isinstance(index, Number):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be a number", exec_ctx)
            )
        try:
            element = array.elements[int(index.value)]
            return RTResult[Value]().success(element)
        except Exception as exe:
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, str(exe), exec_ctx))

    @args(["array"])
    def execute_arr_len(self, exec_ctx: Context) -> RTResult[Value]:
        array_ = exec_ctx.symbol_table.get("array")

        if not isinstance(array_, Array):
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, "Argument must be array", exec_ctx))

        return RTResult[Value]().success(Number(len(array_.elements)))

    @args(["string"])
    def execute_str_len(self, exec_ctx: Context) -> RTResult[Value]:
        string = exec_ctx.symbol_table.get("string")

        if not isinstance(string, String):
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, "Argument must be string", exec_ctx))

        return RTResult[Value]().success(Number(len(string.value)))

    @args(["string", "value"])
    def execute_str_find(self, exec_ctx: Context) -> RTResult[Value]:
        string = exec_ctx.symbol_table.get("string")
        value = exec_ctx.symbol_table.get("value")

        if not isinstance(string, String):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be string", exec_ctx)
            )

        if not isinstance(value, String):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be string", exec_ctx)
            )

        try:
            return RTResult[Value]().success(Number(string.value.find(value.value)))
        except Exception:
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, "Could't find that index", exec_ctx))

    @args(["string", "index"])
    def execute_str_get(self, exec_ctx: Context) -> RTResult[Value]:
        string = exec_ctx.symbol_table.get("string")
        index = exec_ctx.symbol_table.get("index")

        if not isinstance(string, String):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "First argument must be string", exec_ctx)
            )

        if not isinstance(index, Number):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be number", exec_ctx)
            )

        try:
            return RTResult[Value]().success(String(string.value[int(index.value)]))
        except IndexError:
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, "Could't find that index", exec_ctx))

    @args(["value"])
    def execute_int(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")
        try:
            return RTResult[Value]().success(Number(int(value.value)))  # type: ignore
        except Exception:
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Could not convert to int", exec_ctx)
            )

    @args(["value"])
    def execute_float(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")

        try:
            return RTResult[Value]().success(Number(float(value.value)))  # type: ignore
        except Exception:
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Could not convert to float", exec_ctx)
            )

    @args(["value"])
    def execute_str(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")

        try:
            if isinstance(value, Array):
                return RTResult[Value]().success(String(str(value.elements)))
            return RTResult[Value]().success(String(str(value)))
        except Exception:
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Could not convert to string", exec_ctx)
            )

    @args(["value"])
    def execute_bool(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")
        assert value is not None

        return RTResult[Value]().success(Boolean.true() if value.is_true() else Boolean.false())

    @args(["value"])
    def execute_type(self, exec_ctx: Context) -> RTResult[Value]:
        value = exec_ctx.symbol_table.get("value")
        assert value is not None

        return RTResult[Value]().success(Type(value))

    @args(["code", "ns"])
    def execute_pyapi(self, exec_ctx: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        code = exec_ctx.symbol_table.get("code")
        ns = exec_ctx.symbol_table.get("ns")

        if not isinstance(code, String):
            return res.failure(RTError(self.pos_start, self.pos_end, "Code must be string", exec_ctx))
        if not isinstance(ns, HashMap):
            return res.failure(RTError(self.pos_start, self.pos_end, "Namespace must be hashmap", exec_ctx))

        res.register(PyAPI(code.value).set_pos(self.pos_start, self.pos_end).set_context(self.context).pyapi(ns))
        if res.should_return():
            return res
        return res.success(Null.null())

    @args([])
    def execute_time_now(self, exec_ctx: Context) -> RTResult[Value]:
        import time  # Lazy import

        return RTResult[Value]().success(Number(time.time()))

    @args(["module"])
    def execute_require(self, exec_ctx: Context) -> RTResult[Value]:
        module_val = exec_ctx.symbol_table.get("module")

        if not isinstance(module_val, String):
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, "Second argument must be string", exec_ctx)
            )

        module = module_val.value

        try:
            if module not in STDLIBS:
                file_extension = module.split("/")[-1].split(".")[-1]
                if file_extension != "rn":
                    return RTResult[Value]().failure(
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
            return RTResult[Value]().failure(
                RTError(self.pos_start, self.pos_end, f'Failed to load script "{module}"\n' + str(e), exec_ctx)
            )

        _, error, should_exit = run(module, script)

        if error:
            return RTResult[Value]().failure(
                RTError(
                    self.pos_start,
                    self.pos_end,
                    f'Failed to finish executing script "{module}"\n' + error.as_string(),
                    exec_ctx,
                )
            )

        if should_exit:
            return RTResult[Value]().success_exit(Null.null())
        return RTResult[Value]().success(Null.null())

    @args([])
    def execute_exit(self, exec_ctx: Context) -> RTResult[Value]:
        return RTResult[Value]().success_exit(Null.null())

    @args(["value"])
    def execute_is_null(self, ctx: Context) -> RTResult[Value]:
        value = ctx.symbol_table.get("value")

        if isinstance(value, Null):
            return RTResult[Value]().success(Boolean(True))
        else:
            return RTResult[Value]().success(Boolean(False))

    # Shell functions
    @args([])
    def execute_license(self, exec_ctx: Context) -> RTResult[Value]:
        try:
            with open("LICENSE", "r") as file:
                text = file.read()
        except IOError:
            return RTResult[Value]().failure(RTError(self.pos_start, self.pos_end, "Failed to read LICENSE", exec_ctx))
        lines = text.split("\n")
        total_lines = len(lines)
        current_line = 0
        for _ in range(20):
            if current_line >= total_lines:
                break
            print(lines[current_line])
            current_line += 1
        try:
            while current_line < total_lines:
                if current_line >= total_lines:
                    break
                print(lines[current_line])
                current_line += 1
                if current_line < total_lines:
                    input(f"--- More --- (Line {current_line} of {total_lines})")
                    stdout.write("\033[F\033[K")  # go up one line and erase that line
                    stdout.flush()  # flush output stream
        except KeyboardInterrupt:
            stdout.write("\033[H\033[J")
            stdout.flush()
            return RTResult[Value]().success(Null.null())
        return RTResult[Value]().success(Null.null())

    @args([])
    def execute_credits(self, exec_ctx: Context) -> RTResult[Value]:
        print("Project by Md. Almas Ali (github.com/Almas-Ali)")
        print("Contributors:\n\tangelcaru (github.com/angelcaru)\n\tVardan2009 (github.com/Vardan2009)")
        return RTResult[Value]().success(Null.null())


def run(
    fn: str,
    text: str,
    context: Optional[Context] = None,
    entry_pos: Optional[Position] = None,
    return_result: bool = False,
    hide_paths: bool = False,
):
    from core.interpreter import Interpreter  # Lazy import

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
    assert ast.node is not None

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


# Setting all functions to global symbol table
def create_global_symbol_table() -> SymbolTable:
    import core.builtin_classes as bic

    ret = SymbolTable()
    ret.set("null", Null.null())
    ret.set("false", Boolean.false())
    ret.set("true", Boolean.true())
    ret.set("print", BuiltInFunction("print"))
    ret.set("print_ret", BuiltInFunction("print_ret"))
    ret.set("input", BuiltInFunction("input"))
    ret.set("input_int", BuiltInFunction("input_int"))
    ret.set("clear", BuiltInFunction("clear"))
    ret.set("cls", BuiltInFunction("clear"))
    ret.set("require", BuiltInFunction("require"))
    ret.set("exit", BuiltInFunction("exit"))
    ret.set("len", BuiltInFunction("len"))
    # Datatype validator methods
    ret.set("is_num", BuiltInFunction("is_num"))
    ret.set("is_int", BuiltInFunction("is_int"))
    ret.set("is_float", BuiltInFunction("is_float"))
    ret.set("is_str", BuiltInFunction("is_string"))
    ret.set("is_bool", BuiltInFunction("is_bool"))
    ret.set("is_array", BuiltInFunction("is_array"))
    ret.set("is_fun", BuiltInFunction("is_fun"))
    ret.set("is_null", BuiltInFunction("is_null"))
    # Internal array methods
    ret.set("arr_append", BuiltInFunction("arr_append"))
    ret.set("arr_pop", BuiltInFunction("arr_pop"))
    ret.set("arr_extend", BuiltInFunction("arr_extend"))
    ret.set("arr_len", BuiltInFunction("arr_len"))
    ret.set("arr_chunk", BuiltInFunction("arr_chunk"))
    ret.set("arr_get", BuiltInFunction("arr_get"))
    # String methods
    ret.set("str_len", BuiltInFunction("str_len"))
    ret.set("str_find", BuiltInFunction("str_find"))
    ret.set("str_get", BuiltInFunction("str_get"))
    # Typecase methods
    ret.set("int", BuiltInFunction("int"))
    ret.set("float", BuiltInFunction("float"))
    ret.set("str", BuiltInFunction("str"))
    ret.set("bool", BuiltInFunction("bool"))
    ret.set("type", BuiltInFunction("type"))
    # PyAPI methods (Python API)
    ret.set("pyapi", BuiltInFunction("pyapi"))
    # System methods
    ret.set("require", BuiltInFunction("require"))
    ret.set("exit", BuiltInFunction("exit"))
    ret.set("time_now", BuiltInFunction("time_now"))
    # Shell functions
    ret.set("license", BuiltInFunction("license"))
    ret.set("credits", BuiltInFunction("credits"))
    # Built-in classes
    ret.set("File", bic.BuiltInClass("File", bic.FileObject))
    ret.set("String", bic.BuiltInClass("String", bic.StringObject))
    ret.set("Json", bic.BuiltInClass("Json", bic.JSONObject))
    ret.set("Requests", bic.BuiltInClass("Json", bic.RequestsObject))
    return ret


global_symbol_table = create_global_symbol_table()
