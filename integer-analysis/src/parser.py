#!/usr/bin/env python3
import tokenizer
from tokenizer import TokenKind, Op
import ast_nodes as ASTS
from typing import Dict, Optional, Union, Iterable, List #, Literal
import networkx as nx


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
        self._next_token()
        self._unknown_id = 0

        if varname_to_id_map is not None:
            self._var_id_map = varname_to_id_map
        else:
            self._var_id_map = self._parse_var_dec()


    def _get_unknown_id(self) -> int:
        return self._unknown_id

    def _inc_unknown_id(self) -> None:
        self._unknown_id += 1

    def _tkind(self):
        return self._token.kind

    def _next_token(self):
        self._token = self._tokenizer.next_token()

    def _parse_var_dec(self) -> Dict[str, int]:
        ret = {}
        i = 0
        while self._tkind() == TokenKind.VARIABLE:
            ret[self._token.name]=i
            i+=1
            self._next_token()
        return ret

    def parse_labeled_command(self) -> Union[LabeledCommand, type(EOF)]:
        """
        Parse a single command and return a LabeledCommand object,
        containing the command labels and its AST.
        If no command (EOF) return EOF.
        """
        assert self._var_id_map is not None, "Parser variables not initialized"

        if self._tkind() == TokenKind.EOF:
            return EOF
        start_label = self._parse_label()
        command_ast = self._parse_command()
        end_label = self._parse_label()
        return LabeledCommand(command_ast, start_label, end_label)

    def parse_labeled_commands_iter(self) -> Iterable[LabeledCommand]:
        while True:
            c = self.parse_labeled_command()
            if c == EOF:
                return
            yield c

    def parse_complete_program(self, display=False) -> (nx.DiGraph, int):
        num_vars = len(self._var_id_map)
        cfg = nx.DiGraph(list((*c.labels, {"ast": c.ast})
                          for c in self.parse_labeled_commands_iter()))
        if display: display_cfg(cfg)
            
        return cfg, num_vars

    def _parse_command(self) -> Union[ASTS.SyntaxNode, type(EOF)]:
        kind = self._tkind()
        if kind == TokenKind.SKIP:
            return self._parse_skip()
        elif kind == TokenKind.ASSUME:
            return self._parse_assume()
        elif kind == TokenKind.ASSERT:
            return self._parse_assert()
        elif kind in (TokenKind.VARIABLE, TokenKind.FIELD):
            return self._parse_assignment()
        assert False, "Exhausted cases"
        #CommandKeywords = [TokenKind.SKIP, TokenKind.ASSERT, TokenKind.ASSUME]
        #self._expect_cur_token(CommandKeywords+[TokenKind.VARIABLE])

    def _parse_assignment(self) -> ASTS.Assignment:
        dest, dest_is_field = self._parse_var_or_field()
        assert self._token.op == Op.ASSIGN, (f"Expected assignment operator, found {self._token} instead")
        self._next_token()
        kind = self._tkind()
        if dest_is_field:
            assert kind == TokenKind.VARIABLE, "Only a variable can be assigned to a field"
        match kind:
            case TokenKind.UNKNOWN | TokenKind.NULL | TokenKind.NEW:
                self._next_token()
                match kind:
                    case TokenKind.NULL:
                        return ASTS.NullAssignment(dest)
                    case TokenKind.NEW:
                        return ASTS.NewAssignment(dest)
                    case TokenKind.UNKNOWN:
                        i = self._get_unknown_id()
                        self._inc_unknown_id()
                        return ASTS.UnknownAssignment(dest , i)
            case TokenKind.INTEGER:
                return ASTS.ConstAssignment(dest, self._parse_integer())
            case TokenKind.VARIABLE | TokenKind.FIELD:
                src, src_is_field = self._parse_var_or_field()
                if (self._tkind() == TokenKind.OPERATOR
                    and self._token.op in (Op.PLUS, Op.MINUS)):
                    assert not src_is_field
                    op = self._token.op
                    self._next_token()
                    num = self._parse_integer()
                    assert (num == 1)
                    if op == Op.PLUS:
                        return ASTS.IncAssignment(dest, src)
                    elif op == Op.MINUS:
                        return ASTS.DecAssignment(dest, src)
                else:
                    match (dest_is_field, src_is_field):
                        case (False, False):
                            return ASTS.VarAssignment(dest, src)
                        case (True, False):
                            return ASTS.IntoFieldAssignment(dest, src)
                        case (False, True):
                            return ASTS.FromFieldAssignment(dest, src)
                        case (True, True):
                            assert False, "Assignment from field into field isn't allowed, use an intermediate variable instead"


        assert False, "Exhausted cases"

    @_with_trailing_advance
    def _parse_label(self) -> int:
        #self._expect_cur_token(TokenKind.LABEL)
        assert self._tkind() == TokenKind.LABEL, f"Expected label, encountered token {self._token}"
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
        pred_l = []
        for _ in range(MAX_CHAIN_LEN):
            pred_l.append(self._parse_predicate())
            if (self._tkind() == TokenKind.OPERATOR and
                self._token.op == Op.RPAREN):
                return ASTS.AndChain(pred_l)
        assert False, "Chain too long"


    def _parse_bool_expr(self) -> ASTS.BoolExpr:
        kind = self._tkind()
        if kind in {TokenKind.TRUE, TokenKind.FALSE}:
            self._next_token()
            if kind == TokenKind.TRUE:
                return ASTS.ExprTrue
            elif kind == TokenKind.FALSE:
                return ASTS.ExprFalse
        return self._parse_comp()

    def _parse_comp(self) -> ASTS.BaseComp:
        lhs = self._parse_var()

        op = self._next_op()
        assert op in (Op.EQUAL, Op.NEQUAL)
        is_eq = (op == Op.EQUAL)

        if self._tkind() == TokenKind.INTEGER:
            rhs = self._parse_integer()
            if is_eq:
                return ASTS.VarConsEq(lhs, rhs)
            else:
                return ASTS.VarConsNeq(lhs, rhs)
        else:
            if self._tkind() == TokenKind.NULL:
                self._next_token()
                if is_eq:
                    return ASTS.VarEqNull(lhs)
                else:
                    return ASTS.VarNeqNull(lhs)
            rhs, is_field = self._parse_var_or_field()
            if is_field:
                if is_eq:
                    return ASTS.VarEqField(lhs, rhs)
                else:
                    return ASTS.VarNeqField(lhs, rhs)
            else:
                if is_eq:
                    return ASTS.VarEq(lhs, rhs)
                else:
                    return ASTS.VarNeq(lhs, rhs)

    @_with_trailing_advance
    def _next_op(self) -> Op:
        assert self._tkind() == TokenKind.OPERATOR
        return self._token.op

    def _parse_predicate(self) -> ASTS.Predicate:
        kind = self._tkind()
        if kind in (TokenKind.EVEN, TokenKind.ODD):
            return self._parse_parity_bexpr()
        elif kind in (TokenKind.LS, TokenKind.NOLS):
           return self._parse_keyword_operand()
        elif kind == TokenKind.SUM:
            return self._parse_sum_comp()
        elif kind == TokenKind.VARIABLE:
            return self._parse_comp()
        assert False, f"Exhausted options, encountered token {self._token}"

    def _parse_keyword_operand(self) -> ASTS.BaseVarComp:
        op_map = {TokenKind.LS: ASTS.LS, TokenKind.NOLS: ASTS.NOLS}
        kind = self._tkind()
        assert kind in op_map
        self._next_token()
        lhs = self._parse_var()
        rhs = self._parse_var()
        return op_map[kind](lhs, rhs)


    def _parse_parity_bexpr(self) -> ASTS.BaseVarTest | ASTS.BaseVarComp:
        kind = self._tkind()
        assert kind in {TokenKind.EVEN, TokenKind.ODD}
        self._next_token()
        var = self._parse_var()
        if self._tkind() == TokenKind.VARIABLE:
            lhs = var
            rhs = self._parse_var()
            if kind == TokenKind.EVEN:
                return ASTS.EVEN_Path(lhs, rhs)
            elif kind == TokenKind.ODD:
                return ASTS.ODD_Path(lhs, rhs)
        else:
            if kind == TokenKind.EVEN:
                return ASTS.TestEven(var)
            elif kind == TokenKind.ODD:
                return ASTS.TestOdd(var)

    def _parse_sum_comp(self) -> ASTS.SumEq:
        sum1 = self._parse_sum_expr()
        op = self._next_op()
        assert op==Op.EQUAL
        sum2 = self._parse_sum_expr()
        return ASTS.SumEq(sum1, sum2)

    def _parse_sum_expr(self) -> ASTS.SumExpr:
        assert self._tkind() == TokenKind.SUM
        self._next_token()
        assert self._tkind() == TokenKind.VARIABLE, \
                "SUM expression must contain at least one variable"
        return ASTS.SumExpr(self._parse_var_list())

    def _parse_var_list(self) -> List[ASTS.Var]:
        ret = []
        while (self._tkind() == TokenKind.VARIABLE):
            ret.append(self._parse_var())
        return ret

    @_with_trailing_advance
    def _parse_integer(self) -> int:
        assert self._tkind() == TokenKind.INTEGER
        return self._token.val

    def _parse_var(self) -> ASTS.Var:
        assert self._tkind() == TokenKind.VARIABLE
        v,is_field = self._parse_var_or_field()
        assert not is_field
        return v

    @_with_trailing_advance
    def _parse_var_or_field(self) -> (ASTS.Var, bool):
        assert self._tkind() in (TokenKind.VARIABLE, TokenKind.FIELD)
        if self._tkind() == TokenKind.FIELD:
            v_tok = self._token.var
            is_field = True
        else:
            v_tok = self._token
            is_field = False
        name = v_tok.name
        id = self._var_id_map[name]
        return ASTS.Var(name, id), is_field



def display_cfg(cfg):
    import matplotlib.pyplot as plt
    nx.draw(cfg, with_labels = True)
    plt.show()


def _main():
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    p = Parser(text)
    for i, c in enumerate(p.parse_labeled_commands_iter()):
        print(f"{i}. {c}")

    p = Parser(text)
    cfg = p.parse_complete_program()
    #display_cfg(cfg)

if __name__ == "__main__":
    _main()
