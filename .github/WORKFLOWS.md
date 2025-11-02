# GitHub Actions Workflows

This repository uses GitHub Actions for automated testing, releasing, and publishing to PyPI.

## Workflows Overview

### 1. CI Testing (`test.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**What it does:**
- Runs tests across multiple OS (Ubuntu, macOS, Windows) and Python versions (3.8-3.12)
- Performs linting with black and flake8
- Runs type checking with mypy
- Executes test suite with coverage reporting
- Uploads coverage to Codecov
- Builds and validates the package

**Status:** Automatically runs on every push and PR

---

### 2. Create Release (`release.yml`)

**Triggers:**
- Manual workflow dispatch via GitHub Actions UI

**Required Inputs:**
- `version_bump`: Dropdown to select version bump type (patch, minor, major)
- `prerelease`: Optional pre-release suffix (e.g., `beta.1`, `rc.1`) - leave empty for stable release

**What it does:**
1. Reads current version from `pyproject.toml`
2. Automatically calculates new version based on bump type
3. Checks that the tag doesn't already exist
4. Runs full test suite
5. Updates version in `pyproject.toml` and `src/qastudio_pytest/__init__.py`
6. Builds the package
7. Commits version bump
8. Creates and pushes a git tag (`v{version}`)
9. Generates release notes from git commits
10. Creates a GitHub Release with built artifacts

**How to use:**
1. Go to **Actions** → **Create Release**
2. Click **Run workflow**
3. Select version bump type:
   - **Patch** (1.0.0 → 1.0.1): Bug fixes, backward compatible
   - **Minor** (1.0.0 → 1.1.0): New features, backward compatible
   - **Major** (1.0.0 → 2.0.0): Breaking changes
4. (Optional) Enter pre-release suffix (e.g., `beta.1`, `rc.1`)
5. Click **Run workflow**

**Example version bumps:**
- Current: `1.2.3` + Patch → `1.2.4`
- Current: `1.2.3` + Minor → `1.3.0`
- Current: `1.2.3` + Major → `2.0.0`
- Current: `1.2.3` + Patch + `beta.1` → `1.2.4-beta.1`

---

### 3. Publish to PyPI (`publish.yml`)

**Triggers:**
- Automatically when a GitHub Release is published
- Manual workflow dispatch via GitHub Actions UI

**Required Secrets:**
- `PYPI_API_TOKEN`: PyPI API token for publishing to production PyPI
- `TEST_PYPI_API_TOKEN`: (Optional) TestPyPI API token for testing

**What it does:**
1. Runs full test suite
2. Performs linting and type checking
3. Builds the package
4. Validates package with twine
5. Publishes to PyPI or TestPyPI

**Automatic Publishing (on release):**
- When you create a release using `release.yml`, this workflow automatically triggers
- Publishes the package to PyPI using the `PYPI_API_TOKEN` secret

**Manual Publishing:**
1. Go to **Actions** → **Publish to PyPI**
2. Click **Run workflow**
3. Select environment:
   - `testpypi`: Publish to TestPyPI (for testing)
   - `pypi`: Publish to production PyPI
4. Click **Run workflow**

---

## Complete Release Process

### Standard Release Flow

1. **Create a Release**
   ```
   GitHub → Actions → Create Release → Run workflow
   Select: Patch, Minor, or Major
   Pre-release: (leave empty for stable release)
   ```

2. **GitHub Actions will:**
   - Calculate new version automatically
   - Run tests
   - Update version files
   - Create git tag
   - Create GitHub Release

3. **Publish to PyPI** (automatic)
   - The `publish.yml` workflow triggers automatically
   - Publishes to PyPI

### Testing Before Production

To test the release process before publishing to production PyPI:

1. **Manually run Publish workflow**
   ```
   GitHub → Actions → Publish to PyPI → Run workflow
   Environment: testpypi
   ```

2. **Test installation from TestPyPI**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ qastudio-pytest
   ```

3. **If everything works, publish to production**
   ```
   GitHub → Actions → Publish to PyPI → Run workflow
   Environment: pypi
   ```

---

## Required GitHub Secrets

You need to configure these secrets in your GitHub repository:

### `PYPI_API_TOKEN` (Required)

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to **API tokens**
3. Click **Add API token**
4. Name: `github-actions-qastudio-pytest`
5. Scope: **Project: qastudio-pytest** (or Entire account)
6. Copy the token (starts with `pypi-`)
7. Add to GitHub:
   - Go to your repo → **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PYPI_API_TOKEN`
   - Value: (paste the token)

### `TEST_PYPI_API_TOKEN` (Optional)

Same process as above, but use [TestPyPI](https://test.pypi.org/manage/account/).

---

## Workflow Permissions

The workflows require the following permissions:

- **release.yml**: `contents: write` (to create releases and tags)
- **publish.yml**: `contents: read`, `id-token: write` (for trusted publishing)

These are configured in the workflow files.

---

## Troubleshooting

### "Tag already exists" error

The tag `v{version}` already exists. Either:
- Use a different version number
- Delete the existing tag: `git tag -d v1.0.0 && git push origin :refs/tags/v1.0.0`

### "Invalid version format" error

Version must follow semantic versioning:
- Valid: `1.0.0`, `2.1.3`, `1.0.0-beta.1`
- Invalid: `v1.0.0`, `1.0`, `version-1.0.0`

### "Package already exists on PyPI" error

PyPI doesn't allow re-uploading the same version. You need to:
- Bump the version number
- Use a new version for the release

### Authentication errors with PyPI

Check that:
1. `PYPI_API_TOKEN` secret is set correctly
2. Token hasn't expired
3. Token has correct scope (project or entire account)

---

## Version Numbering Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0 → 2.0.0): Breaking changes
- **MINOR** version (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** version (1.0.0 → 1.0.1): Bug fixes, backward compatible

**Pre-release versions:**
- Alpha: `1.0.0-alpha.1`
- Beta: `1.0.0-beta.1`
- Release Candidate: `1.0.0-rc.1`

---

## Manual Publishing (without GitHub Actions)

If you need to publish manually:

```bash
# Install build tools
pip install --upgrade build twine

# Build the package
python -m build

# Check the build
twine check dist/*

# Test on TestPyPI
twine upload --repository testpypi dist/*

# Publish to PyPI
twine upload dist/*
```

Configure `~/.pypirc`:
```ini
[pypi]
  username = __token__
  password = pypi-YOUR_TOKEN_HERE

[testpypi]
  username = __token__
  password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

---

## Monitoring Workflow Runs

- View all workflows: **Actions** tab in GitHub
- Check individual runs for logs and errors
- Failed runs will show error messages
- Download build artifacts from workflow runs if needed

---

## Best Practices

1. **Always test on TestPyPI first** before publishing to production
2. **Run tests locally** before creating a release
3. **Write meaningful release notes** in the GitHub Release
4. **Follow semantic versioning** strictly
5. **Tag pre-releases correctly** to avoid confusion
6. **Keep secrets secure** - never commit them to the repository
7. **Monitor PyPI downloads** and user feedback after releases

---

## References

- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)
- [PyPI API Tokens](https://pypi.org/help/#apitoken)
