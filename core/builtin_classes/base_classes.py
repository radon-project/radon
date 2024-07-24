from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, TypeAlias, TypeVar

from core.builtin_funcs import BuiltInFunction, args
from core.datatypes import BaseClass, BaseFunction, BaseInstance, ResultTuple, Value
from core.errors import RTError
from core.parser import Context, RTResult, SymbolTable


class BuiltInClass(BaseClass):
    instance_class: BuiltInObjectMeta

    def __init__(self, name: str, instance_class: BuiltInObjectMeta) -> None:
        super().__init__(name, instance_class.__symbol_table__)
        self.instance_class = instance_class

    def create(self, args: list[Value]) -> RTResult[BaseInstance]:
        inst = BuiltInInstance(self, self.instance_class(self))
        return RTResult[BaseInstance]().success(inst.set_context(self.context).set_pos(self.pos_start, self.pos_end))

    def init(self, inst: BaseInstance, args: list[Value], kwargs: dict[str, Value]) -> RTResult[None]:
        res = RTResult[None]()
        if len(kwargs) > 0:
            return res.failure(
                RTError(
                    list(kwargs.values())[0].pos_start,
                    list(kwargs.values())[-1].pos_end,
                    "Keyword arguments are not yet supported for built-in functions.",
                    list(kwargs.values())[0].context,
                )
            )
        _, error = inst.operator("__constructor__", *args)
        if error:
            return res.failure(error)
        return res.success(None)

    def get(self, name: str) -> Optional[Value]:
        return self.symbol_table.get(name)

    def __repr__(self) -> str:
        return f"<class {self.name!r} (built-in)>"


class BuiltInInstance(BaseInstance):
    def __init__(self, parent_class: BuiltInClass, obj: BuiltInObject) -> None:
        super().__init__(parent_class, parent_class.instance_class.__symbol_table__)
        self.obj = obj
        self.symbol_table.set("this", self)

    def bind_method(self, method: BaseFunction) -> RTResult[BaseFunction]:
        assert isinstance(method, BuiltInFunction)
        assert method.func is not None

        @args(method.func.arg_names, method.func.defaults)
        def new_func(ctx: Context) -> RTResult[Value]:
            assert method.func is not None
            return method.func(self.obj, ctx)  # type: ignore

        return RTResult[BaseFunction]().success(BuiltInFunction(method.name, new_func))

    def operator(self, operator: str, *args: Value) -> ResultTuple:
        try:
            op = type(self.obj).__operators__[operator]
        except KeyError:
            return None, self.illegal_operation(*args)
        res = RTResult[Value]()
        value = res.register(op(self.obj, list(args)))
        if res.should_return():
            assert res.error is not None
            return None, res.error
        assert value is not None
        return value, None

    def __repr__(self) -> str:
        if "__string_display__" in dir(self.obj):
            return str(getattr(self.obj, "__string_display__")())
        return f"<instance '{self.obj}' (built-in)>"

    def __len__(self) -> int:
        return len(self.obj)  # type: ignore


class BuiltInObjectMeta(type):
    __symbol_table__: SymbolTable
    __operators__: dict[str, Callable[[BuiltInObject, list[Value]], RTResult[Value]]]

    def __new__(cls, class_name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> BuiltInObjectMeta:
        if class_name == "BuiltInObject":
            return type.__new__(cls, class_name, bases, attrs)

        operators = {}
        symbols: dict[str, Value] = {}
        for name, value in attrs.items():
            if hasattr(value, "__operator__"):
                operators[value.__operator__] = value
            elif hasattr(value, "__is_method__") and value.__is_method__:
                assert hasattr(value, "arg_names"), "Make sure to use the args() decorator on any built-in methods!"
                assert hasattr(value, "defaults"), "Unreachable. The first `assert` should have ensured this."
                symbols[name] = BuiltInFunction(value.__name__, value)
        symbol_table = SymbolTable(None)
        symbol_table.symbols = symbols

        attrs["__symbol_table__"] = symbol_table
        attrs["__operators__"] = operators
        return type.__new__(cls, class_name, bases, attrs)


class BuiltInObject(metaclass=BuiltInObjectMeta):
    parent_class: BuiltInClass

    def __init__(self, parent_class: BuiltInClass) -> None:
        self.parent_class = parent_class

    def __str__(self) -> str:
        return self.parent_class.name

    def __repr__(self) -> str:
        return self.parent_class.name


# Decorators for methods and operators
C = TypeVar("C", bound=Callable)  # type: ignore


def operator(dunder: str) -> Callable[[C], C]:
    """Convert to operator."""

    def _deco(f: C) -> C:
        f.__operator__ = dunder  # type: ignore
        return f

    return _deco


def method(f: C) -> C:
    """Convert to method."""
    f.__is_method__ = True  # type: ignore
    return f


MethodType: TypeAlias = (
    Callable[[Any], RTResult[Value]]
    | Callable[[Any, Any], RTResult[Value]]
    | Callable[[Any, Any, Any], RTResult[Value]]
)
DecoReturn: TypeAlias = Callable[[BuiltInInstance, Sequence[str]], RTResult[Value]]
CheckReturn: TypeAlias = Callable[[MethodType], DecoReturn]


def check(types: Sequence[type[Value]], defaults: Optional[Sequence[Optional[Value]]] = None) -> CheckReturn:
    """Decorator to check argument types"""

    if defaults is None:
        defaults = [None] * len(types)

    def _deco(f: MethodType) -> DecoReturn:
        def wrapper(self: BuiltInInstance, args: Sequence[str]) -> RTResult[Value]:
            res = RTResult[Value]()
            func_name = f.__name__
            class_name = self.parent_class.name
            full_func_name = f"{class_name}.{func_name}()"

            # Check arg count
            if len(args) > len(types):
                return res.failure(
                    RTError(
                        self.parent_class.pos_start,
                        self.parent_class.pos_end,
                        f"{len(args) - len(types)} too many args passed into {full_func_name}",
                        self.parent_class.context,
                    )
                )

            if len(args) < len(types) - len(list(filter(lambda default: default is not None, defaults))):
                return res.failure(
                    RTError(
                        self.parent_class.pos_start,
                        self.parent_class.pos_end,
                        f"{(len(types) - len(list(filter(lambda default: default is not None, defaults)))) - len(args)} too few args passed into {full_func_name}",
                        self.parent_class.context,
                    )
                )

            # Populate defaults
            real_args: list[Value | str] = []
            for i, typ in enumerate(types):
                arg = defaults[i] if i >= len(args) else args[i]
                assert arg is not None, "We should have already errored"
                if not isinstance(arg, typ):
                    return res.failure(
                        RTError(
                            self.parent_class.pos_start,
                            self.parent_class.pos_end,
                            f"Expected {typ.__name__} for argument {i} (0-based) of {full_func_name}, got {arg.__class__.__name__} instead",
                            self.parent_class.context,
                        )
                    )
                real_args.append(arg)
            return f(self, *real_args)

        wrapper.__name__ = f.__name__
        return wrapper

    return _deco
