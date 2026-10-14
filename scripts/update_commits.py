#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


def fetch_commit_total(username: str, token: str) -> int:
    query = quote_plus(f"author:{username}")
    url = f"https://api.github.com/search/commits?q={query}&per_page=1"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "User-Agent": "update-commits-workflow",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    return int(payload["total_count"])


def main() -> None:
    username = os.environ["GITHUB_USERNAME"]
    token = os.environ["GH_TOKEN"]

    total_commits = fetch_commit_total(username, token)
    output = {
        "total_commits": total_commits,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    output_path = Path("data/commits.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        missing = exc.args[0]
        raise SystemExit(f"Missing required environment variable: {missing}") from exc
    except (HTTPError, URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to update commit total: {exc}") from exc
