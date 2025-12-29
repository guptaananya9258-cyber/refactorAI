"""
RefactorIQ - AI-Assisted Code Refactoring Tool
Backend Flask application for analyzing Python code quality
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import ast
import json
import os

# Optional AI integration
try:
    import openai
except Exception:
    openai = None

# Code formatter for fallback fixes
try:
    import autopep8
except Exception:
    autopep8 = None

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
        # Map variable name -> set of line numbers where it is defined
        defined_vars = {}
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
                    defined_vars.setdefault(arg.arg, set()).add(node.lineno)
            
            # Detect variable assignments and remember definition line
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_vars.setdefault(target.id, set()).add(getattr(target, 'lineno', node.lineno))
                    elif isinstance(target, ast.Tuple):
                        # e.g. a, b = ...
                        for elt in target.elts:
                            if isinstance(elt, ast.Name):
                                defined_vars.setdefault(elt.id, set()).add(getattr(elt, 'lineno', node.lineno))
            
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
        
        # Check for unused variables (use line info captured when possible)
        for var, def_lines in defined_vars.items():
            if var in ('self', 'cls', 'args', 'kwargs') or var.startswith('_'):
                continue
            if var not in used_vars:
                lineno = min(def_lines) if def_lines else 0
                issues.append({
                    'type': 'Unused Variable',
                    'severity': 'info',
                    'message': f"Variable '{var}' is created but never used in your code.\nRemove it to keep your code clean and easy to read.",
                    'line': lineno,
                    'suggestion': f"Delete the variable '{var}' if you don't need it, or use it somewhere in your code."
                })
                suggestions.append({
                    'type': 'Remove Unused Code',
                    'description': f"Remove unused variable '{var}' to make your code cleaner."
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
    Calculate a simple heuristic quality score (0-100).

    Scoring strategy:
    - Start from 100
    - Subtract points for errors/warnings/info
    - Penalize for very long files to encourage smaller modules

    Args:
        issues: list of issue dicts
        total_lines: number of lines in submitted code

    Returns:
        int: score 0-100
    """
    base_score = 100

    # Deduct points based on issue severity
    for issue in issues:
        sev = (issue.get('severity') or 'info').lower()
        if sev == 'error':
            base_score -= 12
        elif sev == 'warning':
            base_score -= 6
        else:
            base_score -= 2

    # Penalize very long files mildly
    if total_lines > 300:
        base_score -= min(20, (total_lines - 300) // 10)
    elif total_lines > 100:
        base_score -= min(10, (total_lines - 100) // 10)

    # Clamp
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


def detect_intent(code_text: str) -> str:
    """
    Heuristic intent detection: returns one of DSA / OOP / Control Flow / Utility
    """
    s = code_text.lower()
    if 'class ' in s or 'self' in s or 'def __init__' in s:
        return 'OOP'
    algo_keywords = ['sort', 'binary', 'search', 'dijkstra', 'bst', 'dfs', 'bfs', 'merge', 'quick', 'heap']
    if any(k in s for k in algo_keywords):
        return 'DSA'
    if any(k in s for k in ['if ', 'for ', 'while ', 'return ']):
        return 'Control Flow'
    return 'Utility / Script'


def call_openai_for_refactor(prompt: str, model: str | None = None, max_tokens: int = 1200) -> dict:
    """
    Call OpenAI ChatCompletion to get a structured JSON result.
    Returns parsed JSON on success, raises on failure.
    """
    if openai is None:
        raise RuntimeError('OpenAI library not installed')
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY not set')
    openai.api_key = api_key
    model = model or os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

    system = (
        "You are a professional code reviewer and refactoring assistant. "
        "When given source code or a problem, respond with a JSON object containing keys: "
        "'error_explanation', 'fixed_code', 'comments', 'intent', 'notes'. "
        "Do not include extra text outside the JSON. Keep code in the 'fixed_code' value."
    )

    # Use chat completion if available
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        text = resp['choices'][0]['message']['content']
        # Try to parse JSON from the model's output
        try:
            return json.loads(text)
        except Exception:
            # If model didn't return pure JSON, attempt to extract JSON substring
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except Exception as e:
                    raise RuntimeError(f'Failed to parse model output as JSON: {e}\nRaw output:\n{text}')
            raise RuntimeError('Model output is not JSON')
    except Exception as e:
        raise


@app.route('/api/refactor', methods=['POST'])
def api_refactor():
    """
    Production-ready refactor endpoint.

    Accepts JSON:
      - code: source code string (preferred)
      - problem: natural language problem description

    Returns JSON with:
      - error_explanation
      - fixed_code
      - comments (list)
      - intent
      - notes
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400

    if not data:
        return jsonify({'success': False, 'error': 'No payload provided'}), 400

    code = data.get('code')
    problem = data.get('problem')
    lang = (data.get('language') or 'python').lower()

    if not code and not problem:
        return jsonify({'success': False, 'error': 'Provide either `code` or `problem` in the JSON payload.'}), 400

    # Build prompt for AI if available
    prompt_text = ''
    if problem and not code:
        prompt_text = f"Solve and provide a production-ready, well-documented Python solution for the following problem:\n\n{problem}\n\nFollow these deliverables: error explanation, fixed code, and clean comments. Output JSON only."
    else:
        prompt_text = f"Analyze and fix the following Python source. Explain errors (syntax, logical, design), detect intent, and return corrected optimized code with compiler-style and mentor-style comments. Output JSON with keys: error_explanation, fixed_code, comments, intent, notes.\n\nSOURCE:\n{code}"

    # Attempt AI-powered path if API key is set
    if os.environ.get('OPENAI_API_KEY') and openai is not None:
        try:
            model_resp = call_openai_for_refactor(prompt_text)
            model_resp['success'] = True
            return jsonify(model_resp)
        except Exception as e:
            # Log and fallback
            print('OpenAI call failed:', e)

    # Fallback (no API key or AI failed): local static analysis + formatting
    result = {
        'success': True,
        'intent': detect_intent(code or problem or ''),
        'error_explanation': None,
        'fixed_code': None,
        'comments': [],
        'notes': 'Fallback local analysis. To enable AI-powered fixes set OPENAI_API_KEY.'
    }

    # If language is Python, run local analysis
    if lang == 'python' and code:
        is_valid, syntax_err = check_syntax_errors(code)
        if not is_valid:
            result['error_explanation'] = syntax_err
        analysis = analyze_code_with_ast(code)
        # Compose comments from issues
        comments = []
        for it in analysis.get('issues', []):
            comments.append({'line': it.get('line'), 'type': it.get('type'), 'severity': it.get('severity'), 'msg': it.get('message'), 'suggestion': it.get('suggestion')})
        result['comments'] = comments
        result['notes'] = analysis.get('suggestions') or []
        # Try to produce a minimally fixed code using autopep8
        if autopep8 is not None:
            try:
                fixed = autopep8.fix_code(code)
            except Exception:
                fixed = code
        else:
            fixed = code

        result['fixed_code'] = fixed
        result['score'] = analysis.get('score')
        return jsonify(result)

    # Language not supported in fallback
    return jsonify({'success': False, 'error': f'Language {lang} not supported for local fallback and no AI key available.'}), 400


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

