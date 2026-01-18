# Contributing Guide

Thank you for your interest in contributing to Ingress to Gateway API Migrator! 🎉

> **Note:** This project was initially developed with Claude AI assistance to rapidly address urgent migration needs. We welcome human contributions to enhance and expand the tool!

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Running Tests](#running-tests)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Bugs are tracked via [GitHub Issues](https://github.com/jfpucheu/ingress-to-gateway-migrator/issues).

Before creating an issue, check if it already exists. When creating a new issue, include:

- **Clear and descriptive title**
- **Detailed description** of the problem
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Example Ingress** that causes the problem
- **Python version** and operating system
- **Complete error logs**

**Bug report template:**

```markdown
## Description
[Clear description of the bug]

## Steps to Reproduce
1. Create an ingress.yaml file with...
2. Run `./migrate.py -i ingress.yaml -g gateway`
3. Observe error...

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- Python version: 3.x
- OS: [Ubuntu 22.04 / macOS / Windows]
- Script version: [commit hash or version]

## Error Logs
```
[Paste logs here]
```

## Example Ingress
```yaml
[Paste your Ingress YAML here]
```
```

### Suggesting Features

Feature requests are also tracked via GitHub Issues.

**Feature request template:**

```markdown
## Feature Description
[Clear description of the proposed feature]

## Motivation
[Why this feature would be useful]

## Proposed Solution
[How you imagine this would work]

## Alternatives Considered
[Other approaches you've considered]

## Additional Context
[Screenshots, examples, etc.]
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/my-awesome-feature
   ```

2. **Make your changes** following [code standards](#code-standards)

3. **Add tests** if you're adding code
   - Unit tests for new functions
   - Integration tests for new migration scenarios

4. **Ensure all tests pass**
   ```bash
   python3 -m pytest tests/
   ```

5. **Update documentation** if necessary
   - README.md
   - docs/
   - Docstrings in code

6. **Commit your changes** with a descriptive message
   ```bash
   git commit -m "feat: add support for annotation X"
   ```

   Commit message format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Adding or modifying tests
   - `refactor:` Code refactoring
   - `style:` Style changes (formatting, etc.)
   - `chore:` Maintenance tasks

7. **Push to your fork**
   ```bash
   git push origin feature/my-awesome-feature
   ```

8. **Open a Pull Request** to the `main` branch

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows Python style standards (PEP 8)
- [ ] Documentation is updated
- [ ] New files have appropriate license headers
- [ ] Commit message follows conventional format
- [ ] Examples work correctly

## Code Standards

### Python Style

We follow [PEP 8](https://pep8.org/) with some specifics:

- **Indentation:** 4 spaces
- **Line length:** Maximum 100 characters
- **Imports:** Grouped and sorted (stdlib, third-party, local)
- **Docstrings:** Google style format

### Code Example

```python
def convert_http_path(self, path: Dict, ingress: Dict) -> Dict:
    """Convert an Ingress HTTP path to HTTPRoute rule.
    
    Args:
        path: Dictionary containing path configuration
        ingress: Complete Ingress to access annotations
        
    Returns:
        Dictionary representing an HTTPRoute rule
        
    Raises:
        ValueError: If the path is invalid
    """
    # Implementation...
    pass
```

### Code Verification

Before submitting, run:

```bash
# Format with black (optional)
black migrate.py

# Check with flake8
flake8 migrate.py --max-line-length=100

# Type checking with mypy (optional)
mypy migrate.py
```

## Running Tests

### Install test dependencies

```bash
pip install -r requirements-dev.txt
```

### Run all tests

```bash
python3 -m pytest tests/ -v
```

### Run specific tests

```bash
# Tests from a specific file
python3 -m pytest tests/test_migration.py -v

# Test a specific function
python3 -m pytest tests/test_migration.py::test_http_route_creation -v
```

### Code coverage

```bash
pytest --cov=migrate tests/ --cov-report=html
```

## Project Structure

```
ingress-to-gateway-migrator/
├── migrate.py              # Main script
├── README.md              # Main documentation
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
├── CONTRIBUTING.md        # This file
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI
├── docs/                  # Detailed documentation
│   ├── MIGRATION_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── FAQ.md
├── examples/              # Usage examples
│   └── sample-ingresses.yaml
└── tests/                 # Unit and integration tests
    ├── test_migration.py
    ├── test_annotations.py
    └── fixtures/
```

## Adding Support for New Annotations

To add support for a new Nginx annotation:

1. **Add the annotation** to `SUPPORTED_ANNOTATIONS` in `migrate.py`

2. **Implement the conversion** in the appropriate method

3. **Add tests** in `tests/test_annotations.py`

4. **Update documentation** in README.md and docs/

5. **Add an example** in `examples/`

### Example

```python
# In migrate.py
SUPPORTED_ANNOTATIONS = {
    # ... existing annotations
    'nginx.ingress.kubernetes.io/new-annotation': 'description',
}

# Implementation in convert_http_path or create_http_route
if 'nginx.ingress.kubernetes.io/new-annotation' in annotations:
    new_value = annotations['nginx.ingress.kubernetes.io/new-annotation']
    # Conversion logic...
```

## Questions?

If you have questions, feel free to:

- Open a [GitHub Discussion](https://github.com/jfpucheu/ingress-to-gateway-migrator/discussions)
- Join our [Slack channel](#) (if available)
- Contact the maintainers

## Maintainers

- [@jfpucheu](https://github.com/jfpucheu)

## AI Development Note

This project was initially developed with Claude AI assistance. We believe in transparency about AI usage and welcome contributors to help evolve this tool beyond its AI-generated foundation. Human insight, experience, and creativity are invaluable for making this tool even better!

Thank you for contributing! 🙏
