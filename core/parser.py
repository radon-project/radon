from core.errors import *
from core.tokens import *
from core.nodes import *


class ParseResult:
    '''Parser Result'''

    def __init__(self):
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self):
        self.last_registered_advance_count = 1
        self.advance_count += 1

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def try_register(self, res):
        if res.error:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        dummy = ParseResult()
        self.advance(dummy)

    def advance(self, res: ParseResult):
        self.tok_idx += 1
        self.update_current_tok()
        res.register_advancement()
        return self.current_tok

    def reverse(self, amount=1):
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self):
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Token cannot appear after previous tokens"
            ))
        return res

    ###################################

    def statements(self):
        res = ParseResult()
        list_statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            # res.register_advancement()
            # self.advance()
            self.advance(res)

        statement = res.register(self.statement())
        if res.error:
            return res
        list_statements.append(statement)

        more_statements = True

        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                # res.register_advancement()
                # self.advance()
                self.advance(res)
                newline_count += 1
            if newline_count == 0:
                more_statements = False

            if not more_statements:
                break
            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            list_statements.append(statement)

        return res.success(ArrayNode(
            list_statements,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, 'return'):
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, 'continue'):
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, 'break'):
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))
        
        if self.current_tok.matches(TT_KEYWORD, 'try'):
            self.advance(res)
            try_node = res.register(self.try_statement())
            return res.success(try_node)

        expr = res.register(self.expr())
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'return', 'continue', 'break', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '%', '(', '[' or 'not'"
            ))
        return res.success(expr)

    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'var'):
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_tok
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            extra_names = []

            while self.current_tok.type == TT_DOT:
                # res.register_advancement()
                # self.advance()
                self.advance(res)

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier"
                    ))

                extra_names.append(self.current_tok)

                # res.register_advancement()
                # self.advance()
                self.advance(res)

            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            # res.register_advancement()
            # self.advance()
            self.advance(res)
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(VarAssignNode(var_name, expr, extra_names))

        elif self.current_tok.matches(TT_KEYWORD, 'include'):
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            if self.current_tok.type != TT_STRING and \
                    self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected string or identifier"
                ))

            file_name = self.current_tok
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            return res.success(IncludeNode(file_name))

        node = res.register(self.bin_op(
            self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))

        return res.success(node)

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'not'):
            op_tok = self.current_tok
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(self.bin_op(
            self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected int, float, identifier, '+', '-', '(', '[', 'if', 'for', 'while', 'fun' or 'not'"
            ))

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (TT_POW, ), self.factor)

    def mod(self):
        return self.bin_op(self.factor, (TT_MOD, ))

    def plus_equals(self):
        return self.bin_op(self.factor, (TT_PE, ))

    def minus_equals(self):
        return self.bin_op(self.factor, (TT_ME, ))

    def times_equals(self):
        return self.bin_op(self.factor, (TT_TE, ))

    def divide_equals(self):
        return self.bin_op(self.factor, (TT_DE, ))

    def mod_equals(self):
        return self.bin_op(self.factor, (TT_MDE, ))

    def power_equals(self):
        return self.bin_op(self.factor, (TT_POWE, ))

    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error:
            return res

        while self.current_tok.type == TT_DOT:
            child = atom
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            child_ = res.register(self.call())
            if res.error:
                return res

            child.child = child_
            child = child_

        if self.current_tok.type == TT_LPAREN:
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                # res.register_advancement()
                # self.advance()
                self.advance(res)
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
                    ))

                while self.current_tok.type == TT_COMMA:
                    # res.register_advancement()
                    # self.advance()
                    self.advance(res)

                    arg_nodes.append(res.register(self.expr()))
                    if res.error:
                        return res

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected ',' or ')'"
                    ))

                # res.register_advancement()
                # self.advance()
                self.advance(res)
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            return res.success(NumberNode(tok))

        elif tok.type == TT_STRING:
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            return res.success(StringNode(tok))

        elif tok.type == TT_IDENTIFIER:
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                # res.register_advancement()
                # self.advance()
                self.advance(res)
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        elif tok.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list_expr)

        elif tok.matches(TT_KEYWORD, 'if'):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)

        elif tok.matches(TT_KEYWORD, 'for'):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)

        elif tok.matches(TT_KEYWORD, 'while'):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)

        elif tok.matches(TT_KEYWORD, 'fun'):
            func_def = res.register(self.func_def())
            if res.error:
                return res
            return res.success(func_def)

        elif tok.matches(TT_KEYWORD, 'class'):
            class_node = res.register(self.class_node())
            if res.error:
                return res
            return res.success(class_node)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, identifier, '+', '-', '(', '[', if', 'for', 'while', 'fun'"
        ))

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '['"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type == TT_RSQUARE:
            # res.register_advancement()
            # self.advance()
            self.advance(res)
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
                ))

            while self.current_tok.type == TT_COMMA:
                # res.register_advancement()
                # self.advance()
                self.advance(res)

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ']'"
                ))

            # res.register_advancement()
            # self.advance()
            self.advance(res)

        return res.success(ArrayNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def object_expr(self):
        from core.datatypes import ObjectNode # Lazy import

        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))

        # res.register_advancement()
        # self.advance()

        if self.current_tok.type == TT_LBRACE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '}', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
                ))

            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type != TT_RBRACE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ',' or '}'"
                ))

            res.register_advancement()
            self.advance()

        return res.success(ObjectNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases('if'))
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))

    def if_expr_b(self):
        return self.if_expr_cases('elif')

    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, 'else'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == TT_LBRACE:
                res.register_advancement()
                self.advance()

                statements = res.register(self.statements())
                if res.error:
                    return res
                else_case = (statements, True)

                if self.current_tok.type == TT_RBRACE:
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected '}'"
                    ))
            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None

        if self.current_tok.matches(TT_KEYWORD, 'elif'):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res

        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_tok.matches(TT_KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '{case_keyword}'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res

        # if not self.current_tok.matches(TT_KEYWORD, 'then'):
        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))

        if self.current_tok.type == TT_LBRACE:
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            statements = res.register(self.statements())
            if res.error:
                return res
            cases.append((condition, statements, True))

            # if self.current_tok.matches(TT_KEYWORD, 'end'):
            if self.current_tok.type == TT_RBRACE:
                # res.register_advancement()
                # self.advance()
                self.advance(res)

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        else:
            expr = res.register(self.statement())
            if res.error:
                return res
            cases.append((condition, expr, False))

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return res.success((cases, else_case))

    def for_expr(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if not self.current_tok.matches(TT_KEYWORD, 'for'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'for'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        var_name = self.current_tok
        # res.register_advancement()
        # self.advance()
        self.advance(res)

        # if self.current_tok.type != TT_EQ:
        #     return res.failure(InvalidSyntaxError(
        #         self.current_tok.pos_start, self.current_tok.pos_end,
        #         f"Expected '='"
        #     ))

        # # res.register_advancement()
        # # self.advance()
        # self.advance(res)

        # start_value = res.register(self.expr())
        # if res.error:
        #     return res

        is_for_in = False

        if self.current_tok.type != TT_EQ and not self.current_tok.matches(TT_KEYWORD, "in"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '=' or 'in'"
            ))

        elif self.current_tok.matches(TT_KEYWORD, "in"):
            self.advance(res)
            is_for_in = True
            iterable_node = res.register(self.expr())
            if res.error: return res
        else:
            self.advance(res)

            start_value = res.register(self.expr())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'to'):
                return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'to'"
                ))
            
            self.advance(res)
            end_value = res.register(self.expr())
            if res.error: return res

            if self.current_tok.matches(TT_KEYWORD, 'step'):
                self.advance(res)

                step_value = res.register(self.expr())
                if res.error: return res
            else:
                step_value = None


        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))

        # self.advance(res)

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            body = res.register(self.statements())
            if res.error:
                return res

            if self.current_tok.type != TT_RBRACE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '}'"
                ))

            pos_end = self.current_tok.pos_end.copy()
            self.advance(res)

            if is_for_in:
                return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, True))
            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

        body = res.register(self.statement())
        if res.error: return res
        pos_end = self.current_tok.pos_end.copy()

        if is_for_in:
            return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, False))
        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'while'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'while'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res

        # if not self.current_tok.matches(TT_KEYWORD, 'then'):
        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type == TT_LBRACE:
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            body = res.register(self.statements())
            if res.error:
                return res

            # if not self.current_tok.matches(TT_KEYWORD, 'end'):
            if self.current_tok.type != TT_RBRACE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '}'"
                ))

            # res.register_advancement()
            # self.advance()
            self.advance(res)

            return res.success(WhileNode(condition, body, True))

        body = res.register(self.statement())
        if res.error:
            return res

        return res.success(WhileNode(condition, body, False))

    def class_node(self):
        res = ParseResult()

        pos_start = self.current_tok.pos_start

        if not self.current_tok.matches(TT_KEYWORD, 'class'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'class'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        class_name_tok = self.current_tok

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        return res.success(ClassNode(class_name_tok, body, pos_start, self.current_tok.pos_end))

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'fun'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'fun'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected '('"
                ))
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or '('"
                ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)
        arg_name_toks = []
        defaults = []
        hasOptionals = False

        if self.current_tok.type == TT_IDENTIFIER:
            pos_start = self.current_tok.pos_start.copy()
            pos_end = self.current_tok.pos_end.copy()

            arg_name_toks.append(self.current_tok)
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            if self.current_tok.type == TT_EQ:
                # res.register_advancement()
                # self.advance()
                self.advance(res)
                default = res.register(self.expr())
                if res.error: return res
                defaults.append(default)
                hasOptionals = True
            elif hasOptionals:
                return res.failure(InvalidSyntaxError(
                pos_start, pos_end,
                "Expected optional parameter."
                ))
            else:
                defaults.append(None)

            while self.current_tok.type == TT_COMMA:
                # res.register_advancement()
                # self.advance()
                self.advance(res)

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected identifier"
                    ))

                pos_start = self.current_tok.pos_start.copy()
                pos_end = self.current_tok.pos_end.copy()
                arg_name_toks.append(self.current_tok)
                # res.register_advancement()
                # self.advance()
                self.advance(res)

                if self.current_tok.type == TT_EQ:
                    # res.register_advancement()
                    # self.advance()
                    self.advance(res)
                    default = res.register(self.expr())
                    if res.error: return res
                    defaults.append(default)
                    hasOptionals = True
                elif hasOptionals:
                    return res.failure(InvalidSyntaxError(
                        pos_start, pos_end,
                        "Expected optional parameter."
                    ))
                else:
                    defaults.append(None)

            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',', ')' or '='"
                ))
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or ')'"
                ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        # If Arrow function
        if self.current_tok.type == TT_ARROW:
            # res.register_advancement()
            # self.advance()
            self.advance(res)

            body = res.register(self.expr())
            if res.error:
                return res

            return res.success(FuncDefNode(
                var_name_tok,
                arg_name_toks,
                defaults,
                body,
                True
            ))

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '->' or '{'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}'"
            ))

        # res.register_advancement()
        # self.advance()
        self.advance(res)

        return res.success(FuncDefNode(
            var_name_tok,
            arg_name_toks,
            defaults,
            body,
            False
        ))

    # def try_statement(self):
    #     res = ParseResult()
    #     pos_start = self.current_tok.pos_start.copy()

    #     if self.current_tok.type != TT_LBRACE:
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected '{'"
    #         ))
        
    #     self.advance(res)

    #     try_block = res.register(self.statements())
    #     if res.error: return res

    #     if self.current_tok.type != TT_RBRACE:
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected '}'"
    #         ))
        
    #     self.advance(res)

    #     if not self.current_tok.matches(TT_KEYWORD, 'catch'):
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected 'catch', 'return', 'continue', 'break', 'var', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
    #         ))

    #     self.advance(res)

    #     if not self.current_tok.matches(TT_KEYWORD, 'as'):
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected 'as'"
    #         ))

    #     self.advance(res)

    #     if self.current_tok.type != TT_IDENTIFIER:
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected identifier"
    #         ))

    #     exc_iden = self.current_tok
    #     print(self.current_tok.type, self.current_tok.value)

    #     self.advance(res)

    #     if self.current_tok.type != TT_LBRACE:
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected '{'"
    #         ))
        
    #     self.advance(res)
        
    #     catch_block = res.register(self.statement())
    #     if res.error: return res
    #     print(self.current_tok.type, self.current_tok.value)
        
    #     self.advance(res)

    #     if self.current_tok.type != TT_RBRACE:
    #         return res.failure(InvalidSyntaxError(
    #             self.current_tok.pos_start, self.current_tok.pos_end,
    #             "Expected '}'"
    #         ))

    #     self.advance(res)
        
    #     print(self.current_tok.type, self.current_tok.value)
        
    #     return res.success(TryNode(try_block, exc_iden, catch_block, pos_start, self.current_tok.pos_end.copy()))


    def try_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '{'"
            ))
        
        self.advance(res)

        try_block = res.register(self.statements())
        if res.error: return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '}'"
            ))
        
        self.advance(res)

        if self.current_tok.matches(TT_KEYWORD, 'catch'):
            self.advance(res)

            if not self.current_tok.matches(TT_KEYWORD, 'as'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'as'"
                ))

            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            exc_iden = self.current_tok
            self.advance(res)

            if self.current_tok.type != TT_LBRACE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '{'"
                ))
            
            self.advance(res)
            
            catch_block = res.register(self.statements())
            if res.error: return res
            
            if self.current_tok.type != TT_RBRACE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '}'"
                ))

            self.advance(res)
            
            return res.success(TryNode(try_block, exc_iden, catch_block, pos_start, self.current_tok.pos_end.copy()))

        return res.failure(InvalidSyntaxError(
            self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'catch'"
        ))
    

    ###################################

    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error:
            return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            # res.register_advancement()
            # self.advance()
            self.advance(res)
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


class RTResult:
    '''Runtime result'''

    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False
        self.should_exit = False

    def register(self, res):
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        self.should_exit = res.should_exit
        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self

    def success_exit(self, exit_value):
        self.reset()
        self.should_exit = True
        self.value = exit_value
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        # Note: this will allow you to continue and break outside the current function
        return (
            self.error or
            self.func_return_value or
            self.loop_should_continue or
            self.loop_should_break or
            self.should_exit
        )


class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None


class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]
