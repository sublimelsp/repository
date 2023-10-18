"""
Translate GitHub "release event" JSON into a Package Control repository entry,
and then modify the repository.json file appropriately.

The JSON must be supplied over stdin. An optional argument
`--sublime-text-version-range` can be given to specify the valid range of ST
versions.

This script is meant for packages that bundle binaries inside the package.
For those kind of packages, the package entry in the repository.json file must
be updated for each new release. This script automates that boring process.

TODO: The sublime_text version range should be extracted from JSON.
"""

from typing import Dict, Any
import functools
import json
import pathlib
import sys


def st_version_range_from_release_body(body: str) -> str:
    """
    Retrieves the `"sublime_text"` value from the text in the release. If your
    release text contains a line that starts with "Sublime-Text-Version-Range"
    then it's assumed that that's what we need to extract. Otherwise, this
    function defaults to returning the most recent minimal version range.
    """
    prefix = "Sublime-Text-Version-Range: "
    for line in body.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return ">=3154"


def extract_platform_from_asset_name(name: str) -> str:
    """
    The release asset must be of the form
    "LSP-Foobar_$PACKAGE_CONTROL_PLATFORM_KEY.zip".
    For example: LSP-Foobar_windows-x64.zip

    Valid platform indentifiers include:

    - `windows`
    - `windows-x64`
    - `windows-x32`
    - `osx`
    - `osx-x64`
    - `linux`
    - `linux-x32`
    - `linux-x64`
    """
    for needle in ("_windows", "_osx", "_linux"):
        if needle in name:
            return name.split(".")[-2].split("_")[-1]
    return "*"


def translate_date(gh_date: str) -> str:
    """
    Github release JSON has a different date format than the one desired by
    Package Control. For instance, it could be `2020-09-19T23:58:45Z`. Package
    Control expects it in the form `2020-09-19 23:58:45`. Note that 'Z' here
    means UTC so we don't have to do any time zone calculations.
    """
    return gh_date.replace("T", " ", 1)[:-1]


def translate_release_asset(
    sublime_text_version_range: str,
    tag_name: str,
    date: str,
    asset: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert GitHub asset JSON into a Package Control repository entry JSON.
    """
    name = asset["name"]
    if asset["content_type"] != "application/zip":
        fmt = 'Release asset "{}" is not of type "application/zip".'
        print(fmt.format(name), file=sys.stderr)
        exit(1)
    return {
        "url": asset["browser_download_url"],
        "platforms": extract_platform_from_asset_name(name),
        "date": date,
        "version": tag_name,
        "sublime_text": sublime_text_version_range
    }


def update_package(package: Dict[str, Any], payload: Dict[str, str]) -> None:
    """
    Update an existing Package Control repository package entry.
    """
    package.clear()
    package.update(payload)


def create_package(
    repository: Dict[str, Any],
    payload: Dict[str, str]
) -> None:
    """
    Create a new Package Control repository package entry.
    """
    name = payload["name"]
    packages = repository["packages"]
    index_to_insert = len(packages)
    for index, package in enumerate(packages):
        current_name = package["name"]
        if current_name < name:
            continue
        index_to_insert = index
        break
    new_package = {"name": name}  # type: Dict[str, Any]
    packages.insert(index_to_insert, new_package)
    update_package(new_package, payload)


def set_workflow_output(**kwargs: str) -> None:
    for key, value in kwargs.items():
        # https://github.community/t/set-output-truncates-multiline-strings/16852/3
        value = value.replace("%", "%25")
        value = value.replace("\n", "%0A")
        value = value.replace("\r", "%0D")
        print("::set-output name={}::{}".format(key, value))


def main() -> None:
    source = json.load(sys.stdin)
    release = source["release"]
    tag_name = release["tag_name"]
    date = translate_date(release["published_at"])
    body = release["body"]
    st_version_range = st_version_range_from_release_body(body)
    f = functools.partial(translate_release_asset,
                          st_version_range, tag_name, date)
    payload = {
        "releases": [f(asset) for asset in release["assets"]],
        "name": source["repository"]["name"],
        "details": source["repository"]["html_url"]
    }
    repository_path = pathlib.Path(__file__).parent / "repository.json"
    with repository_path.open("r") as fp:
        repository = json.load(fp)
    name = payload["name"]
    found = False
    for package in repository["packages"]:
        if package["name"] == name:
            update_package(package, payload)
            found = True
            break
    if not found:
        create_package(repository, payload)
    with repository_path.open("w") as fp:
        json.dump(repository, fp, indent="\t", sort_keys=True)
        fp.write("\n")
    commit_title = "Update {}".format(name) if found else "Add {}".format(name)
    set_workflow_output(
        commit_message="{}\n\n{}".format(commit_title, body),
        pr_title=commit_title,
        pr_body="## Repo link\n{}\n\n## Release body\n{}".format(
            payload["details"], body)
    )


if __name__ == '__main__':
    main()
