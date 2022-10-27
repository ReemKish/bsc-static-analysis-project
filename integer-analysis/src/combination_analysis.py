#!/usr/bin/env python3

from abc import ABC, abstractmethod
from analysis import BaseAnalysis
from analyzer import debug_analysis, run_analysis
from summation_analysis import SummationAnalysis, AbsVal
from parity_analysis import PAFull
import ast_nodes as ASTS
from typing import Dict, Optional, Union, Iterable, List

class CombinedAnalysis(BaseAnalysis):
    def __init__(self, num_vars):
        self.left = PAFull(num_vars)
        self.right = SummationAnalysis(num_vars)

    def bottom(self):
        return (self.left.bottom(), self.right.bottom())

    def top(self):
        return (self.left.top(), self.right.top())

    def join(self, l: Iterable):
        left, right = zip(*l)
        return (self.left.join(left), self.right.join(right))

    def equiv(self, x, y):
        left, right = zip(x,y)
        return self.left.equiv(*left) and self.right.equiv(*right)

    def verify_assertion(self, ass: ASTS.Assert, x):
        left, right = x
        return (self.left.verify_assertion(ass, left) or
                self.right.verify_assertion(ass, right))

    def transform_nontrivial(self, ast: ASTS.SyntaxNode, x):
        left, right = x
        return (self.left.transform_nontrivial(ast, left),
                self.right.transform_nontrivial(ast, right))

    def stabilize(self, x):
        """
        "Stabilizes" the lattice value of x:
        This operation converts x into an object that does not get mutated
        by any of the other analysis methods (which are present in this
        class). By default, it is assumed that values are already always
        stable, if that isn't the case this method should be overwritten
        accordingally.
        """
        left, right = x
        return (self.left.stabilize(left), self.right.stabilize(right))

class CombinedAnalysisReductive(CombinedAnalysis):
    @abstractmethod
    def reduce_left(self, x):
        return x

    @abstractmethod
    def reduce_right(self, x):
        return x
    def reduce_left(self, x):
        left, right = x
        it = (self._reduce_left_by_single_case_sum(left, r_case)
              for r_case in right)
        it = list(it)
        #print(f"it:\n{it}\n")
        left = self.left.join(it)

        return (left, right)
    def _reduce_left_by_single_case_sum(self, left, right_c):
        #print(f"right_c = {right_c}")
        for i,v in enumerate(right_c):
            #if isinstance(v, AbsVal) and v.unknown is None:
            #    const = v.const
            #print(f"i={i}, v={v}")
            match v:
                case AbsVal(unknown=None, const=const):
                    #print(f"entered case! const={const}")
                    #print(f"left before = {left}")
                    left = self.left.transform(
                        ASTS.Assume(ASTS.VarConsEq(ASTS.Var("",i), const)),
                        left)
                    #print(f"left after = {left}")
        return left

    def reduce_right(self, x):
        left, right = x
        possible_by_left = (lambda c:
                        self._single_sum_case_is_possible_by_left(left, c))
        right = set(filter(possible_by_left, right))
        return (left, right)

    def _single_sum_case_is_possible_by_left(self, left, right_c):
        return self._reduce_left_by_single_case_sum(left, right_c).size!=0



    def reduce(self, x):
        MAX_REDUCTIONS = 100
        for _ in range(MAX_REDUCTIONS):
            x_old = x
            x = self.reduce_left(x)
            x = self.reduce_right(x)
            if self.equiv(x_old, x):
                return x
        assert False, "Exceeded the max reduction cap {MAX_REDUCTIONS}"

    def transform(self, ast, x):
        x = super().transform(ast, x)
        #left_old, right_old = x
        x = self.reduce(x)
        #left, right = x
        #if not self.left.equiv(left_old, left):
        #    print(f"left before: {left_old}")
        #    print(f"left after: {left}")
        return x

    def stabilize(self, x):
        x = super().stabilize(x)
        x = self.reduce(x)
        return x

class CombinedAnalysisLeftReductive(CombinedAnalysisReductive):
    def reduce_right(self, x):
        return x

class CombinedAnalysisRightReductive(CombinedAnalysisReductive):
    def reduce_left(self, x):
        return x

def _main():
    import sys
    method_names = {
        CombinedAnalysisReductive: ["full", "reductive", "fullreductive", "both", "twosidereduction", "fullreduction"],
        CombinedAnalysisRightReductive: ["right", "rightreductive", "leftreduction", "parityreduction"],
        CombinedAnalysisLeftReductive: ["left", "leftreductive", "rightreduction", "sumreduction"],
        CombinedAnalysis : ["basic", "trivial", "cartezian", "noreduction"],
    }
    method_map = {name:method for method,names in method_names.items() for name in names}
    method = CombinedAnalysisReductive # default
    NAME_PARAMETER_INDEX = 2
    if len(sys.argv)>=NAME_PARAMETER_INDEX + 1:
        name = sys.argv[NAME_PARAMETER_INDEX].lower()
        assert name in method_map, f'Unrecognized method name "{name}"'
        method = method_map[name]
    run_analysis(method)
    #from numpy import array
    #abs_0 = AbsVal(const=0)
    #abs_1 = AbsVal(const=1)
    #abs_0_unknown = AbsVal(0, 0)
    #right = {(abs_0, abs_1, abs_1), (abs_0_unknown, abs_1, abs_1)}
    #left = array([[False, False, True, True], [False, True, False ,True], [False, False, False, False]])
    #analysis = CombinedAnalysisReductive(3)
    #reduced = analysis.reduce_left((left,right))
    #print(f"reduced:\n{reduced}")

if __name__ == "__main__":
    _main()
