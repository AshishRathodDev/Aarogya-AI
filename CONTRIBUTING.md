
# Contributing to Aarogya-AI

Thank you for considering contributing to Aarogya-AI! We welcome contributions from the community and are excited to see what you bring to this AI-powered healthcare project.

## 🚀 How to Contribute

### 1. Fork & Clone
```
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/Aarogya-AI.git
cd Aarogya-AI
```

### 2. Create Feature Branch
```
git checkout -b feature/AmazingFeature
# or for bug fixes:
git checkout -b bugfix/fix-issue-name
```

### 3. Make Your Changes
- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```
# Run local tests
python -m pytest tests/
# Test with Docker
docker-compose up --build
```

### 5. Commit & Push
```
git add .
git commit -m 'Add AmazingFeature: brief description of what it does'
git push origin feature/AmazingFeature
```

### 6. Create Pull Request
- Go to the original repository on GitHub
- Click "New Pull Request"
- Provide a clear description of your changes
- Reference any related issues

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- Google Cloud SDK (for deployment)

### Local Development Environment

```
# Clone repository
git clone https://github.com/AshishRathodDev/Aarogya-AI.git
cd Aarogya-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Google Cloud credentials (optional for local dev)
# Add your service account JSON file

# Run with Docker (Recommended)
docker-compose up --build

# Access applications:
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Alternative: Run Services Individually
```
# Terminal 1: Start FastAPI backend
uvicorn src.aarogya_ai.api.main:app --reload --port 8000

# Terminal 2: Start Streamlit dashboard
streamlit run dashboard.py --server.port 8501
```

## 📝 Code Style Guidelines

### Python Code Style
- Follow **PEP 8** standards
- Use **type hints** for function parameters and return values
- Write **docstrings** for all functions, classes, and modules
- Use **meaningful variable names** (avoid single letters except for loops)
- Keep functions small and focused (max 20-30 lines)

### Example Code Style:
```
def extract_medical_data(file_path: str) -> Dict[str, Any]:
    """
    Extract structured data from medical report file.
    
    Args:
        file_path (str): Path to the medical report file
        
    Returns:
        Dict[str, Any]: Structured medical data with patient details and test results
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    # Implementation here
    pass
```

### Commit Message Guidelines
Use conventional commits format:
```
feat: add new medical parser for lab reports
fix: resolve file upload timeout issue
docs: update API documentation
test: add unit tests for fraud detection
refactor: optimize text extraction performance
```

## 🧪 Testing

### Running Tests
```
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_medical_parser.py
```

### Test Structure
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and data flow
- **Performance Tests**: Test with large files and concurrent requests

### Writing Tests
```
import pytest
from src.aarogya_ai.parser import RegexParser

def test_medical_parser_extracts_patient_name():
    """Test that parser correctly extracts patient name."""
    parser = RegexParser()
    sample_text = "Patient Name: John Doe"
    result = parser.parse(sample_text)
    assert result['patient_details']['name'] == "John Doe"
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Bug Description**: Clear description of the issue
2. **Steps to Reproduce**: Step-by-step instructions
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, browser (if applicable)
6. **Screenshots**: If visual issue
7. **Error Logs**: Any error messages or stack traces

### Bug Report Template:
```
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g. macOS 12.0]
- Python: [e.g. 3.11.0]
- Browser: [e.g. Chrome 120.0]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** your feature would solve
3. **Explain your proposed solution**
4. **Consider alternatives** you've thought about
5. **Additional context** like mockups or examples

## 🔧 Development Guidelines

### Project Structure
```
Aarogya-AI/
├── src/
│   └── aarogya_ai/
│       ├── api/              # FastAPI backend
│       ├── data_processing/  # Text extraction & processing
│       ├── fraud_detection/  # Anomaly detection algorithms
│       ├── database/         # Database operations
│       └── parser.py         # Medical report parsers
├── tests/                    # Unit and integration tests
├── notebooks/               # Jupyter notebooks for analysis
├── screenshots/             # Application screenshots
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

### Key Technologies
- **Backend**: FastAPI, Python 3.11, pandas, scikit-learn
- **Frontend**: Streamlit, HTML/CSS
- **AI/ML**: Google Generative AI, PyMuPDF, regex
- **Infrastructure**: Docker, Google Cloud Run
- **Database**: SQLite (dev), PostgreSQL (production ready)

### Performance Considerations
- **File Processing**: Handle files up to 200MB efficiently
- **API Response**: Target < 30 seconds for most requests
- **Memory Usage**: Optimize for serverless environment
- **Error Handling**: Graceful degradation when AI services fail

## 📞 Questions & Support

### Getting Help
- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: ashish3110rathod@gmail.com for direct contact

### Community Guidelines
- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow our code of conduct

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- **New Medical Report Formats**: Support for more document types
- **Enhanced AI Models**: Improve parsing accuracy
- **Performance Optimization**: Faster processing times
- **Security Enhancements**: Additional privacy protections

### Medium Priority
- **User Interface**: Improved dashboard design
- **Mobile Support**: Responsive design improvements
- **API Extensions**: Additional endpoints and features
- **Documentation**: Tutorials and guides

### Beginner Friendly
- **Bug Fixes**: Small issues and edge cases
- **Test Coverage**: Writing unit tests
- **Documentation**: Improving comments and docs
- **Code Style**: Formatting and linting improvements

## 📄 License

By contributing to Aarogya-AI, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be recognized in our README and release notes. We appreciate every contribution, no matter how small!

---

**Thank you for contributing to Aarogya-AI! Together, we're making healthcare more accessible through AI.** 🚀
```

***

## 🛠️ **Commands to Create File:**

```bash
cd Aarogya-AI

# Create CONTRIBUTING.md file
cat > CONTRIBUTING.md << 'EOF'
# Contributing to Aarogya-AI

Thank you for considering contributing to Aarogya-AI! We welcome contributions from the community and are excited to see what you bring to this AI-powered healthcare project.

## 🚀 How to Contribute

### 1. Fork & Clone
```
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/Aarogya-AI.git
cd Aarogya-AI
```

### 2. Create Feature Branch
```
git checkout -b feature/AmazingFeature
# or for bug fixes:
git checkout -b bugfix/fix-issue-name
```

### 3. Make Your Changes
- Write clean, readable code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 4. Test Your Changes
```
# Run local tests
python -m pytest tests/
# Test with Docker
docker-compose up --build
```

### 5. Commit & Push
```
git add .
git commit -m 'Add AmazingFeature: brief description of what it does'
git push origin feature/AmazingFeature
```

### 6. Create Pull Request
- Go to the original repository on GitHub
- Click "New Pull Request"
- Provide a clear description of your changes
- Reference any related issues

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- Google Cloud SDK (for deployment)

### Local Development Environment

```
# Clone repository
git clone https://github.com/AshishRathodDev/Aarogya-AI.git
cd Aarogya-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure Google Cloud credentials (optional for local dev)
# Add your service account JSON file

# Run with Docker (Recommended)
docker-compose up --build

# Access applications:
# Dashboard: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Alternative: Run Services Individually
```
# Terminal 1: Start FastAPI backend
uvicorn src.aarogya_ai.api.main:app --reload --port 8000

# Terminal 2: Start Streamlit dashboard
streamlit run dashboard.py --server.port 8501
```

## 📝 Code Style Guidelines

### Python Code Style
- Follow **PEP 8** standards
- Use **type hints** for function parameters and return values
- Write **docstrings** for all functions, classes, and modules
- Use **meaningful variable names** (avoid single letters except for loops)
- Keep functions small and focused (max 20-30 lines)

### Example Code Style:
```
def extract_medical_data(file_path: str) -> Dict[str, Any]:
    """
    Extract structured data from medical report file.
    
    Args:
        file_path (str): Path to the medical report file
        
    Returns:
        Dict[str, Any]: Structured medical data with patient details and test results
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    # Implementation here
    pass
```

### Commit Message Guidelines
Use conventional commits format:
```
feat: add new medical parser for lab reports
fix: resolve file upload timeout issue
docs: update API documentation
test: add unit tests for fraud detection
refactor: optimize text extraction performance
```

## 🧪 Testing

### Running Tests
```
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_medical_parser.py
```

### Test Structure
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and data flow
- **Performance Tests**: Test with large files and concurrent requests

### Writing Tests
```
import pytest
from src.aarogya_ai.parser import RegexParser

def test_medical_parser_extracts_patient_name():
    """Test that parser correctly extracts patient name."""
    parser = RegexParser()
    sample_text = "Patient Name: John Doe"
    result = parser.parse(sample_text)
    assert result['patient_details']['name'] == "John Doe"
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Bug Description**: Clear description of the issue
2. **Steps to Reproduce**: Step-by-step instructions
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, browser (if applicable)
6. **Screenshots**: If visual issue
7. **Error Logs**: Any error messages or stack traces

### Bug Report Template:
```
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g. macOS 12.0]
- Python: [e.g. 3.11.0]
- Browser: [e.g. Chrome 120.0]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

For new features:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** your feature would solve
3. **Explain your proposed solution**
4. **Consider alternatives** you've thought about
5. **Additional context** like mockups or examples

## 🔧 Development Guidelines

### Project Structure
```
Aarogya-AI/
├── src/
│   └── aarogya_ai/
│       ├── api/              # FastAPI backend
│       ├── data_processing/  # Text extraction & processing
│       ├── fraud_detection/  # Anomaly detection algorithms
│       ├── database/         # Database operations
│       └── parser.py         # Medical report parsers
├── tests/                    # Unit and integration tests
├── notebooks/               # Jupyter notebooks for analysis
├── screenshots/             # Application screenshots
├── docker-compose.yml       # Local development setup
├── requirements.txt         # Python dependencies
└── README.md               # Project documentation
```

### Key Technologies
- **Backend**: FastAPI, Python 3.11, pandas, scikit-learn
- **Frontend**: Streamlit, HTML/CSS
- **AI/ML**: Google Generative AI, PyMuPDF, regex
- **Infrastructure**: Docker, Google Cloud Run
- **Database**: SQLite (dev), PostgreSQL (production ready)

### Performance Considerations
- **File Processing**: Handle files up to 200MB efficiently
- **API Response**: Target < 30 seconds for most requests
- **Memory Usage**: Optimize for serverless environment
- **Error Handling**: Graceful degradation when AI services fail

## 📞 Questions & Support

### Getting Help
- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Email**: ashish3110rathod@gmail.com for direct contact

### Community Guidelines
- Be respectful and inclusive
- Help others learn and grow
- Focus on constructive feedback
- Follow our code of conduct

## 🎯 Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- **New Medical Report Formats**: Support for more document types
- **Enhanced AI Models**: Improve parsing accuracy
- **Performance Optimization**: Faster processing times
- **Security Enhancements**: Additional privacy protections

### Medium Priority
- **User Interface**: Improved dashboard design
- **Mobile Support**: Responsive design improvements
- **API Extensions**: Additional endpoints and features
- **Documentation**: Tutorials and guides

### Beginner Friendly
- **Bug Fixes**: Small issues and edge cases
- **Test Coverage**: Writing unit tests
- **Documentation**: Improving comments and docs
- **Code Style**: Formatting and linting improvements

## 📄 License

By contributing to Aarogya-AI, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be recognized in our README and release notes. We appreciate every contribution, no matter how small!

---

**Thank you for contributing to Aarogya-AI! Together, we're making healthcare more accessible through AI.** 🚀
EOF



