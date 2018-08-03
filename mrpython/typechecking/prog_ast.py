
"""The abstract syntax tree of programs."""

import ast
import tokenize

import os.path, sys

main_path = os.path.dirname(os.path.realpath(__file__))
found_path = False
for path in sys.path:
    if path == main_path:
        found_path = True
        break
if not found_path:
    sys.path.append(main_path)


import astpp

class Program:
    def __init__(self):
        # python parsed AST
        self.ast = None

        # list[str:Import]
        # the list of imported modules
        self.imports = dict()

        # dict[str:FunctionDef]
        # the list of function definitions in the program
        self.functions = dict()

        # test cases
        self.test_cases = []

        # other top level definitions
        self.other_top_defs = []

        # metadata
        self.filename = None
        self.source = None
        self.source_lines = None
        self.ast = None

    def get_source_line(self, linum):
        if self.source is None:
            raise ValueError("Source is empty")
        if self.source_lines is None:
            self.source_lines = self.source.split('\n')

        return self.source_lines[linum-1]

    def build_from_file(self, filename):
        self.filename = filename
        modtxt = ""
        with tokenize.open(filename) as f:
            modtxt = f.read()
        self.source = modtxt
        modast = ast.parse(modtxt, mode="exec")
        self.build_from_ast(modast)

    def build_from_ast(self, modast, filename=None, source=None):
        if filename:
            self.filename = filename
        if source:
            self.source = source

        if not isinstance(modast, ast.Module):
            raise ValueError("Cannot build program from AST: not a module (please report)")
        self.ast = modast

        for node in modast.body:
            #print(node._attributes)
            if isinstance(node, ast.Import):
                imp_ast = Import(node)
                self.imports[imp_ast.name] = imp_ast
            elif isinstance(node, ast.FunctionDef):
                fun_ast = FunctionDef(node)
                if fun_ast.python101ready:
                    self.functions[fun_ast.name] = fun_ast
                else:
                    self.other_top_defs.append(UnsupportedNode(node))
            elif isinstance(node, ast.Assert):
                assert_ast = TestCase(node)
                self.test_cases.append(assert_ast)
            else:
                self.other_top_defs.append(UnsupportedNode(node))

class UnsupportedNode:
    def __init__(self, node):
        self.ast = node
        #print("Unsupported node:", astpp.dump(node))

class Import:
    def __init__(self, node):
        self.ast = node
        #print_ast_fields(self.ast)
        alias = self.ast.names[0]
        self.name = alias.name

class FunctionDef:
    def __init__(self, node):
        self.ast = node
        self.name = self.ast.name
        #print(astpp.dump(self.ast))
        self.python101ready = True

        self.parameters = []
        for arg_obj in self.ast.args.args:
            self.parameters.append(arg_obj.arg)

        first_instr = self.ast.body[0]
        next_instr_index = 0
        if isinstance(first_instr, ast.Expr) and isinstance(first_instr.value, ast.Str):
            self.docstring = first_instr.value.s
            next_instr_index = 1
            #print(self.docstring)
        else:
            self.python101ready = False

        self.body = []
        for inner_node in self.ast.body[next_instr_index:]:
            #print(astpp.dump(inner_node))
            self.body.append(parse_instruction(inner_node))


class TestCase:
    def __init__(self, node):
        self.ast = node
        #print(astpp.dump(node))

        self.expr = parse_expression(self.ast.test)

class Assign:
    def __init__(self, node):
        self.ast = node
        #print(astpp.dump(node))

        target = self.ast.targets[0]
        self.var_name = target.id
        #print("  ==> var_name =", self.var_name)

        self.expr = parse_expression(self.ast.value)

class MultiAssign:
    def __init__(self, node):
        raise NotImplementedError("MultiAssign AST node not yet implemented")

def parse_assign(node):
    if len(node.targets) == 1:
        return Assign(node)
    else:
        return MultiAssign(node)

class Return:
    def __init__(self, node):
        self.ast = node
        #print(astpp.dump(node))
        self.expr = parse_expression(self.ast.value)

class If:
    def __init__(self, node):
        self.ast = node
        print(astpp.dump(node))
        self.cond = parse_expression(self.ast.test)
        self.body = []
        for instr in self.ast.body:
            iinstr = parse_instruction(instr)
            self.body.append(iinstr)
        self.orelse = parse_instruction(self.ast.orelse)


INSTRUCTION_CLASSES = {"Assign" : parse_assign
                       , "Return" : Return
                       , "If" : If
}

def parse_instruction(node):
    instruction_type_name = node.__class__.__name__
    #print("instruction type=",instruction_type_name)
    if instruction_type_name in INSTRUCTION_CLASSES:
        wrap_node = INSTRUCTION_CLASSES[instruction_type_name](node)
        return wrap_node
    else:
        return UnsupportedNode(node)

class ENum:
    def __init__(self, node):
        self.ast = node
        self.value = node.n

class ETrue:
    def __init__(self, node):
        self.ast = node

class EFalse:
    def __init__(self, node):
        self.ast = node

class ENone:
    def __init__(self, node):
        self.ast = node

def parse_constant(node):
    if node.value is True:
        return ETrue(node)
    elif node.value is False:
        return EFalse(node)
    elif node.value is None:
        return ENone(node)

    raise ValueError("Constant not supported: {} (please report)".format(node.value))

class EVar:
    def __init__(self, node):
        self.ast = node
        self.name = self.ast.id

class EAdd:
    def __init__(self, node, left, right):
        self.ast = node
        self.left = left
        self.right = right

class ESub:
    def __init__(self, node, left, right):
        self.ast = node
        self.left = left
        self.right = right

class EMult:
    def __init__(self, node, left, right):
        self.ast = node
        self.left = left
        self.right = right

class EDiv:
    def __init__(self, node, left, right):
        self.ast = node
        self.left = left
        self.right = right

BINOP_CLASSES = { "Add" : EAdd
                  , "Sub" : ESub
                  , "Mult" : EMult
                  , "Div" : EDiv
}

def EBinOp(node):
    #print(astpp.dump(node))
    binop_type_name = node.op.__class__.__name__
    #print("binop type=",binop_type_name)
    if binop_type_name in BINOP_CLASSES:
        left = parse_expression(node.left)
        right = parse_expression(node.right)
        wrap_node = BINOP_CLASSES[binop_type_name](node, left, right)
        return wrap_node
    else:
        return UnsupportedNode(node)

class EUSub:
    def __init__(self, node, operand):
        self.ast = node
        self.operand = operand

UNOP_CLASSES = { "USub" : EUSub
}

def EUnaryOp(node):
    unop_type_name = node.op.__class__.__name__
    if unop_type_name in UNOP_CLASSES:
        operand = parse_expression(node.operand)
        return UNOP_CLASSES[unop_type_name](node, operand)
    else:
        return UnsupportedNode(node)

def parse_function_name(func_descr):
    parts = []
    val = func_descr
    while isinstance(val, ast.Attribute):
        parts.append(val.attr)
        val = val.value
    parts.append(val.id)
    return ".".join(parts[::-1])

class ECompare:
    def __init__(self, node, conds):
        self.ast = node
        self.conds = conds

def parse_compare(node):
    left = node.left
    conds = []
    for (op, right) in zip(node.ops, node.comparators):
        eleft = parse_expression(left)
        if isinstance(eleft, UnsupportedNode):
            return UnsupportedNode(node)
        eright = parse_expression(right)
        if isinstance(right, UnsupportedNode):
            return UnsupportedNode(node)
        econd = parse_cond(op, eleft, eright)
        if econd is None:
            return UnsupportedNode(node)
        conds.append(econd)
        left = right

    return ECompare(node, conds)

class Condition:
    def __init__(self, op, left, right):
        self.ast = op
        self.left = left
        self.right = right

class CEq(Condition):
    def __init__(self, op, left, right):
        super().__init__(op, left, right)

class CGtE(Condition):
    def __init__(self, op, left, right):
        super().__init__(op, left, right)


COMPARE_CLASSES = { "Eq" : CEq
                    , "GtE" : CGtE
}


def parse_cond(op, left, right):
    compare_type_name = op.__class__.__name__
    if compare_type_name in COMPARE_CLASSES:
        return COMPARE_CLASSES[compare_type_name](op, left, right)
    else:
        return None

class ECall:
    def __init__(self, node):
        self.ast = node
        #print(astpp.dump(node))
        self.fun_name = parse_function_name(node.func)
        #print("function name=", self.fun_name)
        self.arguments = []
        for arg in self.ast.args:
            #print(astpp.dump(arg))
            earg = parse_expression(arg)
            self.arguments.append(earg)
            #print("---")


EXPRESSION_CLASSES = { "Num" : ENum
                       , "NameConstant"  : parse_constant
                       , "Name" : EVar
                       , "BinOp" : EBinOp
                       , "UnaryOp" : EUnaryOp
                       , "Call" : ECall
                       , "Compare" : parse_compare
}

def parse_expression(node):
    expression_type_name = node.__class__.__name__
    #print("expression type=",expression_type_name)
    if expression_type_name in EXPRESSION_CLASSES:
        wrap_node = EXPRESSION_CLASSES[expression_type_name](node)
        return wrap_node
    else:
        return UnsupportedNode(node)


def print_ast_fields(node):
    for field, val in ast.iter_fields(node):
        print(field)


def python_ast_from_file(filename):
    with tokenize.open(filename) as f:
        modtxt = f.read()
        modast = ast.parse(modtxt, mode="exec")
        return modast

def python_show_tokenized(filename):
    modtxt = ""
    with tokenize.open(filename) as f:
        modtxt = f.read()

    return modtxt

if __name__ == "__main__":
    prog1 = Program()
    prog1.build_from_file("../../examples/aire.py")
    #print(astpp.dump(prog1.ast))
