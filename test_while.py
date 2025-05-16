import sys
from parser import parse_program
from ssa import SSAConverter
from smt import SMTGenerator
from z3 import sat

def main():
    # Define the while loop example
    program_text = """
    x := 0;
    while (x < 4) {
        x := x + 1;
    }
    assert(x == 4);
    """
    
    print("STEP 1: Parsing the program...")
    statements = parse_program(program_text)
    print(f"Parsed statements: {statements}")
    
    print("\nSTEP 2: Converting to SSA form with loop unrolling...")
    ssa_converter = SSAConverter()
    ssa_form = ssa_converter.convert_to_ssa(statements, unroll_depth=4)
    print(f"SSA form: {ssa_form}")
    
    print("\nSTEP 3: Generating SMT constraints...")
    smt_generator = SMTGenerator()
    constraints = smt_generator.generate_constraints(ssa_form)
    print(f"Constraints: {constraints}")
    
    print("\nSTEP 4: Checking satisfiability...")
    smt_generator.add_constraints(constraints)
    result = smt_generator.check()
    
    print(f"Result: {result}")
    
    if result == sat:
        print("The program is verified successfully!")
        model = smt_generator.model()
        print(f"Model: {model}")
    else:
        print("The program verification failed!")
    
if __name__ == "__main__":
    main() 