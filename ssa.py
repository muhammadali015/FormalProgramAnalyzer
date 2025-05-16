import re

class SSAConverter:
    def __init__(self):
        self.ssa_form = []
        self.var_count = {}

    def reset(self):
        """Reset the state of the converter to process a new program."""
        self.ssa_form = []
        self.var_count = {}

    def new_var(self, var_name):
        if var_name not in self.var_count:
            self.var_count[var_name] = 0
        else:
            self.var_count[var_name] += 1
        return f"{var_name}_{self.var_count[var_name]}"

    def convert_to_ssa(self, statements, unroll_depth=3):
        """
        Convert statements to SSA form, with loop unrolling.
        
        Args:
            statements: List of statements to convert
            unroll_depth: Number of times to unroll loops
        """
        for stmt in statements:
            if isinstance(stmt, list):
                # Recursively process nested blocks
                self.convert_to_ssa(stmt, unroll_depth)
            elif stmt['type'] == 'assign':
                new_var = self.new_var(stmt['var'])
                
                # Replace variables in expression with their latest SSA versions
                expr = stmt['expr']
                for var, count in self.var_count.items():
                    if var in expr:
                        expr = re.sub(r'\b' + var + r'\b', f"{var}_{count}", expr)
                
                self.ssa_form.append(f"{new_var} := {expr}")
            elif stmt['type'] == 'if':
                # Handle if condition
                condition = stmt['condition']
                
                # Replace variables in condition with their latest SSA versions
                for var, count in self.var_count.items():
                    if var in condition:
                        condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", condition)
                
                self.ssa_form.append(f"if ({condition})")
                self.convert_to_ssa(stmt['body'], unroll_depth)
                if 'else' in stmt:
                    self.ssa_form.append("else")
                    self.convert_to_ssa(stmt['else'], unroll_depth)
            elif stmt['type'] == 'assert':
                # Handle assert condition
                condition = stmt['condition']
                
                # Replace variables in condition with their latest SSA versions
                for var, count in self.var_count.items():
                    if var in condition:
                        condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", condition)
                
                self.ssa_form.append(f"assert({condition})")
            elif stmt['type'] == 'while':
                # Unroll while loop
                self.unroll_while_loop(stmt, unroll_depth)
            elif stmt['type'] == 'for':
                # Unroll for loop
                self.unroll_for_loop(stmt, unroll_depth)
                
        return self.ssa_form
    
    def unroll_while_loop(self, while_stmt, unroll_depth):
        """
        Unroll a while loop for a specified number of iterations.
        
        Args:
            while_stmt: The while statement to unroll
            unroll_depth: Number of times to unroll the loop
        """
        # Add a conditional check before each unrolled iteration
        for i in range(unroll_depth):
            # Replace variables in condition with their latest SSA versions
            condition = while_stmt['condition']
            for var, count in self.var_count.items():
                if var in condition:
                    condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", condition)
            
            # Create condition check
            self.ssa_form.append(f"if ({condition})")
            
            # Process the body statements for this iteration and update the body for next iteration
            # We need to track the SSA variables created for the variables modified in the loop body
            modified_vars = {}
            for stmt in while_stmt['body']:
                if stmt['type'] == 'assign':
                    # Get the variable being assigned
                    modified_vars[stmt['var']] = True

                    # Replace variables in the expression with their latest SSA versions
                    expr = stmt['expr']
                    for var, count in self.var_count.items():
                        if var in expr:
                            expr = re.sub(r'\b' + var + r'\b', f"{var}_{count}", expr)
                    
                    # Create new SSA variable for the assigned variable
                    new_var = self.new_var(stmt['var'])
                    self.ssa_form.append(f"{new_var} := {expr}")
            
        # After unrolling, add an assertion that the loop condition is eventually false
        final_condition = while_stmt['condition']
        for var, count in self.var_count.items():
            if var in final_condition:
                final_condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", final_condition)
        
        # Add negated condition assertion
        self.ssa_form.append(f"assert(!({final_condition}))")
    
    def unroll_for_loop(self, for_stmt, unroll_depth):
        """
        Unroll a for loop for a specified number of iterations.
        
        Args:
            for_stmt: The for statement to unroll
            unroll_depth: Number of times to unroll the loop
        """
        # Process initialization (only once)
        if 'init' in for_stmt:
            init_var = for_stmt['init']['var']
            init_expr = for_stmt['init']['expr']
            
            # Replace variables in init expression with their latest SSA versions
            for var, count in self.var_count.items():
                if var in init_expr:
                    init_expr = re.sub(r'\b' + var + r'\b', f"{var}_{count}", init_expr)
                    
            new_var = self.new_var(init_var)
            self.ssa_form.append(f"{new_var} := {init_expr}")
        
        # Unroll the loop body and increment
        for i in range(unroll_depth):
            # Update condition with latest SSA variables
            condition = for_stmt['condition']
            for var, count in self.var_count.items():
                if var in condition:
                    condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", condition)
            
            # Check condition before each iteration
            self.ssa_form.append(f"if ({condition})")
            
            # Process the body statements
            modified_vars = {}
            for stmt in for_stmt['body']:
                if stmt['type'] == 'assign':
                    # Get the variable being assigned
                    modified_vars[stmt['var']] = True

                    # Replace variables in the expression with their latest SSA versions
                    expr = stmt['expr']
                    for var, count in self.var_count.items():
                        if var in expr:
                            expr = re.sub(r'\b' + var + r'\b', f"{var}_{count}", expr)
                    
                    # Create new SSA variable for the assigned variable
                    new_var = self.new_var(stmt['var'])
                    self.ssa_form.append(f"{new_var} := {expr}")
            
            # Process increment
            if 'update' in for_stmt:
                update_var = for_stmt['update']['var']
                update_expr = for_stmt['update']['expr']
                
                # Replace variables in update expression with their latest SSA versions
                for var, count in self.var_count.items():
                    if var in update_expr:
                        update_expr = re.sub(r'\b' + var + r'\b', f"{var}_{count}", update_expr)
                
                new_var = self.new_var(update_var)
                self.ssa_form.append(f"{new_var} := {update_expr}")
        
        # Add final condition check after unrolling
        final_condition = for_stmt['condition']
        for var, count in self.var_count.items():
            if var in final_condition:
                final_condition = re.sub(r'\b' + var + r'\b', f"{var}_{count}", final_condition)
        
        self.ssa_form.append(f"assert(!({final_condition}))")

    def optimize_ssa(self):
        # Implement optimizations like constant propagation, dead code elimination
        pass

# Example usage
ssa_converter = SSAConverter()
statements = [
    {'type': 'assign', 'var': 'x', 'expr': '3'},
    {'type': 'if', 'condition': '(x < 5)', 'body': [
        {'type': 'assign', 'var': 'y', 'expr': 'x + 1'}
    ], 'else': [
        {'type': 'assign', 'var': 'y', 'expr': 'x - 1'}
    ]},
    {'type': 'assert', 'condition': 'y > 0'}
]
ssa_form = ssa_converter.convert_to_ssa(statements)
print("SSA Form:", ssa_form) 