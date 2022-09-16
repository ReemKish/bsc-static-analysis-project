#!/usr/bin/env python3

from enum import Enum
import ast_nodes as ASTS

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

class PADumb:
    def __init__(self, num_vars):
        self.n = num_vars
    def bottom(self):
        return [ PState.BOTTOM ] * n
    def top(self):
        return [ PState.TOP ] * n
    def join(self, x, y):
        return map(join, zip(x,y))
    def equiv(self, x, y):
        return all(a==b for a,b in zip(x,y))

    def transform(self, ast, x):
        if isinstance(ast, ASTS.ConstAssignment):
            ret = list(x)
            ret[ast.dest.id] = PState.EVEN if ast.src%2==0 else PState.ODD
            return ret
        else:
            return x
