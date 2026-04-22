# Contributing Guidelines

Contributions to **Jekwwer/Jekwwer** are welcome — bug fixes, new features, or documentation improvements.

## Getting Started

### Option A: Dev Container (recommended)

Open in VS Code with the Dev Containers extension. The container runs `npm install`, `poetry install`, and
`pre-commit install` automatically via `.devcontainer/post-create.sh`.

### Option B: Manual Setup

1. **Fork the Repository**: Click "Fork" on the top-right of the repository page.

2. **Clone Your Fork**:

   ```bash
   git clone https://github.com/<YOUR_USERNAME>/Jekwwer.git
   cd Jekwwer
   ```

3. **Set Up Upstream Remote**:

   ```bash
   git remote add upstream https://github.com/Jekwwer/Jekwwer.git
   ```

4. **Install Dependencies**:

   ```bash
   npm install
   pipx install poetry
   poetry install --with lint,mypy
   ```

5. **Install Pre-commit Hooks**:

   ```bash
   poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg
   ```

## Running Locally

Set the required environment variables and run the script from the repo root:

```bash
export GH_USERNAME=<your-github-username>
export GITHUB_TOKEN=<personal-access-token-with-read:user-scope>

# Optional — only needed when generating a style that reads Steam data (e.g. the man card):
export STEAM_API_KEY=<steam-web-api-key>
export STEAM_ID=<64-bit-steam-id>

python generate_profile_card.py --style all   # all | glass | man
```

Output writes to `docs/<style>/profile-card.<style>.svg` and `docs/<style>/profile-card.<style>-no-background.svg` for
each generated style (e.g. `docs/glass/profile-card.glass.svg`, `docs/man/profile-card.man-page.svg`).

## Project Layout

The CLI entry point is `generate_profile_card.py` at the repo root. All library code lives under the `profile_card/`
package:

```plaintext
profile_card/
├── __init__.py          # re-exports used by main()
├── fetchers.py          # HTTP session, GitHub GraphQL fetch, Steam fetch, streak/level processing
└── cards/
    ├── __init__.py      # side-effect imports populate CARD_STYLES
    ├── _shared.py       # CardContext, CardStyle, shared SVG generators
    ├── glass.py         # glass-style card
    └── man.py           # man-page-style card
```

### Adding a New Card Style

1. Create `profile_card/cards/<name>.py` that imports `register` + `CardStyle` from `profile_card.cards._shared` and
   calls `register("<name>", CardStyle(...))` at module top level.
2. Add `from profile_card.cards import <name>` to `profile_card/cards/__init__.py` so the module is imported for its
   side effect.
3. Add the corresponding template SVG under `assets/` and (optionally) a background SVG under `docs/<subdir>/`.
4. No edits to `main()`, `fetchers.py`, or other card modules are required.

## Branching and Versioning

### Branching Strategy

Branch names follow these conventions (adapt as needed):

- **Feature branches:** `feature/<short-description>` (e.g., `feature/add-login`)
- **Bugfix branches:** `bugfix/<short-description>` (e.g., `bugfix/fix-auth-error`)
- **Main branch:** `main`

### Versioning Strategy

Releases use a date-based tag format (**YYYY-MM-DD**), tagged after significant changes.

### Merging Guidelines

- **Squash (Preferred):** Use **Squash and Merge** to keep commit history clean. PR title must follow Conventional
  Commits format.
- **Rebase (Optional):** Use **Rebase and Merge** when commit history is already clean and well-structured.
- **Merge (Exceptions):** Use regular merge for larger branches with multiple contributors when preserving individual
  commits is necessary.

## Commit Message Conventions

Follows [Conventional Commits][conventional-commits]. Full template available at [`.gitmessage`][gitmessage].

### Commit Types

- `init`: Initial commit.
- `feat`: New feature.
- `fix`: Bug fix.
- `security`: Security-related changes (vulnerability fixes, input validation).
- `deps`: Dependency updates.
- `docs`: Documentation changes.
- `style`: Formatting/styling with no functional impact.
- `refactor`: Code restructuring without altering functionality.
- `perf`: Performance improvements.
- `test`: Adding or updating tests.
- `chore`: Maintenance tasks (dependency updates, build processes).

### Breaking Changes

Append `!` to the type (e.g., `feat!:`). Add a `BREAKING CHANGE:` footer as the last line of the commit body:

```plaintext
BREAKING CHANGE: <description of breaking changes and required adaptations>
```

## Dependency and Build Management

### Dependency Handling

- **NPM:** Managed via `package.json` and `package-lock.json`.
- **Python:** Managed via `pyproject.toml` and `poetry.lock`.
- **Dependabot:** `.github/dependabot.yml` monitors and updates NPM, Python, and GitHub Actions dependencies.

### Environment Configuration

- **Container Setup:** `.devcontainer/devcontainer.json` (VS Code settings and customizations).

## Testing and Quality Assurance

Linting and formatting are automated at the editor and pre-commit levels.

### Manual Testing

- **make help:** Shows Make help message.
- **make format:** Verifies formatting via Ruff (Python) and Prettier (everything else).
- **make format-fix:** Auto-formats via Ruff and Prettier.
- **make lint:** Checks Python files for lint issues via Ruff.
- **make lint-fix:** Auto-fixes lint issues with Ruff.
- **make type:** Static type checking with MyPy.
- **make spell:** Checks for typos via cspell.

### Automated Testing

Pre-commit hooks mirror the manual commands above.

## Proposing Changes

1. **Check for Existing Issues**: See [Issues][issues] or [Discussions][discussions] before opening anything new.

2. **Create a Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make and Test Changes**: Keep changes consistent with [`STYLEGUIDE.md`][STYLEGUIDE].

4. **Commit**:

   ```bash
   git add .
   git commit
   ```

5. **Push Your Branch**:

   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**:
   - Go to the original repository.
   - Click "Compare & pull request."
   - Fill out the PR template, referencing relevant issues or discussions.

## Code of Conduct

By contributing, you agree to the [Code of Conduct][CODE_OF_CONDUCT].

## Thank You

Your contributions make **Jekwwer/Jekwwer** better. Thank you for your time and effort.

[CODE_OF_CONDUCT]: CODE_OF_CONDUCT.md
[STYLEGUIDE]: STYLEGUIDE.md
[conventional-commits]: https://www.conventionalcommits.org
[discussions]: https://github.com/Jekwwer/Jekwwer/discussions
[gitmessage]: https://github.com/Jekwwer/dotfiles/blob/main/.gitmessage
[issues]: https://github.com/Jekwwer/Jekwwer/issues
