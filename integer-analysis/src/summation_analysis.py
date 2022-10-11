from ast_nodes import *
from analysis import BaseAnalysis
from analyzer import chaotic_iteration
from typing import Tuple
from copy import deepcopy

class AbsVal:
    """Abstract Value.
    Represents a value that may contain an unknown ('?').
    """
    def __init__(self, unknown=None, const=0):
        self.const = const
        self.unknown = unknown

    def inc(self):
        self.const += 1

    def dec(self):
        self.const -= 1

    def __eq__(self, other):
        return self.unknown == other.unknown and \
               self.const == other.const

    def __add__(self, other):
        assert isinstance(other, int)
        return AbsVal(unknown=self.unknown, const=self.const + other)

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __repr__(self):
        return f"AbsVal(unknown={self.unknown}, const={self.const})"

    def __str__(self):
        if self.unknown is not None and self.const != 0:
            return f"?{self.unknown}{self.const:+}"
        if self.unknown is not None:
            return f"?{self.unknown}"
        return f"{self.const}"


class SummationLatticeMember:
    """A member of the basic summation lattice (n=1).
    Is either an abstract value or TOP/BOTTOM. """

    top = lambda: SummationLatticeMember(level=+1)
    bot = lambda: SummationLatticeMember(level=-1)
    def is_top(self): return self == SummationLatticeMember.top()
    def is_bot(self): return self == SummationLatticeMember.bot()

    def __init__(self, absval=None, level=0):
        self.level = level
        if level == 0 and not absval:  # level 0 members require a value
            absval = AbsVal()
        self.absval = absval

    def __str__(self):
        if self.is_top(): return '⊤'
        if self.is_bot(): return '⊥'
        return str(self.absval)

    __repr__ = __str__

    def __eq__(self, other):
        match other:
            case int():
                return self.absval == AbsVal(const=other)
            case SummationLatticeMember():
                return (self.level == other.level) and (self.absval == other.absval)

    def __add__(self, c):
        assert self.level == 0 and isinstance(c, int)
        return SummationLatticeMember(absval=self.absval + c)
    def __sub__(self, c): return self + (-c)

    def join(self, other):
        if self.is_bot(): return other
        if other.is_bot(): return self
        if self.is_top() or other.is_top(): return self.top()
        return SummationLatticeMember.top() if self != other else deepcopy(self)


from functools import reduce
class SAFull(BaseAnalysis):
    def __init__(self, num_vars: int):
        self.n = num_vars

    def bottom(self):
        return (SummationLatticeMember.bot(),) * self.n

    def top(self):
        return (SummationLatticeMember.top(),) * self.n

    def join2(self, x, y):
        return map(SummationLatticeMember.join, x,y)

    def join(self, l):
        l = list(l)
        assert len(l)>0
        return reduce(self.join2, l)

    def equiv(self, x, y):
        return all(a==b for a,b in zip(x,y))

    def transform_nontrivial(self, ast, x):
        Y = deepcopy(list(x))
        new = lambda absval: SummationLatticeMember(absval=absval)
        match ast:
            # ----- Assignment -----
            case ConstAssignment():
                Y[ast.dest.id] = new(AbsVal(const=ast.src))
            case UnknownAssigment():
                Y[ast.dest.id] = new(AbsVal(unknown=ast.src))
            case VarAssignment():
                Y[ast.dest.id] = Y[ast.src.id]
            case IncAssignment():
                Y[ast.dest.id] = Y[ast.src.id] + 1
            case DecAssignment():
                Y[ast.dest.id] = Y[ast.src.id] - 1
            # ----- Assume -----
            case Assume():
                expr = ast.expr
                match expr:
                    case ExprFalse():
                        res = False
                    case ExprTrue():
                        res = True
                    case BaseComp():
                        negate = isinstance(expr, VarNeq) or isinstance(expr, VarConsNeq)
                        rhs_is_cons = isinstance(expr, BaseVarConsComp)
                        rhs = expr.rhs if rhs_is_cons else Y[expr.rhs.id]
                        lhs = Y[expr.lhs.id]
                        res = (lhs == rhs) ^ negate
                if res is False:
                    Y = self.bottom()
        return tuple(Y)

    def stabilize(self, x):
        return tuple(x)


def _parse_file():
    from sys import argv
    from parser import Parser
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cmds = list(p.parse_labeled_commands_iter())
    # for i, c in enumerate(cmds): print(f"{i}. {c}")
    return cmds


def _traverse():
    sl = SAFull(3)
    cmds = _parse_file()
    s = sl.top()
    print(s)
    for cmd in cmds:
        node = cmd.ast 
        s = sl.transform(node, s)
        print(cmd)
        print(s)


def _print_res(res):
    print('\n'.join(f'{i}. {v}' for i,v in enumerate(res)))

def _main():
    from sys import argv
    from parser import Parser
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    res = chaotic_iteration(num_vars, cfg ,SAFull, verbose=True)
    res = map(list,res)
    _print_res(res)


if __name__ == "__main__":
    _main()









