import json
import sys
import pathlib
from typing import Dict, Any
import os


def update_package(package: Dict[str, Any], payload: Dict[str, str]) -> None:
    package.clear()
    package.update(payload)


def create_package(repository: Dict[str, Any], payload: Dict[str, str]) -> None:
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


def main() -> None:
    payload = json.load(sys.stdin)
    repository_path = pathlib.Path(__file__).parent / "repository.json"
    with repository_path.open("r") as fp:
        repository = json.load(fp)
    name = payload["name"]
    found = False
    for package in repository["packages"]:
        if package["name"] == name:
            update_package(package, payload)
            print("Update", name)
            found = True
            break
    if not found:
        create_package(repository, payload)
        print("Add", name)
    with repository_path.open("w") as fp:
        json.dump(repository, fp, indent="\t", sort_keys=True)


if __name__ == '__main__':
    main()
