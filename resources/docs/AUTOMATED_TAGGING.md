# Automated Git Tagging System

This project includes an automated git tagging system that creates version tags automatically when the CHANGELOG.md is updated.

## How it Works

1. **Trigger**: When you push changes to `resources/docs/CHANGELOG.md` to the main branch
2. **Workflow**: The `bump-version.yml` GitHub Actions workflow is triggered
3. **Version Detection**: The system reads the first version section from CHANGELOG.md (e.g., `## [0.1.1]`)
4. **Version Update**: Updates `core/version_info.txt` with the new version
5. **Tag Creation**: Uses `hooks/create_git_tag_from_changelog.py` to create and push a git tag
6. **Release**: The tag creation triggers the `release-auto.yml` workflow to build and publish releases

## Workflow Steps

### bump-version.yml

- Runs on changes to `resources/docs/CHANGELOG.md`
- Executes `hooks/update_version_from_changelog.py` to update version files
- Commits version changes
- Executes `hooks/create_git_tag_from_changelog.py` to create git tags

### create_git_tag_from_changelog.py

- Reads the latest version from CHANGELOG.md
- Creates an annotated git tag (e.g., `v0.1.1`)
- Pushes the tag to the remote repository
- Handles duplicate tags gracefully

## Usage

To create a new release:

1. Update `resources/docs/CHANGELOG.md`:

   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD
   
   ### Added
   - New feature description
   
   ### Fixed  
   - Bug fix description
   ```

2. Commit and push the CHANGELOG changes:

   ```bash
   git add resources/docs/CHANGELOG.md
   git commit -m "docs: update CHANGELOG.md with vX.Y.Z release"
   git push
   ```

3. The automation will:
   - Update version files automatically
   - Create and push the git tag `vX.Y.Z`
   - Trigger the release workflow
   - Build Python packages and Windows executable
   - Create a GitHub release with artifacts

## Manual Tag Creation

You can also manually create tags using the script:

```bash
python hooks/create_git_tag_from_changelog.py
```

This will read the current CHANGELOG.md and create a tag for the latest version if it doesn't already exist.

## File Structure

```
├── .github/workflows/
│   ├── bump-version.yml        # Triggered by CHANGELOG changes
│   └── release-auto.yml        # Triggered by tag creation
├── hooks/
│   ├── create_git_tag_from_changelog.py  # Tag creation script
│   └── update_version_from_changelog.py  # Version update script
├── resources/docs/
│   └── CHANGELOG.md            # Source of truth for versions
└── core/
    └── version_info.txt        # Current version file
```

## Dependencies

- Python 3.10+
- Git command line tools
- GitHub repository with Actions enabled
- Proper GitHub permissions for the workflow (contents: write)
