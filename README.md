# RefactorIQ

RefactorIQ is a beginner-friendly AI-assisted static analysis web app for Python. It uses a Flask backend to analyze Python code via the AST module and a small frontend (HTML/CSS/JS) to paste code and view issues and a quality score.

Quick start

1. Create and activate a virtual environment (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

4. Open http://localhost:5000 in your browser and paste Python code to analyze.

What it detects

- Long functions
- Unused variables
- Deep nesting
- Logical and best-practice hints

API

- `POST /api/refactor` — main production endpoint.
  - Payload JSON: `{ "code": "...", "language": "python" }` or `{ "problem": "..." }`
  - Returns JSON with: `error_explanation`, `fixed_code`, `comments`, `intent`, `notes`, `success`.

Deployment (Render)

1. Create a new Web Service on Render and connect your GitHub repo.
2. Set the build command to:

```bash
pip install -r requirements.txt
```

3. Set the start command to:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 4
```

4. Add an environment variable `OPENAI_API_KEY` in the Render dashboard to enable AI-powered fixes (optional).

Deployment (Docker)

You can also deploy using the provided `Dockerfile`:

```bash
docker build -t refactoriq .
docker run -p 5000:5000 -e OPENAI_API_KEY="your_key" refactoriq
```

Notes

- For production, set `DEBUG=False` and provide `OPENAI_API_KEY` if you want the app to generate corrected code and rich explanations using the OpenAI API. The app will fall back to static AST analysis and `autopep8` formatting if the key is not provided.
- Keep your API key secret — set it in the hosting provider's environment variables.

Project structure

- `app.py` — Flask backend and AST analyzer
- `templates/index.html` — Frontend UI
- `static/style.css` — Dark theme styles
- `static/app.js` — Frontend logic to call backend
- `requirements.txt` — Python dependencies

Notes

- Keep this simple and hackathon-ready. The analyzer is static and conservative — use results as guidance.
# RefactorIQ

**AI-Assisted Code Refactoring Tool for Python**

RefactorIQ is a beginner-friendly web application that helps you improve your Python code quality by analyzing your code and providing actionable refactoring suggestions.

## Features

- 🔍 **Code Analysis**: Analyzes Python code using AST (Abstract Syntax Tree)
- 📊 **Quality Score**: Provides a code quality score (0-100)
- ⚠️ **Issue Detection**: Identifies common code issues:
  - Long functions (>50 lines)
  - Unused variables
  - Deep nesting (>4 levels)
- 💡 **Refactoring Suggestions**: Offers actionable suggestions to improve code quality
- 🎨 **Dark Theme UI**: Clean, modern developer-friendly interface

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Paste your Python code** in the textarea and click "Analyze Code"

## Project Structure

```
RefactorIQ/
│
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── templates/
│   └── index.html        # Main HTML page
│
└── static/
    ├── css/
    │   └── style.css     # Dark theme stylesheet
    └── js/
        └── main.js       # Frontend JavaScript
```

## API Endpoint

### POST `/analyze`

Analyzes Python code and returns issues, quality score, and suggestions.

**Request:**
```json
{
  "code": "def example():\n    pass"
}
```

**Response:**
```json
{
  "success": true,
  "issues": [
    {
      "type": "Long Function",
      "severity": "warning",
      "message": "Function 'example' is 60 lines long",
      "line": 1,
      "suggestion": "Consider breaking 'example' into smaller functions"
    }
  ],
  "score": 85,
  "suggestions": [
    {
      "type": "Extract Function",
      "description": "Function 'example' is too long..."
    }
  ],
  "total_lines": 60
}
```

## How It Works

1. **Frontend**: User pastes Python code in the textarea
2. **Backend**: Code is parsed using Python's AST module
3. **Analysis**: AST is traversed to detect:
   - Function length
   - Variable usage
   - Nesting depth
4. **Results**: Issues and suggestions are returned to the frontend
5. **Display**: Results are shown with color-coded severity levels

## Code Quality Score

The quality score (0-100) is calculated based on:
- **Base Score**: 100
- **Deductions**:
  - Error: -10 points
  - Warning: -5 points
  - Info: -2 points
- **Bonus**: Clean code with no issues gets 100 points

## Example Usage

Try analyzing this code:

```python
def process_data(data):
    result = []
    for item in data:
        if item is not None:
            if item.value > 0:
                if item.value < 100:
                    result.append(item.value * 2)
    return result

unused_var = 42
```

This will detect:
- Deep nesting (multiple if statements)
- Unused variable (`unused_var`)

## Technologies Used

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Code Analysis**: Python AST module

## License

This project is open source and available for educational purposes.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

**Made with ❤️ for developers who want to write better code**

## Continuous Deployment with GitHub Actions -> Render

A GitHub Actions workflow has been included to trigger a Render deploy when you push to `main`.

Setup steps:
1. In your GitHub repo, go to Settings -> Secrets -> Actions and add two secrets:
  - `RENDER_API_KEY` — your Render API key (create in Render dashboard -> Account -> API Keys)
  - `RENDER_SERVICE_ID` — the Render service ID for your web service (found in Render dashboard -> Service -> Settings -> Service ID)
2. The workflow file `.github/workflows/render-deploy.yml` will POST to the Render API to start a deploy on each push to `main`.

This allows an automated public deploy flow: push -> GitHub Actions -> Render -> public URL.

