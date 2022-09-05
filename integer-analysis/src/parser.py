#!/usr/bin/env python3
import tokenizer
from tokenizer import TokenKind, Op
import ast_nodes as ASTS
from Typing import Dict, Optional, Literal


class ParserEOF(object):
    pass

class LabledCommand(object):
    def __init__(self, command_ast, start_l, end_l):
        self.ast = command_ast
        self.labels = (start_l, end_l)

EOF = ParserEOF()

class Parser:

    def _with_trailing_advance(method):
        def wrapped(self, *args, **kwagrs):
            ret = method(self, *args, **kwargs)
            _next_token(self)
            return ret

        return wrapped


    def __init__(self, text: str,
                 varname_to_id_map: Optional[Dict[str, int]] = None):
        self._text = text
        self._tokenizer = tokenizer.Tokenizer(text)
        self._token = None
        self._var_id_map = varname_to_id_map

        self._next_token()

    def _tkind(self):
        return self._token.kind

    def _next_token(self):
        self._token = self._tokenizer.next_token()

    def parse_var_list(self) -> None:
        assert var_id_map == None, "Var name to id map already initialized"
        self._var_id_map = {}
        i = 0
        while self._tkind() == TokenKind.VARIABLE:
            self._var_id_map[self._token.name]=i
            i+=1
            self._next_token()

    def parse_labeled_command(self) -> Nodes.SyntaxNode | Literal[EOF]:
        """Parse a single command and return syntax-tree-node.
        If no command (EOF) return EOF."""
        if self.tkind() == TokenKind.EOF:
            return EOF
        start_label = self._parse_label()
        command_ast = self._parse_command()
        end_label = self.parse_label()
        return LabeledCommand(command_ast, start_label, end_label)

    def _parse_command(self):
        kind = self.__tkind()
        if kind == TokenKind.SKIP:
            return ASTS.Skip()
        elif kind == TokenKind.ASSUME:
            return self._parse_assume()
        elif kind == TokenKind.ASSERT:
            return self._parse_assert()
        elif kind == TokenKind.VARIABLE:
            return self._parse_assignment()
        assert False, "Exhausted cases"
        #CommandKeywords = [TokenKind.SKIP, TokenKind.ASSERT, TokenKind.ASSUME]
        #self._expect_cur_token(CommandKeywords+[TokenKind.VARIABLE])

    def _parse_assignment(self) -> ASTS.Assignment:
        assert self.tkind() == TokenKind.VARIABLE
        dest = self._parse_var()
        assert self.tkind.op == Op.ASSIGN
        self._next_token()
        kind = self.tkind()
        if kind == TokenKind.UNKNOWN:
            self._next_token()
            return ASTS.UnknownAssigment(dest)
        elif kind == TokenKind.INTEGER:
            return ASTS.ConstAssignment(dest, self._parse_integer())
        elif kind == TokenKind.VARIABLE:
            src = self._parse_var()
            if (self._tkind() == TokenKind.OPERATOR
                and self._token.op in (Op.PLUS, Op.MINUS)):
                op = self._token.op
                self._next_token()
                num = self._parse_integer()
                assert (num == 1)
                self._next_token()
                if op == Op.PLUS:
                    return ASTS.IncAsssignment(dest, src)
                elif op == Op.MINUS:
                    return ASTS.DecAssignment(dest, src)
            else:
                return ASTS.VarAssignment(dest, src)

        assert False, "Exhausted cases"

    @_with_trailing_advance
    def _parse_label(self) -> int:
        #self._expect_cur_token(TokenKind.LABEL)
        assert self.tkind() == TokenKind.LABEL
        return self._token.ind

    def _parse_assume(self) -> ASTS.Assume:
        assert self._tkind() == TokenKind.ASSUME
        self._next_token()
        return ASTS.Assume(self._parse_bool_expr())

    def _parse_assert(self) -> ASTS.Assert:
        assert self._tkind() == TokenKind.ASSERT
        self._next_token()
        return ASTS.Assert(self._parse_orc())

    def _parse_orc(self) -> ASTS.OrChain:
        andc_l = []
        while True:
            andc_l.append(self._parse_andc())
            if not (self._tkind() == TokenKind.OPERATOR and
                    self.token.op == OP.LPAREN):
                return andc_l
            
    @_with_trailing_advance
    def _parse_andc(self) -> ASTS.AndChain:
        assert self._token.op == Op.LPAREN
        self._next_token()
        bexpr_l = []
        while True:
            bexpr_l.append(self._parse_bool_expr())
            if (self._tkind() == TokenKind.OPERATOR and
                self._token.op == OP.RPAREN):
                return bexpr_l


    def _parse_bool_expr(self) -> ASTS.BoolExpr:
        kind = self._tkind()
        if kind == TokenKind.TRUE:
            return ASTS.ExprTrue
        elif kind == TokenKind.FALSE:
            return ASTS.ExprFalse
        var1 = self._parse_var()
        assert self._tkind() == TokenKind.OPERATOR
        op = self._token.op
        assert op in (Op.EQUAL, Op.NEQUAL)
        is_eq = (op == Op.EQUAL)
        self.next_token()
        if self._tkind() == TokenKind.INTEGER:
            cons = self._parse_integer()
            if is_eq:
                return ASTS.VarConsEq(var1, cons)
            else:
                return ASTS.VarConsNeq(var1, cons)
        else:
            var2 = self._parse_var()
            if is_eq:
                return ASTS.VarEq(var1, var2)
            else:
                return ASTS.VarNeq(var1, var2)


    @_with_trailing_advance
    def _parse_integer(self) -> int:
        assert self._tkind() == TokenKind.INTEGER
        return self._token.val

    @_with_trailing_advance
    def _parse_var(self) -> ASTS.Var:
        assert self._tkind() == TokenKind.VARIABLE
        name = self._token.name
        id = self._var_id_map[name]
        return ASTS.Var(name, id)
