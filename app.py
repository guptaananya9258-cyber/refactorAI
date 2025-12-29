"""
RefactorIQ - AI-Assisted Code Refactoring Tool
Backend Flask application for analyzing Python code quality
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ast
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Configuration
MAX_FUNCTION_LINES = 50  # Threshold for long functions
MAX_NESTING_DEPTH = 4    # Threshold for deep nesting


def check_syntax_errors(code):
    """
    Check for syntax errors including indentation errors.
    
    Args:
        code (str): Python code to check
        
    Returns:
        tuple: (is_valid, error_info) where error_info is None if valid
    """
    try:
        # Try to compile the code to catch syntax errors
        compile(code, '<string>', 'exec')
        # Try to parse with AST to catch more detailed errors
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        error_type = 'Syntax Error'
        if 'unexpected indent' in str(e).lower() or 'indentation' in str(e).lower():
            error_type = 'Indentation Error'
        
        error_info = {
            'type': error_type,
            'line': e.lineno if hasattr(e, 'lineno') and e.lineno else 0,
            'message': str(e),
            'reason': f'Cannot analyze code further because of {error_type.lower()}. Fix the syntax error first.'
        }
        return False, error_info
    except IndentationError as e:
        error_info = {
            'type': 'Indentation Error',
            'line': e.lineno if hasattr(e, 'lineno') and e.lineno else 0,
            'message': str(e),
            'reason': 'Cannot analyze code further because of indentation error. Fix the indentation first.'
        }
        return False, error_info
    except Exception as e:
        error_info = {
            'type': 'Parse Error',
            'line': 0,
            'message': str(e),
            'reason': 'Cannot parse the code. Check for syntax errors.'
        }
        return False, error_info


def check_unreachable_code(tree, code_lines):
    """
    Check for unreachable code (code after return, break, continue, raise).
    
    Args:
        tree: AST tree
        code_lines: List of code lines
        
    Returns:
        list: List of unreachable code issues
    """
    issues = []
    
    class UnreachableChecker(ast.NodeVisitor):
        def __init__(self):
            self.unreachable_lines = []
            
        def visit_FunctionDef(self, node):
            # Check for unreachable code in functions
            self._check_unreachable_in_node(node)
            self.generic_visit(node)
            
        def _check_unreachable_in_node(self, node):
            # Get all statements in the node
            if not hasattr(node, 'body') or not isinstance(node.body, list):
                return
                
            for i, stmt in enumerate(node.body):
                # Check if this statement makes following code unreachable
                if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    # Check if there are more statements after this
                    if i < len(node.body) - 1:
                        next_stmt = node.body[i + 1]
                        if hasattr(next_stmt, 'lineno'):
                            issues.append({
                                'type': 'Unreachable Code',
                                'severity': 'warning',
                                'message': f"Code after line {stmt.lineno} may be unreachable.\nThis code will never execute because of the {type(stmt).__name__.lower()} statement above it.",
                                'line': next_stmt.lineno,
                                'suggestion': 'Remove unreachable code or restructure your logic to make it reachable.'
                            })
    
    checker = UnreachableChecker()
    checker.visit(tree)
    return issues


def check_logical_errors(tree):
    """
    Check for common logical errors.
    
    Args:
        tree: AST tree
        
    Returns:
        list: List of logical error issues
    """
    issues = []
    
    class LogicalChecker(ast.NodeVisitor):
        def visit_If(self, node):
            # Check for always True/False conditions
            if isinstance(node.test, ast.Constant):
                if node.test.value is True:
                    issues.append({
                        'type': 'Logical Error',
                        'severity': 'warning',
                        'message': f"Condition on line {node.lineno} is always True.\nThis if statement will always execute, making it unnecessary.",
                        'line': node.lineno,
                        'suggestion': 'Remove the if statement or fix the condition.'
                    })
                elif node.test.value is False:
                    issues.append({
                        'type': 'Logical Error',
                        'severity': 'warning',
                        'message': f"Condition on line {node.lineno} is always False.\nThis if statement will never execute.",
                        'line': node.lineno,
                        'suggestion': 'Remove the if statement or fix the condition.'
                    })
            # Check for comparison with same variable (x == x, x != x)
            if isinstance(node.test, ast.Compare):
                if len(node.test.comparators) == 1:
                    left = node.test.left
                    right = node.test.comparators[0]
                    if isinstance(left, ast.Name) and isinstance(right, ast.Name):
                        if left.id == right.id:
                            op = type(node.test.ops[0]).__name__
                            if op in ['Eq', 'NotEq']:
                                issues.append({
                                    'type': 'Logical Error',
                                    'severity': 'error',
                                    'message': f"Comparing '{left.id}' with itself on line {node.lineno}.\nThis condition is always {'True' if op == 'Eq' else 'False'}.",
                                    'line': node.lineno,
                                    'suggestion': 'Fix the comparison to compare with a different variable or value.'
                                })
            self.generic_visit(node)
    
    checker = LogicalChecker()
    checker.visit(tree)
    return issues


def check_best_practices(tree):
    """
    Check for Python best practice violations.
    
    Args:
        tree: AST tree
        
    Returns:
        list: List of best practice issues
    """
    issues = []
    
    class BestPracticeChecker(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            # Check for functions without docstrings
            if not node.body or not isinstance(node.body[0], ast.Expr) or \
               not isinstance(node.body[0].value, ast.Constant) or \
               not isinstance(node.body[0].value.value, str):
                # No docstring found
                if len(node.body) > 3:  # Only flag if function is substantial
                    issues.append({
                        'type': 'Best Practice',
                        'severity': 'info',
                        'message': f"Function '{node.name}' doesn't have a docstring.\nDocstrings help explain what your function does.",
                        'line': node.lineno,
                        'suggestion': f"Add a docstring to function '{node.name}' to document its purpose."
                    })
            self.generic_visit(node)
        
        def visit_For(self, node):
            # Check for using range(len(...)) pattern
            if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
                if node.iter.func.id == 'range' and len(node.iter.args) == 1:
                    if isinstance(node.iter.args[0], ast.Call) and \
                       isinstance(node.iter.args[0].func, ast.Name) and \
                       node.iter.args[0].func.id == 'len':
                        issues.append({
                            'type': 'Best Practice',
                            'severity': 'info',
                            'message': f"Using 'range(len(...))' on line {node.lineno}.\nConsider using 'enumerate()' or iterating directly over the collection.",
                            'line': node.lineno,
                            'suggestion': 'Use enumerate() or iterate directly over items instead of range(len()).'
                        })
            self.generic_visit(node)
    
    checker = BestPracticeChecker()
    checker.visit(tree)
    return issues


def analyze_code_with_ast(code):
    """
    Analyze Python code step by step:
    1. First check for syntax errors (including indentation)
    2. If valid, check for logical errors, unreachable code, and best practices
    
    Args:
        code (str): Python code to analyze
        
    Returns:
        dict: Analysis results with issues, score, and suggestions
    """
    issues = []
    suggestions = []
    code_lines = code.split('\n')
    
    # STEP 1: Check for syntax errors (including indentation)
    is_valid, syntax_error = check_syntax_errors(code)
    
    if not is_valid:
        # Syntax error found - stop analysis
        return {
            'success': False,
            'syntax_status': 'Invalid',
            'syntax_error': syntax_error,
            'error': f"{syntax_error['type']} on line {syntax_error['line']}: {syntax_error['message']}",
            'line': syntax_error['line'],
            'reason': syntax_error['reason']
        }
    
    # STEP 2: Code is syntactically valid - continue analysis
    try:
        tree = ast.parse(code)
        
        # Track variables for unused variable detection
        defined_vars = set()
        used_vars = set()
        
        # Check for logical errors
        logical_issues = check_logical_errors(tree)
        issues.extend(logical_issues)
        
        # Check for unreachable code
        unreachable_issues = check_unreachable_code(tree, code_lines)
        issues.extend(unreachable_issues)
        
        # Check for best practices
        best_practice_issues = check_best_practices(tree)
        issues.extend(best_practice_issues)
        
        # Analyze AST nodes for other issues
        # (defined_vars and used_vars already initialized above)
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            # Detect function definitions
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                
                # Calculate function length - use end_lineno if available, otherwise estimate
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_lines = node.end_lineno - node.lineno + 1
                else:
                    # Estimate: count all statement nodes in the function
                    stmt_count = sum(1 for n in ast.walk(node) 
                                    if isinstance(n, (ast.Expr, ast.Assign, ast.Return, ast.If, 
                                                     ast.For, ast.While, ast.Try, ast.With)))
                    func_lines = max(stmt_count * 2, 10)  # Rough estimate
                
                # Check for long functions
                if func_lines > MAX_FUNCTION_LINES:
                    issues.append({
                        'type': 'Long Function',
                        'severity': 'warning',
                        'message': f"This function has {func_lines} lines, which is longer than recommended ({MAX_FUNCTION_LINES} lines).\nLong functions are harder to read and understand.",
                        'line': node.lineno,
                        'suggestion': f"Split this function into smaller, simpler functions that each do one thing."
                    })
                    suggestions.append({
                        'type': 'Extract Function',
                        'description': f"Break this function into smaller pieces. Each function should do one specific task."
                    })
                
                # Track function parameters as defined variables
                for arg in node.args.args:
                    defined_vars.add(arg.arg)
            
            # Detect variable assignments
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.add(target.id)
            
            # Detect variable usage
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_vars.add(node.id)
            
            # Detect nested structures (if, for, while, try)
            elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                nesting_depth = get_nesting_depth(node)
                if nesting_depth > MAX_NESTING_DEPTH:
                    issues.append({
                        'type': 'Deep Nesting',
                        'severity': 'error',
                        'message': f"Too many nested levels ({nesting_depth} levels deep).\nThis makes your code hard to follow and understand.",
                        'line': node.lineno,
                        'suggestion': 'Use early returns or move nested code into separate functions to make it simpler.'
                    })
                    suggestions.append({
                        'type': 'Reduce Nesting',
                        'description': 'Simplify nested code by returning early when possible or creating helper functions.'
                    })
        
        # Check for unused variables
        unused_vars = defined_vars - used_vars
        for var in unused_vars:
            # Skip common patterns like loop variables and special names
            if not var.startswith('_') and var not in ['self', 'cls', 'args', 'kwargs']:
                issues.append({
                    'type': 'Unused Variable',
                    'severity': 'info',
                    'message': f"Variable '{var}' is created but never used in your code.\nRemove it to keep your code clean and easy to read.",
                    'line': 0,
                    'suggestion': f"Delete the variable '{var}' if you don't need it, or use it somewhere in your code."
                })
                suggestions.append({
                    'type': 'Remove Unused Code',
                    'description': f"Remove unused variables to make your code cleaner and easier to understand."
                })
        
        # Calculate code quality score (0-100)
        score = calculate_quality_score(issues, len(code_lines))
        
        return {
            'success': True,
            'syntax_status': 'Valid',
            'issues': issues,
            'score': score,
            'suggestions': suggestions,
            'total_lines': len(code_lines)
        }
        
    except Exception as e:
        # This should not happen if syntax check passed, but handle it anyway
        return {
            'success': False,
            'syntax_status': 'Unknown',
            'error': f'Analysis Error: {str(e)}'
        }


def get_nesting_depth(node, depth=0):
    """
    Calculate the maximum nesting depth of a node.
    
    Args:
        node: AST node
        depth: Current depth level
        
    Returns:
        int: Maximum nesting depth
    """
    max_depth = depth
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            child_depth = get_nesting_depth(child, depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = get_nesting_depth(child, depth)
            max_depth = max(max_depth, child_depth)
    
    return max_depth


def calculate_quality_score(issues, total_lines):
    """
    Calculate code quality score based on issues found.
    
    Args:
        issues: List of issues found
        total_lines: Total lines of code
        
    Returns:
        int: Quality score (0-100)
    """
    base_score = 100
    
    # Deduct points based on issue severity
    for issue in issues:
        if issue['severity'] == 'error':
            base_score -= 10
        elif issue['severity'] == 'warning':
            base_score -= 5
        elif issue['severity'] == 'info':
            base_score -= 2
    
    # Bonus for clean code (no issues)
    if len(issues) == 0:
        base_score = 100
    
    # Ensure score is between 0 and 100
    return max(0, min(100, base_score))


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    API endpoint to analyze Python code.
    
    Expected JSON:
    {
        "code": "python code string"
    }
    
    Returns:
        JSON response with analysis results
    """
    try:
        data = request.get_json()
        
        if not data or 'code' not in data:
            return jsonify({
                'success': False,
                'error': 'No code provided. Please send code in JSON format: {"code": "your code here"}'
            }), 400
        
        code = data['code']
        
        if not code or not code.strip():
            return jsonify({
                'success': False,
                'error': 'Code is empty. Please provide Python code to analyze.'
            }), 400
        
        # Analyze the code
        result = analyze_code_with_ast(code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    import os
    print("=" * 50)
    print("RefactorIQ Server Starting...")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print(f"Templates folder exists: {os.path.exists('templates')}")
    print(f"Static folder exists: {os.path.exists('static')}")
    print("=" * 50)
    
    # Get port from environment variable (for cloud hosting) or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')  # Use 0.0.0.0 for cloud hosting
    
    # Disable debug mode in production (set DEBUG=False in environment)
    debug_mode = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"Visit http://localhost:{port} to use the application")
    if host == '0.0.0.0':
        print(f"Server is accessible from other devices on your network")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    try:
        app.run(debug=debug_mode, host=host, port=port)
    except OSError as e:
        if "Address already in use" in str(e) or "address is already in use" in str(e):
            print(f"\nERROR: Port {port} is already in use!")
            print(f"Please close the application using port {port} or change the port")
        else:
            print(f"\nERROR: {e}")

