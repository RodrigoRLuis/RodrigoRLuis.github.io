#!/usr/bin/env python3
"""Publish only the authenticated user's historical GitHub commit total."""
import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_URL = "https://api.github.com/graphql"
USERNAME = os.environ.get("GITHUB_USERNAME", "RodrigoRLuis")
TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    print("Missing GH_TOKEN secret.", file=sys.stderr)
    sys.exit(1)

def graphql(query, variables):
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-pages-commit-counter",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        print(f"GitHub API request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.get("errors"):
        print("GitHub GraphQL error: " + json.dumps(result["errors"]), file=sys.stderr)
        sys.exit(1)
    return result["data"]

profile = graphql(
    "query($login: String!) { user(login: $login) { login createdAt } }",
    {"login": USERNAME},
).get("user")

if not profile:
    print(f"GitHub user {USERNAME!r} was not found or is not visible.", file=sys.stderr)
    sys.exit(1)

created_year = datetime.fromisoformat(profile["createdAt"].replace("Z", "+00:00")).year
current_year = datetime.now(timezone.utc).year
total = 0

# GitHub's contribution collection supports a maximum one-year interval.
# Include private contributions; only the aggregate total is written to the site.
query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(
      from: $from
      to: $to
      includePrivateContributions: true
    ) {
      totalCommitContributions
    }
  }
}
"""

for year in range(created_year, current_year + 1):
    from_date = f"{year}-01-01T00:00:00Z"
    to_date = f"{year + 1}-01-01T00:00:00Z"
    data = graphql(query, {"login": USERNAME, "from": from_date, "to": to_date})
    user = data.get("user")
    if not user:
        print(f"Could not read contribution data for {USERNAME!r}.", file=sys.stderr)
        sys.exit(1)
    count = user["contributionsCollection"]["totalCommitContributions"]
    total += count
    print(f"{year}: {count} commits")

output = {
    "username": profile["login"],
    "period": "all-time",
    "total_commits": total,
    "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
}

os.makedirs("data", exist_ok=True)
with open("data/commits.json", "w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False, indent=2)
    file.write("\n")

print(f"Published aggregate total: {total}")
