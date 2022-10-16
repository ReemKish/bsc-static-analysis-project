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
        # self.lat = CartProd([SummationLattice()] * num_vars)
        self.lat = DisjComp(SummationLattice())

    def lattice(self):
        return self.lat

    def verify_assertion(self, ass: ASTS.Assert, x) -> bool:
        return True  # TODO

    def transform_nontrivial(self, ast, X):
        return set(map(lambda x: self._transform_nontrivial(ast, x), X))

    def _transform_nontrivial(self, ast, x):
        if self.lat.lat.is_bot(x): return x
        y = x
        match ast:
            # ----- Assignment -----
            case ASTS.ConstAssignment():
                y = AbsVal(const=ast.src)
            case ASTS.UnknownAssigment():
                y = AbsVal(unknown=ast.src)
            case ASTS.VarAssignment():
                y = y
            case ASTS.IncAssignment():
                y =  self.lat.lat.inc(y)
            case ASTS.DecAssignment():
                y =  self.lat.lat.dec(y)
            # ----- Assume -----
            case ASTS.Assume(expr=expr):
                lhs = y
                match expr:
                    case ASTS.BaseVarConsComp():
                        rhs = AbsVal(const=expr.rhs)
                        lhs_is_const = isinstance(y, AbsVal) and y.unknown is None
                        match expr:
                            case ASTS.VarConsEq():
                                if self.lat.lat.is_bot(lhs) or (lhs_is_const and lhs != rhs):
                                    y = self.lat.lat.bot()
                                else:
                                    y = rhs
                            case ASTS.VarConsNeq():
                                if lhs_is_const and lhs == rhs:
                                    y = self.lat.lat.bot()
                    case ASTS.BaseVarComp():
                        negate = isinstance(expr, ASTS.VarNeq)
                        rhs = y
                        y = y if (self.lat.lat.equiv(lhs, rhs)) ^ negate else self.lat.lat.bot()
        return y

    # def transform_nontrivial(self, ast, x):
    #     Y = deepcopy(list(x))
    #     match ast:
    #         # ----- Assignment -----
    #         case ASTS.ConstAssignment():
    #             Y[ast.dest.id] = AbsVal(const=ast.src)
    #         case ASTS.UnknownAssigment():
    #             Y[ast.dest.id] = AbsVal(unknown=ast.src)
    #         case ASTS.VarAssignment():
    #             Y[ast.dest.id] = Y[ast.src.id]
    #         case ASTS.IncAssignment():
    #             Y[ast.dest.id] =  self.lat.lats[ast.src.id].inc(Y[ast.src.id])
    #         case ASTS.DecAssignment():
    #             Y[ast.dest.id] =  self.lat.lats[ast.src.id].dec(Y[ast.src.id])
    #         # ----- Assume -----
    #         case ASTS.Assume():
    #             expr = ast.expr
    #             match expr:
    #                 case ASTS.BaseComp():
    #                     negate = isinstance(expr, ASTS.VarNeq) or isinstance(expr, ASTS.VarConsNeq)
    #                     rhs_is_cons = isinstance(expr, ASTS.BaseVarConsComp)
    #                     rhs = AbsVal(const=expr.rhs) if rhs_is_cons else Y[expr.rhs.id]
    #                     lhs = Y[expr.lhs.id]
    #                     # self.lat.lats is the list of lattices that compose the CartProd lattice (self.lat) 
    #                     # Therfore, the below line uses the equiv() method of the left lattice member.
    #                     # In cases where the cartesian product is of different types of lattices, it is important 
    #                     # to note which method is used to compare members across the different lattices.
    #                     res = (self.lat.lats[expr.lhs.id].equiv(lhs, rhs)) ^ negate
    #             if res is False:
    #                 Y = self.lat.bot()
    #     return tuple(Y)


def _main():
    debug_analysis(SummationAnalysis, verbose=True)
    # run_analysis(SummationAnalysis)

if __name__ == "__main__":
    _main()
