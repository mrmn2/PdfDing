"""Module for updating the changelog, pyproject.toml and package.json after a release."""

import json
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path


def update_changelog(changelog_path: Path, release_tag: str, release_body: str) -> None:
    """Update the changelog based on the release tag and the release_body."""

    with open(changelog_path, 'r') as f:
        lines = f.readlines()

    now = datetime.now()
    release_date = now.strftime('%b %d, %Y')

    # construct new changelog entry
    changelog_str = '# Changelog\n\n'
    release_header = f'## {release_tag} ({release_date})\n'
    release_body = f'{release_body}\n'
    release_body = release_body.replace("## ", "### ")  # make sure release body headers have the right size

    # construct changelog
    lines = [changelog_str, release_header, release_body] + lines[1:]

    with open(changelog_path, 'w') as f:
        f.writelines(lines)


def update_pyproject(pyproject_path: Path, release_tag: str) -> None:
    """Update the pyproject.toml after a release."""

    with open(pyproject_path, 'r') as f:
        lines = f.readlines()

    if 'version' in lines[3]:
        release_tag = release_tag.replace('v', '')
        lines[3] = f'version = "{release_tag}"\n'
    else:
        raise ValueError('Version not present in line 4!')

    with open(pyproject_path, 'w') as f:
        f.writelines(lines)


def update_package_json(package_json_path: Path, release_tag: str) -> None:
    """Update the package.json after a release."""

    with open(package_json_path, 'r') as f:
        data = json.load(f)

    release_tag = release_tag.replace('v', '')
    data['version'] = release_tag

    with open(package_json_path, 'w') as f:
        json.dump(data, f, indent=2)


def main() -> None:
    parser = ArgumentParser()
    for argument in ['release_tag', 'release_body']:
        parser.add_argument(f'--{argument}')
    args = parser.parse_args()

    root_path = Path(__file__).parents[3]
    changelog_path = root_path / 'CHANGELOG.md'
    pyproject_path = root_path / 'pyproject.toml'
    package_json_path = root_path / 'package.json'

    release_tag = args.release_tag
    release_body = args.release_body

    update_changelog(changelog_path, release_tag, release_body)
    update_pyproject(pyproject_path, release_tag)
    update_package_json(package_json_path, release_tag)


if __name__ == '__main__':
    main()
