from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import ast
import os
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.isdir(FRONTEND_DIST):
    app.mount('/', StaticFiles(directory=FRONTEND_DIST, html=True), name='static')


def check_syntax_errors(code: str):
    try:
        compile(code, '<string>', 'exec')
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, {'type': 'SyntaxError', 'line': e.lineno or 0, 'message': str(e)}
    except IndentationError as e:
        return False, {'type': 'IndentationError', 'line': getattr(e, 'lineno', 0), 'message': str(e)}
    except Exception as e:
        return False, {'type': 'ParseError', 'line': 0, 'message': str(e)}


def detect_intent(code_text: str) -> str:
    s = (code_text or '').lower()
    if 'class ' in s or 'self' in s or 'def __init__' in s:
        return 'OOP'
    algo_keywords = ['sort', 'binary', 'search', 'dijkstra', 'bst', 'dfs', 'bfs', 'merge', 'quick', 'heap']
    if any(k in s for k in algo_keywords):
        return 'DSA'
    if any(k in s for k in ['if ', 'for ', 'while ', 'return ']):
        return 'Control Flow'
    return 'Utility / Script'


def analyze_code_with_ast(code: str):
    # Minimal analyzer: detects deep nesting and unused assignments
    issues = []
    try:
        tree = ast.parse(code)
    except Exception:
        return {'success': False, 'issues': [], 'error': 'parse_error'}

    defined = {}
    used = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.setdefault(t.id, set()).add(getattr(t, 'lineno', node.lineno))
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            # simple nesting depth check
            depth = get_nesting_depth(node)
            if depth > 4:
                issues.append({'type': 'Deep Nesting', 'line': node.lineno, 'message': f'{depth} levels deep', 'severity': 'error'})

    for var, lines in defined.items():
        if var not in used and not var.startswith('_'):
            issues.append({'type': 'Unused Variable', 'line': min(lines), 'message': f"'{var}' assigned but not used", 'severity': 'info'})

    return {'success': True, 'issues': issues}


def get_nesting_depth(node, depth=0):
    max_depth = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
            d = get_nesting_depth(child, depth + 1)
            max_depth = max(max_depth, d)
        else:
            d = get_nesting_depth(child, depth)
            max_depth = max(max_depth, d)
    return max_depth


@app.post('/api/analyze')
async def api_analyze(req: Request):
    payload = await req.json()
    code = payload.get('code', '')
    problem = payload.get('problem', '')
    lang = (payload.get('language') or 'python').lower()

    if lang != 'python':
        return JSONResponse({'success': False, 'error': 'Only python supported in v1'}, status_code=400)

    is_valid, syntax = check_syntax_errors(code)
    if not is_valid:
        return JSONResponse({'success': False, 'paused': True, 'message': 'Analysis paused until code is syntactically valid.', 'syntax_error': syntax})

    analysis = analyze_code_with_ast(code)

    # Attempt to use OpenAI if key present
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if OPENAI_API_KEY:
        # Defer to AI for corrected code and explanations if available
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            prompt = f"Given this Python source code:\n{code}\n\nProduce JSON with keys: error_explanation, fixed_code, comments, intent, explanation."
            resp = openai.ChatCompletion.create(model=os.environ.get('OPENAI_MODEL','gpt-4o-mini'), messages=[{'role':'user','content':prompt}], temperature=0.1)
            text = resp['choices'][0]['message']['content']
            try:
                data = json.loads(text)
                return JSONResponse({'success': True, 'from_ai': True, **data, 'analysis': analysis})
            except Exception:
                # fallback: return AI raw text
                return JSONResponse({'success': True, 'from_ai': True, 'raw': text, 'analysis': analysis})
        except Exception as e:
            print('OpenAI call failed', e)

    # Local fallback: format code and return analysis and intent
    try:
        import autopep8
        fixed = autopep8.fix_code(code)
    except Exception:
        fixed = code

    return JSONResponse({'success': True, 'from_ai': False, 'intent': detect_intent(code or problem), 'fixed_code': fixed, 'analysis': analysis})


@app.get('/api/health')
async def health():
    return {'status': 'ok'}
