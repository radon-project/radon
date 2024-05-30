from core.errors import *
from core.parser import *
from core.datatypes import *
from core.builtin_funcs import run, create_global_symbol_table
from core.colortools import Log

import os
import sys

from typing import NoReturn


class Interpreter:
    def assign(self, *, var_name, value, context, extra_names=[], qualifier=None, pos_start, pos_end):
        res = RTResult()

        if extra_names != []:
            assert qualifier is None
            nd = context.symbol_table.get(var_name)
            prev = None

            if not nd:
                return res.failure(RTError(pos_start, pos_end, f"'{var_name}' not defined", context))

            for index, name_tok in enumerate(extra_names):
                name = name_tok.value

                if not isinstance(nd, Class) and not isinstance(nd, Instance):
                    return res.failure(RTError(pos_start, pos_end, "Value must be instance of class or class", context))

                prev = nd
                nd = nd.symbol_table.symbols[name] if name in nd.symbol_table.symbols else None

                if not nd and index != len(extra_names) - 1:
                    return res.failure(RTError(pos_start, pos_end, f"'{name}' not defined", context))

            res.register(prev.symbol_table.set(name, value))
            if res.should_return():
                return res
            return res.success(value)

        res.register(context.symbol_table.set(var_name, value, qualifier))
        if res.should_return():
            return res
        return res.success(value)

    def call_value(self, value_to_call: Value, node: CallNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        args = []
        for arg_node in node.arg_nodes:
            arg = res.register(self.visit(arg_node, context))
            if res.should_return():
                return res
            assert arg is not None
            args.append(arg)

        kwargs = {}
        for kw, kwarg_node in node.kwarg_nodes.items():
            kwarg = res.register(self.visit(kwarg_node, context))
            if res.should_return():
                return res
            assert kwarg is not None
            kwargs[kw] = kwarg

        return_value = res.register(value_to_call.execute(args, kwargs))
        if res.should_return():
            return res
        assert return_value is not None
        return_value = return_value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)

    def visit(self, node: Node, context: Context) -> RTResult[Value]:
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        try:
            return method(node, context)
        except Exception as e:
            if sys.version_info >= (3, 11):
                e.add_note(f"{node.pos_start} - {node.pos_end}: NOTE: happened here")
            raise

    def visit_block(self, node: Node, context: Context) -> RTResult[Value]:
        new_context = Context("<block scope>", context, node.pos_start)
        new_context.symbol_table = SymbolTable(context.symbol_table)
        return self.visit(node, new_context)

    def no_visit_method(self, node: Node, context: Context) -> NoReturn:
        raise Exception(f"No visit_{type(node).__name__} method defined")

    ###################################

    def visit_NumberNode(self, node: NumberNode, context: Context) -> RTResult[Value]:
        assert isinstance(node.tok.value, int | float), "This could be a bug in the parser or the lexer"
        return RTResult[Value]().success(
            Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node: StringNode, context: Context) -> RTResult[Value]:
        assert isinstance(node.tok.value, str), "This could be a bug in the parser or the lexer"
        return RTResult[Value]().success(
            String(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ArrayNode(self, node: ArrayNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements = []

        for element_node in node.element_nodes:
            elt = res.register(self.visit(element_node, context))
            if res.should_return():
                return res
            assert elt is not None
            elements.append(elt)

        return res.success(Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_VarAccessNode(self, node: VarAccessNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        assert context.symbol_table is not None
        value = context.symbol_table.get(var_name)

        if value is None:
            return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        assert value is not None
        return res.success(value)

    def visit_VarAssignNode(self, node: VarAssignNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res

        return self.assign(
            var_name=var_name,
            value=value,
            context=context,
            extra_names=node.extra_names,
            qualifier=node.qualifier,
            pos_start=node.pos_start,
            pos_end=node.pos_end,
        )

    def visit_RaiseNode(self, node: RaiseNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        call_node = node.call
        value_to_call = res.register(self.visit(call_node.node_to_call, context))
        if res.should_return():
            return res
        assert value_to_call is not None
        value_to_call = value_to_call.copy().set_pos(call_node.pos_start, call_node.pos_end)

        if isinstance(value_to_call, BaseFunction):
            errtype = value_to_call.name
        else:
            errtype = repr(value_to_call)

        msg_val = res.register(self.call_value(value_to_call, call_node, context))
        if res.should_return():
            return res
        assert msg_val is not None
        msg = None if isinstance(msg_val, Null) else str(msg_val)

        return res.failure(Error(call_node.pos_start, call_node.pos_end, errtype, msg))

    def visit_UnitRaiseNode(self, node: UnitRaiseNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        func = res.register(self.visit(node.func, context))
        if res.should_return():
            return res
        assert func is not None
        func = func.copy().set_pos(node.pos_start, node.pos_end)

        if isinstance(func, BaseFunction):
            errtype = func.name
        else:
            errtype = repr(func)

        msg_val = res.register(func.execute([], {}))
        if res.should_return():
            return res
        assert msg_val is not None
        msg = None if isinstance(msg_val, Null) else str(msg_val)

        return res.failure(Error(node.pos_start, node.pos_end, errtype, msg))

    def visit_ImportNode(self, node: ImportNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        exec_ctx = context

        module_name = node.module.value
        assert isinstance(module_name, str), "This could be a bug in the lexer"

        try:
            if module_name not in STDLIBS:
                file_extension = module_name.split("/")[-1].split(".")[-1]
                if file_extension != "rn":
                    module_name += ".rn"
                module_file = module_name.split("/")[-1]
                module_path = os.path.dirname(os.path.realpath(module_name))

                global CURRENT_DIR
                # if CURRENT_DIR is None:
                CURRENT_DIR = module_path

                module_name = os.path.join(CURRENT_DIR, module_file)
            else:
                # For STDLIB modules
                module_name = os.path.join(BASE_DIR, "stdlib", f"{module_name}.rn")

            with open(module_name, "r") as f:
                script = f.read()
        except Exception as e:
            return RTResult[Value]().failure(
                RTError(node.pos_start, node.pos_end, f'Failed to load script "{module_name}"\n' + str(e), exec_ctx)
            )
        symbol_table = create_global_symbol_table()
        new_ctx = Context(module_name, context, node.pos_start)
        new_ctx.symbol_table = symbol_table
        _, error, should_exit = run(module_name, script, context=new_ctx)

        if error:
            return RTResult[Value]().failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    f'{Log.light_error("Failed to finish executing script")} {Log.light_info(module_name)}\n'
                    + error.as_string(),
                    exec_ctx,
                )
            )

        if should_exit:
            return RTResult[Value]().success_exit(Null.null())
        assert isinstance(node.module.value, str), "this could be a bug in the parser"
        module = Module(node.module.value, module_name, symbol_table)

        name = node.name.value if node.name is not None else node.module.value
        assert isinstance(name, str)

        res = RTResult[Value]()
        res.register(
            self.assign(var_name=name, value=module, context=context, pos_start=node.pos_start, pos_end=node.pos_end)
        )
        if res.should_return():
            return res
        return res.success(module)

    def visit_BinOpNode(self, node: BinOpNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        assert left is not None
        right = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res
        assert right is not None

        if node.op_tok.type == TT_PLUS:
            result, error = left.added_to(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subbed_by(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multed_by(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.dived_by(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.powed_by(right)
        elif node.op_tok.type == TT_MOD:
            result, error = left.modded_by(right)
        elif node.op_tok.type == TT_EE:
            result, error = left.get_comparison_eq(right)
        elif node.op_tok.type == TT_NE:
            result, error = left.get_comparison_ne(right)
        elif node.op_tok.type == TT_LT:
            result, error = left.get_comparison_lt(right)
        elif node.op_tok.type == TT_GT:
            result, error = left.get_comparison_gt(right)
        elif node.op_tok.type == TT_LTE:
            result, error = left.get_comparison_lte(right)
        elif node.op_tok.type == TT_GTE:
            result, error = left.get_comparison_gte(right)
        elif node.op_tok.matches(TT_KEYWORD, "and"):
            result, error = left.anded_by(right)
        elif node.op_tok.matches(TT_KEYWORD, "or"):
            result, error = left.ored_by(right)
        elif node.op_tok.type == TT_IDIV:
            result, error = left.idived_by(right)
        elif node.op_tok.matches(TT_KEYWORD, "in"):
            result, error = right.contains(left)
        else:
            assert False, f"invalid binary operation: {node.op_tok}, this is probably a bug in the parser."

        if error:
            return res.failure(error)
        else:
            assert result is not None
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node: UnaryOpNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res
        assert number is not None

        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = number.multed_by(Number(-1))
        elif node.op_tok.matches(TT_KEYWORD, "not"):
            number, error = number.notted()
        else:
            assert False, f"invalid unary operation: {node.op_tok}, this is probably a bug in the parser."

        if error:
            assert error is not None
            return res.failure(error)
        else:
            assert number is not None
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node: IfNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res
            assert condition_value is not None

            if condition_value.is_true():
                expr_value = res.register(self.visit_block(expr, context))
                if res.should_return():
                    return res
                assert expr_value is not None
                return res.success(Null.null() if should_return_null else expr_value)

        if node.else_case is not None:
            expr, should_return_null = node.else_case
            expr_value = res.register(self.visit_block(expr, context))
            if res.should_return():
                return res
            assert expr_value is not None
            return res.success(Null.null() if should_return_null else expr_value)

        return res.success(Null.null())

    def visit_ForNode(self, node: ForNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
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

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return():
            return res
        if not isinstance(end_value, Number):
            return res.failure(
                RTError(
                    node.end_value_node.pos_start, node.end_value_node.pos_end, "End value must be a number", context
                )
            )

        if node.step_value_node:
            step_value = res.register(self.visit(node.step_value_node, context))
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

            def condition():
                return i < end_value.value
        else:

            def condition():
                return i > end_value.value

        while condition():
            assert isinstance(node.var_name_tok.value, str), "this could be a bug in the parser"
            assert context.symbol_table is not None
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value

            value = res.register(self.visit_block(node.body_node, context))
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

    def visit_WhileNode(self, node: WhileNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res
            assert condition is not None

            if not condition.is_true():
                break

            value = res.register(self.visit_block(node.body_node, context))
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

    def visit_FuncDefNode(self, node: FuncDefNode, context: Context) -> RTResult[Value]:
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
            default_value = res.register(self.visit(default, context))
            if res.should_return():
                return res
            defaults.append(default_value)

        func_value = (
            Function(
                func_name, context.symbol_table, body_node, arg_names, defaults, node.should_auto_return, func_desc
            )
            .set_context(context)
            .set_pos(node.pos_start, node.pos_end)
        )

        if node.var_name_tok:
            assert context.symbol_table is not None
            assert isinstance(func_name, str), "this could be a bug in the parser"
            if node.static:
                context.symbol_table.set_static(func_name, func_value)
            else:
                context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_CallNode(self, node: CallNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        assert value_to_call is not None
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        return self.call_value(value_to_call, node, context)

    def visit_ReturnNode(self, node: ReturnNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = Null.null()
        assert value is not None

        return res.success_return(value)

    def visit_ContinueNode(self, node: ContinueNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success_continue()

    def visit_BreakNode(self, node: BreakNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success_break()

    def visit_TryNode(self, node: TryNode, context):
        res = RTResult[Value]()
        res.register(self.visit(node.try_block, context))
        handled_error = res.error
        if res.should_return() and res.error is None:
            return res
        elif handled_error is not None:
            var_name = node.exc_iden.value
            context.symbol_table.set(var_name, res.error)
            res.error = None

            res.register(self.visit(node.catch_block, context))
            if res.error:
                return res.failure(
                    TryError(
                        res.error.pos_start, res.error.pos_end, res.error.details, res.error.context, handled_error
                    )
                )
            return res.success(Null.null())
        else:
            return res.success(Null.null())

    def visit_ForInNode(self, node: ForInNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        body = node.body_node
        should_return_null = node.should_return_null

        iterable = res.register(self.visit(node.iterable_node, context))
        if res.should_return():
            return res
        assert iterable is not None
        it = iterable.iter()

        elements = []

        for it_res in it:
            element = res.register(it_res)
            if res.should_return() and not res.loop_should_continue and not res.loop_should_break:
                return res

            if res.loop_should_break:
                break

            if res.loop_should_continue:
                continue

            assert element is not None

            context.symbol_table.set(var_name, element)

            element = res.register(self.visit(body, context))
            if res.should_return():
                return res
            assert element is not None
            elements.append(element)

        if should_return_null:
            return res.success(Null.null())
        return res.success(Array(elements).set_context(context).set_pos(node.pos_start, node.pos_end))

    def visit_SliceGetNode(self, node: SliceGetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index_start = None
        if node.index_start is not None:
            index_start = res.register(self.visit(node.index_start, context))
            if res.should_return():
                return res

        index_end = None
        if node.index_end is not None:
            index_end = res.register(self.visit(node.index_end, context))
            if res.should_return():
                return res

        index_step = None
        if node.index_step is not None:
            index_step = res.register(self.visit(node.index_step, context))
            if res.should_return():
                return res

        result, error = indexee.get_slice(index_start, index_end, index_step)

        if error is not None:
            return res.failure(error)
        assert result is not None
        return res.success(result.set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_IndexGetNode(self, node: IndexGetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index = res.register(self.visit(node.index, context))
        if res.should_return():
            return res
        assert index is not None

        result, error = indexee.get_index(index)
        if error is not None:
            return res.failure(error)
        assert result is not None

        return res.success(result)

    def visit_IndexSetNode(self, node: IndexSetNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        indexee = res.register(self.visit(node.indexee, context))
        if res.should_return():
            return res
        assert indexee is not None

        index = res.register(self.visit(node.index, context))
        if res.should_return():
            return res
        assert index is not None

        value = res.register(self.visit(node.value, context))
        if res.should_return():
            return res
        assert value is not None

        result, error = indexee.set_index(index, value)
        if error:
            return res.failure(error)
        assert result is not None

        return res.success(result)

    def visit_HashMapNode(self, node: HashMapNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        values = {}

        for key_node, value_node in node.pairs:
            key = res.register(self.visit(key_node, context))
            if res.should_return():
                return res

            if not isinstance(key, String):
                return res.failure(
                    RTError(key_node.pos_start, key_node.pos_end, f"Non-string key for hashmap: '{key!r}'", context)
                )

            value = res.register(self.visit(value_node, context))
            if res.should_return():
                return res
            assert value is not None

            values[key.value] = value

        return res.success(HashMap(values))

    def visit_ClassNode(self, node: ClassNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()

        class_name = node.class_name_tok.value
        assert isinstance(class_name, str), "This could be a bug in the lexer"
        ctx = Context(class_name, context, node.pos_start)
        ctx.symbol_table = SymbolTable(context.symbol_table)

        res.register(self.visit(node.body_nodes, ctx))
        if res.should_return():
            return res

        cls = Class(class_name, ctx.symbol_table).set_context(context).set_pos(node.pos_start, node.pos_end)
        context.symbol_table.set(class_name, cls)
        return res.success(cls)

    def visit_AssertNode(self, node: AssertNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        condition = res.register(self.visit(node.condition, context))
        if res.should_return():
            return res
        assert condition is not None
        if not condition.is_true():
            message = "Assertion failed"
            if node.message is not None:
                message_val = res.register(self.visit(node.message, context))
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

    def visit_IncNode(self, node: IncNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        pre = node.is_pre

        old_value = context.symbol_table.get(var_name)
        if old_value is None:
            return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        new_value, error = old_value.added_to(Number.one())
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

    def visit_DecNode(self, node: DecNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        var_name = node.var_name_tok.value
        assert isinstance(var_name, str), "This could be a bug in the lexer"
        pre = node.is_pre

        old_value = context.symbol_table.get(var_name)
        if old_value is None:
            return res.failure(RTError(node.pos_start, node.pos_end, f"'{var_name}' is not defined", context))

        new_value, error = old_value.subbed_by(Number.one())
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

    def visit_SwitchNode(self, node: SwitchNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        subject = res.register(self.visit(node.subject_node, context))
        if res.should_return():
            return res
        assert subject is not None

        should_continue = False
        fallout = False
        for expr, body in node.cases:
            if not should_continue:
                value = res.register(self.visit(expr, context))
                if res.should_return():
                    return res
                assert value is not None
                bool_, error = subject.get_comparison_eq(value)
                if error is not None:
                    return res.failure(error)
                assert bool_ is not None
                should_continue = bool(bool_.is_true())

            if should_continue:
                res.register(self.visit(body, context))
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
            res.register(self.visit(node.default, context))
            if res.should_return():
                return res
            return res.success(Null.null())

        return res.success(Null.null())

    def visit_FallthroughNode(self, node: FallthroughNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null()).fallthrough()

    def visit_FalloutNode(self, node: FalloutNode, context: Context) -> RTResult[Value]:
        return RTResult[Value]().success(Null.null()).fallout()

    def visit_AttrAccessNode(self, node: AttrAccessNode, context: Context) -> RTResult[Value]:
        res = RTResult[Value]()
        value = res.register(self.visit(node.node_to_access, context))
        if res.should_return():
            return res

        if not isinstance(value, (BaseClass, BaseInstance, Module)):
            return res.failure(
                RTError(
                    node.pos_start,
                    node.pos_end,
                    "Dotted attribute access may only be used on classes, instances and modules for now",
                    context,
                )
            )

        attr_name = node.attr_name_tok.value
        assert isinstance(attr_name, str), "This could be a bug in the lexer"
        orig_value = value
        value = value.symbol_table.get(attr_name)
        if value is None:
            return res.failure(
                RTError(node.pos_start, node.pos_end, f"Attribute '{attr_name}' does not exist", context)
            )

        if isinstance(orig_value, BaseInstance) and isinstance(value, BaseFunction):
            value = res.register(orig_value.bind_method(value))
            if res.should_return():
                return res
        else:
            value = value.copy()
        assert value is not None
        value.set_pos(node.pos_start, node.pos_end).set_context(context)

        return res.success(value)
