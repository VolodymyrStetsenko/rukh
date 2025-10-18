# Contributing to RUKH

Thank you for your interest in contributing to RUKH! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/VolodymyrStetsenko/rukh/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, versions, etc.)
   - Logs or screenshots if applicable

### Suggesting Features

1. Check if the feature has already been requested
2. Create a new issue with:
   - Clear use case and motivation
   - Proposed implementation (if any)
   - Potential impact on existing features

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following the code style guidelines
4. **Write tests** for new functionality
5. **Update documentation** if needed
6. **Commit** using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `refactor:` code refactoring
   - `test:` adding or updating tests
   - `chore:` maintenance tasks
   - `perf:` performance improvements
7. **Push** to your fork and create a pull request

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(fuzz-runner): add adaptive fuzzing scheduler

Implement coverage-guided fuzzing with adaptive scheduling
to prioritize high-value test cases.

Closes #123
```

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 22+
- Python 3.11+
- Rust 1.75+
- Foundry (forge, anvil, cast)

### Local Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/rukh.git
cd rukh

# Install dependencies
make install

# Start services
make up

# Run tests
make test

# Run linters
make lint
```

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Use `ruff` for linting
- Use `mypy` for type checking
- Maximum line length: 100 characters

### Rust

- Follow Rust style guidelines
- Use `cargo fmt` for formatting
- Use `cargo clippy` for linting
- Write documentation comments for public APIs

### TypeScript/JavaScript

- Follow Airbnb style guide
- Use ESLint and Prettier
- Use TypeScript for type safety
- Maximum line length: 100 characters

### Solidity

- Follow Solidity style guide
- Use Foundry formatting
- Add NatSpec comments for public functions

## Testing

- Write unit tests for all new functionality
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage
- Include integration tests for complex features

### Running Tests

```bash
# All tests
make test

# Specific service
make test-service SERVICE=static-intel

# E2E tests
make e2e
```

## Documentation

- Update README.md if adding new features
- Add inline comments for complex logic
- Update API documentation in `docs/api/`
- Add examples for new functionality

## Review Process

1. Maintainers will review your PR within 3-5 business days
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be included in the next release

## Release Process

- Releases follow [Semantic Versioning](https://semver.org/)
- CHANGELOG.md is auto-generated from commit messages
- Release notes are published on GitHub Releases

## Questions?

If you have questions, feel free to:

- Open a [Discussion](https://github.com/VolodymyrStetsenko/rukh/discussions)
- Join our community chat (link TBD)
- Contact the maintainer: Volodymyr Stetsenko

---

Thank you for contributing to RUKH! 🚀

