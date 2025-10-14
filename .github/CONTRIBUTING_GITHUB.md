# Contributing via GitHub

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/rackfish.git
   cd rackfish
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/originalowner/rackfish.git
   ```

4. Create a development branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Making Changes

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Make your changes

3. Run tests:
   ```bash
   pytest tests/
   ```

4. Run linting:
   ```bash
   ruff check rackfish/
   black rackfish/
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request on GitHub

## CI/CD

GitHub Actions will automatically:
- Run tests on all supported Python versions (3.8-3.12)
- Check code formatting (black)
- Run linting (ruff)
- Build distribution packages
- Upload coverage to Codecov

## Release Process

1. Update version in `rackfish/__init__.py` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Commit changes
4. Create and push a tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push upstream v1.0.0
   ```
5. Create a GitHub Release
6. GitHub Actions will automatically publish to PyPI

## Questions?

Open an issue on GitHub for discussion!
