from __future__ import annotations

from core.errors import *
from core.tokens import *
from core.nodes import *

from typing import TYPE_CHECKING, Optional, Generic, TypeVar, Callable
from collections.abc import Sequence
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from core.datatypes import Value

T = TypeVar("T")


class ParseResult(Generic[T]):
    """Parser Result"""

    unignorable: bool
    error: Optional[InvalidSyntaxError]
    node: Optional[T]
    last_registered_advance_count: int
    advance_count: int
    to_reverse_count: int

    def __init__(self) -> None:
        self.unignorable = False
        self.error = None
        self.node = None
        self.last_registered_advance_count = 0
        self.advance_count = 0
        self.to_reverse_count = 0

    def register_advancement(self) -> None:
        self.last_registered_advance_count = 1
        self.advance_count += 1

    U = TypeVar("U")

    def register(self, res):
        self.last_registered_advance_count = res.advance_count
        self.advance_count += res.advance_count
        if res.error:
            self.error = res.error
        return res.node

    def try_register(self, res: ParseResult[U]) -> Optional[U]:
        if res.error and not res.unignorable:
            self.to_reverse_count = res.advance_count
            return None
        return self.register(res)

    def success(self, node: T) -> ParseResult[T]:
        self.node = node
        return self

    def failure(self, error: InvalidSyntaxError) -> ParseResult[T]:
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self

    def make_unignorable(self) -> ParseResult[T]:
        self.unignorable = True
        return self


class Parser:
    tokens: list[Token]
    current_tok: Token
    tok_idx: int
    in_func: int
    in_loop: int
    in_class: int
    in_case: int

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.tok_idx = 0
        self.in_func = 0
        self.in_loop = 0
        self.in_class = 0
        self.in_case = 0

        self.update_current_tok()

    def advance(self, res: ParseResult) -> Token:
        self.tok_idx += 1
        self.update_current_tok()
        res.register_advancement()
        return self.current_tok

    def reverse(self, amount: int = 1) -> Token:
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self) -> None:
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self) -> ParseResult[Node]:
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected EOF"))
        return res

    def skip_newlines(self) -> ParseResult[None]:
        res = ParseResult[None]()
        while self.current_tok.type == TT_NEWLINE:
            self.advance(res)

        return res

    ###################################

    def statements(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        list_statements: list[Node] = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            self.advance(res)

        if self.current_tok.type in (TT_EOF, TT_RBRACE):
            return res.success(ArrayNode(list_statements, pos_start, self.current_tok.pos_end.copy()))
        statement = res.register(self.statement())
        if res.error:
            return res
        assert statement is not None
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
            if self.current_tok.type in (TT_EOF, TT_RBRACE):
                more_statements = False
                continue
            statement = res.register(self.statement())
            if res.error:
                return res
            assert statement is not None
            list_statements.append(statement)

        return res.success(ArrayNode(list_statements, pos_start, self.current_tok.pos_end.copy()))

    def statement(self) -> ParseResult[Optional[Node]] | ParseResult[Node]:
        res = ParseResult[Node]()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "raise"):
            # syntax
            # raise FunctionCall()

            self.advance(res)
            call = res.register(self.expr())
            if res.error is not None:
                return res
            assert call is not None

            if not isinstance(call, CallNode):
                return res.success(UnitRaiseNode(call, call.pos_start, call.pos_end))
            return res.success(RaiseNode(call, call.pos_start, call.pos_end))

        if self.current_tok.matches(TT_KEYWORD, "fallout"):
            if not self.in_case:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Fallout statement must be inside a switch-case statement",
                    )
                )
            self.advance(res)
            return res.success(FalloutNode(pos_start, self.current_tok.pos_start.copy()))

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
            if expr is None:
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
            if res.error:
                return res
            assert try_node is not None
            return res.success(try_node)

        if self.current_tok.matches(TT_KEYWORD, "switch"):
            self.advance(res)
            switch_node = res.register(self.switch_statement())
            if res.error:
                return res
            assert switch_node is not None
            return res.success(switch_node)

        if self.current_tok.matches(TT_KEYWORD, "import"):
            self.advance(res)

            if self.current_tok.type != TT_STRING and self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start,
                        self.current_tok.pos_end,
                        "Expected string or identifier as imported module",
                    )
                )

            module = self.current_tok
            self.advance(res)

            if self.current_tok.matches(TT_KEYWORD, "as"):
                self.advance(res)
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start,
                            self.current_tok.pos_end,
                            "Expected string or identifier as imported module",
                        )
                    )
                name = self.current_tok
                self.advance(res)
                return res.success(ImportNode(module, name, module.pos_start, name.pos_end))

            return res.success(ImportNode(module, None, module.pos_start, module.pos_end))

        expr = res.register(self.expr())
        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected statement")
            )
        assert expr is not None
        return res.success(expr)

    def expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        var_assign_node = res.try_register(self.assign_expr())
        if var_assign_node is not None:
            return res.success(var_assign_node)
        elif res.error is not None:
            return res
        else:
            self.reverse(res.to_reverse_count)

        node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))

        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected expression")
            )

        assert node is not None
        return res.success(node)

    def assign_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, "static"):
            self.advance(res)

        qualifier = None
        if self.current_tok.type == TT_KEYWORD and self.current_tok.value in ("var", "const"):
            qualifier = self.current_tok
            self.advance(res)

        pre_tok = None
        if self.current_tok.type in (TT_PLUS_PLUS, TT_MINUS_MINUS):
            pre_tok = self.current_tok
            self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected expression")
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
                        is_pre=True,
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
                        is_pre=True,
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
                    var_name_tok,
                    extra_names,
                    qualifier,
                    is_pre=False,
                    pos_start=pos_start,
                    pos_end=op_tok.pos_end.copy(),
                )
            )

        if op_tok.type == TT_MINUS_MINUS:
            self.advance(res)
            return res.success(
                DecNode(
                    var_name_tok,
                    extra_names,
                    qualifier,
                    is_pre=False,
                    pos_start=pos_start,
                    pos_end=op_tok.pos_end.copy(),
                )
            )

        self.advance(res)
        assign_expr = res.register(self.expr())
        if res.error:
            return res.make_unignorable()
        assert assign_expr is not None

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
                VarAccessNode(var_name_tok),
                Token(ASSIGN_TO_OPERATORS[op_tok.type], pos_start=op_tok.pos_start, pos_end=op_tok.pos_end),
                assign_expr,
            )
        return res.success(VarAssignNode(var_name_tok, assign_expr, extra_names, qualifier))

    def comp_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        if self.current_tok.matches(TT_KEYWORD, "not"):
            op_tok = self.current_tok
            self.advance(res)

            node = res.register(self.comp_expr())
            if res.error:
                return res
            assert node is not None
            return res.success(UnaryOpNode(op_tok, node))

        node = res.register(
            self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE, (TT_KEYWORD, "in")))
        )

        if res.error:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected expression")
            )
        assert node is not None

        return res.success(node)

    def arith_expr(self) -> ParseResult[Node]:
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def term(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_MUL, TT_DIV, TT_MOD, TT_IDIV))

    def factor(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            self.advance(res)
            factor = res.register(self.factor())
            if res.error:
                return res
            assert factor is not None
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def power(self) -> ParseResult[Node]:
        return self.bin_op(self.call, (TT_POW,), self.factor)

    def mod(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_MOD,))

    def plus_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_PE,))

    def minus_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_ME,))

    def times_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_TE,))

    def divide_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_DE,))

    def mod_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_MDE,))

    def power_equals(self) -> ParseResult[Node]:
        return self.bin_op(self.factor, (TT_POWE,))

    def call(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        index = res.register(self.atom())
        if res.error:
            return res
        assert index is not None

        while self.current_tok.type == TT_DOT:
            self.advance(res)

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
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
                pair = res.register(self.func_arg())
                if res.error:
                    return res
                assert pair is not None
                kw, val = pair
                if kw is None:
                    arg_nodes.append(val)
                else:
                    kwarg_nodes[kw] = val
                if res.error:
                    return res.failure(
                        InvalidSyntaxError(
                            self.current_tok.pos_start, self.current_tok.pos_end, "Expected ')' or expression"
                        )
                    )

                while self.current_tok.type == TT_COMMA:
                    self.advance(res)

                    pair = res.register(self.func_arg())
                    if res.error:
                        return res
                    assert pair is not None
                    kw, val = pair
                    if kw is None and len(kwarg_nodes) == 0:
                        arg_nodes.append(val)
                    elif kw is None:
                        return res.failure(
                            InvalidSyntaxError(
                                val.pos_start, val.pos_end, "Positional arguments may not come after keyword arguments"
                            )
                        )
                    else:
                        kwarg_nodes[kw] = val

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ')'")
                    )

                self.advance(res)
            return res.success(CallNode(index, arg_nodes, kwarg_nodes))
        return res.success(index)

    def func_arg(self) -> ParseResult[tuple[Optional[str], Node]]:
        res = ParseResult[tuple[Optional[str], Node]]()

        kw = None
        if (
            len(self.tokens[self.tok_idx :]) >= 2
            and self.tokens[self.tok_idx + 0].type == TT_IDENTIFIER
            and self.tokens[self.tok_idx + 1].type == TT_EQ
        ):
            kw = str(self.tokens[self.tok_idx].value)
            self.advance(res)
            self.advance(res)
        val = res.register(self.expr())
        if res.error:
            return res
        assert val is not None
        return res.success((kw, val))

    def atom(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        tok = self.current_tok
        node: Optional[Node] = None

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
            assert expr is not None
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
            assert array_expr is not None
            node = array_expr

        elif tok.matches(TT_KEYWORD, "if"):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            assert if_expr is not None
            node = if_expr

        elif tok.matches(TT_KEYWORD, "for"):
            self.in_loop += 1
            for_expr = res.register(self.for_expr())
            self.in_loop -= 1
            if res.error:
                return res
            assert for_expr is not None
            node = for_expr

        elif tok.matches(TT_KEYWORD, "while"):
            self.in_loop += 1
            while_expr = res.register(self.while_expr())
            self.in_loop -= 1
            if res.error:
                return res
            assert while_expr is not None
            node = while_expr

        elif tok.matches(TT_KEYWORD, "fun") or tok.matches(TT_KEYWORD, "static"):
            self.in_func += 1
            func_def = res.register(self.func_def())
            self.in_func -= 1
            if res.error:
                return res
            assert func_def is not None
            node = func_def

        elif tok.matches(TT_KEYWORD, "class"):
            self.in_class += 1
            class_node = res.register(self.class_node())
            self.in_class -= 1
            if res.error:
                return res
            assert class_node is not None
            node = class_node

        elif tok.matches(TT_KEYWORD, "assert"):
            assert_expr = res.register(self.assert_expr())
            if res.error:
                return res
            assert assert_expr is not None
            node = assert_expr

        elif tok.type == TT_LBRACE:
            hashmap_expr = res.register(self.hashmap_expr())
            if res.error:
                return res
            assert hashmap_expr is not None
            node = hashmap_expr

        if node is None:
            return res.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected expression"))

        while self.current_tok.type == TT_LSQUARE:
            assert node is not None
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

            index: list[Optional[Node]] = []
            is_slice = False
            while self.current_tok.type != TT_RSQUARE:
                if self.current_tok.type == TT_COLON:
                    is_slice = True
                    index.append(None)
                    self.advance(res)
                    continue
                val = res.register(self.expr())
                if res.error:
                    return res
                assert val is not None
                index.append(val)

                if self.current_tok.type == TT_COLON:
                    is_slice = True
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
                assert value is not None

                assert index[0] is not None
                node = IndexSetNode(node, index[0], value, tok.pos_start, self.current_tok.pos_end)
            elif is_slice:
                assert node is not None
                node = SliceGetNode(tok.pos_start, self.current_tok.pos_end, node, *index)  # type: ignore
            else:
                assert node is not None
                assert index[0] is not None
                node = IndexGetNode(tok.pos_start, self.current_tok.pos_end, node, index[0])

        return res.success(node)

    def assert_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        assert self.current_tok.matches(TT_KEYWORD, "assert"), "`assert`-ception :D"
        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res
        assert condition is not None

        message = None
        if self.current_tok.type == TT_COMMA:
            self.advance(res)
            message = res.register(self.expr())
            if res.error:
                return res
            assert message is not None

        return res.success(AssertNode(condition, message, self.current_tok.pos_start, self.current_tok.pos_end))

    def array_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            assert False, "unreachable"

        self.advance(res)
        self.skip_newlines()

        if self.current_tok.type == TT_RSQUARE:
            self.advance(res)
        else:
            elt = res.register(self.expr())
            self.skip_newlines()
            if res.error:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected ']' or expression"
                    )
                )
            assert elt is not None
            element_nodes.append(elt)

            while self.current_tok.type == TT_COMMA:
                self.advance(res)
                self.skip_newlines()

                elt = res.register(self.expr())
                self.skip_newlines()
                if res.error:
                    return res
                assert elt is not None
                element_nodes.append(elt)

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or ']'")
                )

            self.advance(res)

        return res.success(ArrayNode(element_nodes, pos_start, self.current_tok.pos_end.copy()))

    def hashmap_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        pairs: list[tuple[Node, Node]] = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LBRACE:
            assert False, "unreachable"

        self.advance(res)
        self.skip_newlines()

        if self.current_tok.type == TT_RBRACE:
            self.advance(res)
            return res.success(HashMapNode(pairs, pos_start, self.current_tok.pos_end.copy()))
        else:
            key = res.register(self.expr())
            if res.error:
                return res
            assert key is not None

            if self.current_tok.type != TT_COLON:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'")
                )

            self.advance(res)

            value = res.register(self.expr())
            if res.error:
                return res
            assert value is not None

            pairs.append((key, value))

            while self.current_tok.type == TT_COMMA:
                self.advance(res)
                self.skip_newlines()

                key = res.register(self.expr())
                self.skip_newlines()
                if res.error:
                    return res
                assert key is not None

                if self.current_tok.type != TT_COLON:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ':'")
                    )

                self.advance(res)
                self.skip_newlines()

                value = res.register(self.expr())
                self.skip_newlines()
                if res.error:
                    return res
                assert value is not None

                pairs.append((key, value))

            self.skip_newlines()
            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',' or '}'")
                )

            self.advance(res)

            return res.success(HashMapNode(pairs, pos_start, self.current_tok.pos_end.copy()))

    def if_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        all_cases = res.register(self.if_expr_cases("if"))
        if res.error:
            return res
        assert all_cases is not None
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))

    def if_expr_b(self) -> ParseResult[tuple[list[Case], Optional[tuple[Node, bool]]]]:
        return self.if_expr_cases("elif")

    def if_expr_c(self) -> ParseResult[Optional[tuple[Node, bool]]]:
        res = ParseResult[Optional[tuple[Node, bool]]]()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, "else"):
            self.advance(res)

            if self.current_tok.type == TT_LBRACE:
                self.advance(res)

                statements = res.register(self.statements())
                if res.error:
                    return res
                assert statements is not None
                else_case = (statements, True)

                if self.current_tok.type != TT_RBRACE:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                    )
                self.advance(res)
            else:
                expr = res.register(self.statement())
                if res.error:
                    return res
                assert expr is not None
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self) -> ParseResult[tuple[list[Case], Optional[tuple[Node, bool]]]]:
        res = ParseResult[tuple[list[Case], Optional[tuple[Node, bool]]]]()
        cases: list[Case] = []
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, "elif"):
            all_cases = res.register(self.if_expr_b())
            if res.error:
                return res
            assert all_cases is not None
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error:
                return res

        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword: str) -> ParseResult[tuple[list[Case], Optional[tuple[Node, bool]]]]:
        res = ParseResult[tuple[list[Case], Optional[tuple[Node, bool]]]]()
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
        assert condition is not None
        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            statements = res.register(self.statements())
            if res.error:
                return res
            assert statements is not None
            cases.append((condition, statements, True))

            if self.current_tok.type == TT_RBRACE:
                self.advance(res)

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            assert all_cases is not None
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        else:
            expr = res.register(self.statement())
            if res.error:
                return res
            assert expr is not None
            cases.append((condition, expr, False))

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error:
                return res
            assert all_cases is not None
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return res.success((cases, else_case))

    def for_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        pos_start = self.current_tok.pos_start.copy()

        if not self.current_tok.matches(TT_KEYWORD, "for"):
            assert False, "unreachable"

        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
            )

        var_name = self.current_tok
        self.advance(res)

        is_for_in = False

        if self.current_tok.type != TT_EQ and not self.current_tok.matches(TT_KEYWORD, "in"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '=' or 'in'")
            )

        elif self.current_tok.matches(TT_KEYWORD, "in"):
            self.advance(res)
            is_for_in = True
            iterable_node = res.register(self.expr())
            if res.error:
                return res
            assert iterable_node is not None
        else:
            self.advance(res)

            start_value = res.register(self.expr())
            if res.error:
                return res
            assert start_value is not None

            if not self.current_tok.matches(TT_KEYWORD, "to"):
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'to'")
                )

            self.advance(res)
            end_value = res.register(self.expr())
            if res.error:
                return res
            assert end_value is not None

            if self.current_tok.matches(TT_KEYWORD, "step"):
                self.advance(res)

                step_value = res.register(self.expr())
                if res.error:
                    return res
                assert step_value is not None
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
            assert body is not None

            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            pos_end = self.current_tok.pos_end.copy()
            self.advance(res)

            if is_for_in:
                assert iterable_node is not None
                return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, True))
            assert start_value is not None
            assert end_value is not None
            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

        body = res.register(self.statement())
        if res.error:
            return res
        assert body is not None
        pos_end = self.current_tok.pos_end.copy()

        if is_for_in:
            assert iterable_node is not None
            return res.success(ForInNode(var_name, iterable_node, body, pos_start, pos_end, False))
        assert start_value is not None
        assert end_value is not None
        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    def while_expr(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        if not self.current_tok.matches(TT_KEYWORD, "while"):
            assert False, "unreachable"

        self.advance(res)

        condition = res.register(self.expr())
        if res.error:
            return res
        assert condition is not None

        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        # self.advance(res)

        if self.current_tok.type == TT_LBRACE:
            self.advance(res)

            body = res.register(self.statements())
            if res.error:
                return res
            assert body is not None

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
        assert body is not None

        return res.success(WhileNode(condition, body, False))

    def class_node(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        pos_start = self.current_tok.pos_start

        if not self.current_tok.matches(TT_KEYWORD, "class"):
            assert False, "unreachable"

        self.advance(res)

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
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
        assert body is not None

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"))

        self.advance(res)

        return res.success(ClassNode(class_name_tok, body, pos_start, self.current_tok.pos_end))

    def func_def(self) -> ParseResult[Node]:
        res = ParseResult[Node]()

        node_pos_start = self.current_tok.pos_start

        static = False
        if self.current_tok.matches(TT_KEYWORD, "static"):
            self.advance(res)
            static = True

        if not self.current_tok.matches(TT_KEYWORD, "fun"):
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'fun' or identifier")
            )

        self.advance(res)

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            self.advance(res)

            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '('")
                )
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier or '('"
                    )
                )

        self.advance(res)
        arg_name_toks = []
        defaults: list[Optional[Node]] = []
        has_optionals = False
        is_va = False
        max_pos_args = 0
        va_name: Optional[str] = None

        if self.current_tok.type == TT_SPREAD:
            is_va = True
            self.advance(res)

        if self.current_tok.type == TT_IDENTIFIER:
            pos_start = self.current_tok.pos_start.copy()
            pos_end = self.current_tok.pos_end.copy()

            arg_name_tok = self.current_tok
            assert isinstance(arg_name_tok.value, str)
            self.advance(res)
            if not is_va:
                arg_name_toks.append(arg_name_tok)
                if va_name is None:
                    max_pos_args += 1

            if is_va:
                va_name = arg_name_tok.value
                is_va = False
            elif self.current_tok.type == TT_EQ:
                self.advance(res)
                default = res.register(self.expr())
                if res.error:
                    return res
                assert default is not None
                defaults.append(default)
                has_optionals = True
            elif has_optionals:
                return res.failure(InvalidSyntaxError(pos_start, pos_end, "Expected optional parameter."))
            else:
                defaults.append(None)

            while self.current_tok.type == TT_COMMA:
                self.advance(res)

                if self.current_tok.type == TT_SPREAD:
                    is_va = True
                    self.advance(res)

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(
                        InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier")
                    )

                pos_start = self.current_tok.pos_start.copy()
                pos_end = self.current_tok.pos_end.copy()

                arg_name_tok = self.current_tok
                assert isinstance(arg_name_tok.value, str)
                if not is_va:
                    arg_name_toks.append(arg_name_tok)
                    if va_name is None:
                        max_pos_args += 1

                self.advance(res)

                if is_va:
                    va_name = arg_name_tok.value
                    is_va = False
                elif self.current_tok.type == TT_EQ:
                    self.advance(res)
                    default = res.register(self.expr())
                    if res.error:
                        return res
                    assert default is not None
                    defaults.append(default)
                    has_optionals = True
                elif has_optionals:
                    return res.failure(InvalidSyntaxError(pos_start, pos_end, "Expected optional parameter."))
                else:
                    defaults.append(None)

            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected ',', ')' or '='")
                )
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(
                    InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end, "Expected identifier or ')'"
                    )
                )

        self.advance(res)

        # If Arrow function
        if self.current_tok.type == TT_ARROW:
            self.advance(res)

            body = res.register(self.expr())
            if res.error:
                return res
            assert body is not None

            return res.success(
                FuncDefNode(
                    var_name_tok,
                    arg_name_toks,
                    defaults,
                    body,
                    True,
                    static=static,
                    desc="[No Description]",
                    va_name=va_name,
                    max_pos_args=max_pos_args,
                    pos_start=node_pos_start,
                    pos_end=self.current_tok.pos_end,
                )
            )

        self.skip_newlines()
        if self.current_tok.type != TT_LBRACE:
            return res.failure(
                InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '->' or '{'")
            )

        self.advance(res)
        self.skip_newlines()

        desc: str = "[No Description]"
        if self.current_tok.type == TT_STRING:
            # Set description
            desc = str(self.current_tok.value)
            self.advance(res)

        body = res.register(self.statements())
        if res.error:
            return res
        assert body is not None

        if self.current_tok.type != TT_RBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'"))

        self.advance(res)

        return res.success(
            FuncDefNode(
                var_name_tok,
                arg_name_toks,
                defaults,
                body,
                False,
                static=static,
                desc=desc,
                va_name=va_name,
                max_pos_args=max_pos_args,
                pos_start=node_pos_start,
                pos_end=self.current_tok.pos_end,
            )
        )

    def switch_statement(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        pos_start = self.current_tok.pos_start.copy()

        subject = res.register(self.expr())
        if res.error:
            return res
        assert subject is not None

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
            assert expr is not None

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
            assert body is not None

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
            assert body is not None

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

    def try_statement(self) -> ParseResult[Node]:
        res = ParseResult[Node]()
        pos_start = self.current_tok.pos_start.copy()
        self.skip_newlines()

        if self.current_tok.type != TT_LBRACE:
            return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '{'"))

        self.advance(res)

        try_block = res.register(self.statements())
        if res.error:
            return res
        assert try_block is not None

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
            assert catch_block is not None

            if self.current_tok.type != TT_RBRACE:
                return res.failure(
                    InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected '}'")
                )

            self.advance(res)

            return res.success(TryNode(try_block, exc_iden, catch_block, pos_start, self.current_tok.pos_end.copy()))

        return res.failure(InvalidSyntaxError(self.current_tok.pos_start, self.current_tok.pos_end, "Expected 'catch'"))

    ###################################

    ParseFunc: TypeAlias = Callable[[], ParseResult[Node]]

    def bin_op(
        self, func_a: ParseFunc, ops: Sequence[TokenType | tuple[TokenType, str]], func_b: Optional[ParseFunc] = None
    ) -> ParseResult[Node]:
        if func_b is None:
            func_b = func_a

        res = ParseResult[Node]()
        left = res.register(func_a())
        if res.error:
            return res
        assert left is not None

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            self.advance(res)
            right = res.register(func_b())
            if res.error:
                return res
            assert right is not None
            left = BinOpNode(left, op_tok, right)

        return res.success(left)


class RTResult(Generic[T]):
    """Runtime result"""

    value: Optional[T]
    error: Optional[RTError | Error]
    func_return_value: Optional[Value]
    loop_should_continue: bool
    loop_should_break: bool
    should_exit: bool
    should_fallthrough: bool
    should_fallout: bool

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False
        self.should_exit = False
        self.should_fallthrough = False
        self.should_fallout = False

    U = TypeVar("U")

    def register(self, res: RTResult[U]) -> Optional[U]:
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        self.should_exit = res.should_exit
        self.should_fallthrough = res.should_fallthrough
        self.should_fallout = res.should_fallout
        return res.value

    def success(self, value: T) -> RTResult[T]:
        should_fallthrough = self.should_fallthrough  # Save `should_fallthrough` because we don't want to lose it
        self.reset()
        self.should_fallthrough = should_fallthrough
        self.value = value
        return self

    def success_return(self, value: Value) -> RTResult[T]:
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self) -> RTResult[T]:
        self.reset()
        self.loop_should_continue = True
        return self

    def success_break(self) -> RTResult[T]:
        self.reset()
        self.loop_should_break = True
        return self

    def success_exit(self, exit_value: T) -> RTResult[T]:
        self.reset()
        self.should_exit = True
        self.value = exit_value
        return self

    def fallthrough(self) -> RTResult[T]:
        # No `self.reset()` because this is meant to be used in conjunction with other methods
        # e.g. `res.success(Null.null()).fallthrough()`
        self.should_fallthrough = True
        return self

    def fallout(self) -> RTResult[T]:
        self.should_fallout = True
        return self

    def failure(self, error: Error) -> RTResult[T]:
        self.reset()
        self.error = error
        return self

    def should_return(self) -> bool:
        # Note: this will allow you to continue and break outside the current function
        return bool(
            self.error is not None
            or self.func_return_value is not None
            or self.loop_should_continue
            or self.loop_should_break
            or self.should_exit
        )

    def __repr__(self) -> str:
        return (
            f"RTResult(value={self.value}, "
            f"error={self.error}, return={self.func_return_value}, "
            f"continue={self.loop_should_continue}, break={self.loop_should_break}, "
            f"exit={self.should_exit})"
        )


class SymbolTable:
    symbols: dict[str, Value]
    consts: set[str]
    statics: set[str]
    parent: Optional[SymbolTable]

    def __init__(self, parent: Optional[SymbolTable] = None) -> None:
        self.symbols = {}
        self.consts = set()
        self.statics = set()
        self.parent = parent

    @property
    def is_global(self) -> bool:
        return self.parent is None

    def get(self, name: str) -> Optional[Value]:
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name: str, value: Value) -> RTResult[None]:
        if name in self.consts:
            return RTResult[None]().failure(
                RTError(value.pos_start, value.pos_end, f"Cannot reassign to constant {name}", value.context)
            )
        self.symbols[name] = value
        return RTResult[None]().success(None)

    def set_var(self, name: str, value: Value, qualifier: Optional[str] = None) -> RTResult[None]:
        if name in self.consts:
            return RTResult[None]().failure(
                RTError(value.pos_start, value.pos_end, f"Cannot reassign to constant {name}", value.context)
            )
        match qualifier:
            case None:
                if name in self.symbols:
                    self.symbols[name] = value
                elif self.parent is not None:
                    self.parent.set_var(name, value, qualifier)
                else:
                    return RTResult[None]().failure(
                        RTError(
                            value.pos_start,
                            value.pos_end,
                            f"Cannot assign to undeclared variable {name}",
                            value.context,
                        )
                    )
            case "var":
                if name in self.symbols:
                    return RTResult[None]().failure(
                        RTError(value.pos_start, value.pos_end, f"Cannot re-declare variable {name}", value.context)
                    )
                self.symbols[name] = value
            case "const":
                self.symbols[name] = value
                self.consts.add(name)
        return RTResult[None]().success(None)

    def set_static(self, name: str, value: Value, qualifier: Optional[str] = None) -> RTResult[None]:
        res = RTResult[None]()
        res.register(self.set_var(name, value, qualifier))
        if res.should_return():
            return res
        self.statics.add(name)
        return res.success(None)


#    def remove(self, name):
#        del self.symbols[name]


@dataclass
class Context:
    display_name: str
    parent: Optional[Context] = None
    parent_entry_pos: Optional[Position] = None
    symbol_table: SymbolTable = field(default_factory=SymbolTable)
    import_cwd: Optional[str] = "."

    def get_import_cwd(self) -> str:
        if self.import_cwd is not None:
            return self.import_cwd
        assert self.parent is not None, "Root context must always have import_cwd"
        return self.parent.get_import_cwd()
