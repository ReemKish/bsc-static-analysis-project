#!/usr/bin/env python3

from analyzer import debug_analysis, run_analysis
from analysis import BaseAnalysis
import ast_nodes as ASTS
from lattice import *
from copy import deepcopy


class AbsVal:
    """Abstract Value.
    Represents a value that may contain an unknown ('?').
    """
    def __init__(self, unknown=None, const=0):
        self.const = const
        self.unknown = unknown

    def __eq__(self, other):
        return self.unknown == other.unknown and \
               self.const == other.const

    def __add__(self, other):
        assert isinstance(other, int)
        return AbsVal(unknown=self.unknown, const=self.const + other)

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __repr__(self):
        return str(self)
        # return f"AbsVal(unknown={self.unknown}, const={self.const})"

    def __str__(self):
        if self.unknown is not None and self.const != 0:
            return f"?{self.unknown}{self.const:+}"
        if self.unknown is not None:
            return f"?{self.unknown}"
        return f"{self.const}"

    def __hash__(self):
        return hash((self.const, self.unknown))

    @staticmethod
    def sum_eq(l1, l2):
        """Returns True iff the sum of the elements in l1 is equal to the sum of the elements in l2."""
        if sum(x.const for x in l1) != sum(x.const for x in l2):
            return False
        l1_unknowns = [x.unknown for x in l1 if x.unknown is not None]
        l2_unknowns = [x.unknown for x in l2 if x.unknown is not None]
        return {x.unknown: l1_unknowns.count(x.unknown) for x in l1} == {x.unknown: l2_unknowns.count(x.unknown) for x in l2}



class SummationLattice(Lattice):
    """The base lattice used for summation analysis."""

    def join_nontrivial(self, x, y):
        return self.top() if x != y else x

    def inc(self, x):
        return x if self.is_top(x) or self.is_bot(x) else x + 1

    def dec(self, x):
        return x if self.is_top(x) or self.is_bot(x) else x - 1


class SummationAnalysis(LatticeBasedAnalysis):
    """The summation analysis created from a lattice fitted with a transform method."""
    def __init__(self, num_vars):
        self.lat = RelProd([SummationLattice()] * num_vars)

    def lattice(self):
        return self.lat

    def verify_assertion(self, ass: ASTS.Assert, Xset) -> bool:
        def satisfies_predicate(X, pred):
            if not isinstance(pred,(ASTS.SumEq)):
                return False
            lhs_ids = [var.id for var in pred.lhs.var_list]
            rhs_ids = [var.id for var in pred.rhs.var_list]
            lhs = [X[i] for i in lhs_ids]
            rhs = [X[i] for i in rhs_ids]
            return AbsVal.sum_eq(lhs, rhs)

        def satisfies_AndChain(X, andc):
            return all(satisfies_predicate(X, pred) for pred in andc.pred_list)

        def satisfies_OrChain(X, orc):
            return any(satisfies_AndChain(X, andc) for andc in orc.andc_list)

        return all(satisfies_OrChain(X, ass.orc) for X in Xset) if Xset else False

    def transform_nontrivial(self, ast, X):
        Y = set()
        for x in X:
            y = self._transform_nontrivial(ast, x)
            if not self.lat.lat.is_bot(y):
                Y.add(y)
        return Y

    def _transform_nontrivial(self, ast, x):
        if self.lat.lat.is_bot(x): return x
        Y = deepcopy(list(x))
        match ast:
            # ----- Assignment -----
            case ASTS.ConstAssignment():
                Y[ast.dest.id] = AbsVal(const=ast.src)
            case ASTS.UnknownAssignment():
                Y[ast.dest.id] = AbsVal(unknown=ast.src)
            case ASTS.VarAssignment():
                Y[ast.dest.id] = Y[ast.src.id]
            case ASTS.IncAssignment():
                Y[ast.dest.id] =  self.lat.lat.lats[ast.src.id].inc(Y[ast.src.id])
            case ASTS.DecAssignment():
                Y[ast.dest.id] =  self.lat.lat.lats[ast.src.id].dec(Y[ast.src.id])
            # ----- Assume -----
            case ASTS.Assume(expr=expr):
                lhs = Y[expr.lhs.id]
                match expr:
                    case ASTS.BaseVarConsComp():
                        rhs = AbsVal(const=expr.rhs)
                        lhs_is_const = isinstance(lhs, AbsVal) and lhs.unknown is None
                        match expr:
                            case ASTS.VarConsEq():
                                if self.lat.lat.lats[expr.lhs.id].is_bot(lhs) or (lhs_is_const and lhs != rhs):
                                    Y = self.lat.lat.bot()
                                else:
                                    Y[expr.lhs.id] = rhs
                            case ASTS.VarConsNeq():
                                if lhs_is_const and lhs == rhs:
                                    Y = self.lat.lat.bot()
                    case ASTS.BaseVarComp():
                        negate = isinstance(expr, ASTS.VarNeq)
                        rhs = Y[expr.rhs.id]
                        Y = Y if self.lat.lat.lats[expr.lhs.id].equiv(lhs, rhs) ^ negate else self.lat.lat.bot()
        return tuple(Y)

def _main():
    run_analysis(SummationAnalysis)

if __name__ == "__main__":
    _main()
