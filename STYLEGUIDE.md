# Style Guide

This document outlines the style guide for **Jekwwer/Jekwwer**.
It covers commit message formatting, coding conventions, repository structure,
and other aspects detailed in [Scope][SCOPE].
Adhering to these guidelines ensures a consistent and readable project.

## Introduction

### Purpose

This guide standardizes coding and documentation practices to ensure consistency, enhance readability,
and support effective collaboration.

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

The project utilizes **Python** and **SVG** as its core technologies. Key dependencies include:

- `types-requests`
- `requests`

For ensuring code quality and security, the project uses [tox][tox-web] with the following configurations:

- `tox`: Executes all environments (lint, format, bandit, mypy).
- `tox -e lint`: Runs linters such as flake8, pylint, isort, and autopep8 to verify code quality.
- `tox -e format`: Automatically formats the code.
- `tox -e bandit`: Scans for security vulnerabilities.
- `tox -e mypy`: Checks for proper type annotations .

### Target Audience

This project is specifically tailored for Jekwwer, aiming to meet his preferences and requirements for a personalized
GitHub profile SVG.

## Repository Structure

### Directory Layout

```plaintext
/ (root)                                # repository root
├── .devcontainer                       ├── # devcontainer-related configurations
│   └── devcontainer.json               │   └── # devcontainer setup
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
├── .pre-commit-config.yaml             ├── # pre-commit hook configuration
├── .prettierrc                         ├── # Prettier configuration
├── CODE_OF_CONDUCT.md                  ├── # code of conduct
├── CONTRIBUTING.md                     ├── # contributing guidelines
├── cspell.json                         ├── # spell checking configuration
├── LICENSE                             ├── # MIT license
├── pyproject.toml                      ├── # python package configuration
├── README.md                           ├── # project README
├── SECURITY.md                         ├── # security information
├── STYLEGUIDE.md                       ├── # style guide (this document)
├── tox.ini                             ├── # tox configuration
└── update_contributions.py             └── # svg update script
```

### File Naming Conventions

- **Documentation Files:**
  Key documentation files (e.g., `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `README.md`, `SECURITY.md`) are named using
  **SCREAMING_SNAKE_CASE** (uppercase with underscores). Files within the `docs` and `assets` directories
  should be named in lowercase.

- **Configuration Files:**
  Tool configuration files (e.g., `cspell.json`, `.editorconfig`, `.pre-commit-config.yaml`, `pyproject.toml`,
  `.prettierrc`, `tox.ini`) use lowercase naming, following the specific requirements of each tool.

- **Scripts:**
  Executable scripts are named in lowercase, typically using **snake_case** for clarity and consistency.

- **GitHub and Workflow Files:**
  Files in the `.github` directory (e.g., `dependabot.yml`, `FUNDING.yml`, and
  templates under `ISSUE_TEMPLATE`/`PULL_REQUEST_TEMPLATE`) follow their provided naming conventions.
  This may include a mix of uppercase (e.g., `BUG_REPORT.md`) and lowercase (e.g., `config.yml`) names
  to ensure proper GitHub integration.

### Directory Naming Conventions

- **General Naming:**
  Use lowercase letters for directory names. For multi-word names, use lowercase without special characters.
  Choose names that clearly indicate the directory's content or purpose (e.g., `docs` for documentation,
  `assets` for media).

- **Special Directories:**
  Directories prefixed with a dot (e.g., `.github`, `.devcontainer`) have specific roles and should remain unchanged.

### Configuration Files

Key configuration files in the repository include:

- `.gitignore`: Specifies files and directories to exclude from version control.
- `.editorconfig`: Defines coding styles across editors.
- `.pre-commit-config.yaml`: Specifies pre-commit hooks.
- `.prettierrc`: Contains formatting rules.
- `cspell.json`: Sets spelling rules for consistency.
- `pyproject.toml`: Configures Python package settings.
- `tox.ini`: Configures testing environments using tox.

### Assets and Resources

SVG images are located in the `assets` directory:

- `bg.svg`: Background image for the GitHub Pages version.
- `profile-card-latest.svg`: README version with background.
- `profile-card-no-bg-latest.svg`: GitHub Pages version without background.
- `profile-card-no-bg.svg`: Template without background.
- `profile-card.svg`: Template with background.

## Naming Conventions

### Variables

- **Python:**
  Use **snake_case** for variable names (e.g., `my_variable`).
- **HTML:**
  Use lowercase letters with hyphens for attribute identifiers (e.g., `data-value`).

### Constants

- **Python:**
  Define constants in **SCREAMING_SNAKE_CASE** (e.g., `MAX_LIMIT`).
- **HTML/CSS:**
  For CSS custom properties used in HTML, use **kebab-case** with a preceding double dash (e.g., `--main-color`).

### Functions/Methods

- **General Guideline:**
  Function and method names should be descriptive verbs that clearly indicate their action.
- **Python:**
  Use **snake_case** (e.g., `update_profile_svg`).

### Classes

- **Python:**
  Use **CamelCase** for class names (e.g., `ProfileCardGenerator`).
- **HTML:**
  Class names should be written in lowercase with hyphens (e.g., `profile-card`).
- **SVG:**
  For SVG element classes, follow the same convention as HTML (e.g., `svg-icon`).

### Files

- For detailed guidelines on file naming, see [File Naming Conventions][FILE_NAMING_CONVENTIONS].

## Code Formatting and Style

These settings are enforced by the `.editorconfig` and `.prettierrc` configurations.

### Indentation and Spacing

- **General:**
  Use **2 spaces** per indentation level throughout the project. Tabs are not permitted.
- **Python:**
  Use **4 spaces** per indentation level.

### Line Length

- **Code Files:**
  Limit lines to a maximum of **88 characters**.
- **Markdown Files:**
  Allow up to **120 characters** per line.

### Braces and Control Structures

- **Python:**
  Python uses indentation to define code blocks rather than braces. Ensure consistent and correct indentation.
- **HTML & SVG:**
  For HTML and SVG files, format nested elements with **2-space** indentation.
  Align opening and closing tags for clarity. For SVG files specifically, the [jock.svg][jock.svg] VS Code extension
  is recommended.

### Comments and Documentation

- **General Guidance:**
  All comments should enhance clarity and avoid redundancy with well-named functions and variables.
  Ensure comments do not exceed the maximum line length.
- **Inline Comments:**
  Place concise inline comments on the same line or immediately above the code they describe.
- **Block Comments:**
  Follow the Google docstring convention.
  In Python, the first line of a docstring should provide a brief description. For example:

  ```python
  """A script to fetch GitHub data, calculate streaks, and generate a heatmap grid."""
  ```

- **File Header Comments:**
  Every file should begin with a header comment (except for files in `.json`, Markdown, and `LICENSE` files)
  that provides a short, third-person description of the file's purpose. For example:

  ```plaintext
  # .pre-commit-config.yaml: Sets up pre-commit hooks to automate code quality checks.
  ```

  If a file starts with a shebang (e.g., `#!/bin/bash`),
  place the header comment on the line immediately following the shebang.

### EditorConfig

- **Purpose:**
  The `.editorconfig` file ensures consistent coding styles across all editors by specifying:
  - **Indentation:** 2 spaces (4 spaces for Python)
  - **Line Endings:** Unix-style (`lf`)
  - **Charset:** UTF-8
  - **Max Line Length:** 88 characters for code (120 for Markdown)
  - **Final Newline:** Enforced
  - **Trailing Whitespace:** Trimmed (with specified exceptions)
- **Note:**
  Contributors should use an editor that supports EditorConfig to automatically apply these settings.

### Linting and Formatting Tools

- **Prettier:**
  Formats code based on the configuration in `.prettierrc`:
  - Enforces semicolons, single quotes, trailing commas, and a print width of 88 characters (except 120 for Markdown).
- **Pre-commit Hooks:**
  The `.pre-commit-config.yaml` is set up to run various checks, including formatting and linting, before commits.
- **Yamllint:**
  Validates YAML files during the pre-commit process to ensure they adhere to defined formatting rules.

### Linting and Formatting Tools

The following tools are used in this project:

- **Prettier:**
  Formats code based on the configuration in `.prettierrc`.
  It enforces semicolons, single quotes, trailing commas, and a print width of 88 characters (120 for Markdown).
- **Pre-commit Hooks:**
  The `.pre-commit-config.yaml` is configured to run various checks, including formatting and linting, before commits.
- **Yamllint:**
  Validates YAML files during the pre-commit process to ensure they adhere to defined formatting rules.
- **autopep8:**
  Automatically formats Python code.
- **flake8:**
  Lints Python code for style and syntax issues.
- **isort:**
  Organizes and sorts Python import statements.
- **mypy:**
  Performs static type checking on Python code.

## Documentation

### Inline Documentation

See [Comments and Documentation][COMMENTS-AND-DOCUMENTATION] from [Code Formatting and Style][CODE_FORMATTING_AND_STYLE].

### External Documentation

- **Repository Documentation:**
  The root-level `README.md` offers an overview of the project and a preview of its appearance on the profile.
  Additional key documents such as `CONTRIBUTING.md`, `STYLEGUIDE.md`, `SECURITY.md`,
  and `LICENSE` are also maintained at the repository root.

- **GitHub Pages:**
  The `docs` directory contains files for GitHub Pages.

### Markdown References

- **Reference-Style Links:**
  Use reference-style links for clarity. For example:

  ```markdown
  [info][link]

  [link]: https://example.com
  ```

- **Local References:**
  For links to repository-related documents (e.g., `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md`) or internal sections,
  use **SCREAMING_SNAKE_CASE** for link identifiers and omit the file extension for documents.
  For example:

  ```markdown
  See our [Code of Conduct][CODE_OF_CONDUCT].

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

- **External Links:**
  For links that reference external resources, use **kebab-case** for link identifiers. For example:

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

- **Prettier:**
  Formats code to ensure a uniform style across the repository.
- **cspell:**
  A spellchecker designed for code and Markdown files.

#### Versioning Documentation

- Documentation versioning is not implemented yet but will be managed using MkDocs in alignment with project releases.

#### Consistency and Updates

- Update documentation alongside code changes.
- Contributors should update docs when introducing new features or modifying existing functionality.

#### Style and Tone

- Maintain a semi-formal tone appropriate for a tech-oriented audience.
- Use clear, precise language and consistent formatting throughout.

#### Contribution Guidelines

- Documentation contributions follow the same process as code changes—submit pull requests for review
  according to the contribution guidelines.

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

This document is a living resource that should evolve with the project.
As new best practices emerge or project requirements change, please update the guide to keep it relevant and effective.

### Feedback and Updates

Your input is valuable. If you have suggestions for improvements, clarifications, or additional guidelines,
please reach out to the maintainers or submit an [issue][issues]. For contributing guidelines,
refer to [`CONTRIBUTING.md`][CONTRIBUTING]; for security concerns, see [`SECURITY.md`][SECURITY];
for discussions, consult the project's [discussion board][discussions]
or contact the project owner at [evgenii.shiliaev@jekwwer.com][evgenii.shiliaev@jekwwer.com].

---

This document is based on a template by [Evgenii Shiliaev][evgenii-shiliaev-github],
licensed under [CC BY 4.0][jekwwer-markdown-docs-kit-license]. All additional content is licensed under [LICENSE][LICENSE].

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
[tox-web]: https://tox.readthedocs.io
