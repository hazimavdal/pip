import re
import operator
import json, sys
from lark import Lark
from lark import Transformer
from datetime import datetime
from lark.visitors import Discard

parser = Lark(
    """
start: exp

exp: selector ATOMIC_OP atom                 -> exp_compare
   | selector STRING_OP STRING               -> exp_compare
   | selector LIST_OP "[" atoms "]"          -> exp_compare
   | selector NULL_OP "null"                 -> exp_compare
   | "(" exp ")"                             -> exp_group 
   | exp BIN_OP exp                          -> exp_binop
   | "!" exp                                 -> exp_not

atom: SIGNED_INT | SIGNED_FLOAT | "d'" DATE "'"
atoms: ints | strings | floats 
ints: SIGNED_INT                            -> list_head
    | SIGNED_INT "," ints                   -> list_cons
strings: STRING                             -> list_head
    | STRING "," strings                    -> list_cons
floats: SIGNED_FLOAT                        -> list_head
    | SIGNED_FLOAT "," floats               -> list_cons

selector : ANY_KEY | dot_selector | dot_selector "." ANY_KEY
dot_selector: key                               -> list_head
    | key "." dot_selector                      -> list_cons
key: CNAME | NON_EMPTY_STRING

BIN_OP: "," | "+"                                    
ATOMIC_OP: "=" | "!=" | "<" | ">" | "<=" | ">="     
STRING_OP: "=" | "!=" | "~" | "!~" | "~" | "*=" | "=*" | "%"   
LIST_OP: "in" | "not_in"                    
NULL_OP: "is" | "is_not"                                 
STRING: /'[^']*'/ 
NON_EMPTY_STRING: /'[^']+'/                                   
ANY_KEY: "*"
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
                return int(token.value)
            if token.type == "SIGNED_FLOAT":
                return float(token.value)
            if token.type in ["STRING", "NON_EMPTY_STRING"]:
                return token.value[1:-1]
            if token.type == "DATE":
                return datetime.strptime(token.value, "%Y-%m-%d")

            raise Exception(f"{token.type}: unknown token type")

        self.SIGNED_INT = get_typed_val
        self.SIGNED_FLOAT = get_typed_val
        self.STRING = get_typed_val
        self.NON_EMPTY_STRING = get_typed_val
        self.DATE = get_typed_val

        self.BIN_OP = get_val
        self.LIST_OP = get_val
        self.ATOMIC_OP = get_val
        self.STRING_OP = get_val
        self.NULL_OP = get_val
        self.CNAME = get_val
        self.KEY = get_val

    def WS(self, _):
        return Discard

    def ANY_KEY(self, children):
        return ["*"]

    def selector(self, children):
        if len(children) == 1:
            return children[0]

        return children[0] + children[1]

    def key(self, children):
        return children[0]

    def list_head(self, children):
        return [children[0]]

    def list_cons(self, children):
        return [children[0]] + children[1]

    def atom(self, children):
        return children[0]

    def atoms(self, children):
        return children[0]

    def exp_compare(self, children):
        return {
            "selector": children[0],
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

    def exp_not(self, children):
        return {
            "op": "!",
            "arg1": children[0],
        }

    def start(self, children):
        return children[0]


def _eval_exp(obj, exp) -> bool:
    op = exp["op"]

    if op == ",":
        return _eval_exp(obj, exp["arg1"]) or _eval_exp(obj, exp["arg2"])
    elif op == "+":
        return _eval_exp(obj, exp["arg1"]) and _eval_exp(obj, exp["arg2"])
    elif op == "!":
        return not _eval_exp(obj, exp["arg1"])

    return _eval_cmp(obj, exp)


def compare(obj, key, op, expected_value):
    cmp_ops = {
        "=": operator.eq,
        "~": lambda a, b: a.lower() == b.lower(),
        "!=": operator.ne,
        "!~": lambda a, b: a.lower() != b.lower(),
        "*=": lambda a, b: a.startswith(b),
        "=*": lambda a, b: a.endswith(b),
        "%": lambda a, b: re.match(b, a) is not None,
        ">": operator.gt,
        ">=": operator.ge,
        "<": operator.lt,
        "<=": operator.le,
    }

    expected_type = type(expected_value)
    actual_value = obj.get(key)

    if actual_value is None:
        return False

    if expected_type is datetime:
        try:
            actual_value = datetime.strptime(actual_value[:10], "%Y-%m-%d")
        except:
            return False
    elif type(actual_value) is not expected_type:
        return False

    return cmp_ops[op](actual_value, expected_value)


def _eval_cmp(obj, exp) -> bool:
    op = exp["op"]
    expected_value = exp.get("value")

    selector = exp.get("selector")
    for key in selector[:-1]:
        if key not in obj or type(obj[key]) is not dict:
            return False
        selector = selector[1:]
        obj = obj.get(key)

    field = selector[-1]

    if op == "is":
        if selector == ["*"]:
            return None in obj.values()
        return obj.get(field, None) is None
    elif op == "is_not":
        if selector == ["*"]:
            return None not in obj.values()

        return obj.get(field, None) is not None
    elif op == "in":
        if selector == ["*"]:
            return bool(set(expected_value).intersection(set(obj.values())))

        return field in obj and obj[field] in expected_value
    elif op == "not_in":
        if selector == ["*"]:
            return not bool(set(expected_value).intersection(set(obj.values())))

        return field not in obj or obj[field] not in expected_value

    if selector == ["*"]:
        for key in obj.keys():
            if compare(obj, key, op, expected_value):
                return True
        return False

    return compare(obj, field, op, expected_value)


class Filter:
    def __init__(self, filter_str):
        if not filter_str:
            self.exp = None
            return
        tree = parser.parse(filter_str)
        self.exp = _visitor(visit_tokens=True).transform(tree)

    def match(self, obj, debug=False) -> bool:
        if debug:
            json.dump(self.exp, sys.stdout, indent=4, default=str)

        if self.exp is None:
            return True

        return _eval_exp(obj, self.exp)
