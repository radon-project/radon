from core.tokens import *
from core.errors import *


class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(
            self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char == '#':
                self.skip_comment()
            elif self.current_char in ';\n':
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in VALID_IDENTIFIERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char == ":":
                tokens.append(Token(TT_COLON, pos_start=self.pos))
                self.advance()
            # elif self.current_char == "'":
            #     tokens.append(self.make_string())
            # elif self.current_char == '+':
            #     tokens.append(Token(TT_PLUS, pos_start=self.pos))
            #     self.advance()
            # elif self.current_char == '-':
            #     tokens.append(self.make_minus_or_arrow())
            # elif self.current_char == '*':
            #     tokens.append(Token(TT_MUL, pos_start=self.pos))
            #     self.advance()
            # elif self.current_char == '/':
            #     tokens.append(Token(TT_DIV, pos_start=self.pos))
            #     self.advance()
            # elif self.current_char == '^':
            #     tokens.append(Token(TT_POW, pos_start=self.pos))
            #     self.advance()
            # elif self.current_char == '%':
            #     tokens.append(Token(TT_MOD, pos_start=self.pos))
            elif self.current_char == '+':
                tokens.append(self.make_plus_equals())
            elif self.current_char == '-':
                tokens.append(self.make_minus_equals())
            elif self.current_char == '*':
                tokens.append(self.make_times_equals())
            elif self.current_char == '/':
                tokens.append(self.make_divide_equals())
            elif self.current_char == '%':
                tokens.append(self.make_mod_equals())
            elif self.current_char == '^':
                tokens.append(self.make_power_equals())
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(TT_LBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TT_RBRACE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                # tokens.append(self.make_slice())
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == '.':
                tokens.append(Token(TT_DOT, pos_start=self.pos))
                self.advance()
            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def make_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1:
                    break
                dot_count += 1
            num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False
        self.advance()

        while self.current_char is not None and (self.current_char != '"' or escape_character):
            if self.current_char == '\\':
                escape_character = True
            else:
                escape_character = False
            string += self.current_char
            self.advance()

        self.advance()
        return Token(TT_STRING, string.encode("utf-8").decode("unicode-escape"), pos_start, self.pos)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in VALID_IDENTIFIERS:
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)

    def make_slice(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char in DIGITS:
            start = self.make_number()
            if self.current_char == ':':
                self.advance()
                end = self.make_number()
                if self.current_char == ':':
                    self.advance()
                    step = self.make_number()
                    if self.current_char == ']':
                        self.advance()
                        return Token(TT_SLICE, (start, end, step), pos_start, self.pos)
                    return Token(TT_SLICE, (start, end, step), pos_start, self.pos), ExpectedCharError(pos_start, self.pos, "']'")
                return Token(TT_SLICE, (start, end, None), pos_start, self.pos), ExpectedCharError(pos_start, self.pos, "']'")
            return Token(TT_SLICE, (start, None, None), pos_start, self.pos), ExpectedCharError(pos_start, self.pos, "']'")
        return Token(TT_SLICE, (None, None, None), pos_start, self.pos), ExpectedCharError(pos_start, self.pos, "']'")

    # def make_minus_or_arrow(self):
    #     tok_type = TT_MINUS
    #     pos_start = self.pos.copy()
    #     self.advance()

    #     if self.current_char == '>':
    #         self.advance()
    #         tok_type = TT_ARROW

    #     return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_not_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

    def make_equals(self):
        tok_type = TT_EQ
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_EE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        tok_type = TT_LT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_LTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        tok_type = TT_GT
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            tok_type = TT_GTE

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_plus_equals(self):
        tok_type = TT_PLUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            tok_type = TT_PE
            self.advance()

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_minus_equals(self):
        tok_type = TT_MINUS
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            tok_type = TT_ME
            self.advance()

        elif self.current_char == '>':
            tok_type = TT_ARROW
            self.advance()

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_times_equals(self):
        tok_type = TT_MUL
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            tok_type = TT_TE
            self.advance()
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_divide_equals(self):
        tok_type = TT_DIV
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            tok_type = TT_DE
            self.advance()

        if self.current_char == '/':
            tok_type = TT_IDIV
            self.advance()

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_mod_equals(self):
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            self.advance()
            return Token(TT_MDE, pos_start=pos_start, pos_end=self.pos)
        return Token(TT_MOD, pos_start=pos_start, pos_end=self.pos)

    def make_power_equals(self):
        tok_type = TT_POW
        pos_start = self.pos.copy()
        self.advance()

        if self.current_char == '=':
            tok_type = TT_POWE
            self.advance()

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def skip_comment(self):
        multi_line = False
        self.advance()

        if self.current_char == '!':
            multi_line = True
            self.advance()

        while True:
            if self.current_char == None:
                return
            if multi_line:
                if self.current_char == '!':
                    self.advance()
                    if self.current_char == '#':
                        self.advance()
                        return
            else:
                if self.current_char == '\n':
                    return
            self.advance()

        