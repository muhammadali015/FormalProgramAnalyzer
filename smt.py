from z3 import *
import re

class SMTGenerator:
    def __init__(self):
        self.solver = Solver()
        self.variables = {}
        self.variable_mapping = {}  # Maps original var names to their SSA versions

    def reset(self):
        self.solver = Solver()
        self.variables = {}
        self.variable_mapping = {}

    def define_variable(self, var_name):
        if var_name not in self.variables:
            self.variables[var_name] = Int(var_name)
            
            # Update variable mapping for SSA variables
            base_name = var_name.split('_')[0] if '_' in var_name else var_name
            self.variable_mapping[base_name] = var_name
            
        return self.variables[var_name]

    def generate_constraints(self, ssa_form):
        # Define all variables at the start
        for stmt in ssa_form:
            if ":=" in stmt:
                var, _ = stmt.split(' := ')
                self.define_variable(var)

        constraints = []
        for stmt in ssa_form:
            if ":=" in stmt:
                var, expr = stmt.split(' := ')
                var_z3 = self.variables[var]
                
                # Replace original variable names with their SSA versions in the expression
                for orig_var, ssa_var in self.variable_mapping.items():
                    expr = re.sub(r'\b' + orig_var + r'\b', ssa_var, expr)
                
                # Define all variables in the expression
                expr_vars = [v.strip() for v in expr.replace('+', ' ').replace('-', ' ').replace('*', ' ').replace('/', ' ').split()]
                for v in expr_vars:
                    if v.isidentifier():
                        self.define_variable(v)
                
                # Custom expression evaluation instead of using eval()
                expr_z3 = self.evaluate_expression(expr)
                constraints.append(var_z3 == expr_z3)
            
            elif stmt.startswith('if') or stmt.startswith('assert'):
                # Handle if and assert conditions
                condition = stmt.split('(', 1)[1].rsplit(')', 1)[0].strip()
                
                # Replace original variable names with their SSA versions in the condition
                for orig_var, ssa_var in self.variable_mapping.items():
                    condition = re.sub(r'\b' + orig_var + r'\b', ssa_var, condition)
                
                # Define all variables in the condition
                condition_vars = [v.strip() for v in condition.replace('<', ' ').replace('>', ' ').replace('==', ' ').replace('!=', ' ').replace('<=', ' ').replace('>=', ' ').replace('&&', ' ').replace('||', ' ').split()]
                for v in condition_vars:
                    if v.isidentifier():
                        self.define_variable(v)
                
                # Custom condition evaluation
                condition_z3 = self.evaluate_condition(condition)
                constraints.append(condition_z3)
            
            elif stmt == 'else':
                # Handle else block
                continue
        
        return constraints
        
    def evaluate_expression(self, expr):
        """
        Safely evaluate an expression into a Z3 formula.
        
        Args:
            expr (str): The expression to evaluate
            
        Returns:
            Z3 expression
        """
        # Recursively parse an expression into a Z3 formula
        expr = expr.strip()
        
        # Handle numeric literals
        if expr.isdigit():
            return IntVal(int(expr))
            
        # Handle variables
        if expr.isidentifier():
            if expr in self.variables:
                return self.variables[expr]
            else:
                raise ValueError(f"Variable {expr} not defined")
                
        # Handle addition
        if '+' in expr:
            parts = self.split_at_operator(expr, '+')
            left = self.evaluate_expression(parts[0])
            right = self.evaluate_expression(parts[1])
            return left + right
            
        # Handle subtraction
        if '-' in expr:
            parts = self.split_at_operator(expr, '-')
            left = self.evaluate_expression(parts[0])
            right = self.evaluate_expression(parts[1])
            return left - right
            
        # Handle multiplication
        if '*' in expr:
            parts = self.split_at_operator(expr, '*')
            left = self.evaluate_expression(parts[0])
            right = self.evaluate_expression(parts[1])
            return left * right
            
        # Handle division
        if '/' in expr:
            parts = self.split_at_operator(expr, '/')
            left = self.evaluate_expression(parts[0])
            right = self.evaluate_expression(parts[1])
            return left / right
            
        # Handle parentheses
        if expr.startswith('(') and expr.endswith(')'):
            return self.evaluate_expression(expr[1:-1])
            
        raise ValueError(f"Cannot evaluate expression: {expr}")
    
    def evaluate_condition(self, condition):
        """
        Evaluate a condition into a Z3 formula.
        
        Args:
            condition (str): The condition to evaluate
            
        Returns:
            Z3 formula
        """
        condition = condition.strip()
        
        # Handle negation (!) - must check this first
        if condition.startswith('!'):
            # Remove the exclamation mark and any surrounding parentheses if present
            inner_condition = condition[1:].strip()
            if inner_condition.startswith('(') and inner_condition.endswith(')'):
                inner_condition = inner_condition[1:-1].strip()
            
            return Not(self.evaluate_condition(inner_condition))
        
        # Handle equality (==)
        if '==' in condition:
            parts = condition.split('==')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left == right
            
        # Handle inequality (!=)
        if '!=' in condition:
            parts = condition.split('!=')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left != right
            
        # Handle less than (<)
        if '<' in condition and not '<=' in condition:
            parts = condition.split('<')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left < right
            
        # Handle greater than (>)
        if '>' in condition and not '>=' in condition:
            parts = condition.split('>')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left > right
            
        # Handle less than or equal to (<=)
        if '<=' in condition:
            parts = condition.split('<=')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left <= right
            
        # Handle greater than or equal to (>=)
        if '>=' in condition:
            parts = condition.split('>=')
            left = self.evaluate_expression(parts[0].strip())
            right = self.evaluate_expression(parts[1].strip())
            return left >= right
            
        # Handle logical AND (&&)
        if '&&' in condition:
            parts = condition.split('&&')
            left = self.evaluate_condition(parts[0].strip())
            right = self.evaluate_condition(parts[1].strip())
            return And(left, right)
            
        # Handle logical OR (||)
        if '||' in condition:
            parts = condition.split('||')
            left = self.evaluate_condition(parts[0].strip())
            right = self.evaluate_condition(parts[1].strip())
            return Or(left, right)
        
        # If none of the above, it might be a simple expression that should evaluate to boolean
        # For example, a variable name that represents a boolean value
        return self.evaluate_expression(condition) != 0
    
    def split_at_operator(self, expr, operator):
        """
        Split an expression at the given operator, but only at the top level.
        
        Args:
            expr (str): The expression to split
            operator (str): The operator to split at
            
        Returns:
            tuple: (left part, right part)
        """
        paren_count = 0
        for i in range(len(expr)):
            if expr[i] == '(':
                paren_count += 1
            elif expr[i] == ')':
                paren_count -= 1
            elif expr[i] == operator and paren_count == 0:
                return (expr[:i].strip(), expr[i+1:].strip())
        
        # If we reach here, the operator was not found at the top level
        return (expr, "")

    def check_equivalence(self, ssa_form1, ssa_form2, output_vars):
        """
        Check if two programs are equivalent based on their output variables.
        
        Args:
            ssa_form1 (list): SSA form of the first program
            ssa_form2 (list): SSA form of the second program
            output_vars (list): List of output variable names to check for equivalence
            
        Returns:
            tuple: (is_equivalent, counterexamples)
        """
        # Reset the solver and variables
        self.reset()
        
        # Generate constraints for the first program
        constraints1 = self.generate_constraints(ssa_form1)
        
        # Save the variable mapping and variables from the first program
        variables1 = self.variables.copy()
        variable_mapping1 = self.variable_mapping.copy()
        
        # Reset for the second program
        self.reset()
        
        # Append "_prog2" to all variables in the second program to avoid name conflicts
        ssa_form2_renamed = []
        for stmt in ssa_form2:
            renamed_stmt = stmt
            if ":=" in stmt:
                var, expr = stmt.split(' := ')
                renamed_var = var + "_prog2"
                renamed_expr = expr
                for word in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr):
                    if word.isidentifier():
                        renamed_expr = re.sub(r'\b' + word + r'\b', word + "_prog2", renamed_expr)
                renamed_stmt = renamed_var + " := " + renamed_expr
            elif stmt.startswith('if') or stmt.startswith('assert'):
                condition = stmt.split('(', 1)[1].rsplit(')', 1)[0].strip()
                renamed_condition = condition
                for word in re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', condition):
                    if word.isidentifier():
                        renamed_condition = re.sub(r'\b' + word + r'\b', word + "_prog2", renamed_condition)
                renamed_stmt = stmt.split('(', 1)[0] + '(' + renamed_condition + ')'
            ssa_form2_renamed.append(renamed_stmt)
        
        # Generate constraints for the second program
        constraints2 = self.generate_constraints(ssa_form2_renamed)
        
        # Save the variable mapping and variables from the second program
        variables2 = self.variables.copy()
        variable_mapping2 = self.variable_mapping.copy()
        
        # Create a combined solver for equivalence checking
        solver = Solver()
        
        # Add all constraints from both programs
        for constraint in constraints1:
            solver.add(constraint)
        for constraint in constraints2:
            solver.add(constraint)
        
        # Find the SSA version of each output variable in both programs
        output_var_mappings = []
        for var in output_vars:
            # For program 1, find variables matching the base name
            var1_candidates = []
            for v in variables1:
                if re.match(f"{var}_\\d+$", v):
                    var1_candidates.append(v)
            
            # For program 2, find variables matching the base name with _prog2 suffix
            var2_candidates = []
            for v in variables2:
                if re.match(f"{var}_\\d+_prog2$", v):
                    var2_candidates.append(v)
            
            # If we found candidates, get the ones with highest version numbers
            if var1_candidates and var2_candidates:
                # Sort by version number (descending)
                var1_candidates.sort(key=lambda x: int(x.split('_')[1]), reverse=True)
                var2_candidates.sort(key=lambda x: int(x.split('_')[1]), reverse=True)
                
                # Get the highest version
                var1 = var1_candidates[0]
                var2 = var2_candidates[0]
                
                # Add to our mappings
                if var1 in variables1 and var2 in variables2:
                    output_var_mappings.append((var1, var2))
        
        # If we couldn't find mappings for any variables, try direct base name lookup
        if not output_var_mappings:
            for var in output_vars:
                if var in variable_mapping1 and var in variable_mapping2:
                    var1 = variable_mapping1[var]
                    var2 = variable_mapping2[var] + "_prog2"
                    if var1 in variables1 and var2 in variables2:
                        output_var_mappings.append((var1, var2))
        
        # Check if we have variables to compare
        if not output_var_mappings:
            return False, []  # No output variables to compare
        
        # Build equivalence constraints
        equiv_constraints = []
        for var1, var2 in output_var_mappings:
            equiv_constraints.append(variables1[var1] == variables2[var2])
        
        # Check that solver is satisfiable (programs can be executed)
        if solver.check() != sat:
            return False, []  # Programs have unsatisfiable constraints
            
        solver.push()
        
        # First check if the programs are equivalent for all inputs
        # We do this by checking for a counterexample where the outputs differ
        solver.add(Not(And(*equiv_constraints)))
        
        if solver.check() == sat:
            # Found a counterexample where programs behave differently
            counterexamples = []
            
            # Extract up to 3 counterexamples
            for _ in range(3):
                if solver.check() == sat:
                    model = solver.model()
                    
                    # Extract values that demonstrate the difference
                    example = {}
                    
                    # Process variables from first program
                    for var in variables1:
                        try:
                            # Extract base variable name (without SSA index)
                            base_var = var.split('_')[0]
                            if variables1[var] in model:
                                value = model[variables1[var]].as_long()
                                example[f"{base_var} (prog1)"] = value
                        except:
                            pass
                    
                    # Process variables from second program
                    for var in variables2:
                        try:
                            # Extract base variable name (without SSA index and prog2 suffix)
                            if "_prog2" in var:
                                base_var = var.split('_')[0]
                                if variables2[var] in model:
                                    value = model[variables2[var]].as_long()
                                    example[f"{base_var} (prog2)"] = value
                        except:
                            pass
                    
                    if example:  # Only add if we have values
                        counterexamples.append(example)
                    
                    # Add constraint to find a different counterexample
                    block = []
                    for var in variables1:
                        try:
                            if variables1[var] in model:
                                block.append(variables1[var] != model[variables1[var]])
                        except:
                            pass
                    for var in variables2:
                        try:
                            if variables2[var] in model:
                                block.append(variables2[var] != model[variables2[var]])
                        except:
                            pass
                    
                    if block:
                        solver.add(Or(*block))
                    else:
                        break
                else:
                    break
            
            solver.pop()
            return False, counterexamples
        
        # If we reach here, the programs produce the same outputs for all inputs
        solver.pop()
        return True, []  # Programs are equivalent

    def add_constraints(self, constraints):
        for constraint in constraints:
            self.solver.add(constraint)

    def check(self):
        return self.solver.check()

    def model(self):
        return self.solver.model()
    
    def get_examples(self, ssa_form, num_examples=2):
        """
        Get examples where the constraints are satisfied.
        
        Args:
            ssa_form (list): SSA form of the program
            num_examples (int): Number of examples to generate
            
        Returns:
            list: List of examples (dictionaries mapping variables to values)
        """
        constraints = self.generate_constraints(ssa_form)
        self.add_constraints(constraints)
        
        examples = []
        
        # Get up to num_examples satisfying assignments
        for _ in range(num_examples):
            if self.check() == sat:
                model = self.solver.model()
                
                # Extract variable values
                example = {}
                for var in self.variables:
                    try:
                        if self.variables[var] in model:
                            example[var] = model[self.variables[var]].as_long()
                    except:
                        pass
                
                examples.append(example)
                
                # Add constraint to find different example
                block = []
                for var in self.variables:
                    try:
                        if self.variables[var] in model:
                            block.append(self.variables[var] != model[self.variables[var]])
                    except:
                        pass
                
                self.solver.add(Or(block))
            else:
                break
        
        return examples

# Example usage
if __name__ == "__main__":
    smt_generator = SMTGenerator()
    ssa_form = ["x_0 := 3", "if ((x < 5))", "y_0 := x + 1", "else", "y_1 := x - 1", "assert(y > 0)"]
    constraints = smt_generator.generate_constraints(ssa_form)
    smt_generator.add_constraints(constraints)
    result = smt_generator.check()
    print("SMT Check Result:", result)
    if result == sat:
        print("Model:", smt_generator.model()) 