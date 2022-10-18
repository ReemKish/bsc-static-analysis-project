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

# ===============================================
#      Var
# ===============================================
class Var(SyntaxNode):
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id

    __str__ = lambda self: self.name


# ===============================================
#      SumExpr
# ===============================================
class SumExpr(SyntaxNode):
    def __init__(self, var_list: List[Var]):
        self.var_list = var_list

    __str__ = lambda self: "SUM " + ' '.join(map(str, self.var_list))


# ===============================================
#      BoolExpr
# ===============================================
class BoolExpr(SyntaxNode):
    """
    Base class for boolean expressions used in assume statements.
    """

class Predicate(SyntaxNode):
    """
    Base class for boolean predicates used in assert statements.
    """

    pass

class ExprFalse(BoolExpr): pass

class ExprTrue(BoolExpr): pass

# BaseComp
# ---------------------------
class BaseComp(BoolExpr):
    def __init__(self, lhs: Var, rhs):
        self.lhs = lhs
        self.rhs = rhs

# BaseVarComp
class BaseVarComp(BaseComp, Predicate):
    def __init__(self, lhs: Var, rhs: Var):
        BaseComp.__init__(self, lhs, rhs)
class VarEq(BaseVarComp): pass
class VarNeq(BaseVarComp): pass

# BaseVarConsComp
class BaseVarConsComp(BaseComp):
    def __init__(self, lhs: Var, rhs: int):
        BaseComp.__init__(self, lhs,rhs)
class VarConsEq(BaseVarConsComp): pass
class VarConsNeq(BaseVarConsComp): pass

# BaseVarTest
# ---------------------------


class BaseVarTest(Predicate):
    def __init__(self, var: Var):
        self.var = var

class TestEven(BaseVarTest):
    __str__ = lambda self: 'EVEN ' + str(self.var) 

class TestOdd(BaseVarTest):
    __str__ = lambda self: 'ODD ' + str(self.var) 


# SumEq
class SumEq(Predicate):
    def __init__(self, lhs: SumExpr, rhs: SumExpr):
        self.lhs = lhs
        self.rhs = rhs

    __str__ = lambda self: f"{self.lhs} = {self.rhs}"


# ===============================================
#      AndChain
# ===============================================
class AndChain(SyntaxNode):
    def __init__(self, pred_list: List[Predicate]):
        self.pred_list = pred_list

    __str__ = lambda self: ' '.join(map(str, self.pred_list))


# ===============================================
#      OrChain
# ===============================================
class OrChain(SyntaxNode):
    def __init__(self, andc_list: List[AndChain]):
        self.andc_list = andc_list

    def __repr__(self):
        return (  self.__class__.__name__ + "\n\t"
                + "\n\t".join(map(repr,self.andc_list))
               )

    __str__ = lambda self: ' '.join(map(lambda c: f"({c})", self.andc_list))
        



# ===============================================
#      Command
# ===============================================
class Command(SyntaxNode): pass

# Skip
# ---------------------------
class Skip(Command): pass

# Assume
# ---------------------------
class Assume(Command):
    def __init__(self, expr: BoolExpr):
        self.expr = expr

# Assert
# ---------------------------
class Assert(Command):
    def __init__(self, orc: OrChain):
        self.orc = orc

    __str__ = lambda self: 'assert ' + str(self.orc)

# Assignment
# ---------------------------
class Assignment(Command):
    def __init__(self, dest: Var, src):
        self.dest = dest
        self.src = src

# ConstAssignment 
class ConstAssignment(Assignment):
    def __init__(self, dest: Var, src: int):
        Assignment.__init__(self, dest, src)

# UnknownAssignment 
class UnknownAssignment(Assignment):
    def __init__(self, dest: Var, src: int):
        # src is an identifier for the specific unknown in this case
        Assignment.__init__(self, dest, src)

# BaseVarAssignment 
class BaseVarAssignment(Assignment):
    def __init__(self, dest: Var, src: Var):
        Assignment.__init__(self, dest, src)
class VarAssignment(BaseVarAssignment): pass
class StepAssignment(BaseVarAssignment): pass
class DecAssignment(StepAssignment): pass
class IncAssignment(StepAssignment): pass



# Shape analysis
class NoSrcAssignment(Assignment):
    def __init__(self, dest: Var):
        Assignment.__init__(self, dest, None)

class NullAssignment(NoSrcAssignment): pass
class NewAssignment(NoSrcAssignment): pass

class FromFieldAssignment(BaseVarAssignment): pass
class IntoFieldAssignment(BaseVarAssignment): pass

class NoRhsComp(BaseComp):
    def __init__(self, lhs: Var):
        BaseComp.__init__(self, lhs, None)
        self.var = lhs # Another alias

class VarEqNull(NoRhsComp): pass
class VarNeqNull(NoRhsComp): pass

class VarEqField(BaseVarComp): pass
class VarNeqField(BaseVarComp): pass
class LS(BaseVarComp): pass
class NOLS(BaseVarComp): pass
class ODD_Path(BaseVarComp): pass
class EVEN_Path(BaseVarComp): pass

