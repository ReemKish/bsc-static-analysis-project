# ===== tokenizer.py ======================================
# Converts raw text into a list of tokens.
# Exposes API for tokenization.
# When run directly, receives program filename from commandline and prints its tokenization.

from typing import *
from enum import Enum

# =========================================================
#      Token kind and operation enums
# =========================================================

class TokenKind(Enum):
    # Simple tokens:
    EOF      = 0
    SKIP     = 1
    ASSUME   = 2
    ASSERT   = 3
    INPUT    = 4
    # Tokens with stored data:
    BOOLEAN  = 5
    LABEL    = 6
    VARIABLE = 7
    INTEGER  = 8
    OPERATOR = 9

class Op(Enum):
    ASSIGN   = 0  # :=
    PLUS     = 1  # +
    MINUS    = 2  # -
    EQUAL    = 3  # =
    NEQUAL   = 4  # !=
    LPAREN   = 5  # (
    RPAREN   = 6  # )


# =========================================================
#      Token classes
# =========================================================

# ----- Generic Token ------------
class Token:
    def __init__(self, kind : TokenKind):
        self.kind = kind

    def __str__(self):
        return f"{self.kind._name_}"
    
    def __repr__(self):
        return str(self)

# ----- Label Token --------------
class LabelTok(Token):
    def __init__(self, ind : int):
        Token.__init__(self, TokenKind.LABEL)
        self.ind : int = ind
    __str__ = lambda self: f"Label[{self.ind}]"

# ----- Variable Token -----------
class VarTok(Token):
    def __init__(self, name : str):
        Token.__init__(self, TokenKind.VARIABLE)
        self.name : str = name
    __str__ = lambda self: f"Var[{self.name}]"

# ----- Integer Token ------------
class IntTok(Token):
    def __init__(self, val : int):
        Token.__init__(self, TokenKind.INTEGER)
        self.val : int = val
    __str__ = lambda self: f"Int[{self.val}]"

# ----- Operator Token -----------
class OpTok(Token):
    def __init__(self, op : Op):
        Token.__init__(self, TokenKind.OPERATOR)
        self.op : Op = op
    __str__ = lambda self: f"Op[{self.op._name_}]"

# ----- Boolean Token ------------
class BoolTok(Token):
    def __init__(self, val : bool):
        Token.__init__(self, TokenKind.BOOLEAN)
        self.val : bool = val
    __str__ = lambda self: f"Bool[{self.val}]"


# =========================================================
#      Tokenizer class
# =========================================================

class Tokenizer:
    _reserved_words = {
        'skip'  : TokenKind.SKIP,
        'assume': TokenKind.ASSUME,
        'assert': TokenKind.ASSERT,
        'TRUE'  : True,
        'FALSE' : False,
    }

    _operators = {
        ':=': Op.ASSIGN,
        '+' : Op.PLUS,
        '-' : Op.MINUS,
        '=' : Op.EQUAL,
        '!=': Op.NEQUAL,
        '(' : Op.LPAREN,
        ')' : Op.RPAREN,
    }

    def __init__(self, text : str):
        self.text : str = text
        self._len : int = len(text)
        self._pos : int = 0
        self._tokens : List[Token] = []

    def next_token(self) -> Token:
        self._skip_whitespace()
        if not self._eof() and self._cur() == '#':  # comment - skip line
            self._skip_till_eoline()
            self._skip_whitespace()
        if self._eof():
            tok = Token(TokenKind.EOF)
        elif self._cur() == 'L':  # label (e.g. "L13")
            self._next_char()
            ind = self._next_lit_numeric()
            tok = LabelTok(ind)
        elif self._cur() == '?':  # arbitrary value (input)
            self._next_char()
            tok = Token(TokenKind.INPUT)
        elif self._cur().isalpha():  # a variable name or a reserved word
            tok = self._next_alpha()
        elif self._cur().isdigit():  # an integer
            val = self._next_lit_numeric()
            tok = IntTok(val)
        else:  # an operator
            op = self._next_operator()
            tok = OpTok(op)
        self._tokens.append(tok)
        return tok

    def _next_alpha(self) -> Token:
        identifer = self._next_lit_string()
        if self._is_reserved_word(identifer):
            val = Tokenizer._reserved_words[identifer]
            if identifer == "TRUE" or identifer == "FALSE":
                return BoolTok(val)
            return Token(val)
        return VarTok(identifer)

    def _next_lit_numeric(self) -> int:
        i = self._pos
        while not self._eof() and self._cur().isdigit():
            self._next_char()
        j = self._pos
        return int(self.text[i:j])

    def _next_lit_string(self) -> str:
        i = self._pos
        while not self._eof() and self._cur().isalpha():
            self._next_char()
        j = self._pos
        return self.text[i:j]

    def _next_operator(self) -> Op:
        for op in Tokenizer._operators:
            if self.text[self._pos:].startswith(op):
                self._pos += len(op)
                return Tokenizer._operators[op]


    def _skip_whitespace(self) -> None:
        while not self._eof() and self._cur().isspace():
            self._next_char()

    def _skip_till_eoline(self) -> None:
        while not self._eof():
            c = self._cur()
            self._next_char()
            if c == "\n":
                break

    def _next_char(self) -> None:
        self._pos += 1

    def _cur(self) -> str:
        return self.text[self._pos]

    def _eof(self) -> bool:
        return self._pos >= self._len

    def _is_reserved_word(self, w) -> bool:
        return w in Tokenizer._reserved_words

    @property
    def tokens(self) -> List[Token]:
        if self._eof():
            return self._tokens
        while not self._eof():
            self.next_token()
        return self._tokens
        

# =========================================================
#      Print program tokenization
# =========================================================

def _print_tokens(tokens):
    newline = False
    for tok in tokens:
        if tok.kind is TokenKind.LABEL:
            newline = not newline
            if newline: print()
        print(tok, end=" ")
    print("\n")

def _main():
    from sys import argv
    fname = argv[1]
    with open(fname, 'r') as f:
        text = f.read()
    tokens = Tokenizer(text).tokens
    _print_tokens(tokens)


if __name__ == "__main__":
    _main()

