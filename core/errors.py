#######################################
# ERRORS
#######################################


def string_with_arrows(text, pos_start, pos_end):
    '''Return string with arrows'''
    result = ''

    # Calculate indices
    idx_start = max(text.rfind('\n', 0, pos_start.idx), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0: idx_end = len(text)
    
    # Generate each line
    line_count = pos_end.ln - pos_start.ln + 1
    for i in range(line_count):
        # Calculate line columns
        line = text[idx_start:idx_end]
        col_start = pos_start.col if i == 0 else 0
        col_end = pos_end.col if i == line_count - 1 else len(line) - 1

        # Append to result
        result += line + '\n'
        result += ' ' * col_start + '^' * (col_end - col_start)

        # Re-calculate indices
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0: idx_end = len(text)

    return result.replace('\t', '')


class Error:
    '''Base Error class'''
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details
        self.value = details

    def as_string(self):
        '''Return error as string'''
        result = f'{self.error_name}: {self.details}\n'
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        result += '\n' + \
            string_with_arrows(self.pos_start.ftxt,
                               self.pos_start, self.pos_end)
        return result
    
    def set_pos(self, pos_start=None, pos_end=None):
        return self

    def __repr__(self) -> str:
        return f'{self.error_name}: {self.details}'
    
    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.error_name, self.details)


class IllegalCharError(Error):
    '''Illegal Character Error class'''
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Illegal Character', details)


class ExpectedCharError(Error):
    '''Expected Character Error class'''
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, 'Expected Character', details)


class InvalidSyntaxError(Error):
    '''Invalid Syntax Error class'''
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)


class IndexError(Error):
    '''Index Error class'''
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Index Error', details)


class RTError(Error):
    '''Runtime Error class'''
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, 'Runtime Error', details)
        self.context = context

    def as_string(self):
        '''Return error as string'''
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}'
        result += '\n' + \
            string_with_arrows(self.pos_start.ftxt,
                               self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        '''Generate traceback for runtime error'''
        result = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f'  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback (most recent call last):\n' + result

    def set_context(self, context=None):
        return self
    
    def copy(self):
        return __class__(self.pos_start, self.pos_end, self.details, self.context)

class TryError(RTError):
    def __init__(self, pos_start, pos_end, details, context, prev_error):
        super().__init__(pos_start, pos_end, details, context)
        self.prev_error = prev_error 

    def generate_traceback(self):
        result = ""
        if self.prev_error:
            result += self.prev_error.as_string()
        result += "\nDuring the handling of the above error, another error occurred:\n\n"
        return result + super().generate_traceback()
    
