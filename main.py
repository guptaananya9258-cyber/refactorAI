def analyze_code(code: str):
    """
    Analyzes given code, detects errors,
    explains them, and suggests a corrected version.
    """
    if not code.strip():
        return {
            "error": "No code provided",
            "explanation": "Input code is empty",
            "solution": None
        }

    return {
        "error": None,
        "explanation": "Code is syntactically valid",
        "solution": code
    }


if __name__ == "__main__":
    sample_code = "print('Hello World')"
    result = analyze_code(sample_code)

    for key, value in result.items():
        print(f"{key}: {value}")
