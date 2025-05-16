import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QTabWidget, QSpinBox, QComboBox, QGroupBox, QScrollArea, 
                           QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from ssa import SSAConverter
from smt import SMTGenerator
from z3 import sat, unsat
from parser import parse_program

class ProgramAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Program Analyzer')
        self.setGeometry(100, 100, 1000, 800)

        # Main widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create verification tab
        self.verification_tab = QWidget()
        self.create_verification_tab()
        self.tab_widget.addTab(self.verification_tab, "Verification Mode")
        
        # Create equivalence tab
        self.equivalence_tab = QWidget()
        self.create_equivalence_tab()
        self.tab_widget.addTab(self.equivalence_tab, "Equivalence Mode")
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tab_widget)
        self.main_widget.setLayout(self.main_layout)

    def create_verification_tab(self):
        layout = QVBoxLayout()
        
        # Input area
        input_group = QGroupBox("Program Input")
        input_layout = QVBoxLayout()
        
        self.verification_input = QTextEdit()
        self.verification_input.setPlaceholderText('Enter your program here...')
        input_layout.addWidget(self.verification_input)
        
        # Loop unrolling options
        unroll_layout = QHBoxLayout()
        unroll_layout.addWidget(QLabel("Loop Unrolling Depth:"))
        self.unroll_depth_spinbox = QSpinBox()
        self.unroll_depth_spinbox.setMinimum(1)
        self.unroll_depth_spinbox.setMaximum(10)
        self.unroll_depth_spinbox.setValue(3)
        unroll_layout.addWidget(self.unroll_depth_spinbox)
        
        # Add some spacing
        unroll_layout.addStretch()
        
        # Analyze button
        self.verify_button = QPushButton('Verify Program')
        self.verify_button.clicked.connect(self.verify_program)
        unroll_layout.addWidget(self.verify_button)
        
        input_layout.addLayout(unroll_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Results area (scrollable)
        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # SSA output
        ssa_group = QGroupBox("SSA Form")
        ssa_layout = QVBoxLayout()
        self.ssa_output = QTextEdit()
        self.ssa_output.setReadOnly(True)
        ssa_layout.addWidget(self.ssa_output)
        ssa_group.setLayout(ssa_layout)
        results_layout.addWidget(ssa_group)
        
        # SMT output
        smt_group = QGroupBox("SMT Constraints")
        smt_layout = QVBoxLayout()
        self.smt_output = QTextEdit()
        self.smt_output.setReadOnly(True)
        smt_layout.addWidget(self.smt_output)
        smt_group.setLayout(smt_layout)
        results_layout.addWidget(smt_group)
        
        # Verification result
        result_group = QGroupBox("Verification Result")
        result_layout = QVBoxLayout()
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)
        result_layout.addWidget(self.result_output)
        result_group.setLayout(result_layout)
        results_layout.addWidget(result_group)
        
        # Examples/counterexamples
        examples_group = QGroupBox("Examples")
        examples_layout = QVBoxLayout()
        self.examples_table = QTableWidget()
        self.examples_table.setColumnCount(0)
        self.examples_table.setRowCount(0)
        examples_layout.addWidget(self.examples_table)
        examples_group.setLayout(examples_layout)
        results_layout.addWidget(examples_group)
        
        results_scroll.setWidget(results_widget)
        layout.addWidget(results_scroll)
        
        self.verification_tab.setLayout(layout)
    
    def create_equivalence_tab(self):
        layout = QVBoxLayout()
        
        # Input areas
        input_layout = QHBoxLayout()
        
        # Program 1
        prog1_group = QGroupBox("Program 1")
        prog1_layout = QVBoxLayout()
        self.program1_input = QTextEdit()
        self.program1_input.setPlaceholderText('Enter first program here...')
        prog1_layout.addWidget(self.program1_input)
        prog1_group.setLayout(prog1_layout)
        input_layout.addWidget(prog1_group)
        
        # Program 2
        prog2_group = QGroupBox("Program 2")
        prog2_layout = QVBoxLayout()
        self.program2_input = QTextEdit()
        self.program2_input.setPlaceholderText('Enter second program here...')
        prog2_layout.addWidget(self.program2_input)
        prog2_group.setLayout(prog2_layout)
        input_layout.addWidget(prog2_group)
        
        layout.addLayout(input_layout)
        
        # Options and control area
        options_layout = QHBoxLayout()
        
        # Output variables
        output_vars_group = QGroupBox("Output Variables")
        output_vars_layout = QVBoxLayout()
        self.output_vars_input = QTextEdit()
        self.output_vars_input.setPlaceholderText('Enter output variable names separated by commas (e.g., x,y,z)')
        self.output_vars_input.setMaximumHeight(50)
        output_vars_layout.addWidget(self.output_vars_input)
        output_vars_group.setLayout(output_vars_layout)
        options_layout.addWidget(output_vars_group)
        
        # Loop unrolling options
        unroll_group = QGroupBox("Loop Unrolling")
        unroll_group_layout = QFormLayout()
        self.eq_unroll_depth_spinbox = QSpinBox()
        self.eq_unroll_depth_spinbox.setMinimum(1)
        self.eq_unroll_depth_spinbox.setMaximum(10)
        self.eq_unroll_depth_spinbox.setValue(3)
        unroll_group_layout.addRow("Unrolling Depth:", self.eq_unroll_depth_spinbox)
        unroll_group.setLayout(unroll_group_layout)
        options_layout.addWidget(unroll_group)
        
        # Check equivalence button
        self.check_equiv_button = QPushButton('Check Equivalence')
        self.check_equiv_button.clicked.connect(self.check_equivalence)
        options_layout.addWidget(self.check_equiv_button)
        
        layout.addLayout(options_layout)
        
        # Results area (scrollable)
        results_scroll = QScrollArea()
        results_scroll.setWidgetResizable(True)
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # SSA outputs
        ssa_group = QGroupBox("SSA Forms")
        ssa_layout = QVBoxLayout()
        
        ssa1_label = QLabel("Program 1 SSA:")
        ssa_layout.addWidget(ssa1_label)
        self.ssa1_output = QTextEdit()
        self.ssa1_output.setReadOnly(True)
        self.ssa1_output.setMaximumHeight(150)
        ssa_layout.addWidget(self.ssa1_output)
        
        ssa2_label = QLabel("Program 2 SSA:")
        ssa_layout.addWidget(ssa2_label)
        self.ssa2_output = QTextEdit()
        self.ssa2_output.setReadOnly(True)
        self.ssa2_output.setMaximumHeight(150)
        ssa_layout.addWidget(self.ssa2_output)
        
        ssa_group.setLayout(ssa_layout)
        results_layout.addWidget(ssa_group)
        
        # Equivalence result
        equiv_group = QGroupBox("Equivalence Result")
        equiv_layout = QVBoxLayout()
        self.equiv_result = QTextEdit()
        self.equiv_result.setReadOnly(True)
        equiv_layout.addWidget(self.equiv_result)
        equiv_group.setLayout(equiv_layout)
        results_layout.addWidget(equiv_group)
        
        # Examples/counterexamples
        counter_group = QGroupBox("Counterexamples")
        counter_layout = QVBoxLayout()
        self.counter_table = QTableWidget()
        self.counter_table.setColumnCount(0)
        self.counter_table.setRowCount(0)
        counter_layout.addWidget(self.counter_table)
        counter_group.setLayout(counter_layout)
        results_layout.addWidget(counter_group)
        
        results_scroll.setWidget(results_widget)
        layout.addWidget(results_scroll)
        
        self.equivalence_tab.setLayout(layout)

    def verify_program(self):
        # Clear previous results
        self.ssa_output.clear()
        self.smt_output.clear()
        self.result_output.clear()
        self.examples_table.setRowCount(0)
        self.examples_table.setColumnCount(0)
        
        # Get input program
        program_text = self.verification_input.toPlainText()
        if not program_text.strip():
            self.result_output.setText("Error: Please enter a program to verify.")
            return
        
        try:
            # Get loop unrolling depth
            unroll_depth = self.unroll_depth_spinbox.value()
            
            # Parse the input program
            statements = parse_program(program_text)
            
            # Convert to SSA with loop unrolling
            ssa_converter = SSAConverter()
            ssa_form = ssa_converter.convert_to_ssa(statements, unroll_depth)
            self.ssa_output.setText("\n".join(ssa_form))
            
            # Generate SMT constraints
            smt_generator = SMTGenerator()
            constraints = smt_generator.generate_constraints(ssa_form)
            constraint_text = "\n".join([str(c) for c in constraints])
            self.smt_output.setText(constraint_text)
            
            # Check satisfiability
            smt_generator.add_constraints(constraints)
            result = smt_generator.check()
            
            # Display result
            if result == sat:
                self.result_output.setText("Verification Result: SATISFIABLE\nAll assertions hold for some inputs.")
                
                # Get examples
                examples = smt_generator.get_examples(ssa_form, 2)
                if examples:
                    self.display_examples(examples)
            elif result == unsat:
                self.result_output.setText("Verification Result: UNSATISFIABLE\nAssertions don't hold.")
            else:
                self.result_output.setText(f"Verification Result: {result}")
        
        except Exception as e:
            self.result_output.setText(f"Error during verification: {str(e)}")
    
    def check_equivalence(self):
        # Clear previous results
        self.ssa1_output.clear()
        self.ssa2_output.clear()
        self.equiv_result.clear()
        self.counter_table.setRowCount(0)
        self.counter_table.setColumnCount(0)
        
        # Get input programs
        program1_text = self.program1_input.toPlainText()
        program2_text = self.program2_input.toPlainText()
        output_vars_text = self.output_vars_input.toPlainText()
        
        if not program1_text.strip() or not program2_text.strip():
            self.equiv_result.setText("Error: Please enter both programs to compare.")
            return
        
        if not output_vars_text.strip():
            self.equiv_result.setText("Error: Please specify output variables to compare.")
            return
        
        output_vars = [v.strip() for v in output_vars_text.split(',')]
        
        try:
            # Get loop unrolling depth
            unroll_depth = self.eq_unroll_depth_spinbox.value()
            
            # Parse the input programs
            statements1 = parse_program(program1_text)
            statements2 = parse_program(program2_text)
            
            # Convert to SSA with loop unrolling
            ssa_converter = SSAConverter()
            ssa_form1 = ssa_converter.convert_to_ssa(statements1, unroll_depth)
            ssa_converter.reset()
            ssa_form2 = ssa_converter.convert_to_ssa(statements2, unroll_depth)
            
            # Display SSA forms
            self.ssa1_output.setText("\n".join(ssa_form1))
            self.ssa2_output.setText("\n".join(ssa_form2))
            
            # Check equivalence
            smt_generator = SMTGenerator()
            is_equivalent, counterexamples = smt_generator.check_equivalence(ssa_form1, ssa_form2, output_vars)
            
            if is_equivalent:
                self.equiv_result.setText("Result: The programs are semantically equivalent for all inputs.")
            else:
                if not counterexamples:
                    self.equiv_result.setText("Result: The programs are NOT semantically equivalent, but no counterexample could be generated.")
                else:
                    self.equiv_result.setText("Result: The programs are NOT semantically equivalent. Counterexamples are shown below.")
                    self.display_counterexamples(counterexamples)
        
        except Exception as e:
            self.equiv_result.setText(f"Error during equivalence check: {str(e)}")
    
    def display_examples(self, examples):
        if not examples:
            return
        
        # Get all variables
        all_vars = set()
        for example in examples:
            all_vars.update(example.keys())
        
        # Sort variables for consistent display
        var_list = sorted(list(all_vars))
        
        # Set up table
        self.examples_table.setColumnCount(len(var_list))
        self.examples_table.setRowCount(len(examples))
        self.examples_table.setHorizontalHeaderLabels(var_list)
        
        # Fill table with data
        for row, example in enumerate(examples):
            for col, var in enumerate(var_list):
                value = example.get(var, "")
                self.examples_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        # Resize columns to content
        self.examples_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def display_counterexamples(self, counterexamples):
        if not counterexamples:
            return
        
        # Get all variables
        all_vars = set()
        for example in counterexamples:
            all_vars.update(example.keys())
        
        # Sort variables for consistent display
        var_list = sorted(list(all_vars))
        
        # Set up table
        self.counter_table.setColumnCount(len(var_list))
        self.counter_table.setRowCount(len(counterexamples))
        self.counter_table.setHorizontalHeaderLabels(var_list)
        
        # Fill table with data
        for row, example in enumerate(counterexamples):
            for col, var in enumerate(var_list):
                value = example.get(var, "")
                self.counter_table.setItem(row, col, QTableWidgetItem(str(value)))
        
        # Resize columns to content
        self.counter_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

# Main function to run the application
def main():
    app = QApplication(sys.argv)
    window = ProgramAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 