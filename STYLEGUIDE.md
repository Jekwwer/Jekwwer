# Style Guide

This document outlines the style guide for **Jekwwer/Jekwwer**. It covers commit message formatting, coding conventions,
repository structure, and other aspects detailed in [Scope][SCOPE]. Adhering to these guidelines ensures a consistent
and readable project.

## Introduction

### Purpose

This guide standardizes coding and documentation practices to ensure consistency, enhance readability, and support
effective collaboration.

### Audience

This style guide is intended for:

- **Developers and Contributors:** Those writing code or documentation for the project.
- **Maintainers:** Individuals responsible for reviewing and merging contributions.
- **Reviewers:** Participants in code reviews to ensure adherence to standards.

### Scope

This document covers:

- **Repository Structure:** Directory layout, file naming conventions, and configuration file details.
- **Naming Conventions:** Standards for variables, constants, functions, and file/directory names.
- **Code Formatting and Style:** Guidelines on indentation, line length, brace styles, comments, EditorConfig settings,
  and linting/formatting tools.
- **Documentation:** Standards for creating and maintaining project documentation.
- **Additional Best Practices:** Other practices to improve overall code quality and project maintainability.

## Project Overview

### Project Goals

The primary objective of this project is to create a stunning, responsive, and dynamic SVG for Jekwwer's GitHub profile
`README`. The design aims to combine visual appeal with functionality.

### Technology Stack

The project utilizes **Python** and **SVG** as its core technologies.

### Target Audience

This project is specifically tailored for Jekwwer, aiming to meet his preferences and requirements for a personalized
GitHub profile SVG.

## Repository Structure

### Directory Layout

```plaintext
/ (root)                                # repository root
├── .devcontainer                       ├── # devcontainer-related configurations
│   ├── devcontainer.json               │   ├── # devcontainer setup
│   └── post-create.sh                  │   └── # post-create initialization script
├── .github                             ├── # GitHub-related configurations
│   ├── ISSUE_TEMPLATE                  │   ├── # issue templates
│   │   └── *                           │   │   └── # all files in the folder
│   ├── PULL_REQUEST_TEMPLATE           │   ├── # pull request templates
│   │   └── *                           │   │   └── # all files in the folder
│   ├── workflows                       │   ├── # GitHub workflows
│   │   ├── deploy.yml                  │   │   ├── # deployment workflow
│   │   └── update.yml                  │   │   └── # daily update workflow
│   ├── dependabot.yml                  │   ├── # Dependabot configuration
│   ├── FUNDING.yml                     │   ├── # funding configuration
│   └── PULL_REQUEST_TEMPLATE.md        │   ├── # default pull request template
├── docs                                ├── # GitHub Pages files
│   └── index.html                      │   └── # main index
├── .editorconfig                       ├── # editor configuration
├── .gitignore                          ├── # files to ignore in Git
├── .markdownlint.json                  ├── # markdown linting configuration
├── .pre-commit-config.yaml             ├── # pre-commit hook configuration
├── .prettierrc                         ├── # Prettier configuration
├── .yamllint.yml                       ├── # yaml linting configuration
├── CODE_OF_CONDUCT.md                  ├── # code of conduct
├── CONTRIBUTING.md                     ├── # contributing guidelines
├── cspell.json                         ├── # spell checking configuration
├── LICENSE                             ├── # MIT license
├── Makefile                            ├── # common development tasks
├── package-lock.json                   ├── # npm lock file
├── package.json                        ├── # npm package metadata
├── poetry.lock                         ├── # poetry lock file
├── pyproject.toml                      ├── # Python project metadata
├── README.md                           ├── # project README
├── SECURITY.md                         ├── # security information
├── STYLEGUIDE.md                       ├── # style guide (this document)
└── update_contributions.py             └── # svg update script
```

### File Naming Conventions

- **Documentation Files:** Key documentation files (e.g., `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `README.md`,
  `SECURITY.md`) are named using **SCREAMING_SNAKE_CASE**. Files within the `docs` and `assets` directories should be
  named in **kebab-case**.

- **Configuration Files:** Tool configuration files (e.g., `cspell.json`, `.editorconfig`, `.pre-commit-config.yaml`,
  `pyproject.toml`, `.prettierrc`) use lowercase naming, following the specific requirements of each tool.

- **Scripts:** Executable scripts are named in lowercase, typically using **snake_case** for clarity and consistency.

- **GitHub and Workflow Files:** Files within the `.github` directory—such as `dependabot.yml`, `FUNDING.yml`, and
  templates under `ISSUE_TEMPLATE`/`PULL_REQUEST_TEMPLATE` follow GitHub's naming conventions. This may include a mix of
  uppercase (e.g., `BUG_REPORT.md`) and lowercase (e.g., `config.yml`) filenames to ensure proper GitHub integration. In
  the `.github/workflows/` directory, YAML files for GitHub Actions are recommended to use **kebab-case** (e.g.,
  `deploy-app.yml`, `run-tests.yml`), aligning with GitHub's documentation and best practices.

### Directory Naming Conventions

- **General Naming:** Use lowercase letters for directory names. For multi-word names, use **kebab-case** (e.g.,
  `node-modules`, `source-files`). Choose names that clearly indicate the directory's content or purpose (e.g., `docs`
  for documentation, `assets` for media).

- **Special Directories:** Directories prefixed with a dot (e.g., `.github`, `.devcontainer`) have specific roles and
  should remain unchanged.

### Configuration Files

Key configuration files in the repository:

- `.devcontainer/devcontainer.json`: Development container setup, including VS Code settings, environment variables, and
  extensions.
- `.github/dependabot.yml`: Dependabot configuration for automated dependency version updates.
- `.gitignore`: Files and directories excluded from version control.
- `.editorconfig`: EditorConfig rules for consistent code style across editors.
- `.markdownlint.json`: Markdown linting rules and file exclusions.
- `.pre-commit-config.yaml`: Definitions for pre-commit hooks (linting, formatting, type checks, tests).
- `.prettierrc`: Prettier formatting rules for JSON, YAML, Markdown, etc.
- `.yamllint`: YAML linting configuration for CI and project YAML files.
- `cspell.json`: Code spell-check configuration with custom dictionaries and file globs.
- `Makefile`: Targets for common development tasks (linting, formatting, type checking, spell-checking, testing,Add
  commentMore actions running, and releasing).
- `package-lock.json`: npm lockfile capturing exact dependency versions.
- `package.json`: npm manifest with project metadata, script definitions, and dependency declarations.
- `poetry.lock`: Poetry lockfile locking Python dependency versions for reproducible environments.
- `pyproject.toml`: Python project metadata, Poetry settings, build-system requirements, and tool configurations
  (linting, typing, docs).

### Assets and Resources

SVG images are located in the `assets` directory:

- `bg.svg`: Background image for the GitHub Pages version.
- `profile-card-latest.svg`: README version with background.
- `profile-card-no-bg-latest.svg`: GitHub Pages version without background.
- `profile-card-no-bg.svg`: Template without background.
- `profile-card.svg`: Template with background.

## Naming Conventions

### General Guidelines

Naming should be clear, descriptive, and consistent across the project to ensure maintainability and readability.

### Variables

- **Python:** Use **snake_case** for variable names to enhance readability (e.g., `my_variable`).

### Constants

- **Python:** Constants should be written in **SCREAMING_SNAKE_CASE** to distinguish them from regular variables (e.g.,
  `MAX_LIMIT`).

### Functions/Methods

- **General Guidelines:** Function and method names should use descriptive verbs that accurately convey the action being
  performed.
- **Python:** Use **snake_case** for function and method names (e.g., `update_profile_svg`).

### Classes

- **Python:** Class names should be written in **CamelCase** to clearly distinguish them (e.g., `ProfileCardGenerator`).

### IDs and Classes (HTML, CSS, SVG)

- **General Guidelines:** Use **kebab-case** for all IDs and class names in HTML, CSS and SVG for consistency across the
  frontend (e.g., `icon-button`, `svg-logo`).

### CSS Custom Properties

- **General Guidelines:** Use **kebab-case** with double dashes for CSS custom properties to maintain consistency and
  readability (e.g., `--primary-color`).

### Attributes

- **HTML and SVG:** Use **kebab-case** for all attribute names (e.g., `data-index`, `aria-label`) to maintain uniformity
  with IDs and class names.

### Files

- For detailed guidelines on file naming, see [File Naming Conventions][FILE_NAMING_CONVENTIONS].

## Code Formatting and Style

The project adheres to the rules specified in the `.editorconfig`, `.markdownlint.json`, `.prettierrc`, `.yamllint` and
`pyproject.toml` configuration files.

### Indentation and Spacing

- **General Guidelines:** Use **2 spaces** per indentation level throughout the project. Tabs are allowed only forAdd
  commentMore actions `Makefile`. _(Enforced by EditorConfig and Prettier for supported files)_
- **Python:** Use **4 spaces** per indentation level for Python files. _(Enforced by EditorConfig)_

### Line Length

- **Code Files:** Limit lines to **88 characters**. _(Enforced by Ruff for Python, Prettier for supported files, and
  yamllint pre-commit hook for YAML)_
- **HTML, CSS, SVG:** Allow up to **120 characters** per line. _(Enforced by Prettier for HTML/CSS and markdownlint
  pre-commit for Markdown)_
- **Markdown:** Allow up to **120 characters** per line. _(Enforced by Prettier and markdownlint pre-commit)_
- **JSON:** No line-length limit. _(Enforced by Prettier)_

### Braces and Control Structures

- **Python:** Python uses indentation to define code blocks instead of braces. Ensure consistent and correct
  indentation.
- **HTML & SVG:**
  - **Nested Elements:** Format nested elements with **2-space** indentation. _(Enforced by Prettier and EditorConfig)_
  - **Tag Alignment:** Align opening and closing tags for clarity in HTML/SVG files. For SVG files, the
    [jock.svg][jock.svg] extension is recommended.

### Comments and Documentation

- **General Guidance:** All comments should enhance clarity and avoid redundancy with well-named functions and
  variables. Ensure comments do not exceed the maximum line length.
- **Inline Comments:** Place concise inline comments on the same line or immediately above the code they describe.
- **Block Comments / Docstrings:** Follow the Google-style docstring convention. The first line should be a short
  summary. _(Enforced by Ruff)_

  ```python
  """A script to fetch GitHub data, calculate streaks, and generate a heatmap grid."""
  ```

- **File Header Comments:** Every source file (except JSON, Markdown, `Python` and `LICENSE`) should begin with a
  one-line header comment describing its purpose.

  ```plaintext
  # .gitignore: Specifies files and directories that should not be tracked by Git.
  ```

  If a file starts with a shebang (e.g., `#!/bin/bash`), place the header comment immediately after the shebang line.

### EditorConfig

- **Purpose:** The `.editorconfig` file ensures consistent coding styles across all editors by specifying:
  - **Indentation:** 2 spaces (4 spaces for Python; tab-indented with 2-space width for `Makefile`)
  - **Line Endings:** Unix-style (`lf`)
  - **Charset:** UTF-8
  - **Max Line Length:** 88, 120 for Markdown _(Note: `.editorconfig` provides these values for reference; enforcement
    is handled by other tools.)_
  - **Final Newline:** Enforced
  - **Trailing Whitespace:** Trimmed (with exceptions)
- **Note:** Contributors should use an editor that supports EditorConfig to automatically apply these settings.

### Prettier

- **Purpose:** The `.prettierrc` file defines formatting rules for Prettier-supported files:
  - **Semicolons:** Enabled
  - **Quote Style:** Single quotes
  - **Trailing Commas:** Added where possible
  - **Tab Width:** 2 spaces
  - **End of Line:** Unix-style (`lf`)
  - **Print Width:** 88, 120 for CSS, HTML, and Markdown; JSON has no enforced limit.
- **Note:** Prettier runs in VS Code and as a pre-commit hook to auto-format code before commits.

### Ruff

- **Purpose:** Provide fast, incremental linting and formatting for Python code, enforcing style rules (line length,
  import order, docstrings) and catching errors early.
- **Note:** Ruff runs as a local pre-commit hook to auto-format code before commits.

### Additional Code Quality Tools

- **Pre-commit Framework:** Enforces automated checks before each commit via `.pre-commit-config.yaml`:
  - **pre-commit-hooks:** Normalizes line endings, trims whitespace, validates JSON/TOML/YAML syntax, detects private
    keys, checks for merge conflicts, enforces shebangs, and other generic sanity checks.
  - **pygrep-hooks:** Catches anti-patterns and enforces conventions (no `eval`, no `log.warn`, blanket
    `# noqa`/`# type: ignore`, improper mock usage, stray Unicode replacement chars).
- **markdownlint-cli & markdown-link-check:** Lints Markdown files according to `.markdownlint.json` rules and validate
  links.
- **yamllint:** Lints YAML files according to `.yamllint.yml` rules.
- **pyupgrade:** Auto-upgrades Python syntax to modern versions.
- **mypy:** Does static type checks for Python code.

## Documentation

### Inline Documentation

See [Comments and Documentation][COMMENTS-AND-DOCUMENTATION].

### External Documentation

- **Repository Documentation:** The root-level `README.md` offers an overview of the project and a preview of its
  appearance on the profile. Additional key documents such as `CONTRIBUTING.md`, `STYLEGUIDE.md`, `SECURITY.md`, and
  `LICENSE` are also maintained at the repository root.

- **GitHub Pages:** The `docs` directory contains files for GitHub Pages.

_Note: File and directory names referenced in Markdown should always be formatted using backticks, for example:_

```markdown
Other external documentation is maintained in the `docs` directory.
```

### Markdown References

- **Reference-Style Links:** Use reference-style links for clarity. For example:

  ```markdown
  [info][link]

  [link]: https://example.com
  ```

- **Local References:** For links to repository-related documents (e.g., `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md`) or
  internal sections, use **SCREAMING_SNAKE_CASE** for link identifiers and omit the file extension for documents. For
  example:

  ```markdown
  See [Code of Conduct][CODE_OF_CONDUCT].

  [CODE_OF_CONDUCT]: CODE_OF_CONDUCT.md
  ```

  And for internal sections:

  ```markdown
  See [File Naming Conventions][FILE_NAMING_CONVENTIONS].

  [FILE_NAMING_CONVENTIONS]: #file-naming-conventions
  ```

  **Note:** Local references should always appear at the top and be sorted alphabetically. For example:

  ```markdown
  [FILE_NAMING_CONVENTIONS]: #file-naming-conventions
  [SECURITY]: SECURITY.md
  [external-link]: https://example.com
  ```

- **External Links:** For links that reference external resources, use **kebab-case** for link identifiers. For example:

  ```markdown
  [info][external-link]

  [external-link]: https://example.com
  ```

  **Note:** External references should be sorted alphabetically and always appear below local references. For example:

  ```markdown
  [SECURITY]: SECURITY.md
  [external-link]: https://example.com
  ```

### Documentation Tools and Best Practices

#### Tools

- **cspell:** Spell-checks code and Markdown. Runs as a pre-commit hook; local command: `make spell`.
- **markdown-link-check:** Validates Markdown links. Runs as a pre-commit hook.
- **markdownlint:** Enforces Markdown style rules. Runs as a pre-commit hook.

#### Consistency and Updates

- Update documentation alongside code changes.
- Contributors should update docs when introducing new features or modifying existing functionality.

#### Style and Tone

- Maintain a semi-formal tone appropriate for a tech-oriented audience.
- Use clear, precise language and consistent formatting throughout.

#### Contribution Guidelines

- Documentation contributions follow the same process as code changes—submit pull requests for review according to the
  contribution guidelines.

## Additional Best Practices

### Security and Privacy

- Avoid exposing sensitive information in logs or error messages.
- Regularly review dependencies for security vulnerabilities.

### Error Handling and Logging

- Implement robust error handling to manage unexpected issues gracefully.
- Use structured logging to capture context without exposing sensitive data.

### Code Organization and Maintenance

- Keep the codebase clean and modular to facilitate understanding and future extensions.
- Regularly review and refactor code to eliminate redundancy.
- Use design patterns where appropriate to improve clarity and reusability.

## Conclusion

### Continuous Improvement

This document is a living resource that should evolve with the project. As new best practices emerge or project
requirements change, please update the guide to keep it relevant and effective.

### Feedback and Updates

Your input is valuable. If you have suggestions for improvements, clarifications, or additional guidelines, please reach
out to the maintainers or submit an [issue][issues]. For contributing guidelines, refer to
[`CONTRIBUTING.md`][CONTRIBUTING]; for security concerns, see [`SECURITY.md`][SECURITY]; for discussions, consult the
project's [discussion board][discussions] or contact the project owner at
[evgenii.shiliaev@jekwwer.com][evgenii.shiliaev@jekwwer.com].

---

This document is based on a template by [Evgenii Shiliaev][evgenii-shiliaev-github], licensed under [CC BY
4.0][jekwwer-markdown-docs-kit-license]. All additional content is licensed under [LICENSE][LICENSE].

[COMMENTS-AND-DOCUMENTATION]: #comments-and-documentation
[CONTRIBUTING]: CONTRIBUTING.md
[FILE_NAMING_CONVENTIONS]: #file-naming-conventions
[LICENSE]: LICENSE
[SCOPE]: #scope
[SECURITY]: SECURITY.md
[discussions]: https://github.com/Jekwwer/Jekwwer/discussions
[evgenii-shiliaev-github]: https://github.com/Jekwwer
[evgenii.shiliaev@jekwwer.com]: mailto:evgenii.shiliaev@jekwwer.com
[issues]: https://github.com/Jekwwer/Jekwwer
[jekwwer-markdown-docs-kit-license]: https://github.com/Jekwwer/markdown-docs-kit/blob/main/LICENSE
[jock.svg]: https://marketplace.visualstudio.com/items?itemName=jock.svg
