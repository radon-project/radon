'''All Nodes'''


class NumberNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

        self.child = None

    def __repr__(self):
        return f'{self.tok}'


class StringNode:
    def __init__(self, tok):
        self.tok = tok

        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end

        self.child = None

    def __repr__(self):
        return f'{self.tok}'


class ArrayNode:
    def __init__(self, element_nodes, pos_start, pos_end):
        self.element_nodes = element_nodes

        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None


class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.var_name_tok.pos_end

        self.child = None


class VarAssignNode:
    def __init__(self, var_name_tok, value_node, extra_names=[]):
        self.var_name_tok = var_name_tok
        self.value_node = value_node
        self.extra_names = extra_names

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.extra_names[len(
            self.extra_names)-1].pos_end if len(self.extra_names) > 0 else self.var_name_tok.pos_end

        self.child = None


class VarManipulateNode:
    def __init__(self, var_name_tok, op_tok, value_node):
        self.var_name_tok = var_name_tok
        self.op_tok = op_tok
        self.value_node = value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.value_node.pos_end

        self.child = None


class SliceNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.step_value_node.pos_end

        self.child = None


class IncludeNode:
    def __init__(self, module_tok):
        self.module_tok = module_tok

        self.pos_start = self.module_tok.pos_start
        self.pos_end = self.module_tok.pos_end

        self.child = None


class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

        self.child = None

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'


class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

        self.pos_start = self.op_tok.pos_start
        self.pos_end = node.pos_end

        self.child = None

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'


class IfNode:
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case

        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (
            self.else_case or self.cases[len(self.cases) - 1])[0].pos_end

        self.child = None


class ForNode:
    def __init__(self, var_name_tok, start_value_node, end_value_node, step_value_node, body_node, should_return_null):
        self.var_name_tok = var_name_tok
        self.start_value_node = start_value_node
        self.end_value_node = end_value_node
        self.step_value_node = step_value_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.var_name_tok.pos_start
        self.pos_end = self.body_node.pos_end

        self.child = None


class WhileNode:
    def __init__(self, condition_node, body_node, should_return_null):
        self.condition_node = condition_node
        self.body_node = body_node
        self.should_return_null = should_return_null

        self.pos_start = self.condition_node.pos_start
        self.pos_end = self.body_node.pos_end

        self.child = None


class FuncDefNode:
    def __init__(self, var_name_tok, arg_name_toks, defaults, body_node, should_auto_return):
        self.var_name_tok = var_name_tok
        self.arg_name_toks = arg_name_toks
        self.defaults = defaults
        self.body_node = body_node
        self.should_auto_return = should_auto_return

        if self.var_name_tok:
            self.pos_start = self.var_name_tok.pos_start
        elif len(self.arg_name_toks) > 0:
            self.pos_start = self.arg_name_toks[0].pos_start
        else:
            self.pos_start = self.body_node.pos_start

        self.pos_end = self.body_node.pos_end

        self.child = None


class CallNode:
    def __init__(self, node_to_call, arg_nodes):
        self.node_to_call = node_to_call
        self.arg_nodes = arg_nodes

        self.pos_start = self.node_to_call.pos_start

        if len(self.arg_nodes) > 0:
            self.pos_end = self.arg_nodes[len(self.arg_nodes) - 1].pos_end
        else:
            self.pos_end = self.node_to_call.pos_end

        self.child = None


class ReturnNode:
    def __init__(self, node_to_return, pos_start, pos_end):
        self.node_to_return = node_to_return

        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None


class ContinueNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None


class BreakNode:
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None


class TryNode:
    def __init__(self, try_block, exc_iden, catch_block, pos_start, pos_end):
        self.try_block = try_block
        self.exc_iden = exc_iden
        self.catch_block = catch_block

        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None

class ForInNode:
    def __init__(self, var_name_tok, iterable_node, body_node, pos_start, pos_end, should_return_null):
        self.var_name_tok = var_name_tok
        self.iterable_node = iterable_node
        self.body_node = body_node
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.should_return_null = should_return_null

        self.child = None

class ClassNode:
    def __init__(self, class_name_tok, body_nodes, pos_start, pos_end):
        self.class_name_tok = class_name_tok
        self.body_nodes = body_nodes
        self.pos_start = pos_start
        self.pos_end = pos_end

        self.child = None
