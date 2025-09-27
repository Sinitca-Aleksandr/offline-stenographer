# Release Instructions

This document explains how to create releases for the offline-stenographer project using semantic versioning and GitHub releases.

## Release Process

### 1. Version Management

The project uses [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning) for automatic version management based on Git tags.

- **Current version**: Defined in `pyproject.toml` with `poetry-dynamic-versioning`
- **Version format**: `MAJOR.MINOR.PATCH` (e.g., `1.0.0`, `2.1.3`)
- **Version source**: Automatically determined from Git tags

### 2. Creating a Release

#### Step 1: Create and Push a Release Tag

Create an annotated tag with the version number:

```bash
# Create an annotated tag (recommended)
git tag -a release/1.0.0 -m "Release version 1.0.0"

# Push the tag to trigger the release workflow
git push origin release/1.0.0
```

#### Step 2: Create GitHub Release

After pushing the tag, create a GitHub release:

1. Go to the [releases page](https://github.com/Sinitca-Aleksandr/offline-stenographer/releases)
2. Click "Create a new release"
3. Select the tag you just pushed (`release/1.0.0`)
4. Add release notes describing the changes
5. Click "Publish release"

### 3. Automatic Release Workflow

When a release is published, the GitHub Actions workflow (`.github/workflows/python-publish.yml`) automatically:

1. **Builds the package**:
   - Installs dependencies with Poetry
   - Builds wheel distribution using `poetry build`

2. **Publishes to PyPI**:
   - Downloads the built distributions
   - Publishes to PyPI using trusted publishing

3. **Uploads assets to GitHub Release**:
   - Downloads the built wheel files
   - Attaches them to the GitHub release

### 4. Supported Release Artifacts

Currently supported:
- **Python wheel** (`.whl`) - Published to PyPI and attached to GitHub release

Future support (commented out in workflow):
- **Windows executable** (`.exe`) - Can be enabled by uncommenting the `release-build-exe` job

## Release Checklist

Before creating a release, ensure:

- [ ] All tests pass (`pytest`)
- [ ] Code is properly formatted (`black`)
- [ ] No linting errors (`flake8`)
- [ ] Version follows semantic versioning
- [ ] Release notes are prepared
- [ ] Tag is pushed to repository
- [ ] GitHub release is created with proper description

## Version Bumping Strategy

The project uses semantic versioning:

- **MAJOR** (x.0.0): Breaking changes
- **MINOR** (x.y.0): New features, backward compatible
- **PATCH** (x.y.z): Bug fixes, backward compatible

## Troubleshooting

### Common Issues

1. **Tag already exists**: Delete the tag locally and remotely, then recreate
   ```bash
   git tag -d release/1.0.0
   git push origin :refs/tags/release/1.0.0
   ```

2. **PyPI publish fails**: Check that the PyPI environment is properly configured in repository settings

3. **Build fails**: Ensure all dependencies are properly specified in `pyproject.toml`

### Manual Release (if needed)

If the automated workflow fails, you can manually build and publish:

```bash
# Build the package
poetry build

# Publish to PyPI (requires API token)
poetry publish

# Upload to GitHub release manually
```

## Configuration Files

- **`.github/workflows/python-publish.yml`**: GitHub Actions workflow for automated releases
- **`pyproject.toml`**: Poetry configuration with dynamic versioning
- **`poetry.lock`**: Dependency lock file (auto-generated)

## Security Notes

- PyPI publishing uses trusted publishing with OIDC tokens
- The `pypi` environment must be configured in repository settings
- GitHub token has write permissions for releases
