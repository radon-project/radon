import os
import sys
from typing import Any, Callable, Coroutine, NoReturn, Optional, Type

import core.builtin_classes as bic
from core.builtin_funcs import BuiltInFunction, create_global_symbol_table, run
from core.colortools import Log
from core.datatypes import (
    Array,
    BaseClass,
    BaseFunction,
    BaseInstance,
    Boolean,
    Class,
    Function,
    HashMap,
    Instance,
    Module,
    Null,
    Number,
    String,
    Task,
    Value,
)
from core.errors import Error, RNModuleNotFoundError, RNNameError, RTError, TryError
from core.nodes import (
    ArrayNode,
    AssertNode,
    AttrAccessNode,
    AwaitNode,
    BinOpNode,
    BreakNode,
    CallNode,
    ClassNode,
    ContinueNode,
    DecNode,
    DelNode,
    FalloutNode,
    FallthroughNode,
    ForInNode,
    ForNode,
    FromImportNode,
    FuncDefNode,
    HashMapNode,
    HashMapUnpackNode,
    IfNode,
    ImportNode,
    IncNode,
    IndexGetNode,
    IndexSetNode,
    Node,
    NumberNode,
    RaiseNode,
    ReturnNode,
    SliceGetNode,
    SpreadNode,
    StringNode,
    SwitchNode,
    TryNode,
    UnaryOpNode,
    UnitRaiseNode,
    VarAccessNode,
    VarAssignNode,
    WhileNode,
)
from core.parser import Context, RTResult, SymbolTable
from core.tokens import (
    BASE_DIR,
    STDLIBS,
    TT_DIV,
    TT_EE,
    TT_GT,
    TT_GTE,
    TT_IDIV,
    TT_KEYWORD,
    TT_LT,
    TT_LTE,
    TT_MINUS,
    TT_MOD,
    TT_MUL,
    TT_NE,
    TT_PLUS,
    TT_POW,
    Position,
    Token,
    TokenValue,
)


async def resolve_module(
    pos_start: Position, pos_end: Position, exec_ctx: Context, module_ident: str
) -> RTResult[Module]:
    res = RTResult[Module]()
    module_name = module_ident
    try:
        if module_name not in STDLIBS:
            file_extension = module_name.split("/")[-1].split(".")[-1]
            if file_extension != "rn":
                module_name += ".rn"
            # module_file = module_name.split("/")[-1]
            module_path = os.path.dirname(os.path.realpath(module_name))

            module_name = os.path.join(exec_ctx.get_import_cwd(), module_name)
            # module_name = os.path.join(module_path, module_file)
        else:
            # For STDLIB modules
            module_path = os.path.join(BASE_DIR, "stdlib")
            module_name = os.path.join(module_path, f"{module_name}.rn")

        with open(module_name, "r") as f:
            script = f.read()
            # take the first string as the docs
            try:
                docs = script.split('"')[1]
            except IndexError:
                docs = ""
            except Exception as e:
                return res.failure(RTError(pos_start, pos_end, "Failed to load script docs\n" + str(e), exec_ctx))

    except FileNotFoundError:
        return res.failure(
            RNModuleNotFoundError(
                pos_start,
                pos_end,
                # f'Failed to load script "{module_name}"\n' + str(e),
                f"No module named '{module_name}'",
                exec_ctx,
            )
        )

    symbol_table = create_global_symbol_table()
    new_ctx = Context(module_name, exec_ctx, pos_start)
    new_ctx.symbol_table = symbol_table
    new_ctx.import_cwd = module_path
    # error: Error
    _, error, should_exit = await run(module_name, script, context=new_ctx)

    if error:
        return RTResult[Value]().failure(
            RTError(
                pos_start,
                pos_end,
                f"{Log.light_error('Failed to finish executing script')} {Log.light_info(module_name)}\n"
                + error.as_string(),  # type: ignore
                exec_ctx,
            )
        )

    module = Module(module_ident, module_name, docs, symbol_table)
    if should_exit:
        return res.success_exit(module)
    return res.success(module)


class Interpreter:
    def _merge_mro(self, sequences: list[list[Class]], node: ClassNode, context: Context) -> RTResult[list[Class]]:
        res = RTResult[list[Class]]()
        merged: list[Class] = []
        seqs = [seq[:] for seq in sequences if len(seq) > 0]

        while len(seqs) > 0:
            candidate: Optional[Class] = None
            for seq in seqs:
                head = seq[0]
                if not any(head in other[1:] for other in seqs):
                    candidate = head
                    break

            if candidate is None:
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        "Cannot create a consistent method resolution order (MRO) for inheritance graph",
                        context,
                    )
                )

            merged.append(candidate)
            next_seqs: list[list[Class]] = []
            for seq in seqs:
                if len(seq) > 0 and seq[0] is candidate:
                    seq.pop(0)
                if len(seq) > 0:
                    next_seqs.append(seq)
            seqs = next_seqs

        return res.success(merged)

    def _get_current_class(self, context: Context) -> Optional[Class]:
        # Walk the (stable, lexically-scoped) symbol table chain rather than
        # Context.parent -- a Function's `.context` gets rebound to the call
        # site every time it crosses a call/attribute-access boundary (see
        # call_value and visit_AttrAccessNode), which would lose the class a
        # closure was defined in. `.symbol_table` is set once at definition
        # time and never reassigned, so it reliably threads through closures.
        value = context.symbol_table.get("__class__")
        if isinstance(value, Class):
            return value
        return None

    def _check_member_access(
        self, attr_value: Value, attr_name: str, context: Context, pos_start: Position, pos_end: Position
    ) -> Optional[RTError]:
        if not isinstance(attr_value, Function) or attr_value.access_modifier == "public":
            return None

        owner = attr_value.owner_class
        if owner is None:
            return None

        caller_class = self._get_current_class(context)
        if attr_value.access_modifier == "private":
            allowed = caller_class is owner
        else:  # protected -- visible to the whole ancestor/descendant chain,
            # in both directions: a subclass reaching an inherited protected
            # member (owner in caller_class.mro), and base-class code that
            # virtually dispatches into a subclass's protected override
            # (caller_class in owner.mro), as in the Template Method pattern.
            allowed = caller_class is not None and (owner in caller_class.mro or caller_class in owner.mro)

        if allowed:
            return None

        return RTError(
            pos_start,
            pos_end,
            f"Cannot access {attr_value.access_modifier} member '{attr_name}' of class '{owner.name}' "
            "from outside its class hierarchy",
            context,
        )

    def _compute_parent_mro(self, parents: list[Class], node: ClassNode, context: Context) -> RTResult[list[Class]]:
        res = RTResult[list[Class]]()
        sequences = [parent.mro[:] for parent in parents]
        sequences.append(parents[:])
        merged = res.register(self._merge_mro(sequences, node, context))
        if res.should_return():
            return res
        assert merged is not None
        return res.success(merged)

    def assign(
        self,
        *,
        var_name: str,
        value: Value,
        context: Context,
        extra_names: list[Token] = [],
        qualifier: Optional[Token] = None,
        pos_start: Position,
        pos_end: Position,
    ) -> RTResult[Value]:
        res = RTResult[Value]()

        if extra_names != []:
            assert qualifier is None
            nd = context.symbol_table.get(var_name)
            prev = None

            if nd is None:
                return res.failure(RTError(pos_start, pos_end, f"'{var_name}' not defined", context))

            name: Optional[TokenValue] = None
            for index, name_tok in enumerate(extra_names):
                name = name_tok.value
                assert isinstance(name, str)

                if not isinstance(nd, Class) and not isinstance(nd, Instance):
                    return res.failure(RTError(pos_start, pos_end, "Value must be instance of class or class", context))

                prev = nd
                nd = nd.symbol_table.symbols[name] if name in nd.symbol_table.symbols else None

                if nd is None and index != len(extra_names) - 1:
                    return res.failure(RTError(pos_start, pos_end, f"'{name}' not defined", context))

            assert prev is not None
            assert isinstance(name, str)
            res.register(prev.symbol_table.set(name, value))
            if res.should_return():
                return res
            return res.success(value)

        qualifier_str = None if qualifier is None else qualifier.value
        assert qualifier_str is None or isinstance(qualifier_str, str)
        res.register(context.symbol_table.set_var(var_name, value, qualifier_str))
        if res.should_return():
            return res
        return res.success(value)

    async def call_value(self, value_to_call: Value, node: CallNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        args: list[Value] = []
        for arg_node in node.arg_nodes:
            arg = res.register(await self.visit(arg_node, context))
            if res.should_return():
                return res
            assert arg is not None
            args.append(arg)

        kwargs: dict[str, Value] = {}
        for kw, kwarg_node in node.kwarg_nodes.items():
            kwarg = res.register(await self.visit(kwarg_node, context))
            if res.should_return():
                return res
            assert kwarg is not None
            kwargs[kw] = kwarg

        return_value = res.register(await value_to_call.execute(args, kwargs))
        if res.should_return():
            return res
        assert return_value is not None
        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)

    async def visit(self, node: Node, context: Context) -> RTResult[Value]:
        method_name = f"visit_{type(node).__name__}"
        method: Callable[[Node, Context], Coroutine[Any, Any, RTResult[Value]]] = getattr(
            self, method_name, self.no_visit_method
        )
        try:
            return await method(node, context)
        except Exception as e:
            if sys.version_info >= (3, 11):
                e.add_note(f"{node.pos_start} - {node.pos_end}: NOTE: happened here")
            raise

    async def visit_block(self, node: Node, context: Context) -> RTResult[Value]:
        new_context = Context("<block scope>", context, node.pos_start)
        new_context.symbol_table = SymbolTable(context.symbol_table)
        return await self.visit(node, new_context)

    def no_visit_method(self, node: Node, context: Context) -> NoReturn:
        raise Exception(f"No visit_{type(node).__name__} method defined")

    ###################################

    async def visit_NullNode(self, node: Node, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null())

    async def visit_NumberNode(self, node: NumberNode, context: Context) -> RTResult[Value]:
        assert isinstance(node.tok.value, int | float), "This could be a bug in the parser or the lexer"
        return RTResult[Value]().success(
            Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    async def visit_StringNode(self, node: StringNode, context: Context) -> RTResult[Value]:
        assert isinstance(node.tok.value, str), "This could be a bug in the parser or the lexer"
        return RTResult[Value]().success(
            String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    async def visit_ArrayNode(self, node: ArrayNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements: list[Value] = []

        for element_node in node.element_nodes:
            if isinstance(element_node, SpreadNode):
                elt = res.register(await self.visit(element_node.node_to_spread, context))
                if res.should_return():
                    return res
                assert elt is not None
                if not isinstance(elt, Array):
                    return res.failure(
                        RTError(
                            element_node.pos_start,
                            element_node.pos_end,
                            f"Spread operator requires an array, got {type(elt).__name__}",
                            context,
                        )
                    )
                elements.extend(elt.elements)
            else:
                elt = res.register(await self.visit(element_node, context))
                if res.should_return():
                    return res
                assert elt is not None
                elements.append(elt)

        return res.success(Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    async def visit_VarAccessNode(self, node: VarAccessNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        assert context.symbol_table is not None
        value = context.symbol_table.get(var_name)

        if value is None:
            return res.failure(RNNameError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        assert value is not None
        return res.success(value)

    async def visit_VarAssignNode(self, node: VarAssignNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str)
        value = res.register(await self.visit(node.value_node, context))
        if res.should_return():
            return res
        assert value is not None

        return self.assign(
            var_name=var_name,
            value=value,
            context=context,
            extra_names=node.extra_names,
            qualifier=node.qualifier,
            pos_start=node.pos_start,
            pos_end=node.pos_end,
        )

    async def visit_RaiseNode(self, node: RaiseNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        call_node = node.call
        value_to_call = res.register(await self.visit(call_node.node_to_call, context))
        if res.should_return():
            return res
        assert value_to_call is not None
        value_to_call = value_to_call.copy().set_pos(call_node.pos_start, call_node.pos_end)

        if isinstance(value_to_call, BaseFunction):
            errtype = value_to_call.name
        else:
            errtype = repr(value_to_call)

        msg_val = res.register(await self.call_value(value_to_call, call_node, context))
        if res.should_return():
            return res
        assert msg_val is not None
        msg = None if isinstance(msg_val, Null) else str(msg_val)

        return res.failure(Error(call_node.pos_start, call_node.pos_end, errtype, msg))

    async def visit_UnitRaiseNode(self, node: UnitRaiseNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        func = res.register(await self.visit(node.func, context))
        if res.should_return():
            return res
        assert func is not None
        func = func.copy().set_pos(node.pos_start, node.pos_end)

        if isinstance(func, BaseFunction):
            errtype = func.name
        else:
            errtype = repr(func)

        msg_val = res.register(await func.execute([], {}))
        if res.should_return():
            return res
        assert msg_val is not None
        msg = None if isinstance(msg_val, Null) else str(msg_val)

        return res.failure(Error(node.pos_start, node.pos_end, errtype, msg))

    async def visit_FromImportNode(self, node: FromImportNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        module_name = node.module.value
        assert isinstance(module_name, str), "This could be a bug in the lexer"

        module = res.register(await resolve_module(node.pos_start, node.pos_end, context, module_name))
        if res.should_return():
            return res
        assert module is not None

        for name_from_module, name_to_import_tok in node.names:
            name_to_import = name_to_import_tok.value
            assert isinstance(name_to_import, str), "this could be a bug in the parser"

            value = module.symbol_table.get(name_from_module)
            if value is None:
                return res.failure(
                    RNNameError(
                        node.pos_start,
                        node.pos_end,
                        f"'{name_from_module}' is not defined in module '{module.name}'",
                        context,
                    )
                )

            res.register(
                self.assign(
                    var_name=name_to_import,
                    value=value,
                    context=context,
                    qualifier=Token(
                        TT_KEYWORD, "const", pos_start=name_to_import_tok.pos_start, pos_end=name_to_import_tok.pos_end
                    ),
                    pos_start=node.pos_start,
                    pos_end=node.pos_end,
                )
            )
            if res.should_return():
                return res
        return res.success(Null.null())

    async def visit_ImportNode(self, node: ImportNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        module_name = node.module.value
        assert isinstance(module_name, str), "This could be a bug in the lexer"

        module = res.register(await resolve_module(node.pos_start, node.pos_end, context, module_name))
        if res.should_return():
            return res
        assert module is not None

        name = node.name.value if node.name is not None else node.module.value
        assert isinstance(name, str)

        res = RTResult[Value]()
        res.register(
            self.assign(
                var_name=name,
                value=module,
                context=context,
                pos_start=node.pos_start,
                pos_end=node.pos_end,
                qualifier=Token(TT_KEYWORD, "const", pos_start=node.pos_start),
            )
        )
        if res.should_return():
            return res
        return res.success(module)

    async def visit_BinOpNode(self, node: BinOpNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        left = res.register(await self.visit(node.left_node, context))
        if res.should_return():
            return res
        assert left is not None
        right = res.register(await self.visit(node.right_node, context))
        if res.should_return():
            return res
        assert right is not None

        if node.op_tok.type == TT_PLUS:
            result, error = await left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = await left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = await left.multed_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = await left.dived_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = await left.powed_by(right)
        elif node.op_tok.type == TT_MOD:
            result, error = await left.modded_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = await left.get_comparison_eq(right)
        elif node.op_tok.type == TT_NE:
            result, error = await left.get_comparison_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = await left.get_comparison_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = await left.get_comparison_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = await left.get_comparison_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = await left.get_comparison_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, "and"):
            result, error = await left.anded_by(right)
        elif node.op_tok.matches(TT_KEYWORD, "or"):
            result, error = await left.ored_by(right)
        elif node.op_tok.type == TT_IDIV:
            result, error = await left.idived_by(right)
        elif node.op_tok.matches(TT_KEYWORD, "in"):
            result, error = await right.contains(left)
        else:
            assert False, f"invalid binary operation: {node.op_tok}, this is probably a bug in the parser."

        if error:
            return res.failure(error)
        else:
            assert result is not None
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    async def visit_UnaryOpNode(self, node: UnaryOpNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        number = res.register(await self.visit(node.node, context))
        if res.should_return():
            return res
        assert number is not None

        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = await number.multed_by(Number(-1))
        elif node.op_tok.matches(TT_KEYWORD, "not"):
            number, error = await number.notted()
        else:
            assert False, f"invalid unary operation: {node.op_tok}, this is probably a bug in the parser."

        if error:
            assert error is not None
            return res.failure(error)
        else:
            assert number is not None
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    async def visit_AwaitNode(self, node: AwaitNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        value = res.register(await self.visit(node.value_node, context))
        if res.should_return():
            return res
        assert value is not None

        # Awaiting a Task (from spawn()) suspends until it resolves and
        # unwraps its value/error; awaiting anything else is a passthrough,
        # since a plain (un-spawned) call already ran to completion inline.
        if isinstance(value, Task):
            task_value = res.register(await value.asyncio_task)
            if res.should_return():
                return res
            assert task_value is not None
            return res.success(task_value.set_pos(node.pos_start, node.pos_end))

        return res.success(value.set_pos(node.pos_start, node.pos_end))

    async def visit_IfNode(self, node: IfNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(await self.visit(condition, context))
            if res.should_return():
                return res
            assert condition_value is not None

            if condition_value.is_true():
                expr_value = res.register(await self.visit_block(expr, context))
                if res.should_return():
                    return res
                assert expr_value is not None
                return res.success(Null.null() if should_return_null else expr_value)

        if node.else_case is not None:
            expr, should_return_null = node.else_case
            expr_value = res.register(await self.visit_block(expr, context))
            if res.should_return():
                return res
            assert expr_value is not None
            return res.success(Null.null() if should_return_null else expr_value)

        return res.success(Null.null())

    async def visit_ForNode(self, node: ForNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements: list[Value] = []

        start_value = res.register(await self.visit(node.start_value_node, context))
        if res.should_return():
            return res
        if not isinstance(start_value, Number):
            return res.failure(
                RTError(
                    node.start_value_node.pos_start,
                    node.start_value_node.pos_end,
                    "Start value must be a number",
                    context,
                )
            )

        end_value = res.register(await self.visit(node.end_value_node, context))
        if res.should_return():
            return res
        if not isinstance(end_value, Number):
            return res.failure(
                RTError(
                    node.end_value_node.pos_start, node.end_value_node.pos_end, "End value must be a number", context
                )
            )

        if node.step_value_node:
            step_value = res.register(await self.visit(node.step_value_node, context))
            if res.should_return():
                return res
            if not isinstance(step_value, Number):
                return res.failure(
                    RTError(
                        node.step_value_node.pos_start,
                        node.step_value_node.pos_end,
                        "Step value must be a number",
                        context,
                    )
                )
        else:
            step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0:

            def condition() -> bool:
                return i < end_value.value
        else:

            def condition() -> bool:
                return i > end_value.value

        while condition():
            assert isinstance(node.var_name_tok.value, str), "this could be a bug in the parser"
            assert context.symbol_table is not None
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value

            value = res.register(await self.visit_block(node.body_node, context))
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            assert value is not None
            elements.append(value)

        return res.success(
            Null.null()
            if node.should_return_null
            else Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    async def visit_WhileNode(self, node: WhileNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements: list[Value] = []

        while True:
            condition = res.register(await self.visit(node.condition_node, context))
            if res.should_return():
                return res
            assert condition is not None

            if not condition.is_true():
                break

            value = res.register(await self.visit_block(node.body_node, context))
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            assert value is not None
            elements.append(value)

        return res.success(
            Null.null()
            if node.should_return_null
            else Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    async def visit_FuncDefNode(self, node: FuncDefNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        func_desc = node.desc
        assert func_name is None or isinstance(func_name, str)
        body_node = node.body_node
        arg_names = [str(arg_name.value) for arg_name in node.arg_name_toks]
        defaults: list[Optional[Value]] = []
        for default in node.defaults:
            if default is None:
                defaults.append(None)
                continue
            default_value = res.register(await self.visit(default, context))
            if res.should_return():
                return res
            defaults.append(default_value)

        func_value = (
            Function(
                func_name,
                context.symbol_table,
                body_node,
                arg_names,
                defaults,
                node.should_auto_return,
                func_desc,
                va_name=node.va_name,
                va_kw_name=node.va_kw_name,
                max_pos_args=node.max_pos_args,
            )
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )
        func_value.access_modifier = node.access_modifier
        func_value.is_abstract = node.is_abstract

        if node.var_name_tok:
            assert context.symbol_table is not None
            assert isinstance(func_name, str), "this could be a bug in the parser"
            if node.static:
                context.symbol_table.set_static(func_name, func_value, "var")
            else:
                context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    async def visit_CallNode(self, node: CallNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        value_to_call = res.register(await self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        assert value_to_call is not None
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        return await self.call_value(value_to_call, node, context)

    async def visit_ReturnNode(self, node: ReturnNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        if node.node_to_return:
            value = res.register(await self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = Null.null()
        assert value is not None

        return res.success_return(value)

    async def visit_ContinueNode(self, node: ContinueNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success_continue()

    async def visit_BreakNode(self, node: BreakNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success_break()

    async def visit_DelNode(self, node: DelNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        for target in node.targets:
            if isinstance(target, VarAccessNode):
                var_name = target.var_name_tok.value
                assert isinstance(var_name, str)

                value = context.symbol_table.get(var_name)
                if value is None:
                    return res.failure(
                        RNNameError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context)
                    )

                # Call __destructor__ if it exists on class instances
                if isinstance(value, Instance):
                    destructor = value.symbol_table.symbols.get("__destructor__", None)
                    if destructor is not None and isinstance(destructor, Function):
                        if destructor.symbol_table is None:
                            destructor.symbol_table = SymbolTable()
                        destructor.symbol_table.set("this", value)
                        res.register(await destructor.execute([], {}))
                        if res.should_return():
                            return res

                table: Optional[SymbolTable] = context.symbol_table
                while table is not None:
                    if var_name in table.symbols:
                        del table.symbols[var_name]
                        break
                    table = table.parent

            elif isinstance(target, IndexGetNode):
                indexee = res.register(await self.visit(target.indexee, context))
                if res.should_return():
                    return res
                assert indexee is not None

                index = res.register(await self.visit(target.index, context))
                if res.should_return():
                    return res
                assert index is not None

                _, error = await indexee.del_index(index)
                if error is not None:
                    return res.failure(error)

        return res.success(Null.null())

    async def visit_TryNode(self, node: TryNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        res.register(await self.visit(node.try_block, context))
        handled_error = res.error
        if res.should_return() and res.error is None:
            return res
        elif handled_error is not None:
            var_name = node.exc_iden.value
            context.symbol_table.set(str(var_name), String(res.error.details))  # type: ignore
            res.error = None

            res.register(await self.visit(node.catch_block, context))

            if res.should_return():
                return res

            if res.error:
                return res.failure(
                    TryError(
                        res.error.pos_start, res.error.pos_end, res.error.details, res.error.context, handled_error
                    )
                )
            return res.success(Null.null())
        else:
            return res.success(Null.null())

    async def visit_ForInNode(self, node: ForInNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        body = node.body_node
        should_return_null = node.should_return_null

        iterable = res.register(await self.visit(node.iterable_node, context))
        if res.should_return():
            return res
        assert iterable is not None
        it = iterable.iter()

        elements: list[Value] = []

        for it_res in it:
            element = res.register(it_res)
            if res.should_return():
                return res

            assert element is not None

            context.symbol_table.set(var_name, element)

            value = res.register(await self.visit(body, context))
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_break:
                break

            if res.loop_should_continue:
                continue
            assert value is not None
            elements.append(value)

        if should_return_null:
            return res.success(Null.null())
        return res.success(Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    async def visit_SliceGetNode(self, node: SliceGetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(await self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index_start = None
        if node.index_start is not None:
            index_start = res.register(await self.visit(node.index_start, context))
            if res.should_return():
                return res

        index_end = None
        if node.index_end is not None:
            index_end = res.register(await self.visit(node.index_end, context))
            if res.should_return():
                return res

        index_step = None
        if node.index_step is not None:
            index_step = res.register(await self.visit(node.index_step, context))
            if res.should_return():
                return res

        result, error = await indexee.get_slice(index_start, index_end, index_step)

        if error is not None:
            return res.failure(error)
        assert result is not None
        return res.success(result.set_pos(node.pos_start, node.pos_end).set_context(context))

    async def visit_IndexGetNode(self, node: IndexGetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(await self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index = res.register(await self.visit(node.index, context))
        if res.should_return():
            return res
        assert index is not None

        result, error = await indexee.get_index(index)
        if error is not None:
            return res.failure(error)
        assert result is not None

        return res.success(result)

    async def visit_IndexSetNode(self, node: IndexSetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(await self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index = res.register(await self.visit(node.index, context))
        if res.should_return():
            return res
        assert index is not None

        value = res.register(await self.visit(node.value, context))
        if res.should_return():
            return res
        assert value is not None

        result, error = await indexee.set_index(index, value)
        if error:
            return res.failure(error)
        assert result is not None

        return res.success(result)

    async def visit_HashMapNode(self, node: HashMapNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        values: dict[str, Value] = {}

        for entry in node.pairs:
            if isinstance(entry, HashMapUnpackNode):
                unpack_val = res.register(await self.visit(entry.node, context))
                if res.should_return():
                    return res
                assert unpack_val is not None

                if not isinstance(unpack_val, HashMap):
                    return res.failure(
                        RTError(
                            entry.pos_start,
                            entry.pos_end,
                            f"Can only unpack HashMap, not '{type(unpack_val).__name__}'",
                            context,
                        )
                    )

                for k, v in unpack_val.values.items():
                    values[k] = v
            else:
                key_node, value_node = entry
                key = res.register(await self.visit(key_node, context))
                if res.should_return():
                    return res

                if not isinstance(key, String):
                    return res.failure(
                        RTError(key_node.pos_start, key_node.pos_end, f"Non-string key for hashmap: '{key!r}'", context)
                    )

                value = res.register(await self.visit(value_node, context))
                if res.should_return():
                    return res
                assert value is not None

                values[key.value] = value

        return res.success(HashMap(values))

    async def visit_ClassNode(self, node: ClassNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        class_name = node.class_name_tok.value
        assert isinstance(class_name, str), "This could be a bug in the lexer"

        parents: list[Class] = []
        for parent_node in node.parent_nodes:
            parent = res.register(await self.visit(parent_node, context))
            if res.should_return():
                return res
            if not isinstance(parent, Class):
                return res.failure(
                    RTError(
                        parent_node.pos_start,
                        parent_node.pos_end,
                        f"Can only inherit from class values, got '{type(parent).__name__}'",
                        context,
                    )
                )
            parents.append(parent)

        parent_mro: list[Class] = []
        if len(parents) > 0:
            parent_mro_result = res.register(self._compute_parent_mro(parents, node, context))
            if res.should_return():
                return res
            assert parent_mro_result is not None
            parent_mro = parent_mro_result

        ctx = Context(class_name, context, node.pos_start)
        ctx.symbol_table = SymbolTable(context.symbol_table)

        res.register(await self.visit(node.body_nodes, ctx))
        if res.should_return():
            return res

        merged_symbol_table = SymbolTable(context.symbol_table)
        for parent in reversed(parent_mro):
            for name, value in parent.own_symbol_table.symbols.items():
                merged_symbol_table.set(name, value.copy())

        for name, value in ctx.symbol_table.symbols.items():
            merged_symbol_table.set(name, value)

        cls = (
            Class(class_name, node.desc, merged_symbol_table, bases=parents, mro=[], own_symbol_table=ctx.symbol_table)
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )
        cls.mro = [cls, *parent_mro]
        cls.is_abstract = node.is_abstract

        for value in cls.own_symbol_table.symbols.values():
            if isinstance(value, Function):
                value.owner_class = cls

        if not node.is_abstract:
            abstract_names: set[str] = set()
            for ancestor in cls.mro:
                for name, value in ancestor.own_symbol_table.symbols.items():
                    if isinstance(value, Function) and value.is_abstract:
                        abstract_names.add(name)

            def is_still_abstract(name: str) -> bool:
                resolved = merged_symbol_table.symbols.get(name)
                return not isinstance(resolved, Function) or resolved.is_abstract

            unimplemented = sorted(name for name in abstract_names if is_still_abstract(name))
            if unimplemented:
                return res.failure(
                    RTError(
                        node.pos_start,
                        node.pos_end,
                        f"Class '{class_name}' must implement abstract method(s): {', '.join(unimplemented)}",
                        context,
                    )
                )

        context.symbol_table.set(class_name, cls)
        return res.success(cls)

    async def visit_AssertNode(self, node: AssertNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        condition = res.register(await self.visit(node.condition, context))
        if res.should_return():
            return res
        assert condition is not None
        if not condition.is_true():
            message = "Assertion failed"
            if node.message is not None:
                message_val = res.register(await self.visit(node.message, context))
                if res.should_return():
                    return res
                if not isinstance(message_val, String):
                    return res.failure(
                        RTError(
                            node.message.pos_start, node.message.pos_end, "Assertion message must be a string", context
                        )
                    )
                message = f"Assertion failed: {message_val.value}"

            return res.failure(RTError(node.condition.pos_start, node.condition.pos_end, message, context))
        return res.success(condition)

    async def visit_IncNode(self, node: IncNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        pre = node.is_pre

        old_value = context.symbol_table.get(var_name)
        if old_value is None:
            return res.failure(RNNameError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        new_value, error = await old_value.added_to(Number.one())
        if error is not None:
            return res.failure(error)
        assert new_value is not None

        res.register(
            self.assign(
                var_name=var_name,
                value=new_value,
                context=context,
                extra_names=node.extra_names,
                qualifier=node.qualifier,
                pos_start=node.pos_start,
                pos_end=node.pos_end,
            )
        )
        if res.should_return():
            return res

        return res.success(new_value if pre else old_value)

    async def visit_DecNode(self, node: DecNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        pre = node.is_pre

        old_value = context.symbol_table.get(var_name)
        if old_value is None:
            return res.failure(RNNameError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        new_value, error = await old_value.subbed_by(Number.one())
        if error is not None:
            return res.failure(error)
        assert new_value is not None

        res.register(
            self.assign(
                var_name=var_name,
                value=new_value,
                context=context,
                extra_names=node.extra_names,
                qualifier=node.qualifier,
                pos_start=node.pos_start,
                pos_end=node.pos_end,
            )
        )
        if res.should_return():
            return res

        return res.success(new_value if pre else old_value)

    async def visit_SwitchNode(self, node: SwitchNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        subject = res.register(await self.visit(node.subject_node, context))
        if res.should_return():
            return res
        assert subject is not None

        should_continue = False
        fallout = False
        for expr, body in node.cases:
            if not should_continue:
                value = res.register(await self.visit(expr, context))
                if res.should_return():
                    return res
                assert value is not None
                bool_, error = await subject.get_comparison_eq(value)
                if error is not None:
                    return res.failure(error)
                assert bool_ is not None
                should_continue = bool(bool_.is_true())

            if should_continue:
                res.register(await self.visit(body, context))
                if res.should_return():
                    return res

                if res.should_fallout:
                    should_continue = True
                    fallout = True
                    continue

                if fallout:
                    continue

                if res.should_fallthrough:
                    should_continue = True
                    continue
                return res.success(Null.null())
            should_continue = False

        if node.default is not None:
            res.register(await self.visit(node.default, context))
            if res.should_return():
                return res
            return res.success(Null.null())

        return res.success(Null.null())

    async def visit_FallthroughNode(self, node: FallthroughNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null()).fallthrough()

    async def visit_FalloutNode(self, node: FalloutNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null()).fallout()

    async def visit_AttrAccessNode(self, node: AttrAccessNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        value = res.register(await self.visit(node.node_to_access, context))
        if res.should_return():
            return res
        assert value is not None

        attr_name = node.attr_name_tok.value
        assert isinstance(attr_name, str), "This could be a bug in the lexer"

        # Handle classes, instances, and modules as before
        if isinstance(value, (BaseClass, BaseInstance, Module)):
            orig_value = value
            attr_value = value.symbol_table.get(attr_name)
            if attr_value is None:
                return res.failure(
                    RTError(node.pos_start, node.pos_end, f"Attribute '{attr_name}' does not exist", context)
                )

            access_error = self._check_member_access(attr_value, attr_name, context, node.pos_start, node.pos_end)
            if access_error is not None:
                return res.failure(access_error)

            if isinstance(orig_value, BaseInstance) and isinstance(attr_value, BaseFunction):
                attr_value = res.register(orig_value.bind_method(attr_value))
                if res.should_return():
                    return res
            else:
                attr_value = attr_value.copy()
            assert attr_value is not None
            attr_value.set_pos(node.pos_start, node.pos_end).set_context(context)
            return res.success(attr_value)

        # Handle method access on built-in value types using BuiltIn wrapper classes
        wrapper_class = _get_value_wrapper_class(value)
        if wrapper_class is not None:
            # Create a BuiltInClass for the wrapper
            builtin_class = bic.BuiltInClass(type(value).__name__, wrapper_class.__doc__, wrapper_class)
            builtin_class.set_pos(node.pos_start, node.pos_end).set_context(context)

            # Create an instance that wraps the primitive value
            inst_res = builtin_class.create([value])
            inst = res.register(inst_res)
            if res.should_return():
                return res
            assert inst is not None

            # Initialize the instance with the primitive value
            init_res = await builtin_class.init(inst, [value], {})
            if init_res.error:
                return res.failure(init_res.error)

            # Look up the method in the wrapper's symbol table
            method = wrapper_class.__symbol_table__.get(attr_name)
            if method is not None and isinstance(method, BuiltInFunction):
                # Bind the method to the instance
                bound_method = res.register(inst.bind_method(method))
                if res.should_return():
                    return res
                assert bound_method is not None
                bound_method.set_pos(node.pos_start, node.pos_end).set_context(context)
                return res.success(bound_method)

        return res.failure(
            RTError(
                node.pos_start, node.pos_end, f"'{type(value).__name__}' object has no attribute '{attr_name}'", context
            )
        )


# Registry mapping primitive types to their BuiltIn wrapper classes
_VALUE_WRAPPER_REGISTRY: dict[Type[Value], Type[bic.BuiltInObject]] = {
    Array: bic.ArrayObject,
    String: bic.StringObject,
    Number: bic.NumberObject,
    Boolean: bic.BooleanObject,
    HashMap: bic.HashMapObject,
}


def _get_value_wrapper_class(value: Value) -> Optional[Type[bic.BuiltInObject]]:
    """Get the BuiltIn wrapper class for a primitive value type."""
    return _VALUE_WRAPPER_REGISTRY.get(type(value))
