#!/usr/bin/env python3

from abc import ABC, abstractmethod
import ast_nodes as ASTS
from typing import Dict, Optional, Union, Iterable, List

class BaseAnalysis(ABC):
    @abstractmethod
    def __init__(self, num_vars):
        self.num_vars = num_vars

    @abstractmethod
    def bottom(self):
        pass

    @abstractmethod
    def top(self):
        pass

    @abstractmethod
    def join(self, l: Iterable):
        """
        Returns the join of the lattice elements in the iterable l.
        """
        pass

    @abstractmethod
    def equiv(self, x, y):
        """
        Returns true iff x and y represent the same abstract lattice element
        """
        pass

    @abstractmethod
    def verify_assertion(ass: ASTS.Assert, x) -> bool:
        """
        Returns True if and only if the assertion is completely proven
        according to the analysis information (the abstract lattice element).
        """

    @abstractmethod
    def transform_nontrivial(self, ast: ASTS.SyntaxNode, x):
        """
        Transforms the lattice element x according to the abstract syntax
        tree given in ast, with the assumption that ast is not an ast of
        a trivial transformation (see cases in transform_trivial for the
        list of trivial ones).
        """
        pass

    def transform_trivial(self, ast: ASTS.SyntaxNode, x):
        match ast:
            case ASTS.Skip():
                return x
            case ASTS.Assume(expr=expr):
                match expr:
                    case ASTS.ExprTrue:
                        return x
                    case ASTS.ExprFalse():
                        return self.bottom()
            case _:
                return None

    def transform(self, ast: ASTS.SyntaxNode, x):
        """
        Transforms the lattice element x according to the abstract syntax
        tree given in ast.
        """
        ret = self.transform_trivial(ast,x)
        if ret is not None:
            return ret
        return self.transform_nontrivial(ast,x)

    def stabilize(self, x):
        """
        "Stabilizes" the lattice value of x:
        This operation converts x into an object that does not get mutated
        by any of the other analysis methods (which are present in this
        class). By default, it is assumed that values are already always
        stable, if that isn't the case this method should be overwritten
        accordingally.
        """
        return x
