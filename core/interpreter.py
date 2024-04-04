from core.errors import *
from core.parser import *
from core.datatypes import *
from core.builtin_funcs import run

import os


class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def visit_block(self, node, context):
        new_context = Context("<block scope>", context, node.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return self.visit(node, new_context)

    def no_visit_method(self, node, context):
        raise Exception(f'No visit_{type(node).__name__} method defined')

    ###################################

    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.tok.value).set_context(
                context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.tok.value).set_context(
                context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_ArrayNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res

        return res.success(
            Array(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    def visit_ObjectNode(self, node, context):
        res = RTResult()
        elements = []

        for element_node in node.element_nodes:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res

        return res.success(
            ObjectNode(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))

        if node.child:
            if not isinstance(value, Instance) and not isinstance(value, Class):
                return res.failure(RTError(
                    node.pos_start, node.pos_end,
                    f"Value must be instance of class or class",
                    context
                ))

            new_context = Context(value.parent_class.name,
                                  context, node.pos_start)
            new_context.symbol_table = value.symbol_table

            child = res.register(self.visit(node.child, new_context))
            if res.error:
                return res

            value = child

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, context))
        if res.should_return():
            return res

        if node.extra_names != []:

            nd = context.symbol_table.get(var_name)
            prev = None

            if not nd:
                return res.failure(RTError(
                    node.pos_start, node.pos_end,
                    f"'{name}' not defined",
                    context
                ))

            for index, name_tok in enumerate(node.extra_names):
                name = name_tok.value

                if not isinstance(nd, Class) and not isinstance(nd, Instance):
                    return res.failure(RTError(
                        node.pos_start, node.pos_end,
                        "Value must be instance of class or class",
                        context
                    ))

                prev = nd
                nd = nd.symbol_table.symbols[name] if name in nd.symbol_table.symbols else None

                if not nd and index != len(node.extra_names)-1:
                    return res.failure(RTError(
                        node.pos_start, node.pos_end,
                        f"'{name}' not defined",
                        context
                    ))

            prev.symbol_table.set(name, value)
            return res.success(value)

        context.symbol_table.set(var_name, value)
        return res.success(value)

    def visit_VarManipulateNode(self, node, context):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.pos_start, node.pos_end,
                f"'{var_name}' is not defined",
                context
            ))

        if node.child:
            if not isinstance(value, Instance) and not isinstance(value, Class):
                return res.failure(RTError(
                    node.pos_start, node.pos_end,
                    f"Value must be instance of class or class",
                    context
                ))

            new_context = Context(value.parent_class.name,
                                  context, node.pos_start)
            new_context.symbol_table = value.symbol_table

            child = res.register(self.visit(node.child, new_context))
            if res.error:
                return res

            value = child

        value = value.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)

    def visit_IncludeNode(self, node, context):
        res = RTResult()
        exec_ctx = context

        module = node.module_tok.value

        try:
            if module not in STDLIBS:
                file_extension = module.split("/")[-1].split('.')[-1]
                if file_extension != "rn":
                    return res.failure(RTError(
                        node.pos_start, node.pos_end,
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
                node.pos_start, node.pos_end,
                f"Failed to load script \"{module}\"\n" + str(e),
                exec_ctx
            ))

        _, error, should_exit = run(module, script)

        if error:
            return RTResult().failure(RTError(
                node.pos_start, node.pos_end,
                f"Failed to finish executing script \"{module}\"\n" +
                error.as_string(),
                exec_ctx
            ))

        if should_exit:
            return RTResult().success_exit(Number.null)
        return RTResult().success(Number.null)

    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.should_return():
            return res
        right = res.register(self.visit(node.right_node, context))
        if res.should_return():
            return res

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
        elif node.op_tok.type == TT_PE:
            result, error = left.plus_equals(right)
        elif node.op_tok.type == TT_ME:
            result, error = left.minus_equals(right)
        elif node.op_tok.type == TT_TE:
            result, error = left.times_equals(right)
        elif node.op_tok.type == TT_DE:
            result, error = left.divide_equals(right)
        elif node.op_tok.type == TT_ME:
            result, error = left.mod_equals(right)
        elif node.op_tok.type == TT_POWE:
            result, error = left.power_equals(right)
        elif node.op_tok.matches(TT_KEYWORD, 'and'):
            result, error = left.anded_by(right)
        elif node.op_tok.matches(TT_KEYWORD, 'or'):
            result, error = left.ored_by(right)

        if error:
            return res.failure(error)
        else:
            return res.success(result.set_pos(node.pos_start, node.pos_end))

    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.should_return():
            return res

        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = number.multed_by(Number(-1))
        elif node.op_tok.matches(TT_KEYWORD, 'not'):
            number, error = number.notted()

        if error:
            return res.failure(error)
        else:
            return res.success(number.set_pos(node.pos_start, node.pos_end))

    def visit_IfNode(self, node, context):
        res = RTResult()

        for condition, expr, should_return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res

            if condition_value.is_true():
                expr_value = res.register(self.visit_block(expr, context))
                if res.should_return():
                    return res
                return res.success(Number.null if should_return_null else expr_value)

        if node.else_case:
            expr, should_return_null = node.else_case
            expr_value = res.register(self.visit_block(expr, context))
            if res.should_return():
                return res
            return res.success(Number.null if should_return_null else expr_value)

        return res.success(Number.null)

    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []

        start_value = res.register(self.visit(node.start_value_node, context))
        if res.should_return():
            return res

        end_value = res.register(self.visit(node.end_value_node, context))
        if res.should_return():
            return res

        if node.step_value_node:
            step_value = res.register(
                self.visit(node.step_value_node, context))
            if res.should_return():
                return res
        else:
            step_value = Number(1)

        i = start_value.value

        if step_value.value >= 0:
            def condition(): return i < end_value.value
        else:
            def condition(): return i > end_value.value

        while condition():
            context.symbol_table.set(node.var_name_tok.value, Number(i))
            i += step_value.value

            value = res.register(self.visit_block(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        return res.success(
            Number.null if node.should_return_null else
            Array(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []

        while True:
            condition = res.register(self.visit(node.condition_node, context))
            if res.should_return():
                return res

            if not condition.is_true():
                break

            value = res.register(self.visit_block(node.body_node, context))
            if res.should_return() and res.loop_should_continue == False and res.loop_should_break == False:
                return res

            if res.loop_should_continue:
                continue

            if res.loop_should_break:
                break

            elements.append(value)

        return res.success(
            Number.null if node.should_return_null else
            Array(elements).set_context(context).set_pos(
                node.pos_start, node.pos_end)
        )

    def visit_FuncDefNode(self, node, context):
        res = RTResult()

        func_name = node.var_name_tok.value if node.var_name_tok else None
        body_node = node.body_node
        arg_names = [arg_name.value for arg_name in node.arg_name_toks]
        defaults = []
        for default in node.defaults:
            if default is None:
                defaults.append(None)
                continue
            default_value = res.register(self.visit(default, context))
            if res.should_return(): return res
            defaults.append(default_value)

        func_value = Function(func_name, body_node, arg_names, defaults, node.should_auto_return).set_context(context).set_pos(node.pos_start, node.pos_end)

        if node.var_name_tok:
            context.symbol_table.set(func_name, func_value)

        return res.success(func_value)

    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []

        value_to_call = res.register(self.visit(node.node_to_call, context))
        if res.should_return():
            return res
        value_to_call = value_to_call.copy().set_pos(node.pos_start, node.pos_end)

        for arg_node in node.arg_nodes:
            args.append(res.register(self.visit(arg_node, context)))
            if res.should_return():
                return res

        return_value = res.register(value_to_call.execute(args))
        if res.should_return():
            return res
        return_value = return_value.copy().set_pos(
            node.pos_start, node.pos_end).set_context(context)
        return res.success(return_value)

    def visit_ReturnNode(self, node, context):
        res = RTResult()

        # # if out of function scope return error
        # if not context.symbol_table.get("func"):
        #     return RTResult().failure(STError(
        #         node.pos_start, node.pos_end,
        #         "'return' outside function",
        #         context
        #     ))

        if node.node_to_return:
            value = res.register(self.visit(node.node_to_return, context))
            if res.should_return():
                return res
        else:
            value = Number.null

        return res.success_return(value)

    def visit_ContinueNode(self, node, context):
        # # if out of loop scope return error
        # if not context.symbol_table.get("loop"):
        #     return RTResult().failure(STError(
        #         node.pos_start, node.pos_end,
        #         "'continue' not properly in loop",
        #         context
        #     ))
        return RTResult().success_continue()

    def visit_BreakNode(self, node, context):
        return RTResult().success_break()

    def visit_TryNode(self, node: TryNode, context):
        res = RTResult()
        res.register(self.visit(node.try_block, context))
        handled_error = res.error
        if res.should_return() and res.error is None: return res
        elif handled_error is not None:
            var_name = node.exc_iden.value
            context.symbol_table.set(var_name, res.error)
            res.error = None

            res.register(self.visit(node.catch_block, context))
            if res.error:
                return res.failure(TryError(
                    res.error.pos_start, res.error.pos_end, res.error.details, res.error.context, handled_error
                ))
            return res.success(Number.null)
        else:
            return res.success(Number.null)

    def visit_ClassNode(self, node, context):
        res = RTResult()

        ctx = Context(node.class_name_tok.value, node.pos_start)
        ctx.symbol_table = SymbolTable(context.symbol_table)

        res.register(self.visit(node.body_nodes, ctx))
        if res.should_return():
            return res

        cls_ = Class(node.class_name_tok.value, ctx.symbol_table).set_context(
            context).set_pos(node.pos_start, node.pos_end)
        context.symbol_table.set(node.class_name_tok.value, cls_)
        return res.success(cls_)
