#!/usr/bin/env python3

from analysis import BaseAnalysis
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

Parity = bool
ODD = _parity_val(1)
EVEN = _parity_val(2)

class PAFull(BaseAnalysis):

    def __init__(self, num_vars):
        self.n = num_vars
        self.BOTTOM = np.array([[] for _ in range(self.n)], dtype=Parity)
        prod = itertools.product((EVEN, ODD),repeat=self.n)
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

    def _remove_duplicates(self, x):
        return np.unique(x, axis=1)

    def _clean_duplicates(method):
        def wrapped(self, *args, **kwargs):
            ret = method(self, *args, **kwargs)
            return self._remove_duplicates(ret)

        return wrapped

    def _copy_if_nonwrite(self,x):
        if not x.flags.writeable:
            return x.copy()
        return x

    def bottom(self):
        return self.BOTTOM

    def top(self):
        return self.TOP

    @_clean_duplicates
    def join(self, l):
        l = list(l)
        return np.hstack(l)

    def _set_rep(self, x):
        return { tuple(col) for col in x.transpose() }

    def equiv(self, x, y):
        print(type(x), type(y))
        #x,y = map(self._set_rep, (x,y))
        return self._set_rep(x)==self._set_rep(y)

    def _assume_var_parity(self, var : ASTS.Var, parity: Parity, x):
        x = self._copy_if_nonwrite(x)
        i = var.id
        return x[:, x[i] == parity ]

    def _assume_pred(self, pred: ASTS.Predicate, x):
        parity = None
        match pred:
            case ASTS.BaseVarTest(var=var):
                match pred:
                    case ASTS.TestOdd():
                        parity = ODD
                    case ASTS.TestEven():
                        parity = EVEN
                return self._assume_var_parity(var, parity, x)
        return x

    def _assume_andc(self, andc: ASTS.AndChain, x):
        for p in andc.pred_list:
            x = self._assume_pred(p, x)
        return x

    def _assume_orc(self, orc: ASTS.OrChain, x):
        return self.join(self._assume_andc(c, x) for c in orc.andc_list)

    def _assume_assert(self, assertion: ASTS.Assert, x):
        return self._assume_orc(assertion.orc, x)

    @_clean_duplicates
    def transform_nontrivial(self, ast, x):
        #x = x.copy()
        x = self._copy_if_nonwrite(x)
        match ast:
            case ASTS.Assignment(dest=dest, src=src):
                dest = dest.id
                match ast:
                    case ASTS.ConstAssignment():
                        x[dest] = _parity_val(src)
                    case ASTS.UnknownAssignment():
                        x[dest] = EVEN
                        x = np.hstack((x,x))
                        x[dest, x.shape[1]//2:] = ODD
                    case ASTS.VarAssignment():
                        x[dest] = x[src.id]
                    case ASTS.StepAssignment():
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
                                p = _parity_val(rhs)
                                return self._assume_var_parity(p)
            case ASTS.Assert():
                return self._assume_assert(ast, x)
            case _:
                assert False, "Unhandled AST encountered in PAFull transform"
        return x

    def stabilize(self, x):
        x.setflags(write=False)
        return x

    def verify_assertion(self, ass: ASTS.Assert, x):
        if not all(isinstance(p,(ASTS.TestOdd, ASTS.TestEven))
                   for andc in ass.orc.andc_list for p in andc.pred_list):
            return False
        return self.equiv(x, self._assume_assert(ass, x))

def _print_res(res):
    print('\n'.join(f'{i}. {v}' for i,v in enumerate(res)))

def _main():
    from analyzer import run_analysis, debug_analysis
    # debug_analysis(PAFull, verbose=False)
    run_analysis(PAFull)

if __name__ == "__main__":
    _main()
