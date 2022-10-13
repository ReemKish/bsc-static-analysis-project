#!/usr/bin/env python3

from analysis import BaseAnalysis
from lattice import Lattice
from enum import Enum
import ast_nodes as ASTS
import numpy as np
import itertools


class PState(Enum):
    BOTTOM = 0
    TOP = 1
    EVEN = 2
    ODD = 3
    def join(self, other):
        if self == other:
            return self
        elif self == PState.BOTTOM:
            return other
        elif other == PState.BOTTOM:
            return self
        else:
            return PState.TOP

    def meet(self, other):
        if self == other:
            return self
        elif self == PState.TOP:
            return other
        elif other == PState.TOP:
            return self
        else:
            return PState.BOTTOM

from functools import reduce
class PADumb(BaseAnalysis):
    def __init__(self, num_vars):
        self.n = num_vars

    def bottom(self):
        return [ PState.BOTTOM ] * self.n

    def top(self):
        return [ PState.TOP ] * self.n

    def join2(self, x, y):
        return map(PState.join, x,y)

    def join(self, l):
        l = list(l)
        assert len(l)>0
        return reduce(self.join2, l)

    def equiv(self, x, y):
        return all(a==b for a,b in zip(x,y))

    def transform_nontrivial(self, ast, x):
        if self.equiv(x,self.bottom()):
            return x
        x = list(x)
        if isinstance(ast, ASTS.ConstAssignment):
            ret = list(x)
            ret[ast.dest.id] = PState.EVEN if ast.src%2==0 else PState.ODD
            return ret
        elif isinstance(ast, ASTS.Assume):
            bexpr = ast.expr
            if isinstance(bexpr, ASTS.VarEq):
                v1 = bexpr.lhs
                v2 = bexpr.rhs
                i1 = v1.id
                i2 = v2.id
                m = PState.meet(x[i1], x[i2])
                if m == PState.BOTTOM:
                    return self.bottom()
                x[i1] = x[i2] = m
                return x
        return x

    def stabilize(self, x):
        return tuple(x)



def _parity_val(num: int):
    return num%2==0

def _clean_unique(method):
    def wrapped(self, *args, **kwargs):
        ret = method(self, *args, **kwargs)
        return _remove_unique(ret)
    return wrapped

def _remove_unique(x):
    return np.unique(x, axis=1)

class ParityLattice(Lattice):
    def __init__(self, num_vars):
        self.n = num_vars
        self.BOTTOM = np.array([[] for _ in range(self.n)], dtype=bool)
        prod = itertools.product((True,False),repeat=self.n)
        self.TOP = np.transpose(list(prod))
        self.BOTTOM.setflags(write=False)
        self.TOP.setflags(write=False)

    def bot(self):
        return self.BOTTOM

    def top(self):
        return self.TOP

    @_clean_unique
    def join_nontrivial(self, l):
        l = list(l)
        return np.hstack(l)

    def _set_rep(self, x):
        return { tuple(col) for col in x.transpose() }

    def equiv(self, x, y):
        print(type(x), type(y))
        #x,y = map(self._set_rep, (x,y))
        return self._set_rep(x)==self._set_rep(y)

class ParityAnalysis(BaseAnalysis):
    def __init__(self, num_vars):
        self.lat = ParityLattice(num_vars)
        self.n = num_vars
        self.BOTTOM = np.array([[] for _ in range(self.n)], dtype=bool)
        prod = itertools.product((True,False),repeat=self.n)
        self.TOP = np.transpose(list(prod))
        self.BOTTOM.setflags(write=False)
        self.TOP.setflags(write=False)
        print("---------------------------------")
        print(self.n)
        print("---------------------------------")
        print(self.TOP.shape,"---------------", self.BOTTOM.shape)
        print("---------------------------------")
        print(type(self.TOP),"---------------", type(self.BOTTOM))
        print("---------------------------------")

    def _clean_unique(method):
        def wrapped(self, *args, **kwargs):
            ret = method(self, *args, **kwargs)
            return _remove_unique(ret)
        return wrapped

    def _copy_if_nonwrite(self,x):
        if not x.flags.writeable:
            return x.copy()

    def _remove_unique(self, x):
        return np.unique(x, axis=1)

    @_clean_unique
    def transform_nontrivial(self, ast, x):
        #x = x.copy()
        x = self._copy_if_nonwrite(x)
        match ast:
            case ASTS.Assignment(dest=dest, src=src):
                dest = dest.id
                match ast:
                    case ASTS.ConstAssignment():
                        x[dest] = _parity_val(src)
                    case ASTS.UnknownAssigment():
                        x[dest] = True
                        x = np.hstack((x,x))
                        x[dest, x.shape[1]//2:] = False
                    case ASTS.VarAssignment():
                        x[dest] = x[src.id]
                    case ASTS.StepAssigment():
                        x[dest] = ~x[src.id]
            case ASTS.Assume(expr=expr):
                match expr:
                    case ASTS.BaseComp(lhs=lhs, rhs=rhs):
                        i = lhs.id
                        match expr:
                            case ASTS.VarNeq() | ASTS.VarConsNeq:
                                pass
                            case ASTS.VarEq():
                                j=rhs.id
                                return x[:, x[i] == x[j]]
                            case ASTS.VarConsEq:
                                return x[:, x[i] == _parity_val(rhs)]

            case _:
                print(f"Entered default case with type(ast)={type(ast)}")
        return x

    def stabilize(self, x):
        x.setflags(write=False)
        return x


def _main():
    from sys import argv
    from parser import Parser
    from analyzer import chaotic_iteration, _print_res
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    cfg, num_vars = p.parse_complete_program()
    res = chaotic_iteration(num_vars, cfg, ParityAnalysis, verbose=True)
    _print_res(res)

if __name__ == "__main__":
    _main()

