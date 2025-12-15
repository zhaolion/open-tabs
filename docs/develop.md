# Developer Guide

This guide will help you set up your development environment and understand the development workflow for TabAPI.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Initialization](#project-initialization)
- [Git Hooks Setup](#git-hooks-setup)
- [Git Commit Guidelines](#git-commit-guidelines)
- [Development Workflow](#development-workflow)
- [Code Quality Tools](#code-quality-tools)

## Prerequisites

- **Python 3.14+** - Required for this project
- **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** - Version control

## Project Initialization

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TabAPI
```

### 2. Quick Setup (Recommended)

The easiest way to set up the project is using the Makefile:

```bash
# One command to install dependencies and set up git hooks
make setup
```

This will:
- Install all dependencies with `uv sync`
- Install git hooks (commit-msg and pre-commit)
- Configure git commit template

### 3. Manual Setup

If you prefer manual setup, or want to understand what `make setup` does:

```bash
# Install dependencies
uv sync

# Install git hooks
uv run pre-commit install --hook-type commit-msg
uv run pre-commit install

# Configure commit template
git config commit.template .gitmessage
```

**Using uv run:**

With `uv`, you don't need to manually activate the virtual environment. Use `uv run` to execute commands directly:

```bash
# Run any Python script
uv run python main.py

# Run any command in the virtual environment
uv run pre-commit --version
```

**Manual activation (optional):**

If you prefer to activate the environment manually:

```bash
source .venv/bin/activate
```

### 4. Verify Installation

```bash
# Check Python version
uv run python --version  # Should be 3.14+

# Run the main application
uv run python main.py

# Or using make
make run
```

## Quick Command Reference

The project includes a Makefile with commonly used commands. View all available commands:

```bash
make help
```

**Most used commands:**

```bash
make setup          # Complete project setup (run once)
make run            # Run the application
make check          # Run code quality checks (format + lint)
make pre-commit     # Run all pre-commit hooks
make clean          # Clean up generated files
```

**Full command list:**

| Command | Description |
|---------|-------------|
| `make setup` | Install dependencies + git hooks |
| `make install` | Install dependencies only |
| `make setup-hooks` | Install git hooks only |
| `make run` | Run the main application |
| `make fmt` | Format code with ruff |
| `make lint` | Run linter (ruff check) |
| `make check` | Run all code quality checks |
| `make pre-commit` | Run pre-commit hooks on all files |
| `make pre-commit-update` | Update pre-commit hooks |
| `make commit-check` | Validate last commit message |
| `make test` | Run tests (not yet implemented) |
| `make clean` | Clean up generated files |
| `make clean-all` | Deep clean (including .venv) |
| `make version` | Show Python and uv versions |
| `make deps` | Show installed dependencies |
| `make help` | Display help message |

## Git Hooks Setup

This project uses `pre-commit` to manage Git hooks, ensuring code quality and commit message standards.

**If you used `make setup`, git hooks are already installed!**

### Manual Git Hooks Installation

If you need to install hooks manually:

```bash
# Using make (recommended)
make setup-hooks

# Or manually
uv run pre-commit install --hook-type commit-msg
uv run pre-commit install
git config commit.template .gitmessage
```

### Verify Hooks Installation

```bash
# Check installed hooks
ls -la .git/hooks/

# You should see:
# - commit-msg (for commit message validation)
# - pre-commit (for code quality checks)
```

### Test the Hooks

Try making a commit with an invalid message:

```bash
git commit --allow-empty -m "bad message"
# This should be rejected with helpful error messages
```

Try with a valid message:

```bash
git commit --allow-empty -m "docs: test commit hook"
# This should pass
```

## Git Commit Guidelines

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification to maintain a clean and meaningful commit history.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type** (required): The type of change
- **scope** (optional): The area of the codebase affected
- **subject** (required): A brief description of the change
- **body** (optional): Detailed explanation of the change
- **footer** (optional): References to issues, breaking changes, etc.

### Types

Choose the appropriate type for your commit:

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(provider): add OpenAI adapter` |
| `fix` | Bug fix | `fix(router): correct provider selection logic` |
| `docs` | Documentation changes | `docs: update API usage examples` |
| `style` | Code style/formatting | `style: format with black` |
| `refactor` | Code refactoring | `refactor(client): simplify async API` |
| `perf` | Performance improvements | `perf(embedding): optimize vector storage` |
| `test` | Adding or updating tests | `test(agent): add tool calling tests` |
| `build` | Build system/dependencies | `build: add anthropic SDK dependency` |
| `ci` | CI/CD changes | `ci: add GitHub Actions workflow` |
| `chore` | Other changes | `chore: update .gitignore` |
| `revert` | Revert previous commit | `revert: feat(core): add OpenAI adapter` |

### Scopes

Scopes help identify which part of the codebase is affected. Based on TabAPI's architecture:

**Core Layer:**
- `core`, `provider`, `adapter`, `router`, `client`

**AI Infrastructure:**
- `cost`, `safety`, `observability`, `metrics`, `logging`

**Agent Framework:**
- `agent`, `tool`, `memory`, `orchestration`

**Context Engineering:**
- `prompt`, `template`, `rag`, `few-shot`

**General:**
- `deps`, `config`, `tests`, `docs`, `ci`

### Subject Guidelines

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize the first letter
- No period (.) at the end
- Keep it under 50 characters
- Be descriptive but concise

### Examples

#### Simple Commit

```
feat(provider): add Anthropic Claude adapter
```

#### Commit with Scope and Body

```
fix(router): handle provider failover correctly

When the primary provider fails, the router now correctly falls back
to the next available provider instead of raising an error.

Fixes #42
```

#### Breaking Change

```
refactor(core): simplify unified client API

- Remove redundant abstraction layers
- Improve type hints
- Better error messages

BREAKING CHANGE: `LLMClient.call()` renamed to `LLMClient.chat()`
```

#### Multiple Changes

```
feat(agent): implement tool calling and memory system

Add core functionality for AI agents:
- Tool registration and execution
- Function calling interface
- Short-term conversation memory
- Memory management utilities

Closes #15, #16
```

### Common Mistakes to Avoid

❌ Bad:
```
Updated the docs
fixed bug
Added new feature for users
feat: Added OpenAI support.
```

✅ Good:
```
docs: update installation instructions
fix(router): prevent null pointer error
feat(user): add user preference management
feat(provider): add OpenAI adapter
```

## Development Workflow

### Daily Development

1. **Pull latest changes**
   ```bash
   git pull origin main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feat/my-feature
   # or
   git checkout -b fix/bug-description
   ```

3. **Make your changes**
   - Write code
   - Run tests (when available)
   - Ensure code quality

4. **Commit with proper message**
   ```bash
   git add .
   git commit -m "feat(scope): descriptive message"
   ```

5. **Push and create PR**
   ```bash
   git push origin feat/my-feature
   ```

### Running the Application

```bash
# Run main application (recommended)
uv run python main.py

# Or activate virtual environment first
source .venv/bin/activate
python main.py
```

## Code Quality Tools

### Current Tools

The project currently uses:

- **pre-commit**: Git hooks framework
- **gitlint**: Commit message linter
- **ruff**: Fast Python linter and formatter (optional)

### Future Tools

As the project grows, we plan to add:

- **mypy**: Static type checking
- **pytest**: Testing framework
- **coverage**: Code coverage reporting

### Manual Code Quality Checks

```bash
# Run pre-commit on all files
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files

# Check commit message manually (gitlint runs automatically on commit)
uv run gitlint --msg-filename .git/COMMIT_EDITMSG
```

## IDE Configuration

### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- GitLens
- Conventional Commits

Recommended settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true
}
```

### PyCharm

1. Set Python interpreter to `.venv/bin/python`
2. Enable "Reformat code" on commit
3. Enable "Optimize imports" on commit

## Getting Help

- Check existing documentation in `docs/`
- Review the main [README](../README.md)
- Check open issues on GitHub
- Ask in project discussions

## Contributing

1. Follow the commit guidelines above
2. Write clean, readable code
3. Add tests for new features (when testing is set up)
4. Update documentation as needed
5. Ensure all hooks pass before pushing

Happy coding! 🚀
