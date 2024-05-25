"""All Nodes"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Optional, TypeAlias, runtime_checkable

if TYPE_CHECKING:
    from core.tokens import Token, Position


@runtime_checkable
class Node(Protocol):
    @property
    def pos_start(self) -> Position:
        ...

    @property
    def pos_end(self) -> Position:
        ...


class NumberNode:
    tok: Token

    pos_start: Position
    pos_end: Position

    def __init__(self, tok: Token) -> None:
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self) -> str:
        return f"{self.tok}"


class StringNode:
    tok: Token

    pos_start: Position
    pos_end: Position

    def __init__(self, tok: Token) -> None:
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

    def __repr__(self) -> str:
        return f"{self.tok}"


class ArrayNode:
    element_nodes: list[Node]

    pos_start: Position
    pos_end: Position

    def __init__(self, element_nodes: list[Node], pos_start: Position, pos_end: Position) -> None:
        self.element_nodes = element_nodes

        self.pos_start = pos_start
        self.pos_end = pos_end


class VarAccessNode:
    var_name_tok: Token

    pos_start: Position
    pos_end: Position

    def __init__(self, var_name_tok: Token) -> None:
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end


class VarAssignNode:
    var_name_tok: Token
    value_node: Node
    extra_names: list[Token]
    qualifier: Optional[Token]

    pos_start: Position
    pos_end: Position

    def __init__(
        self, var_name_tok: Token, value_node: Node, extra_names: list[Token] = [], qualifier: Optional[Token] = None
    ):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.extra_names = extra_names
        self.qualifier = qualifier

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = (
            self.extra_names[len(self.extra_names) - 1].pos_end
            if len(self.extra_names) > 0
            else self.var_name_tok.pos_end
        )


class ImportNode:
    module: Token

    pos_start: Position
    pos_end: Position

    def __init__(self, module: Token) -> None:
        self.module = module

        self.pos_start = self.module.pos_start
        self.pos_end = self.module.pos_end


class RaiseNode:
    errtype: Token
    message: Optional[Node]
    pos_start: Position
    pos_end: Position

    def __init__(self, errtype: Token, message: Optional[Node]) -> None:
        self.message = message
        self.errtype = errtype

        if self.message:
            self.pos_start = self.errtype.pos_start
            self.pos_end = self.message.pos_end
        else:
            self.pos_start = self.errtype.pos_start
            self.pos_end = self.errtype.pos_end


class BinOpNode:
    left_node: Node
    op_tok: Token
    right_node: Node

    pos_start: Position
    pos_end: Position

    def __init__(self, left_node: Node, op_tok: Token, right_node: Node) -> None:
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self) -> str:
        return f"({self.left_node}, {self.op_tok}, {self.right_node})"


class UnaryOpNode:
    op_tok: Token
    node: Node

    pos_start: Position
    pos_end: Position

    def __init__(self, op_tok: Token, node: Node) -> None:
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

    def __repr__(self) -> str:
        return f"({self.op_tok}, {self.node})"


Case: TypeAlias = tuple[Node, Node, bool]


class IfNode:
    cases: list[Case]
    else_case: Optional[tuple[Node, bool]]

    pos_start: Position
    pos_end: Position

    def __init__(self, cases: list[Case], else_case: Optional[tuple[Node, bool]]):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (else_case or cases[len(self.cases) - 1])[0].pos_end


class ForNode:
    var_name_tok: Token
    start_value_node: Node
    end_value_node: Node
    step_value_node: Optional[Node]

    body_node: Node
    should_return_null: bool

    pos_start: Position
    pos_end: Position

    def __init__(
        self,
        var_name_tok: Token,
        start_value_node: Node,
        end_value_node: Node,
        step_value_node: Optional[Node],
        body_node: Node,
        should_return_null: bool,
    ) -> None:
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end


class WhileNode:
    condition_node: Node
    body_node: Node
    should_return_null: bool

    pos_start: Position
    pos_end: Position

    def __init__(self, condition_node: Node, body_node: Node, should_return_null: bool) -> None:
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end


class FuncDefNode:
    var_name_tok: Optional[Token]
    arg_name_toks: list[Token]
    defaults: list[Optional[Node]]
    body_node: Node
    should_auto_return: bool
    static: bool

    pos_start: Position
    pos_end: Position

    def __init__(
        self,
        var_name_tok: Optional[Token],
        arg_name_toks: list[Token],
        defaults: list[Optional[Node]],
        body_node: Node,
        should_auto_return: bool,
        static: bool = False,
    ) -> None:
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.defaults = defaults
        self.body_node = body_node
        self.should_auto_return = should_auto_return
        self.static = static

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end


class CallNode:
    node_to_call: Node
    arg_nodes: list[Node]
    kwarg_nodes: dict[str, Node]

    pos_start: Position
    pos_end: Position

    def __init__(self, node_to_call: Node, arg_nodes: list[Node], kwarg_nodes: dict[str, Node]):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes
        self.kwarg_nodes = kwarg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end


@dataclass
class ReturnNode:
    node_to_return: Optional[Node]

    pos_start: Position
    pos_end: Position


@dataclass
class ContinueNode:
    pos_start: Position
    pos_end: Position


@dataclass
class BreakNode:
    pos_start: Position
    pos_end: Position


@dataclass
class FallthroughNode:
    pos_start: Position
    pos_end: Position


@dataclass
class TryNode:
    try_block: Node
    exc_iden: Token
    catch_block: Node

    pos_start: Position
    pos_end: Position


@dataclass
class ForInNode:
    var_name_tok: Token
    iterable_node: Node
    body_node: Node

    pos_start: Position
    pos_end: Position

    should_return_null: bool


@dataclass
class IndexGetNode:
    pos_start: Position
    pos_end: Position

    indexee: Node
    index: Node


@dataclass
class SliceGetNode:
    pos_start: Position
    pos_end: Position

    indexee: Node
    index_start: Node
    index_end: Optional[Node] = None
    index_step: Optional[Node] = None


@dataclass
class IndexSetNode:
    indexee: Node
    index: Node
    value: Node

    pos_start: Position
    pos_end: Position


@dataclass
class HashMapNode:
    pairs: list[tuple[Node, Node]]

    pos_start: Position
    pos_end: Position


@dataclass
class ClassNode:
    class_name_tok: Token
    body_nodes: Node

    pos_start: Position
    pos_end: Position


@dataclass
class AssertNode:
    condition: Node
    message: Optional[Node]

    pos_start: Position
    pos_end: Position


@dataclass
class IncNode:
    var_name_tok: Token
    extra_names: list[Token]
    qualifier: Optional[Token]
    is_pre: bool

    pos_start: Position
    pos_end: Position


@dataclass
class DecNode:
    var_name_tok: Token
    extra_names: list[Token]
    qualifier: Optional[Token]
    is_pre: bool

    pos_start: Position
    pos_end: Position


@dataclass
class SwitchNode:
    subject_node: Node
    cases: list[tuple[Node, Node]]
    default: Optional[Node]

    pos_start: Position
    pos_end: Position


@dataclass
class AttrAccessNode:
    node_to_access: Node
    attr_name_tok: Token

    pos_start: Position
    pos_end: Position
