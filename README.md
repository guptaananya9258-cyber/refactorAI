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

