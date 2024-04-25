from core.errors import *
from core.tokens import *
from core.nodes import *


class ParseResult:
    """Parser Result"""

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
        self.in_func = 0
        self.in_loop = 0
        self.in_class = 0
        self.in_case = 0

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
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end, "Token cannot appear after previous tokens"
                )
            )
        return res

    def skip_newlines(self):
        res = ParseResult()
        while self.current_tok.type == TT_NEWLINE:
            self.advance(res)

        return res

    ###################################

    def statements(self):
        res = ParseResult()
        list_statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            self.advance(res)

        statement = res.try_register(self.statement())
        if not statement:
            return res.success(ArrayNode(list_statements, pos_start, self.current_tok.pos_end.copy()))
        list_statements.append(statement)

        more_statements = True

        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
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

        return res.success(ArrayNode(list_statements, pos_start, self.current_tok.pos_end.copy()))

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "return"):
            if not self.in_func:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Return statement must be inside a function",
                    )
                )
            self.advance(res)

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, "continue"):
            if not self.in_loop:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Continue statement must be inside a loop"
                    )
                )
            self.advance(res)
            return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, "break"):
            if not self.in_loop:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Break statement must be inside a loop"
                    )
                )
            self.advance(res)
            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, "fallthrough"):
            if not self.in_case:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Fallthrough statement must be inside a switch-case statement",
                    )
                )
            self.advance(res)
            return res.success(FallthroughNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, "try"):
            self.advance(res)
            try_node = res.register(self.try_statement())
            return res.success(try_node)

        if self.current_tok.matches(TT_KEYWORD, "switch"):
            self.advance(res)
            switch_node = res.register(self.switch_statement())
            return res.success(switch_node)

        if self.current_tok.matches(TT_KEYWORD, "include"):
            self.advance(res)

            if self.current_tok.type != TT_STRING and self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected string or identifier"
                    )
                )

            module = self.current_tok
            self.advance(res)

            return res.success(IncludeNode(module))

        expr = res.register(self.expr())
        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'return', 'continue', 'break', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '%', '(', '[', '{', or 'not'",
                )
            )
        return res.success(expr)

    def expr(self):
        res = ParseResult()

        var_assign_node = res.try_register(self.assign_expr())
        if var_assign_node:
            return res.success(var_assign_node)
        else:
            self.reverse(res.to_reverse_count)

        node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[', '{', or 'not'",
                )
            )

        return res.success(node)

    def assign_expr(self):
        res = ParseResult()

        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "static"):
            self.advance(res)

        qualifier = None
        if self.current_tok.type == TT_KEYWORD and self.current_tok.value in ("global", "nonlocal", "const"):
            qualifier = self.current_tok
            self.advance(res)

        pre_tok = None
        if self.current_tok.type in (TT_PLUS_PLUS, TT_MINUS_MINUS):
            pre_tok = self.current_tok
            self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[', '{', or 'not'",
                )
            )

        var_name_tok = self.current_tok
        self.advance(res)

        # handle class properties
        extra_names = []

        while self.current_tok.type == TT_DOT:
            if qualifier is not None:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        f"Dotted assignment must not be {qualifier.value}",
                    )
                )
            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
                )

            extra_names.append(self.current_tok)
            self.advance(res)
        #####

        if pre_tok is not None:
            if pre_tok.type == TT_PLUS_PLUS:
                self.advance(res)
                return res.success(
                    IncNode(
                        var_name_tok,
                        extra_names,
                        qualifier,
                        pre=True,
                        pos_start=pos_start,
                        pos_end=pre_tok.pos_end.copy(),
                    )
                )

            if pre_tok.type == TT_MINUS_MINUS:
                self.advance(res)
                return res.success(
                    DecNode(
                        var_name_tok,
                        extra_names,
                        qualifier,
                        pre=True,
                        pos_start=pos_start,
                        pos_end=pre_tok.pos_end.copy(),
                    )
                )

        op_tok = self.current_tok
        if op_tok.type not in (
            TT_EQ,
            TT_PLUS_PLUS,
            TT_MINUS_MINUS,
            TT_PE,
            TT_ME,
            TT_TE,
            TT_DE,
            TT_MDE,
            TT_POWE,
            TT_IDE,
        ):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected assignment operator")
            )

        if op_tok.type == TT_PLUS_PLUS:
            self.advance(res)
            return res.success(
                IncNode(
                    var_name_tok, extra_names, qualifier, pre=False, pos_start=pos_start, pos_end=op_tok.pos_end.copy()
                )
            )

        if op_tok.type == TT_MINUS_MINUS:
            self.advance(res)
            return res.success(
                DecNode(
                    var_name_tok, extra_names, qualifier, pre=False, pos_start=pos_start, pos_end=op_tok.pos_end.copy()
                )
            )

        self.advance(res)
        assign_expr = res.register(self.expr())
        if res.error:
            return res

        ASSIGN_TO_OPERATORS = {
            TT_PE: TT_PLUS,
            TT_ME: TT_MINUS,
            TT_TE: TT_MUL,
            TT_DE: TT_DIV,
            TT_MDE: TT_MOD,
            TT_POWE: TT_POW,
            TT_IDE: TT_IDIV,
        }
        if op_tok.type != TT_EQ:
            assign_expr = BinOpNode(
                VarAccessNode.with_extra_names(var_name_tok, extra_names),
                Token(ASSIGN_TO_OPERATORS[op_tok.type], pos_start=op_tok.pos_start, pos_end=op_tok.pos_end),
                assign_expr,
            )
        return res.success(VarAssignNode(var_name_tok, assign_expr, extra_names, qualifier))

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, "not"):
            op_tok = self.current_tok
            self.advance(res)

            node = res.register(self.comp_expr())
            if res.error:
                return res
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

        if res.error:
            return res.failure(
                InvalidSyntaxError(
                    self.current_tok.pos_start,
                    self.current_tok.pos_end,
                    "Expected int, float, identifier, '+', '-', '(', '[', 'if', 'for', 'while', 'fun' or 'not'",
                )
            )

        return res.success(node)

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD))

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            self.advance(res)
            factor = res.register(self.factor())
            if res.error:
                return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self):
        return self.bin_op(self.call, (TT_POW,), self.factor)

    def mod(self):
        return self.bin_op(self.factor, (TT_MOD,))

    def plus_equals(self):
        return self.bin_op(self.factor, (TT_PE,))

    def minus_equals(self):
        return self.bin_op(self.factor, (TT_ME,))

    def times_equals(self):
        return self.bin_op(self.factor, (TT_TE,))

    def divide_equals(self):
        return self.bin_op(self.factor, (TT_DE,))

    def mod_equals(self):
        return self.bin_op(self.factor, (TT_MDE,))

    def power_equals(self):
        return self.bin_op(self.factor, (TT_POWE,))

    def call(self):
        res = ParseResult()
        index = res.register(self.atom())
        if res.error:
            return res

        while self.current_tok.type == TT_DOT:
            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected identifier",
                    )
                )

            index = AttrAccessNode(index, self.current_tok, index.pos_start, self.current_tok.pos_end)
            self.advance(res)

        if self.current_tok.type == TT_LPAREN:
            self.advance(res)
            arg_nodes = []
            kwarg_nodes = {}

            if self.current_tok.type == TT_RPAREN:
                self.advance(res)
            else:
                kw, val = res.register(self.func_arg())
                if res.error:
                    return res
                if kw is None:
                    arg_nodes.append(val)
                else:
                    kwarg_nodes[kw] = val
                if res.error:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected ')', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[', '{', or 'not'",
                        )
                    )

                while self.current_tok.type == TT_COMMA:
                    self.advance(res)

                    kw, val = res.register(self.func_arg())
                    if res.error:
                        return res
                    if kw is None:
                        arg_nodes.append(val)
                    else:
                        kwarg_nodes[kw] = val

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected ',' or ')'")
                    )

                self.advance(res)
            return res.success(CallNode(index, arg_nodes, kwarg_nodes))
        return res.success(index)

    def func_arg(self):
        res = ParseResult()

        kw = None
        if (
            len(self.tokens[self.tok_idx :]) >= 2
            and self.tokens[self.tok_idx + 0].type == TT_IDENTIFIER
            and self.tokens[self.tok_idx + 1].type == TT_EQ
        ):
            kw = self.tokens[self.tok_idx].value
            self.advance(res)
            self.advance(res)
        val = res.register(self.expr())
        if res.error:
            return res
        return res.success((kw, val))

    def atom(self):
        res = ParseResult()
        tok = self.current_tok
        node = None

        if tok.type in (TT_INT, TT_FLOAT):
            self.advance(res)
            node = NumberNode(tok)

        elif tok.type == TT_STRING:
            self.advance(res)
            node = StringNode(tok)

        elif tok.type == TT_IDENTIFIER:
            self.advance(res)
            node = VarAccessNode(tok)

        elif tok.type == TT_LPAREN:
            self.advance(res)
            expr = res.register(self.expr())
            if res.error:
                return res
            if self.current_tok.type == TT_RPAREN:
                self.advance(res)
                node = expr
            else:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')'")
                )

        elif tok.type == TT_LSQUARE:
            array_expr = res.register(self.array_expr())
            if res.error:
                return res
            node = array_expr

        elif tok.matches(TT_KEYWORD, "if"):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            node = if_expr

        elif tok.matches(TT_KEYWORD, "for"):
            self.in_loop += 1
            for_expr = res.register(self.for_expr())
            self.in_loop -= 1
            if res.error:
                return res
            node = for_expr

        elif tok.matches(TT_KEYWORD, "while"):
            self.in_loop += 1
            while_expr = res.register(self.while_expr())
            self.in_loop -= 1
            if res.error:
                return res
            node = while_expr

        elif tok.matches(TT_KEYWORD, "fun") or tok.matches(TT_KEYWORD, "static"):
            self.in_func += 1
            func_def = res.register(self.func_def())
            self.in_func -= 1
            if res.error:
                return res
            node = func_def

        elif tok.matches(TT_KEYWORD, "class"):
            self.in_class += 1
            class_node = res.register(self.class_node())
            self.in_class -= 1
            if res.error:
                return res
            node = class_node

        elif tok.matches(TT_KEYWORD, "assert"):
            assert_expr = res.register(self.assert_expr())
            if res.error:
                return res
            node = assert_expr

        elif tok.type == TT_LBRACE:
            hashmap_expr = res.register(self.hashmap_expr())
            if res.error:
                return res
            node = hashmap_expr

        if node is None:
            return res.failure(
                InvalidSyntaxError(
                    tok.pos_start,
                    tok.pos_end,
                    "Expected int, float, identifier, '+', '-', '(', '[', if', 'for', 'while', 'fun'",
                )
            )

        if self.current_tok.type == TT_LSQUARE:
            self.advance(res)

            # handle empty call [] errors here
            if self.current_tok.type == TT_RSQUARE:
                self.advance(res)
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected expression inside []"
                    )
                )

            # [index_start:index_end:index_step] or [index_start:index_end] or [index_start]

            # if it's a HashMap it will be key as string get and set
            #            if self.current_tok.type == TT_STRING or self.current_tok.type == TT_IDENTIFIER:
            #                if self.current_tok.type == TT_IDENTIFIER:
            #                    # get the value from identifier token type
            #                    key = res.register(self.expr())
            #                    if res.error:
            #                        return res
            #
            #                elif self.current_tok.type == TT_STRING:
            #                    key = self.current_tok
            #
            #                self.advance(res)
            #
            #                if self.current_tok.type != TT_RSQUARE:
            #                    return res.failure(InvalidSyntaxError(tok.pos_start, self.current_tok.pos_end, "Expected ']'"))
            #                self.advance(res)
            #
            #                if self.current_tok.type == TT_EQ:
            #                    self.advance(res)
            #
            #                    value = res.register(self.expr())
            #                    if res.error:
            #                        return res
            #
            #                    return res.success(IndexSetNode(node, key, value, tok.pos_start, self.current_tok.pos_end))
            #
            #                return res.success(IndexGetNode(tok.pos_start, self.current_tok.pos_end, node, key))

            index = []
            while self.current_tok.type != TT_RSQUARE:
                index.append(res.register(self.expr()))
                if res.error:
                    return res

                if self.current_tok.type == TT_COLON:
                    self.advance(res)
                else:
                    break

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(tok.pos_start, self.current_tok.pos_end, "Expected ']'"))

            self.advance(res)

            if self.current_tok.type == TT_EQ:
                self.advance(res)

                value = res.register(self.expr())
                if res.error:
                    return res

                return res.success(IndexSetNode(node, index[0], value, tok.pos_start, self.current_tok.pos_end))

            return res.success(IndexGetNode(tok.pos_start, self.current_tok.pos_end, node, *index))

        return res.success(node)

    def assert_expr(self):
        res = ParseResult()
        assert self.current_tok.matches(TT_KEYWORD, "assert"), "`assert`-ception :D"
        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res

        message = None
        if self.current_tok.type == TT_COMMA:
            self.advance(res)
            message = res.register(self.expr())
            if res.error:
                return res

        return res.success(AssertNode(condition, message, self.current_tok.pos_start, self.current_tok.pos_end))

    def array_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '['")
            )

        self.advance(res)

        if self.current_tok.type == TT_RSQUARE:
            self.advance(res)
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected ']', 'if', 'for', 'while', 'fun', int, float, identifier, '+', '-', '(', '[', '{' or 'not'",
                    )
                )

            while self.current_tok.type == TT_COMMA:
                self.advance(res)

                element_nodes.append(res.register(self.expr()))
                if res.error:
                    return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected ',' or ']'")
                )

            self.advance(res)

        return res.success(ArrayNode(element_nodes, pos_start, self.current_tok.pos_end.copy()))

    def hashmap_expr(self):
        res = ParseResult()
        pairs = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        self.advance(res)
        self.skip_newlines()

        if self.current_tok.type == TT_RBRACE:
            self.advance(res)
        else:
            key = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.type != TT_COLON:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'")
                )

            self.advance(res)

            value = res.register(self.expr())
            if res.error:
                return res

            pairs.append((key, value))

            while self.current_tok.type == TT_COMMA:
                self.advance(res)
                self.skip_newlines()

                key = res.register(self.expr())
                if res.error:
                    return res

                if self.current_tok.type != TT_COLON:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'")
                    )

                self.advance(res)

                value = res.register(self.expr())
                if res.error:
                    return res

                pairs.append((key, value))

            self.skip_newlines()
            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or '}'")
                )

            self.advance(res)

            return res.success(HashMapNode(pairs, pos_start, self.current_tok.pos_end.copy()))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases("if"))
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))

    def if_expr_b(self):
        return self.if_expr_cases("elif")

    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, "else"):
            self.advance(res)

            if self.current_tok.type == TT_LBRACE:
                self.advance(res)

                statements = res.register(self.statements())
                if res.error:
                    return res
                else_case = (statements, True)

                if self.current_tok.type == TT_RBRACE:
                    self.advance(res)
                else:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                    )
            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None

        if self.current_tok.matches(TT_KEYWORD, "elif"):
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
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '{case_keyword}'")
            )

        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res
        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            statements = res.register(self.statements())
            if res.error:
                return res
            cases.append((condition, statements, True))

            if self.current_tok.type == TT_RBRACE:
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

        if not self.current_tok.matches(TT_KEYWORD, "for"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'for'")
            )

        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier")
            )

        var_name = self.current_tok
        self.advance(res)

        is_for_in = False

        if self.current_tok.type != TT_EQ and not self.current_tok.matches(TT_KEYWORD, "in"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '=' or 'in'")
            )

        elif self.current_tok.matches(TT_KEYWORD, "in"):
            self.advance(res)
            is_for_in = True
            iterable_node = res.register(self.expr())
            if res.error:
                return res
        else:
            self.advance(res)

            start_value = res.register(self.expr())
            if res.error:
                return res

            if not self.current_tok.matches(TT_KEYWORD, "to"):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'to'")
                )

            self.advance(res)
            end_value = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.matches(TT_KEYWORD, "step"):
                self.advance(res)

                step_value = res.register(self.expr())
                if res.error:
                    return res
            else:
                step_value = None

        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        # self.advance(res)

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            body = res.register(self.statements())
            if res.error:
                return res

            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            pos_end = self.current_tok.pos_end.copy()
            self.advance(res)

            if is_for_in:
                return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, True))
            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

        body = res.register(self.statement())
        if res.error:
            return res
        pos_end = self.current_tok.pos_end.copy()

        if is_for_in:
            return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, False))
        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "while"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'while'")
            )

        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res

        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        # self.advance(res)

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            body = res.register(self.statements())
            if res.error:
                return res

            # if not self.current_tok.matches(TT_KEYWORD, 'end'):
            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            self.advance(res)

            return res.success(WhileNode(condition, body, True))

        body = res.register(self.statement())
        if res.error:
            return res

        return res.success(WhileNode(condition, body, False))

    def class_node(self):
        res = ParseResult()

        pos_start = self.current_tok.pos_start

        if not self.current_tok.matches(TT_KEYWORD, "class"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'class'")
            )

        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier")
            )

        class_name_tok = self.current_tok

        self.advance(res)
        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        self.advance(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"))

        self.advance(res)

        return res.success(ClassNode(class_name_tok, body, pos_start, self.current_tok.pos_end))

    def func_def(self):
        res = ParseResult()

        static = False
        if self.current_tok.matches(TT_KEYWORD, "static"):
            self.advance(res)
            static = True

        if not self.current_tok.matches(TT_KEYWORD, "fun"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected 'fun'")
            )

        self.advance(res)

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            self.advance(res)

            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected '('")
                )
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier or '('"
                    )
                )

        self.advance(res)
        arg_name_toks = []
        defaults = []
        hasOptionals = False

        if self.current_tok.type == TT_IDENTIFIER:
            pos_start = self.current_tok.pos_start.copy()
            pos_end = self.current_tok.pos_end.copy()

            arg_name_toks.append(self.current_tok)
            self.advance(res)

            if self.current_tok.type == TT_EQ:
                self.advance(res)
                default = res.register(self.expr())
                if res.error:
                    return res
                defaults.append(default)
                hasOptionals = True
            elif hasOptionals:
                return res.failure(InvalidSyntaxError(pos_start, pos_end, "Expected optional parameter."))
            else:
                defaults.append(None)

            while self.current_tok.type == TT_COMMA:
                self.advance(res)

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier")
                    )

                pos_start = self.current_tok.pos_start.copy()
                pos_end = self.current_tok.pos_end.copy()
                arg_name_toks.append(self.current_tok)
                self.advance(res)

                if self.current_tok.type == TT_EQ:
                    self.advance(res)
                    default = res.register(self.expr())
                    if res.error:
                        return res
                    defaults.append(default)
                    hasOptionals = True
                elif hasOptionals:
                    return res.failure(InvalidSyntaxError(pos_start, pos_end, "Expected optional parameter."))
                else:
                    defaults.append(None)

            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, f"Expected ',', ')' or '='"
                    )
                )
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, f"Expected identifier or ')'"
                    )
                )

        self.advance(res)

        # If Arrow function
        if self.current_tok.type == TT_ARROW:
            self.advance(res)

            body = res.register(self.expr())
            if res.error:
                return res

            return res.success(FuncDefNode(var_name_tok, arg_name_toks, defaults, body, True, static=static))

        self.skip_newlines()
        if self.current_tok.type != TT_LBRACE:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '->' or '{'")
            )

        self.advance(res)

        body = res.register(self.statements())
        if res.error:
            return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"))

        self.advance(res)

        return res.success(FuncDefNode(var_name_tok, arg_name_toks, defaults, body, False, static=static))

    def switch_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        subject = res.register(self.expr())
        if res.error:
            return res

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))
        self.advance(res)

        self.skip_newlines()

        cases = []
        while self.current_tok.matches(TT_KEYWORD, "case"):
            self.advance(res)
            expr = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.type == TT_LBRACE:
                single_statement = False
                self.advance(res)
            elif self.current_tok.type == TT_ARROW:
                single_statement = True
                self.advance(res)
            else:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{' or '->'")
                )
            self.skip_newlines()

            self.in_case += 1
            body = res.register(self.statements() if not single_statement else self.statement())
            self.in_case -= 1
            if (not single_statement) and self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            cases.append((expr, body))

            if not single_statement:
                self.advance(res)
            self.skip_newlines()

        default = None
        if self.current_tok.matches(TT_KEYWORD, "default"):
            self.advance(res)
            if self.current_tok.type == TT_LBRACE:
                single_statement = False
                self.advance(res)
            elif self.current_tok.type == TT_ARROW:
                single_statement = True
                self.advance(res)
            else:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{' or '->'")
                )
            self.skip_newlines()

            self.in_case += 1
            body = res.register(self.statements() if not single_statement else self.statement())
            self.in_case -= 1
            if (not single_statement) and self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            default = body

            if not single_statement:
                self.advance(res)
            self.skip_newlines()

        self.skip_newlines()

        if self.current_tok.type != TT_RBRACE:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}' or 'case'")
            )
        self.advance(res)

        return res.success(SwitchNode(subject, cases, default, pos_start=pos_start, pos_end=self.current_tok.pos_end))

    def try_statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()
        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        self.advance(res)

        try_block = res.register(self.statements())
        if res.error:
            return res

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"))

        self.advance(res)
        self.skip_newlines()

        if self.current_tok.matches(TT_KEYWORD, "catch"):
            self.advance(res)

            if not self.current_tok.matches(TT_KEYWORD, "as"):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'as'")
                )

            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
                )

            exc_iden = self.current_tok
            self.advance(res)
            self.skip_newlines()

            if self.current_tok.type != TT_LBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'")
                )

            self.advance(res)

            catch_block = res.register(self.statements())
            if res.error:
                return res

            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            self.advance(res)

            return res.success(TryNode(try_block, exc_iden, catch_block, pos_start, self.current_tok.pos_end.copy()))

        return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'catch'"))

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
            self.advance(res)
            right = res.register(func_b())
            if res.error:
                return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


class RTResult:
    """Runtime result"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False
        self.should_exit = False
        self.should_fallthrough = False

    def register(self, res):
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        self.should_exit = res.should_exit
        self.should_fallthrough = res.should_fallthrough
        return res.value

    def success(self, value):
        should_fallthrough = self.should_fallthrough  # Save `should_fallthrough` because we don't want to lose it
        self.reset()
        self.should_fallthrough = should_fallthrough
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

    def fallthrough(self):
        # No `self.reset()` because this is meant to be used in conjunction with other methods
        # e.g. `res.success(Number.null).fallthrough()`
        self.should_fallthrough = True
        return self

    def failure(self, error):
        self.reset()
        self.error = error
        return self

    def should_return(self):
        # Note: this will allow you to continue and break outside the current function
        return (
            self.error
            or self.func_return_value
            or self.loop_should_continue
            or self.loop_should_break
            or self.should_exit
        )

    def __repr__(self):
        return (
            f"RTResult(value={self.value}, "
            f"error={self.error}, return={self.func_return_value}, "
            f"continue={self.loop_should_continue}, break={self.loop_should_break}, "
            f"exit={self.should_exit})"
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
        self.consts = set()
        self.statics = set()
        self.parent = parent

    @property
    def is_global(self):
        return self.parent is None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value, qualifier=None):
        if name in self.consts:
            return RTResult().failure(
                RTError(value.pos_start, value.pos_end, f"Cannot reassign to constant {name}", value.context)
            )
        match qualifier:
            case None:
                self.symbols[name] = value
            case Token(TT_KEYWORD, "nonlocal"):
                if name in self.symbols:
                    self.symbols[name] = value
                else:
                    self.parent.set(name, value, qualifier)
            case Token(TT_KEYWORD, "global"):
                if self.is_global:
                    self.symbols[name] = value
                else:
                    self.parent.set(name, value, qualifier)
            case Token(TT_KEYWORD, "const"):
                self.symbols[name] = value
                self.consts.add(name)
            case _:
                assert False, "invalid qualifier"
        return RTResult().success(None)

    def set_static(self, name, value, qualifier=None):
        res = RTResult()
        value = res.register(self.set(name, value, qualifier))
        if res.should_return():
            return res
        self.statics.add(name)
        return res.success(value)

    def remove(self, name):
        del self.symbols[name]
