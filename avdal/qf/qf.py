import operator
from lark import Lark
from lark import Transformer
from datetime import datetime
from lark.visitors import Discard

parser = Lark(
    """
start: exp

exp: CNAME WS? ATOMIC_OP WS? atom                 -> exp_compare
   | CNAME WS? LIST_OP WS? "[" atoms "]"          -> exp_compare
   | CNAME WS? NULL_OP WS? "null"                 -> exp_compare
   | "(" WS? exp WS? ")"                          -> exp_group 
   | exp WS? BIN_OP WS? exp                       -> exp_binop  

atom: STRING | SIGNED_INT | SIGNED_FLOAT | "'" DATE "'"
atoms: ints | strings | floats 
ints: SIGNED_INT | SIGNED_INT WS? "," WS? ints            
strings: STRING | STRING WS? "," WS? strings                
floats: SIGNED_FLOAT | SIGNED_FLOAT WS? "," WS? floats      

BIN_OP: "," | "+"                                    
ATOMIC_OP: "=" | "!=" | "<" | ">" | "<=" | ">="     
LIST_OP: "!=" | "=" | "~" | "!~"                    
NULL_OP: "!=" | "="                                 
STRING: /'[^']'*/                                   
DATE.1: /\d{4}-\d{2}-\d{2}/

%import common.SIGNED_INT
%import common.SIGNED_FLOAT
%import common.WS
%import common.CNAME
%ignore WS
"""
)


class __visitor(Transformer):
    def __init__(self, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)

        def get_val(token):
            return token.value

        self.SIGNED_INT = int
        self.SIGNED_FLOAT = float
        self.STRING = lambda raw: raw[1:-1]
        self.BIN_OP = get_val
        self.LIST_OP = get_val
        self.ATOMIC_OP = get_val
        self.NULL_OP = get_val
        self.CNAME = get_val

    def WS(self, _):
        return Discard

    def DATE(self, token):
        return datetime.strptime(token.value, "%Y-%m-%d")

    def atom(self, children):
        return children[0]

    def atoms(self, children):
        result = []
        cur = children[0]
        while len(cur.children) > 0:
            result.append(cur.children[0])
            if len(cur.children) == 1:
                break
            cur = cur.children[1]
        return result

    def exp_compare(self, children):
        return {
            "field": children[0],
            "op": children[1],
            "value": None if len(children) < 3 else children[2],
        }

    def exp_group(self, children):
        return children[0]

    def exp_binop(self, children):
        return {
            "arg1": children[0],
            "op": children[1],
            "arg2": children[2],
        }

    def start(self, children):
        return children[0]


def __eval_exp(obj, exp) -> bool:
    op = exp["op"]
    field = exp.get("field")
    expected_value = exp.get("value")

    cmp_ops = {
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "~": operator.contains,
    }

    if op == ",":
        return __eval_exp(obj, exp["arg1"]) or __eval_exp(obj, exp["arg2"])
    elif op == "+":
        return __eval_exp(obj, exp["arg1"]) and __eval_exp(obj, exp["arg2"])
    elif op in cmp_ops:
        actual_value = obj.get(field)

        if expected_value is not None and type(expected_value) != type(actual_value):
            return False

        return cmp_ops[op](
            expected_value, actual_value
        )  # order is important because of "in"
    else:
        raise Exception(f"{op}: unknown operation")


def match_object(obj, query):
    tree = parser.parse(filter)
    exp = __visitor(visit_tokens=True).transform(tree)
    return __eval_exp(obj, exp)
