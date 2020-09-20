from typing import Dict, Any
import json
import sys


def deduce_platform(name: str) -> str:
    return name.split(".")[-2].split("-")[-1] + "-x64"


def translate_date(gh_date: str) -> str:
    # 2020-09-19T23:58:45Z
    return gh_date.replace("T", " ", 1)[:-1]


def translate_release_asset(tag_name: str, date: str,
                            asset: Dict[str, Any]) -> Dict[str, Any]:
    name = asset["name"]
    if asset["content_type"] != "application/zip":
        fmt = 'Release asset "{}" is not of type "application/zip".'
        print(fmt.format(name), file=sys.stderr)
        exit(1)
    return {
        "url": asset["browser_download_url"],
        "platforms": [deduce_platform(name)],
        "date": date,
        "version": tag_name,
        "sublime_text": ">=4070"
    }


def main() -> None:
    source = json.load(sys.stdin)
    release = source["release"]
    tag_name = release["tag_name"]
    date = translate_date(release["published_at"])
    json.dump({
        "releases": [translate_release_asset(tag_name, date, asset)
                     for asset in release["assets"]],
        "name": source["repository"]["name"],
        "details": source["repository"]["html_url"]
    }, sys.stdout, separators=(",", ":"), check_circular=False)


if __name__ == '__main__':
    main()
