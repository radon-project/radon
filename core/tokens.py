from __future__ import annotations

import string
import pathlib

from typing import Optional, NewType, TypeAlias
from dataclasses import dataclass


# STANDARD LIBRARIES
BASE_DIR = pathlib.Path(__file__).parent.parent
CURRENT_DIR: Optional[str] = None

STDLIBS = [
    "Argparser",
    "Array",
    "Colorlib",
    "Math",
    "System",
    "String",
    "Universe",  # ester egg
    "Winlib",
]


# CONSTANTS
DIGITS = string.digits
LETTERS = string.ascii_letters + "$_"
VALID_IDENTIFIERS = LETTERS + DIGITS

@dataclass
class Position:
    """Cursor Position"""
    idx: int
    ln: int
    col: int
    fn: str
    ftxt: str

    def __str__(self) -> str:
        return f"{self.fn}:{self.ln}:{self.col}"

    def advance(self, current_char: Optional[str] = None) -> Position:
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self) -> Position:
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


# TOKENS
TokenType = NewType("TokenType", str)

TT_INT = TokenType("INT")  # 123456
TT_FLOAT = TokenType("FLOAT")  # 5.5
TT_STRING = TokenType("STRING")  # "Hello World"
TT_IDENTIFIER = TokenType("IDENTIFIER")  # var_name
TT_KEYWORD = TokenType("KEYWORD")  # var, if, for, while, fun
TT_PLUS = TokenType("PLUS")  # Plus
TT_MINUS = TokenType("MINUS")  # Minus
TT_MUL = TokenType("MUL")  # Times
TT_DIV = TokenType("DIV")  # Divide
TT_POW = TokenType("POW")  # Power
TT_MOD = TokenType("MOD")  # Modulo
TT_EQ = TokenType("EQ")  # Equal
TT_LPAREN = TokenType("LPAREN")  # (
TT_RPAREN = TokenType("RPAREN")  # )
TT_LBRACE = TokenType("LBRACE")  # {
TT_RBRACE = TokenType("RBRACE")  # }
TT_LSQUARE = TokenType("LSQUARE")  # [
TT_RSQUARE = TokenType("RSQUARE")  # ]
TT_EE = TokenType("EE")  # Equal Equal
TT_NE = TokenType("NE")  # Not Equal
TT_LT = TokenType("LT")  # Less Than
TT_GT = TokenType("GT")  # Greater Than
TT_LTE = TokenType("LTE")  # Less Than or Equal
TT_GTE = TokenType("GTE")  # Greater Than or Equal
TT_PE = TokenType("PE")  # Plus Equal
TT_ME = TokenType("ME")  # Minus Equal
TT_TE = TokenType("TE")  # Times Equal
TT_DE = TokenType("DE")  # Divide Equal
TT_IDIV = TokenType("IDIV")  # Int Divide
TT_MDE = TokenType("MDE")  # Modulo Divide Equal
TT_POWE = TokenType("POWE")  # Power Equal
TT_IDE = TokenType("IDE")  # Int Divide Equal
TT_COMMA = TokenType("COMMA")  # ,
TT_COLON = TokenType("COLON")  # :
TT_ARROW = TokenType("ARROW")  # ->
TT_NEWLINE = TokenType("NEWLINE")  # \n
TT_DOT = TokenType("DOT")  # .
TT_EOF = TokenType("EOF")  # End Of File
TT_SLICE = TokenType("SLICE")  # x[1:2:3]
TT_PLUS_PLUS = TokenType("PLUS_PLUS")  # ++
TT_MINUS_MINUS = TokenType("MINUS_MINUS")  # --

KEYWORDS = [
    "and",
    "or",
    "not",
    "if",
    "elif",
    "else",
    "for",
    "to",
    "step",
    "while",
    "fun",
    "return",
    "continue",
    "break",
    "class",
    "include",
    "try",
    "catch",
    "as",
    "in",
    "nonlocal",
    "global",
    "const",
    "static",
    "assert",
    "switch",
    "case",
    "default",
    "fallthrough",
]

TokenValue: TypeAlias = Optional[str | int | float]

class Token:
    __match_args__ = "type", "value"

    type: TokenType
    value: TokenValue
    pos_start: Position
    pos_end: Position

    def __init__(self, type_: TokenType, value: TokenValue = None, *, pos_start: Position, pos_end: Optional[Position] = None) -> None:
        self.type = type_
        self.value = value

        self.pos_start = pos_start
        self.pos_end = pos_end if pos_end is not None else pos_start

    def matches(self, type_: TokenType, value: TokenValue) -> bool:
        return self.type == type_ and self.value == value

    def __repr__(self) -> str:
        if self.value != None:
            return f"{self.type}:{self.value}"
        return f"{self.type}"

