import operator
import json, sys
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
STRING: /'[^']*'/                                   
DATE.1: /\d{4}-\d{2}-\d{2}/

%import common.SIGNED_INT
%import common.SIGNED_FLOAT
%import common.WS
%import common.CNAME
%ignore WS
"""
)


class _visitor(Transformer):
    def __init__(self, visit_tokens: bool = True) -> None:
        super().__init__(visit_tokens)

        def get_val(token):
            return token.value

        def get_typed_val(token):
            if token.type == "SIGNED_INT":
                return {"type": int, "value": int(token.value)}
            if token.type == "SIGNED_FLOAT":
                return {"type": float, "value": float(token.value)}

            if token.type == "STRING":
                return {"type": str, "value": token.value[1:-1]}

            if token.type == "DATE":
                return {
                    "type": datetime,
                    "value": datetime.strptime(token.value, "%Y-%m-%d"),
                }

            raise Exception(f"{token.type}: unknown token type")

        self.SIGNED_INT = get_typed_val
        self.SIGNED_FLOAT = get_typed_val
        self.STRING = get_typed_val
        self.DATE = get_typed_val

        self.BIN_OP = get_val
        self.LIST_OP = get_val
        self.ATOMIC_OP = get_val
        self.NULL_OP = get_val
        self.CNAME = get_val

    def WS(self, _):
        return Discard

    def atom(self, children):
        return children[0]

    def atoms(self, children):
        result = []
        cur = children[0]
        while len(cur.children) > 0:
            result.append(cur.children[0]["value"])
            if len(cur.children) == 1:
                break
            cur = cur.children[1]
        return {"type": list, "value": result}

    def exp_compare(self, children):
        return {
            "field": children[0],
            "op": children[1],
            "value": {"type": type(None), "value": None}
            if len(children) < 3
            else children[2],
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


def _eval_exp(obj, exp) -> bool:
    op = exp["op"]
    field = exp.get("field")
    expected_value = exp.get("value", {}).get("value")

    cmp_ops = {
        "=": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
        "~": lambda a, b: a in b,
        "!~": lambda a, b: a not in b,
    }

    if op == ",":
        return _eval_exp(obj, exp["arg1"]) or _eval_exp(obj, exp["arg2"])
    elif op == "+":
        return _eval_exp(obj, exp["arg1"]) and _eval_exp(obj, exp["arg2"])
    elif op in cmp_ops:
        actual_value = obj.get(field)

        if expected_value is not None:
            try:
                actual_value = datetime.strptime(actual_value, "%Y-%m-%d")
            except:
                pass

        # order is important because of "in"
        return cmp_ops[op](actual_value, expected_value)
    else:
        raise Exception(f"{op}: unknown operation")


class Filter:
    def __init__(self, query):
        if not query:
            self.exp = None
            return
        tree = parser.parse(query)
        self.exp = _visitor(visit_tokens=True).transform(tree)

    def match(self, obj, debug=False) -> bool:
        if debug:
            json.dump(self.exp, sys.stdout, indent=4, default=str)

        if self.exp is None:
            return True

        return _eval_exp(obj, self.exp)
