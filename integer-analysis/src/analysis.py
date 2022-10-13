#!/usr/bin/env python3

from abc import ABC, abstractmethod
import ast_nodes as ASTS

class BaseAnalysis(ABC):
    def __init__(self, lat):
        self.lat = lat

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
                    case ASTS.ExprTrue():
                        return x
                    case ASTS.ExprFalse():
                        return self.bot()
            case _:
                return None

    def transform(self, ast: ASTS.SyntaxNode, x):
        """
        Transforms the lattice element x according to the abstract syntax
        tree given in ast.
        """
        ret = self.transform_trivial(ast,x)
        return self.transform_nontrivial(ast,x) if ret is None else ret

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
