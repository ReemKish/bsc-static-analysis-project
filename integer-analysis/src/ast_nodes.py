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

class BaseVarTest(BoolExpr):
    def __init__(self, var: Var):
        self.var = var

class TestEven(BaseVarTest):
    pass

class TestOdd(BaseVarTest):
    pass

class BaseComp(BoolExpr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class BaseVarComp(BoolExpr):
    def __init__(self, lhs: Var, rhs: Var):
        BaseComp.__init__(self, lhs,rhs)

class VarEq(BaseVarComp):
    pass

class VarNeq(BaseVarComp):
    pass

class BaseVarConsComp(BaseComp):
    def __init__(self, lhs: Var, rhs: int):
        BaseComp.__init__(self, lhs,rhs)

class VarConsEq(BaseVarConsComp):
    pass

class VarConsNeq(BaseVarConsComp):
    pass

class SumExpr(SyntaxNode):
    def __init__(self, var_list: List[Var]):
        self.var_list = var_list

class SumEq(BaseComp):
    def __init__(self, lhs: SumExpr, rhs: SumExpr):
        BaseComp.__init__(self, lhs,rhs)

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

