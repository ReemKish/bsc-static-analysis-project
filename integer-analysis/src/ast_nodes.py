#!/usr/bin/env python3

from typing import List


class SyntaxNode(object):
    """base class for all syntax-tree nodes"""
    def _attributes(self):
        attributes = (a for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a)))
        for attr in attributes:
            yield attr, getattr(self, attr)

    def __repr__(self):
        attrs = ", ".join(f"{n}: {v}" for n, v in self._attributes())
        return  f"{self.__class__.__name__} {{{attrs}}}"

class Var(SyntaxNode):
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

class BoolExpr(SyntaxNode):
    pass

class ExprFalse(BoolExpr):
    pass

class ExprTrue(BoolExpr):
    pass


class BaseVarComp(BoolExpr):
    def __init__(self, var1: Var, var2: Var):
        self.var1 = var1
        self.var2 = var2

class VarEq(BaseVarComp):
    pass

class VarNeq(BaseVarComp):
    pass

class BaseVarConsComp(BoolExpr):
    def __init__(self, var: Var, cons: int):
        self.var = var
        self.cons = cons

class VarConsEq(BaseVarConsComp):
    pass

class VarConsNeq(BaseVarConsComp):
    pass

class AndChain(SyntaxNode):
    def __init__(self, bool_expr_list: List[BoolExpr]):
        self.bool_expr_list = bool_expr_list

class OrChain(SyntaxNode):
    def __init__(self, andc_list: List[AndChain]):
        self.andc_list = andc_list

    def __str__(self):
        return (  self.__class__.__name__ + "\n\t"
                + "\n\t".join(map(repr,self.andc_list))
               )

class Command(SyntaxNode):
    pass

class Skip(Command):
    pass

class Assume(Command):
    def __init__(self, expr: BoolExpr):
        self.expr = expr

class Assert(Command):
    def __init__(self, orc: OrChain):
        self.orc = orc

class Assignment(Command):
    def __init__(self, dest , src):
        self.dest = dest
        self.src = src

class ConstAssignment(Assignment):
    def __init__(self, dest: Var, src: int):
        Assignment.__init__(self, dest, src)

class UnknownAssigment(Assignment):
    def __init__(self, dest: Var):
        Assignment.__init__(self, dest, None)

class BaseVarAssignment(Assignment):
    def __init__(self, dest: Var, src: Var):
        Assignment.__init__(self, dest, src)

class VarAssignment(BaseVarAssignment):
    pass

class DecAssignment(BaseVarAssignment):
    pass

class IncAsssignment(BaseVarAssignment):
    pass

