# Style Guide

Style guide for **Jekwwer/Jekwwer** — covers repository structure, naming conventions, code formatting, and
documentation standards.

## Introduction

Standardizes coding and documentation practices for consistency, readability, and collaboration. Covers:

- **Repository Structure:** Directory layout, file naming conventions, and configuration file details.
- **Naming Conventions:** Standards for variables, constants, functions, env vars, and file/directory names.
- **Code Formatting and Style:** Indentation, line length, brace styles, comments, EditorConfig settings, and
  linting/formatting tools.
- **Documentation:** Standards for creating and maintaining project documentation.

## Repository Structure

### Directory Layout

```plaintext
/ (root)                                        # repository root
├── .devcontainer                               ├── # devcontainer-related configurations
│   ├── devcontainer.json                       │   ├── # devcontainer setup
│   └── post-create.sh                          │   └── # post-create initialization script
├── .github                                     ├── # GitHub-related configurations
│   ├── ISSUE_TEMPLATE                          │   ├── # issue templates
│   │   └── *                                   │   │   └── # all files in the folder
│   ├── PULL_REQUEST_TEMPLATE                   │   ├── # pull request templates
│   │   └── *                                   │   │   └── # all files in the folder
│   ├── workflows                               │   ├── # GitHub workflows
│   │   ├── deploy.yml                          │   │   ├── # deployment workflow
│   │   └── update.yml                          │   │   └── # daily update workflow
│   ├── dependabot.yml                          │   ├── # Dependabot configuration
│   ├── FUNDING.yml                             │   ├── # funding configuration
│   └── PULL_REQUEST_TEMPLATE.md                │   └── # default pull request template
├── assets                                      ├── # SVG source templates (one per style)
│   └── profile-card.glass.template.svg         │   └── # glass style card template
├── docs                                        ├── # GitHub Pages files
│   ├── glass                                   │   ├── # glass style assets
│   │   ├── background.glass.svg                │   │   ├── # animated background
│   │   ├── index.html                          │   │   ├── # glass style page
│   │   ├── profile-card.glass.svg              │   │   ├── # output with background
│   │   └── profile-card.glass-no-background.svg│   │   └── # output without background
│   └── index.html                              │   └── # redirect to active style
├── .editorconfig                               ├── # editor configuration
├── .gitignore                                  ├── # files to ignore in Git
├── .markdownlint.json                          ├── # markdown linting configuration
├── .mlc-config.json                            ├── # markdown link check configuration
├── .pre-commit-config.yaml                     ├── # pre-commit hook configuration
├── .prettierrc                                 ├── # Prettier configuration
├── .yamllint.yml                               ├── # yaml linting configuration
├── CODE_OF_CONDUCT.md                          ├── # code of conduct
├── CONTRIBUTING.md                             ├── # contributing guidelines
├── cspell.json                                 ├── # spell checking configuration
├── LICENSE                                     ├── # MIT license
├── Makefile                                    ├── # common development tasks
├── package-lock.json                           ├── # npm lock file
├── package.json                                ├── # npm package metadata
├── poetry.lock                                 ├── # poetry lock file
├── pyproject.toml                              ├── # Python project metadata
├── README.md                                   ├── # project README
├── SECURITY.md                                 ├── # security information
├── STYLEGUIDE.md                               ├── # style guide (this document)
└── generate_profile_card.py                    └── # profile card generator script
```

### File Naming Conventions

- **Documentation Files:** `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `README.md`, `SECURITY.md` and similar root docs use
  **SCREAMING_SNAKE_CASE**. Files in `docs` and `assets` use **kebab-case**.

- **Configuration Files:** Tool config files (e.g., `cspell.json`, `.editorconfig`, `.pre-commit-config.yaml`,
  `pyproject.toml`, `.prettierrc`) use lowercase, following each tool's requirements.

- **Scripts:** Executable scripts use lowercase **snake_case**.

- **GitHub and Workflow Files:** Files in `.github` follow GitHub's naming conventions — mix of uppercase (e.g.,
  `BUG_REPORT.md`) and lowercase (e.g., `config.yml`). Workflow YAML files in `.github/workflows/` use **kebab-case**
  (e.g., `deploy-app.yml`, `run-tests.yml`).

### Directory Naming Conventions

- **General Naming:** Lowercase letters. Multi-word names use **kebab-case** (e.g., `node-modules`, `source-files`).
  Names should clearly indicate content or purpose.

- **Special Directories:** Dot-prefixed directories (e.g., `.github`, `.devcontainer`) have specific roles — leave
  unchanged.

### Configuration Files

- `.devcontainer/devcontainer.json`: Dev container setup — VS Code settings, environment variables, extensions.
- `.github/dependabot.yml`: Dependabot config for automated dependency updates.
- `.gitignore`: Files and directories excluded from version control.
- `.editorconfig`: EditorConfig rules for consistent code style across editors.
- `.markdownlint.json`: Markdown linting rules and file exclusions.
- `.mlc-config.json`: markdown-link-check config — URL patterns to ignore and other link validation rules.
- `.pre-commit-config.yaml`: Pre-commit hook definitions (linting, formatting, type checks, tests).
- `.prettierrc`: Prettier formatting rules for JSON, YAML, Markdown, etc.
- `.yamllint.yml`: YAML linting config for CI and project YAML files.
- `cspell.json`: Spell-check config with custom dictionaries and file globs.
- `Makefile`: Targets for linting, formatting, type checking, spell-checking, testing, running, and releasing.
- `package-lock.json`: npm lockfile with exact dependency versions.
- `package.json`: npm manifest — metadata, scripts, and dependency declarations.
- `poetry.lock`: Poetry lockfile for reproducible Python environments.
- `pyproject.toml`: Python project metadata, Poetry settings, build-system requirements, and tool configs.

### Assets and Resources

SVG source templates in `assets` (one per style):

- `profile-card.glass.template.svg`: Glass style card template; background injected at runtime from
  `docs/glass/background.glass.svg`.

Each style gets its own subdirectory under `docs/`:

- `docs/index.html`: Redirects to the currently active style page.
- `docs/glass/index.html`: Glass style GitHub Pages page.
- `docs/glass/background.glass.svg`: Animated gradient background for the glass style.
- `docs/glass/profile-card.glass.svg`: Glass style output with background (embedded in README).
- `docs/glass/profile-card.glass-no-background.svg`: Glass style output without background (overlaid on
  `background.glass.svg` by the glass style page).

## Naming Conventions

### General Guidelines

Names should be clear, descriptive, and consistent across the project.

### Variables

- **Python:** **snake_case** (e.g., `my_variable`).

### Constants

- **Python:** **SCREAMING_SNAKE_CASE** (e.g., `MAX_LIMIT`).

### Environment Variables

- **General:** **SCREAMING_SNAKE_CASE** (e.g., `GH_USERNAME`, `GITHUB_TOKEN`).

### Functions/Methods

- **General Guidelines:** Use descriptive verbs that convey the action performed.
- **Python:** **snake_case** (e.g., `update_profile_svg`).

### Classes

- **Python:** **CamelCase** (e.g., `ProfileCardGenerator`).

### IDs and Classes (HTML, CSS, SVG)

- **General Guidelines:** **kebab-case** for all IDs and class names (e.g., `icon-button`, `svg-logo`).

### CSS Custom Properties

- **General Guidelines:** **kebab-case** with double dashes (e.g., `--primary-color`).

### Attributes

- **HTML and SVG:** **kebab-case** for all attribute names (e.g., `data-index`, `aria-label`).

### Files

See [File Naming Conventions][FILE_NAMING_CONVENTIONS].

## Code Formatting and Style

Rules specified in `.editorconfig`, `.markdownlint.json`, `.prettierrc`, `.yamllint.yml`, and `pyproject.toml`.

### Indentation and Spacing

- **General:** **2 spaces** per indentation level. Tabs only for `Makefile`. _(Enforced by EditorConfig and Prettier)_
- **Python:** **4 spaces** per indentation level. _(Enforced by EditorConfig)_

### Line Length

- **Code Files:** Max **88 characters**. _(Enforced by Ruff for Python, Prettier for supported files, yamllint for
  YAML)_
- **HTML, CSS, SVG:** Max **120 characters**. _(Enforced by Prettier)_
- **Markdown:** Max **120 characters**. _(Enforced by Prettier and markdownlint)_
- **JSON:** No limit. _(Enforced by Prettier)_

### Braces and Control Structures

- **Python:** Uses indentation for code blocks — no braces. Ensure consistent indentation.
- **HTML & SVG:**
  - **Nested Elements:** **2-space** indentation. _(Enforced by Prettier and EditorConfig)_
  - **Tag Alignment:** Align opening and closing tags. For SVG files, [jock.svg][jock.svg] extension is recommended.

### Comments and Documentation

- **General:** Comments should enhance clarity, not restate what well-named identifiers already express. Don't exceed
  max line length.
- **Inline Comments:** Concise — same line or immediately above the code they describe.
- **Block Comments / Docstrings:** Google-style. First line is a short summary. _(Enforced by Ruff)_

  ```python
  """A script to fetch GitHub data, calculate streaks, and generate a heatmap grid."""
  ```

- **File Header Comments:** Every source file (except JSON, Markdown, Python, and `LICENSE`) starts with a one-line
  header describing its purpose.

  ```plaintext
  # .gitignore: Specifies files and directories that should not be tracked by Git.
  ```

  If the file starts with a shebang (e.g., `#!/bin/bash`), place the header comment immediately after it.

### EditorConfig

`.editorconfig` ensures consistent style across editors:

- **Indentation:** 2 spaces (4 for Python; tab-indented with 2-space width for `Makefile`)
- **Line Endings:** Unix-style (`lf`)
- **Charset:** UTF-8
- **Max Line Length:** 88; 120 for Markdown _(reference only — enforcement by other tools)_
- **Final Newline:** Enforced
- **Trailing Whitespace:** Trimmed (with exceptions)

Use an editor that supports EditorConfig to apply these settings automatically.

### Prettier

`.prettierrc` formatting rules:

- **Semicolons:** Enabled
- **Quote Style:** Single quotes
- **Trailing Commas:** Added where possible
- **Tab Width:** 2 spaces
- **End of Line:** Unix-style (`lf`)
- **Print Width:** 88; 120 for CSS, HTML, and Markdown; no limit for JSON

Prettier runs in VS Code and as a pre-commit hook.

### Ruff

Fast linting and formatting for Python — enforces line length, import order, and docstrings. Runs as a pre-commit hook.

### Additional Code Quality Tools

- **Pre-commit Framework** (`.pre-commit-config.yaml`):
  - **pre-commit-hooks:** Normalizes line endings, trims whitespace, validates JSON/TOML/YAML, detects private keys,
    checks merge conflicts, enforces shebangs, and other sanity checks.
  - **pygrep-hooks:** Catches anti-patterns (no `eval`, no `log.warn`, blanket `# noqa`/`# type: ignore`, improper mock
    usage, stray Unicode replacement chars).
- **markdownlint-cli & markdown-link-check:** Lints Markdown per `.markdownlint.json` and validates links.
- **yamllint:** Lints YAML per `.yamllint.yml`.
- **pyupgrade:** Auto-upgrades Python syntax to modern versions.
- **mypy:** Static type checking for Python.

## Documentation

### Inline Documentation

See [Comments and Documentation][COMMENTS-AND-DOCUMENTATION].

### External Documentation

- **Repository Documentation:** Root `README.md` gives a project overview and profile preview. Key docs
  (`CONTRIBUTING.md`, `STYLEGUIDE.md`, `SECURITY.md`, `LICENSE`) live at the repository root.

- **GitHub Pages:** `docs` directory contains GitHub Pages files.

_Note: File and directory names in Markdown must always use backticks, e.g.:_

```markdown
Other external documentation is maintained in the `docs` directory.
```

### Markdown References

- **Reference-Style Links:** Use reference-style links for clarity:

  ```markdown
  [info][link]

  [link]: https://example.com
  ```

- **Local References:** Use **SCREAMING_SNAKE_CASE** identifiers, omit file extensions:

  ```markdown
  See [Code of Conduct][CODE_OF_CONDUCT].

  [CODE_OF_CONDUCT]: CODE_OF_CONDUCT.md
  ```

  For internal sections:

  ```markdown
  See [File Naming Conventions][FILE_NAMING_CONVENTIONS].

  [FILE_NAMING_CONVENTIONS]: #file-naming-conventions
  ```

  Local references go at the top, sorted alphabetically:

  ```markdown
  [FILE_NAMING_CONVENTIONS]: #file-naming-conventions
  [SECURITY]: SECURITY.md
  [external-link]: https://example.com
  ```

- **External Links:** Use **kebab-case** identifiers:

  ```markdown
  [info][external-link]

  [external-link]: https://example.com
  ```

  External references go below local references, sorted alphabetically:

  ```markdown
  [SECURITY]: SECURITY.md
  [external-link]: https://example.com
  ```

### Documentation Tools and Best Practices

#### Tools

- **cspell:** Spell-checks code and Markdown. Pre-commit hook; local: `make spell`.
- **markdown-link-check:** Validates Markdown links. Pre-commit hook.
- **markdownlint:** Enforces Markdown style rules. Pre-commit hook.

#### Consistency and Updates

- Update docs alongside code changes.
- Update docs when introducing new features or modifying existing functionality.

#### Style and Tone

- Semi-formal tone for a tech-oriented audience.
- Clear, precise language and consistent formatting throughout.

#### Contribution Guidelines

- Doc contributions follow the same process as code — submit pull requests for review per [CONTRIBUTING][CONTRIBUTING].

[COMMENTS-AND-DOCUMENTATION]: #comments-and-documentation
[CONTRIBUTING]: CONTRIBUTING.md
[FILE_NAMING_CONVENTIONS]: #file-naming-conventions
[jock.svg]: https://marketplace.visualstudio.com/items?itemName=jock.svg
