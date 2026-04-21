"""
Syntax highlighting for the Radon REPL.

Uses the existing Lexer to tokenize a source line and maps each token
back to its character span in the original text, wrapping it in the
matching SyntaxColor ANSI escape.  Gaps (whitespace) and comments are
handled separately so the reconstructed string is always identical to
the input when the ANSI codes are stripped.
"""

from __future__ import annotations

from core.colortools import ForegroundColor, Style, SyntaxColor
from core.lexer import Lexer
from core.tokens import (
    TT_EOF,
    TT_FLOAT,
    TT_IDENTIFIER,
    TT_INT,
    TT_KEYWORD,
    TT_NEWLINE,
    TT_STRING,
    TT_LPAREN,
    TT_RPAREN,
    TT_LBRACE,
    TT_RBRACE,
    TT_LSQUARE,
    TT_RSQUARE,
    TT_COMMA,
    TT_COLON,
    TT_DOT,
    TT_PLUS,
    TT_MINUS,
    TT_MUL,
    TT_DIV,
    TT_MOD,
    TT_POW,
    TT_EQ,
    TT_EE,
    TT_NE,
    TT_LT,
    TT_GT,
    TT_LTE,
    TT_GTE,
    TT_PE,
    TT_ME,
    TT_TE,
    TT_DE,
    TT_IDIV,
    TT_MDE,
    TT_POWE,
    TT_IDE,
    TT_ARROW,
    TT_PLUS_PLUS,
    TT_MINUS_MINUS,
    TT_SPREAD,
    TT_UNPACK,
)

_RESET = Style.CLEAR.value

# Lazily resolved from the live global symbol table so there is no duplication.
# Populated on first call to highlight().
_BUILTINS: frozenset[str] = frozenset()


def _get_builtins() -> frozenset[str]:
    global _BUILTINS
    if not _BUILTINS:
        from core.builtin_funcs import global_symbol_table
        _BUILTINS = frozenset(global_symbol_table.symbols.keys())
    return _BUILTINS

_OPERATOR_TYPES: frozenset[str] = frozenset({
    TT_PLUS, TT_MINUS, TT_MUL, TT_DIV, TT_MOD, TT_POW,
    TT_EQ, TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE,
    TT_PE, TT_ME, TT_TE, TT_DE, TT_IDIV, TT_MDE, TT_POWE, TT_IDE,
    TT_ARROW, TT_PLUS_PLUS, TT_MINUS_MINUS, TT_SPREAD, TT_UNPACK,
})

_PUNCTUATION_TYPES: frozenset[str] = frozenset({
    TT_LPAREN, TT_RPAREN, TT_LBRACE, TT_RBRACE,
    TT_LSQUARE, TT_RSQUARE, TT_COMMA, TT_COLON, TT_DOT,
})


def _color_span(text: str, tok_type: str, tok_value: object, next_tok_type: str) -> str:
    """Return *text* wrapped in the appropriate ANSI escape for this token."""
    if tok_type == TT_KEYWORD:
        return SyntaxColor.keyword(text)
    if tok_type == TT_STRING:
        return SyntaxColor.string(text)
    if tok_type in (TT_INT, TT_FLOAT):
        return SyntaxColor.number(text)
    if tok_type == TT_IDENTIFIER:
        name = str(tok_value) if tok_value is not None else text
        if name in _get_builtins():
            return SyntaxColor.builtin(text)
        if next_tok_type == TT_LPAREN:
            return SyntaxColor.function(text)
        return text  # plain identifier — no color
    if tok_type in _OPERATOR_TYPES:
        return SyntaxColor.operator(text)
    if tok_type in _PUNCTUATION_TYPES:
        return SyntaxColor.punctuation(text)
    # TT_NEWLINE, TT_EOF, unknown → no color
    return text


def highlight(source: str) -> str:
    """
    Return *source* with ANSI syntax-highlight codes inserted.

    If the lexer fails on the input (e.g. mid-line incomplete expression)
    the original source is returned unchanged so the REPL never errors.
    """
    if not source.strip():
        return source

    lexer = Lexer("<highlight>", source)
    tokens, error = lexer.make_tokens()
    if error:
        return source  # fall back to plain text on lex error

    # Build a map: start_idx → (exclusive_end, tok_type, tok_value, next_tok_type)
    #
    # The Lexer sets pos_end inconsistently:
    #   - Single-char tokens (operators, punctuation): pos_end == pos_start
    #   - Multi-char tokens (string, identifier, number): pos_end points to the
    #     first character AFTER the token (exclusive).
    # We normalize to an always-exclusive end so slicing is simply source[start:end].
    span_map: dict[int, tuple[int, str, object, str]] = {}
    for i, tok in enumerate(tokens):
        if tok.type in (TT_NEWLINE, TT_EOF):
            continue
        start = tok.pos_start.idx
        raw_end = tok.pos_end.idx
        # single-char: raw_end == start  → exclusive end is start + 1
        # multi-char:  raw_end >  start  → raw_end is already exclusive
        exclusive_end = raw_end if raw_end > start else start + 1
        next_type = tokens[i + 1].type if i + 1 < len(tokens) else TT_EOF
        span_map[start] = (exclusive_end, tok.type, tok.value, next_type)

    # Find comment spans: '#' not inside a string token
    string_ranges: set[int] = set()
    for tok in tokens:
        if tok.type == TT_STRING:
            raw_end = tok.pos_end.idx
            exclusive_end = raw_end if raw_end > tok.pos_start.idx else tok.pos_start.idx + 1
            for idx in range(tok.pos_start.idx, exclusive_end):
                string_ranges.add(idx)

    comment_ranges: set[int] = set()
    i = 0
    while i < len(source):
        if source[i] == "#" and i not in string_ranges:
            # Color from '#' to end of line
            j = i
            while j < len(source) and source[j] != "\n":
                comment_ranges.add(j)
                j += 1
            i = j
        else:
            i += 1

    # Reconstruct the highlighted source
    out: list[str] = []
    pos = 0
    while pos < len(source):
        if pos in comment_ranges:
            # Collect the full comment run
            end = pos
            while end < len(source) and end in comment_ranges:
                end += 1
            out.append(SyntaxColor.comment(source[pos:end]))
            pos = end
        elif pos in span_map:
            exclusive_end, tok_type, tok_value, next_tok_type = span_map[pos]
            span_text = source[pos:exclusive_end]
            out.append(_color_span(span_text, tok_type, tok_value, next_tok_type))
            pos = exclusive_end
        else:
            out.append(source[pos])
            pos += 1

    return "".join(out)


# ---------------------------------------------------------------------------
# prompt_toolkit integration
# ---------------------------------------------------------------------------

def _make_pt_lexer():
    """
    Return a prompt_toolkit Lexer that highlights Radon source live as the
    user types.  The import is deferred so prompt_toolkit stays optional —
    if it is not installed the REPL falls back to plain input().
    """
    from prompt_toolkit.lexers import Lexer as PTLexer
    from prompt_toolkit.document import Document
    from prompt_toolkit.formatted_text import ANSI

    class _RadonLexer(PTLexer):
        def lex_document(self, document: Document):
            lines = document.lines

            def get_line(lineno: int):
                if lineno >= len(lines):
                    return []
                return [("", lines[lineno])]   # fallback: plain text per line

            # Build one highlighted string per line up-front
            highlighted = [ANSI(highlight(line)) for line in lines]

            def get_line_highlighted(lineno: int):
                if lineno >= len(highlighted):
                    return []
                return highlighted[lineno].__pt_formatted_text__()

            return get_line_highlighted

    return _RadonLexer()


try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

    _pt_session: PromptSession = PromptSession(
        lexer=_make_pt_lexer(),
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
    )
    _PT_AVAILABLE = True
except ImportError:
    _PT_AVAILABLE = False
    _pt_session = None  # type: ignore


def pt_input(prompt: str) -> str:
    """
    Drop-in replacement for input() that renders live syntax highlighting
    as the user types.  Falls back to plain input() if prompt_toolkit is
    not installed.
    """
    if _PT_AVAILABLE and _pt_session is not None:
        return _pt_session.prompt(prompt)
    return input(prompt)
