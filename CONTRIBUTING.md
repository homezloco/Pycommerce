
# Contributing to PyCommerce

Thank you for your interest in contributing to PyCommerce! This document provides guidelines and instructions for contributing to the project.

## 🎯 Ways to Contribute

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit bug fixes or new features
- **Documentation**: Improve or add documentation
- **Testing**: Help test new features and report bugs
- **Plugin Development**: Create plugins for the ecosystem

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- PostgreSQL
- Git
- Basic knowledge of FastAPI, Flask, and SQLAlchemy

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/pycommerce.git
   cd pycommerce
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Database**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/pycommerce_dev"
   python initialize_db.py
   ```

4. **Run Tests**
   ```bash
   python -m pytest
   ```

5. **Start Development Server**
   ```bash
   python main.py
   ```

## 📋 Development Guidelines

### Code Style
- Follow [PEP 8](https://pep8.org/) Python style guide
- Use meaningful variable and function names
- Add type hints to all function signatures
- Maximum line length: 88 characters (Black formatter)

### Documentation
- Add docstrings to all classes and functions
- Use Google-style docstrings
- Update relevant documentation files
- Include code examples where helpful

### Testing
- Write tests for all new features
- Maintain or improve test coverage
- Test both happy path and edge cases
- Use pytest for testing framework

### Git Workflow
- Create feature branches: `feature/your-feature-name`
- Write descriptive commit messages
- Keep commits focused and atomic
- Rebase before submitting pull requests

## 🐛 Reporting Bugs

### Before Reporting
1. Check if the bug has already been reported
2. Try to reproduce the issue
3. Gather relevant information (OS, Python version, etc.)

### Bug Report Template
```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**
1. Go to...
2. Click on...
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.11.0]
- PyCommerce Version: [e.g., 0.1.0]
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Problem It Solves**
What problem does this feature address?

**Proposed Solution**
How would you like this feature to work?

**Alternatives Considered**
Any alternative solutions you've considered.

**Additional Context**
Any other context or screenshots about the feature.
```

## 🔧 Code Contributions

### Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write your code
   - Add tests
   - Update documentation
   - Run tests locally

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

4. **Push to Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Submit Pull Request**
   - Use the pull request template
   - Link related issues
   - Provide clear description

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add product search endpoint
fix(auth): resolve JWT token expiration issue
docs(readme): update installation instructions
```

### Pull Request Template
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
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

## 🧪 Testing Guidelines

### Test Structure
```python
import pytest
from pycommerce.models.product import Product

class TestProduct:
    def test_product_creation(self):
        """Test basic product creation."""
        product = Product(name="Test Product", price=10.00)
        assert product.name == "Test Product"
        assert product.price == 10.00
        
    def test_product_validation(self):
        """Test product validation rules."""
        with pytest.raises(ValueError):
            Product(name="", price=-5.00)
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=pycommerce --cov-report=html

# Run specific test file
python -m pytest tests/test_products.py

# Run tests with specific marker
python -m pytest -m integration
```

## 🔌 Plugin Development

### Plugin Structure
```python
from pycommerce.core.plugin import Plugin

class MyCustomPlugin(Plugin):
    name = "my_plugin"
    version = "1.0.0"
    description = "Description of what the plugin does"
    
    def __init__(self):
        super().__init__()
        self.setup()
    
    def setup(self):
        """Initialize plugin."""
        pass
        
    def process(self, data):
        """Main plugin functionality."""
        return data
```

### Plugin Guidelines
- Follow the base plugin interface
- Include comprehensive documentation
- Add unit tests for plugin functionality
- Handle errors gracefully
- Use semantic versioning

## 📚 Documentation

### Types of Documentation
- **API Documentation**: Function and class docstrings
- **User Documentation**: How-to guides and tutorials
- **Developer Documentation**: Architecture and design decisions
- **Plugin Documentation**: Plugin development guides

### Writing Documentation
```python
def calculate_shipping(weight: float, distance: float) -> float:
    """Calculate shipping cost based on weight and distance.
    
    Args:
        weight: Package weight in kilograms
        distance: Shipping distance in kilometers
        
    Returns:
        Shipping cost in USD
        
    Raises:
        ValueError: If weight or distance is negative
        
    Example:
        >>> calculate_shipping(2.5, 100)
        15.50
    """
    if weight < 0 or distance < 0:
        raise ValueError("Weight and distance must be positive")
    
    return weight * 0.5 + distance * 0.1
```

## 🎨 UI/UX Contributions

### Design Guidelines
- Follow existing design patterns
- Ensure responsive design
- Maintain accessibility standards
- Test across different browsers
- Consider user experience flow

### Frontend Technologies
- HTML5/CSS3
- Bootstrap 5
- JavaScript (ES6+)
- Jinja2 templates
- Font Awesome icons

## 🚀 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, backwards compatible

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers bumped
- [ ] Release notes prepared

## 💬 Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code review and collaboration

### Code of Conduct
We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

Key points:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints
- Help maintain a positive environment

## 🏆 Recognition

Contributors are recognized through:
- GitHub contributor listings
- CHANGELOG.md credits
- Release note mentions
- Community spotlight features

## ❓ Questions?

If you have questions about contributing:
- Check existing documentation
- Search GitHub issues
- Start a GitHub discussion
- Reach out to maintainers

Thank you for contributing to PyCommerce! 🙏
