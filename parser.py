import ply.lex as lex
import ply.yacc as yacc

# List of token names
tokens = (
    'NUMBER',
    'IDENTIFIER',
    'ASSIGN',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'LBRACE',
    'RBRACE',
    'SEMICOLON',
    'IF',
    'ELSE',
    'WHILE',
    'FOR',
    'ASSERT',
    'LT',
    'GT',
    'EQ',
    'LE',
    'GE',
    'NE',
)

# Regular expression rules for simple tokens
...

# A regular expression rule with some action code
# Note addition of self parameter since we're in a class
class MiniLangLexer:
    # List of token names
    tokens = (
        'NUMBER',
        'IDENTIFIER',
        'ASSIGN',
        'PLUS',
        'MINUS',
        'TIMES',
        'DIVIDE',
        'LPAREN',
        'RPAREN',
        'LBRACE',
        'RBRACE',
        'SEMICOLON',
        'IF',
        'ELSE',
        'WHILE',
        'FOR',
        'ASSERT',
        'LT',
        'GT',
        'EQ',
        'LE',
        'GE',
        'NE',
    )

    # Regular expression rules for simple tokens
    t_ASSIGN = r':='
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_SEMICOLON = r';'
    t_LT = r'<'
    t_GT = r'>'
    t_EQ = r'=='
    t_LE = r'<='
    t_GE = r'>='
    t_NE = r'!='

    # Regular expression rules with some action code
    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        return t

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Error handling rule
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}'")
        t.lexer.skip(1)

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Test it output
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)

# Build the lexer
lexer = MiniLangLexer()
lexer.build()

# Test the lexer
lexer.test("x := 3; if (x < 5) { y := x + 1; } else { y := x - 1; } assert(y > 0);")

# Parser rules
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

# dictionary of names
names = {}

def p_statement_assign(p):
    'statement : IDENTIFIER ASSIGN expression SEMICOLON'
    names[p[1]] = p[3]

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    if p[2] == '+':
        p[0] = p[1] + p[3]
    elif p[2] == '-':
        p[0] = p[1] - p[3]
    elif p[2] == '*':
        p[0] = p[1] * p[3]
    elif p[2] == '/':
        p[0] = p[1] / p[3]

def p_expression_number(p):
    'expression : NUMBER'
    p[0] = p[1]

def p_expression_identifier(p):
    'expression : IDENTIFIER'
    try:
        p[0] = names[p[1]]
    except LookupError:
        print(f"Undefined name '{p[1]}'")
        p[0] = 0

def p_error(p):
    print(f"Syntax error at '{p.value}'")

# Build the parser
parser = yacc.yacc()

# Test the parser
parser.parse("x := 3; if (x < 5) { y := x + 1; } else { y := x - 1; } assert(y > 0);")

def parse_program(program_text):
    """
    Parse a program written in the mini-language.
    
    Args:
        program_text (str): The program text to parse
        
    Returns:
        list: List of parsed statements
    """
    # Main outer statements list
    statements = []
    
    # Stack for tracking nested blocks
    block_stack = []
    current_block = statements
    
    # Preprocess the program text to normalize spacing
    lines = []
    for line in program_text.splitlines():
        line = line.strip()
        if line:  # Skip empty lines
            # Temporarily normalize braces
            if line.endswith('{'):
                line = line[:-1].strip()
                lines.append(line)
                lines.append('{')
            elif line == '}' or line == '};':
                lines.append('}')
            elif line.endswith(';}'):
                line = line[:-2].strip() + ';'
                lines.append(line)
                lines.append('}')
            else:
                lines.append(line)
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Handle semicolons
        if line.endswith(';'):
            line = line[:-1].strip()
        
        # Assignment statements
        if ':=' in line:
            parts = line.split(':=', 1)
            if len(parts) == 2:
                var, expr = parts
                current_block.append({'type': 'assign', 'var': var.strip(), 'expr': expr.strip()})
        
        # If statements
        elif line.startswith('if'):
            # Extract condition between parentheses
            open_paren = line.find('(')
            close_paren = line.rfind(')')
            
            if open_paren >= 0 and close_paren >= 0:
                condition = line[open_paren+1:close_paren].strip()
                if_block = {'type': 'if', 'condition': condition, 'body': []}
                current_block.append(if_block)
                block_stack.append((current_block, if_block))
                current_block = if_block['body']
        
        # Else statements
        elif line.startswith('else'):
            if block_stack:
                parent_block, parent_stmt = block_stack.pop()
                if parent_stmt.get('type') == 'if':
                    parent_stmt['else'] = []
                    current_block = parent_stmt['else']
                    block_stack.append((parent_block, parent_stmt))
        
        # While loops
        elif line.startswith('while'):
            # Extract condition between parentheses
            open_paren = line.find('(')
            close_paren = line.rfind(')')
            
            if open_paren >= 0 and close_paren >= 0:
                condition = line[open_paren+1:close_paren].strip()
                while_block = {'type': 'while', 'condition': condition, 'body': []}
                current_block.append(while_block)
                block_stack.append((current_block, while_block))
                current_block = while_block['body']
        
        # For loops
        elif line.startswith('for'):
            # Extract the three parts from the for loop: init; condition; update
            open_paren = line.find('(')
            close_paren = line.rfind(')')
            
            if open_paren >= 0 and close_paren >= 0:
                for_parts = line[open_paren+1:close_paren].strip()
                parts = for_parts.split(';')
                
                if len(parts) == 3:
                    init_part = parts[0].strip()
                    condition_part = parts[1].strip()
                    update_part = parts[2].strip()
                    
                    for_block = {
                        'type': 'for',
                        'condition': condition_part,
                        'body': []
                    }
                    
                    # Parse initialization part
                    if ':=' in init_part:
                        init_var, init_expr = init_part.split(':=', 1)
                        for_block['init'] = {'var': init_var.strip(), 'expr': init_expr.strip()}
                    
                    # Parse update part
                    if ':=' in update_part:
                        update_var, update_expr = update_part.split(':=', 1)
                        for_block['update'] = {'var': update_var.strip(), 'expr': update_expr.strip()}
                    
                    current_block.append(for_block)
                    block_stack.append((current_block, for_block))
                    current_block = for_block['body']
        
        # Block opening
        elif line == '{':
            # Opening brace already handled by if/else/while/for
            pass
        
        # Block closing
        elif line == '}':
            if block_stack:
                current_block, _ = block_stack.pop()
        
        # Assert statements
        elif line.startswith('assert'):
            # Extract condition between parentheses
            open_paren = line.find('(')
            close_paren = line.rfind(')')
            
            if open_paren >= 0 and close_paren >= 0:
                condition = line[open_paren+1:close_paren].strip()
                current_block.append({'type': 'assert', 'condition': condition})
        
        i += 1
    
    return statements

# Example usage
program_text = """
x := 3;
if (x < 5) {
    y := x + 1;
} else {
    y := x - 1;
}
assert(y > 0);
"""
parsed_statements = parse_program(program_text)
print("Parsed Statements:", parsed_statements) 