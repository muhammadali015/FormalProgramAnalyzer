import sys
from parser import parse_program
from ssa import SSAConverter
from smt import SMTGenerator
from z3 import sat

def main():
    # Define two equivalent programs
    program1_text = """
    a := 5;
    b := 10;
    c := a + b;
    """
    
    program2_text = """
    a := 5; 
    b := 10;
    c := b + a;
    """
    
    # Define output variables to check
    output_vars = ["c"]
    
    print("STEP 1: Parsing the programs...")
    statements1 = parse_program(program1_text)
    statements2 = parse_program(program2_text)
    print(f"Program 1 statements: {statements1}")
    print(f"Program 2 statements: {statements2}")
    
    print("\nSTEP 2: Converting to SSA form...")
    ssa_converter = SSAConverter()
    ssa_form1 = ssa_converter.convert_to_ssa(statements1)
    
    ssa_converter.reset()
    ssa_form2 = ssa_converter.convert_to_ssa(statements2)
    
    print(f"Program 1 SSA form: {ssa_form1}")
    print(f"Program 2 SSA form: {ssa_form2}")
    
    print("\nSTEP 3: Checking equivalence...")
    smt_generator = SMTGenerator()
    is_equivalent, counterexamples = smt_generator.check_equivalence(ssa_form1, ssa_form2, output_vars)
    
    print(f"Are the programs equivalent? {is_equivalent}")
    
    if is_equivalent:
        print("The programs are semantically equivalent!")
    else:
        print("The programs are NOT semantically equivalent!")
        if counterexamples:
            print("\nCounterexamples:")
            for i, example in enumerate(counterexamples, 1):
                print(f"Example {i}:", example)
        else:
            print("No specific counterexamples were found.")
    
    print("\nTest with non-equivalent programs...")
    
    # Define two non-equivalent programs
    program3_text = """
    x := 4;
    if (x > 3) {
        y := 10;
    } else {
        y := 0;
    }
    """
    
    program4_text = """
    x := 4;
    if (x > 4) {
        y := 10;
    } else {
        y := 0;
    }
    """
    
    # Define output variables to check for the second test
    output_vars2 = ["y"]
    
    statements3 = parse_program(program3_text)
    statements4 = parse_program(program4_text)
    
    ssa_converter = SSAConverter()
    ssa_form3 = ssa_converter.convert_to_ssa(statements3)
    
    ssa_converter.reset()
    ssa_form4 = ssa_converter.convert_to_ssa(statements4)
    
    print(f"Program 3 SSA form: {ssa_form3}")
    print(f"Program 4 SSA form: {ssa_form4}")
    
    smt_generator = SMTGenerator()
    is_equivalent2, counterexamples2 = smt_generator.check_equivalence(ssa_form3, ssa_form4, output_vars2)
    
    print(f"Are the programs equivalent? {is_equivalent2}")
    
    if is_equivalent2:
        print("The programs are semantically equivalent!")
    else:
        print("The programs are NOT semantically equivalent!")
        if counterexamples2:
            print("\nCounterexamples:")
            for i, example in enumerate(counterexamples2, 1):
                print(f"Example {i}:", example)
        else:
            print("No specific counterexamples were found.")
    
if __name__ == "__main__":
    main() 