#!/usr/bin/env python3
class SyntaxNode(object):
    """base class for all syntax-tree nodes"""
    def __init__(self, table_name):
        self.table_name = table_name

    def __iter__(self):
        attributes = [a for a in dir(self) if not a.startswith('__') and not callable(getattr(self,a))]
        for attr in attributes:
            yield attr, getattr(self, attr)

    def __str__(self):
        res = ""
        for (attr, value) in self:
            res += f"{attr}: {value}\n"
        return res

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
    def __init__(self, bool_expr_list: list[BoolExpr]):
        self.bool_expr_list = bool_expr_list

class OrChain(SyntaxNode):
    def __init__(self, andc_list: list[AndChain]):
        self.andc_list = andc_list

class Command(SyntaxNode):
    pass

class Skip(Command):
    pass

class Assume(Command):
    def __init__(self, expr: BoolExpr):
        this.expr = expr

class Assert(Command):
    def __init__(self, orc: OrChain):
        this.orc = orc

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

