#!/usr/bin/env python3
import tokenizer
from tokenizer import TokenKind, Op
import ast_nodes as ASTS
from typing import Dict, Optional, Union #, Literal


MAX_CHAIN_LEN = 10
class ParserEOF(object):
    pass

class LabeledCommand(object):
    def __init__(self, command_ast, start_l, end_l):
        self.ast = command_ast
        self.labels = (start_l, end_l)

    def __str__(self):
        return f"{self.labels}: {self.ast}"

EOF = ParserEOF()

class Parser:

    def _with_trailing_advance(method):
        def wrapped(self, *args, **kwargs):
            ret = method(self, *args, **kwargs)
            self._next_token()
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
        assert self._var_id_map == None, "Var name to id map already initialized"
        self._var_id_map = {}
        i = 0
        while self._tkind() == TokenKind.VARIABLE:
            self._var_id_map[self._token.name]=i
            i+=1
            self._next_token()

    def parse_labeled_command(self) -> Union[ASTS.SyntaxNode, type(EOF)]:
        """Parse a single command and return syntax-tree-node.
        If no command (EOF) return EOF."""
        if self._tkind() == TokenKind.EOF:
            return EOF
        start_label = self._parse_label()
        command_ast = self._parse_command()
        end_label = self._parse_label()
        return LabeledCommand(command_ast, start_label, end_label)

    def _parse_command(self):
        kind = self._tkind()
        if kind == TokenKind.SKIP:
            return self._parse_skip()
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
        assert self._tkind() == TokenKind.VARIABLE
        dest = self._parse_var()
        assert self._token.op == Op.ASSIGN
        self._next_token()
        kind = self._tkind()
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
                if op == Op.PLUS:
                    print(f"token: {self._token}")
                    return ASTS.IncAsssignment(dest, src)
                elif op == Op.MINUS:
                    return ASTS.DecAssignment(dest, src)
            else:
                print(f"token: {self._token}")
                return ASTS.VarAssignment(dest, src)


        assert False, "Exhausted cases"

    @_with_trailing_advance
    def _parse_label(self) -> int:
        #self._expect_cur_token(TokenKind.LABEL)
        assert self._tkind() == TokenKind.LABEL
        return self._token.ind

    @_with_trailing_advance
    def _parse_skip(self) -> ASTS.Skip:
        return ASTS.Skip()

    def _parse_assume(self) -> ASTS.Assume:
        assert self._tkind() == TokenKind.ASSUME
        self._next_token()
        with_parens = False
        if (self._tkind() == TokenKind.OPERATOR and
            self._token.op == Op.LPAREN):
            with_parens = True
            self._next_token()
        ret = ASTS.Assume(self._parse_bool_expr())
        if with_parens:
            assert (self._tkind() == TokenKind.OPERATOR and
                    self._token.op == Op.RPAREN)
            self._next_token()
        return ret

    def _parse_assert(self) -> ASTS.Assert:
        assert self._tkind() == TokenKind.ASSERT
        self._next_token()
        return ASTS.Assert(self._parse_orc())

    def _parse_orc(self) -> ASTS.OrChain:
        andc_l = []
        for _ in range(MAX_CHAIN_LEN):
            andc_l.append(self._parse_andc())
            if (self._tkind() == TokenKind.OPERATOR and
                self._token.op == Op.LPAREN):
                continue
            return ASTS.OrChain(andc_l)
        assert False, "Chain too long"
            
    @_with_trailing_advance
    def _parse_andc(self) -> ASTS.AndChain:
        assert self._token.op == Op.LPAREN
        self._next_token()
        bexpr_l = []
        for _ in range(MAX_CHAIN_LEN):
            bexpr_l.append(self._parse_bool_expr())
            if (self._tkind() == TokenKind.OPERATOR and
                self._token.op == Op.RPAREN):
                return ASTS.AndChain(bexpr_l)
        assert False, "Chain too long"


    def _parse_bool_expr(self) -> ASTS.BoolExpr:
        kind = self._tkind()
        if kind == TokenKind.TRUE:
            self._next_token()
            return ASTS.ExprTrue
        elif kind == TokenKind.FALSE:
            self._next_token()
            return ASTS.ExprFalse
        var1 = self._parse_var()
        assert self._tkind() == TokenKind.OPERATOR
        op = self._token.op
        assert op in (Op.EQUAL, Op.NEQUAL)
        is_eq = (op == Op.EQUAL)
        self._next_token()
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


def _main():
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    p.parse_var_list()
    i=1
    while True:
        c = p.parse_labeled_command()
        print(f"{i}. {c}")
        i+=1
        if c==EOF:
            break

if __name__ == "__main__":
    _main()
