# Contributing to CrisisMap AI

Thank you for considering contributing to CrisisMap AI! This guide will help you get started with contributing to our project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

We pledge to make participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- MongoDB Atlas account (or local MongoDB)
- Basic knowledge of FastAPI, AI/ML, and web development

### First Time Setup

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/CrisisMap_AI.git
   cd CrisisMap_AI
   ```

2. **Set up the development environment**
   ```bash
   # Install development tools
   make setup-dev
   
   # Or manually:
   pip install -e ".[dev,monitoring,deployment]"
   pre-commit install
   ```

3. **Configure environment variables**
   ```bash
   cp crisismap_ai/.env.example crisismap_ai/.env
   # Edit .env with your configuration
   ```

4. **Run tests to verify setup**
   ```bash
   make test
   ```

## Development Setup

### Quick Setup

```bash
# Clone and setup everything
git clone https://github.com/Mukprojects/CrisisMap_AI.git
cd CrisisMap_AI
make quick-start
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run the application
make run-dev
```

### Docker Setup

```bash
# Build and run with Docker
make docker-build
make docker-run

# Or use Docker Compose
docker-compose up -d
```

## Project Structure

```
crisismap_ai/
├── api/                    # FastAPI application
│   ├── app.py             # Main application
│   └── models.py          # Pydantic models
├── database/              # Database operations
├── embedding/             # Vector embedding generation
├── models/                # AI/ML models
├── static/                # Frontend assets
├── templates/             # HTML templates
├── data_ingestion/        # Data processing pipeline
└── config.py              # Configuration

tests/
├── unit/                  # Unit tests
├── integration/           # Integration tests
└── conftest.py           # Test configuration

docs/                      # Documentation
Dataset/                   # Sample datasets
```

## Making Changes

### Branching Strategy

We use a simplified Git flow:

1. `main` - Production-ready code
2. `develop` - Development branch
3. Feature branches - `feature/description`
4. Bug fix branches - `fix/description`
5. Hotfix branches - `hotfix/description`

### Creating a Feature Branch

```bash
# Start from develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes...

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add crisis event search endpoint
fix(database): resolve connection timeout issue
docs: update API documentation
test(api): add unit tests for search endpoint
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests
```

### Writing Tests

1. **Unit tests** - Test individual functions/classes
   ```python
   # tests/unit/test_example.py
   import pytest
   from crisismap_ai.some_module import some_function

   def test_some_function():
       result = some_function("input")
       assert result == "expected_output"
   ```

2. **Integration tests** - Test component interactions
   ```python
   # tests/integration/test_api_integration.py
   def test_search_endpoint_integration(client):
       response = client.post("/api/search", json={"query": "test"})
       assert response.status_code == 200
   ```

3. **Test fixtures** - Use pytest fixtures for common test data

### Test Requirements

- All new features must include tests
- Bug fixes should include regression tests
- Aim for >80% code coverage
- Tests should be fast and isolated
- Use mocks for external dependencies

## Code Style

We use several tools to maintain code quality:

### Formatting and Linting

```bash
# Format code
make format

# Check formatting and linting
make lint

# Security check
make security-check
```

### Style Guidelines

1. **Python Style**
   - Follow PEP 8
   - Use Black for formatting (88 character line length)
   - Use isort for import organization
   - Use type hints where possible

2. **Documentation**
   - Write docstrings for all public functions/classes
   - Use Google-style docstrings
   - Include examples in docstrings

3. **Error Handling**
   - Use specific exception types
   - Include helpful error messages
   - Log errors appropriately

### Example Code Style

```python
"""Module docstring describing the module purpose."""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class CrisisEvent:
    """A crisis event with location and impact data.
    
    Args:
        title: The crisis event title
        location: Geographic location of the event
        date: Date when the event occurred
        
    Example:
        >>> event = CrisisEvent("Earthquake", "Japan", "2011-03-11")
        >>> print(event.title)
        "Earthquake"
    """
    
    def __init__(
        self,
        title: str,
        location: str,
        date: str,
        casualties: Optional[int] = None
    ) -> None:
        self.title = title
        self.location = location
        self.date = date
        self.casualties = casualties
    
    def get_summary(self) -> str:
        """Generate a summary of the crisis event.
        
        Returns:
            A formatted summary string.
            
        Raises:
            ValueError: If required data is missing.
        """
        if not self.title or not self.location:
            raise ValueError("Title and location are required")
            
        summary = f"{self.title} in {self.location} on {self.date}"
        if self.casualties:
            summary += f" (Casualties: {self.casualties})"
            
        return summary
```

## Submitting Changes

### Pull Request Process

1. **Before submitting:**
   - Run tests: `make test`
   - Check code style: `make lint`
   - Update documentation if needed
   - Add/update tests for your changes

2. **Create pull request:**
   - Use a descriptive title
   - Reference any related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes

3. **Pull request template:**
   ```markdown
   ## Description
   Brief description of changes made.

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added new tests for changes
   - [ ] Updated existing tests

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   ```

### Review Process

1. Automated checks must pass (tests, linting, etc.)
2. At least one maintainer review required
3. Address review feedback
4. Squash commits if requested
5. Maintainer will merge when approved

## Issue Guidelines

### Reporting Bugs

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug.

**Steps to Reproduce**
1. Step one
2. Step two
3. Step three

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happens.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Browser: [e.g., Chrome 96]

**Additional Context**
Screenshots, logs, etc.
```

### Feature Requests

Use the feature request template:

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Why is this feature needed?

**Proposed Solution**
How should this feature work?

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Mockups, examples, etc.
```

## Development Guidelines

### API Development

1. **Endpoints**
   - Use RESTful conventions
   - Include proper HTTP status codes
   - Validate input data
   - Return consistent response formats

2. **Error Handling**
   - Use appropriate HTTP status codes
   - Include helpful error messages
   - Log errors for debugging

3. **Documentation**
   - Document all endpoints
   - Include request/response examples
   - Use OpenAPI/Swagger annotations

### Database Operations

1. **Queries**
   - Use parameterized queries
   - Implement proper indexing
   - Handle connection errors

2. **Data Validation**
   - Validate data before insertion
   - Use appropriate data types
   - Implement data consistency checks

### AI/ML Components

1. **Model Management**
   - Version control for models
   - Fallback mechanisms
   - Performance monitoring

2. **Data Processing**
   - Handle large datasets efficiently
   - Implement data cleaning
   - Cache expensive operations

## Getting Help

- **Documentation**: Check the [README](README.md) and docs/
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainers for sensitive issues

## Recognition

Contributors will be recognized in:
- Contributors section of README
- Release notes for significant contributions
- Annual contributor acknowledgments

Thank you for contributing to CrisisMap AI! 🚀