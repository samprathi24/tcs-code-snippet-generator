"""
Code Snippet Validator Module
Validates generated Python code for:
- Syntax correctness
- Runtime execution
- Requirement fulfillment
- Code quality
- Test case passing
"""

import ast
import re
import sys
from io import StringIO
from typing import Dict, List, Tuple, Any
import traceback


class CodeValidator:
    """
    Validates generated Python code snippets against requirements and test cases.
    
    Attributes:
        max_execution_time: Maximum time allowed for code execution (seconds)
        max_code_length: Maximum allowed code length (characters)
    """
    
    def __init__(self, max_execution_time=5, max_code_length=10000):
        self.max_execution_time = max_execution_time
        self.max_code_length = max_code_length
        self.errors = []
        self.warnings = []
    
    def validate(self, 
                 code_snippet: str, 
                 requirements: str = None,
                 test_cases: List[Dict] = None) -> Dict[str, Any]:
        """
        Main validation method - performs comprehensive code validation.
        
        Args:
            code_snippet (str): Generated Python code to validate
            requirements (str): Natural language requirements description
            test_cases (List[Dict]): Test cases with format:
                [{"input": {...}, "expected_output": ...}, ...]
        
        Returns:
            Dict with validation results including:
                - syntax_valid (bool)
                - execution_success (bool)
                - test_pass_rate (float)
                - code_quality_score (int)
                - meets_requirements (bool)
                - errors (List)
                - warnings (List)
                - overall_score (int)
        """
        self.errors = []
        self.warnings = []
        
        results = {
            'syntax_valid': False,
            'execution_success': False,
            'test_pass_rate': 0.0,
            'code_quality_score': 0,
            'meets_requirements': False,
            'errors': [],
            'warnings': [],
            'overall_score': 0,
            'details': {}
        }
        
        # Step 1: Check code length
        if len(code_snippet) > self.max_code_length:
            self.errors.append(f"Code exceeds maximum length ({self.max_code_length} chars)")
            results['errors'] = self.errors
            return results
        
        # Step 2: Syntax validation
        syntax_valid, syntax_msg = self._check_syntax(code_snippet)
        results['syntax_valid'] = syntax_valid
        results['details']['syntax'] = syntax_msg
        
        if not syntax_valid:
            self.errors.append(f"Syntax Error: {syntax_msg}")
            results['errors'] = self.errors
            return results
        
        # Step 3: Code quality analysis
        quality_score, quality_issues = self._analyze_code_quality(code_snippet)
        results['code_quality_score'] = quality_score
        self.warnings.extend(quality_issues)
        
        # Step 4: Execution testing
        exec_success, exec_output, exec_error = self._test_execution(code_snippet)
        results['execution_success'] = exec_success
        results['details']['execution'] = {
            'success': exec_success,
            'output': exec_output,
            'error': exec_error
        }
        
        if not exec_success:
            self.errors.append(f"Execution Error: {exec_error}")
        
        # Step 5: Test case validation
        if test_cases:
            test_results, pass_rate = self._run_test_cases(code_snippet, test_cases)
            results['test_pass_rate'] = pass_rate
            results['details']['test_cases'] = test_results
        
        # Step 6: Requirement matching
        if requirements:
            req_match = self._matches_requirements(code_snippet, requirements, exec_success)
            results['meets_requirements'] = req_match
        else:
            results['meets_requirements'] = exec_success
        
        # Step 7: Calculate overall score
        results['errors'] = self.errors
        results['warnings'] = self.warnings
        results['overall_score'] = self._calculate_overall_score(results)
        
        return results
    
    def _check_syntax(self, code_snippet: str) -> Tuple[bool, str]:
        """
        Verify Python syntax correctness.
        
        Args:
            code_snippet (str): Code to check
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            ast.parse(code_snippet)
            return True, "Syntax is valid"
        except SyntaxError as e:
            error_msg = f"Line {e.lineno}: {e.msg}"
            return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def _test_execution(self, code_snippet: str) -> Tuple[bool, str, str]:
        """
        Execute code and capture output/errors.
        
        Args:
            code_snippet (str): Code to execute
        
        Returns:
            Tuple of (success, output, error_message)
        """
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = captured_output = StringIO()
            
            # Execute the code
            exec_globals = {}
            exec(code_snippet, exec_globals)
            
            # Restore stdout
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            return True, output, ""
        
        except Exception as e:
            sys.stdout = old_stdout
            error_msg = f"{type(e).__name__}: {str(e)}"
            return False, "", error_msg
    
    def _run_test_cases(self, 
                        code_snippet: str, 
                        test_cases: List[Dict]) -> Tuple[List[Dict], float]:
        """
        Execute code against provided test cases.
        
        Args:
            code_snippet (str): Code to test
            test_cases (List[Dict]): Test cases with 'input' and 'expected_output'
        
        Returns:
            Tuple of (test_results, pass_rate)
        """
        test_results = []
        passed = 0
        
        for idx, test_case in enumerate(test_cases):
            try:
                # Extract test case components
                test_input = test_case.get('input')
                expected_output = test_case.get('expected_output')
                
                # Execute code with test input
                exec_globals = {}
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                # Create test execution environment
                if isinstance(test_input, dict):
                    exec_globals.update(test_input)
                    exec(code_snippet, exec_globals)
                else:
                    # For single input, assign to 'input' variable
                    exec_globals['input'] = test_input
                    exec(code_snippet, exec_globals)
                
                sys.stdout = old_stdout
                actual_output = captured_output.getvalue().strip()
                
                # Compare outputs
                expected_str = str(expected_output).strip()
                if actual_output == expected_str:
                    test_results.append({
                        'test_number': idx + 1,
                        'passed': True,
                        'input': test_input,
                        'expected': expected_output,
                        'actual': actual_output
                    })
                    passed += 1
                else:
                    test_results.append({
                        'test_number': idx + 1,
                        'passed': False,
                        'input': test_input,
                        'expected': expected_output,
                        'actual': actual_output
                    })
            
            except Exception as e:
                sys.stdout = old_stdout
                test_results.append({
                    'test_number': idx + 1,
                    'passed': False,
                    'input': test_case.get('input'),
                    'expected': test_case.get('expected_output'),
                    'actual': f"Error: {str(e)}"
                })
        
        # Calculate pass rate
        pass_rate = (passed / len(test_cases) * 100) if test_cases else 0
        return test_results, pass_rate
    
    def _analyze_code_quality(self, code_snippet: str) -> Tuple[int, List[str]]:
        """
        Analyze code quality and best practices.
        
        Args:
            code_snippet (str): Code to analyze
        
        Returns:
            Tuple of (quality_score, issues_found)
        """
        score = 100
        issues = []
        
        try:
            tree = ast.parse(code_snippet)
            
            # Check 1: Code has functions
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if not functions:
                issues.append("No functions defined - consider wrapping code in functions")
                score -= 10
            
            # Check 2: Docstrings
            has_docstring = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    if ast.get_docstring(node):
                        has_docstring = True
            
            if not has_docstring and len(functions) > 0:
                issues.append("Missing docstrings - add documentation to functions")
                score -= 15
            
            # Check 3: Variable naming (check for single letters except loop variables)
            poor_names = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and len(node.id) == 1:
                    if node.id not in ['i', 'j', 'k', 'x', 'y', 'z']:
                        poor_names.append(node.id)
            
            if poor_names:
                issues.append(f"Poor variable naming: {set(poor_names)} - use descriptive names")
                score -= 5
            
            # Check 4: Line length (rough heuristic)
            lines = code_snippet.split('\n')
            long_lines = sum(1 for line in lines if len(line) > 100)
            if long_lines > len(lines) * 0.2:
                issues.append("Some lines are too long (>100 chars) - improve readability")
                score -= 10
            
            # Check 5: Code complexity (nested depth)
            max_depth = self._calculate_nesting_depth(tree)
            if max_depth > 4:
                issues.append(f"High nesting depth ({max_depth}) - consider refactoring")
                score -= 10
            
            # Check 6: Try-except blocks
            try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
            if len(try_blocks) == 0 and len(functions) > 0:
                issues.append("No error handling - consider adding try-except blocks")
                score -= 5
            
            # Ensure score doesn't go below 0
            score = max(0, score)
            
        except Exception as e:
            issues.append(f"Could not analyze code quality: {str(e)}")
            score = 50
        
        return score, issues
    
    def _calculate_nesting_depth(self, node: ast.AST, depth: int = 0) -> int:
        """Calculate maximum nesting depth of code."""
        max_depth = depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While, ast.If, ast.With, ast.FunctionDef)):
                child_depth = self._calculate_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _matches_requirements(self, 
                             code_snippet: str, 
                             requirements: str,
                             execution_success: bool) -> bool:
        """
        Check if code appears to meet the stated requirements.
        
        Args:
            code_snippet (str): Generated code
            requirements (str): Natural language requirements
            execution_success (bool): Whether code executed without errors
        
        Returns:
            bool: Whether requirements appear to be met
        """
        if not execution_success:
            return False
        
        # Extract key requirement keywords
        requirement_keywords = self._extract_keywords(requirements)
        code_keywords = self._extract_keywords(code_snippet)
        
        # Check if code contains relevant keywords
        keyword_match = sum(1 for kw in requirement_keywords 
                           if kw.lower() in code_snippet.lower())
        
        # If at least 50% of requirement keywords are in code, likely matches
        if requirement_keywords:
            match_ratio = keyword_match / len(requirement_keywords)
            return match_ratio >= 0.5
        
        return True
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Remove common words and extract potential keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'is', 'it', 'to', 'of', 'in', 'from'}
        
        # Split and clean
        words = re.findall(r'\b[a-zA-Z_]\w*\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return list(set(keywords))
    
    def _calculate_overall_score(self, results: Dict[str, Any]) -> int:
        """
        Calculate overall validation score (0-100).
        
        Weighting:
        - Syntax valid: 20%
        - Execution success: 20%
        - Test pass rate: 30%
        - Code quality: 20%
        - Requirements met: 10%
        """
        score = 0
        
        # Syntax (20%)
        if results['syntax_valid']:
            score += 20
        
        # Execution (20%)
        if results['execution_success']:
            score += 20
        
        # Test cases (30%)
        test_rate = results.get('test_pass_rate', 0)
        score += (test_rate / 100) * 30
        
        # Code quality (20%)
        quality = results.get('code_quality_score', 0)
        score += (quality / 100) * 20
        
        # Requirements (10%)
        if results.get('meets_requirements', False):
            score += 10
        
        return int(score)


# Helper function for easy validation
def validate_code(code_snippet: str,
                 requirements: str = None,
                 test_cases: List[Dict] = None) -> Dict[str, Any]:
    """
    Quick validation function.
    
    Args:
        code_snippet (str): Code to validate
        requirements (str): Optional requirement description
        test_cases (List[Dict]): Optional test cases
    
    Returns:
        Dict with validation results
    """
    validator = CodeValidator()
    return validator.validate(code_snippet, requirements, test_cases)


# Example usage
if __name__ == "__main__":
    # Example 1: Simple function
    test_code = """
def add_numbers(a, b):
    '''Add two numbers and return the result.'''
    return a + b

result = add_numbers(5, 3)
print(result)
"""
    
    test_requirements = "Create a function that adds two numbers"
    test_cases = [
        {"input": {"a": 5, "b": 3}, "expected_output": "8"},
        {"input": {"a": 10, "b": 20}, "expected_output": "30"}
    ]
    
    validator = CodeValidator()
    results = validator.validate(test_code, test_requirements, test_cases)
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    print(f"Syntax Valid: {results['syntax_valid']}")
    print(f"Execution Success: {results['execution_success']}")
    print(f"Code Quality Score: {results['code_quality_score']}/100")
    print(f"Test Pass Rate: {results['test_pass_rate']:.1f}%")
    print(f"Meets Requirements: {results['meets_requirements']}")
    print(f"Overall Score: {results['overall_score']}/100")
    print(f"\nWarnings: {results['warnings']}")
    print(f"Errors: {results['errors']}")
    print("="*60)