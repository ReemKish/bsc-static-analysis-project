#!/usr/bin/env python3

from abc import ABC, abstractmethod
import ast_nodes as ASTS
from typing import Dict, Optional, Union, Iterable, List #, Literal

class BaseAnalysis(ABC):
    @abstractmethod
    def __init__(self, num_vars):
        self.n = num_vars

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

    def equiv(self, x, y):
        """
        Returns true iff x and y represent the same abstract lattice element
        """
        pass

    def transform(self, ast: ASTS.SyntaxNode, x):
        """
        Transforms the lattice element x according to the abstract syntax tree given in ast
        """
        pass

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
