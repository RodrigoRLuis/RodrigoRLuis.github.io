import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://api.github.com/graphql"
USERNAME = os.environ.get("GITHUB_USERNAME", "RodrigoRLuis")
TOKEN = os.environ.get("GH_TOKEN")

if not TOKEN:
    print("Missing GH_TOKEN secret.", file=sys.stderr)
    sys.exit(1)


def graphql(query, variables):
    payload = json.dumps({
        "query": query,
        "variables": variables
    }).encode("utf-8")

    request = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "github-commit-counter"
        },
        method="POST"
    )

    try:
        with urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError) as error:
        print(f"GitHub request failed: {error}", file=sys.stderr)
        sys.exit(1)

    if result.get("errors"):
        print(f"GitHub GraphQL error: {result['errors']}", file=sys.stderr)
        sys.exit(1)

    return result["data"]


query = """
query($from: DateTime!, $to: DateTime!) {
  viewer {
    login
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
      doesIncludePrivateContributions
    }
  }
}
"""

now = datetime.now(timezone.utc)
start = datetime(2000, 1, 1, tzinfo=timezone.utc)
total_commits = 0
includes_private = False
current = start

while current < now:
    end = min(current + timedelta(days=365), now)

    data = graphql(query, {
        "from": current.isoformat(),
        "to": end.isoformat()
    })

    viewer = data["viewer"]

    if viewer["login"].lower() != USERNAME.lower():
        print("The token does not belong to the configured user.", file=sys.stderr)
        sys.exit(1)

    contributions = viewer["contributionsCollection"]
    total_commits += contributions["totalCommitContributions"]
    includes_private = (
        includes_private
        or contributions["doesIncludePrivateContributions"]
    )

    current = end + timedelta(seconds=1)

output = {
    "username": USERNAME,
    "period": "all-time",
    "total_commits": total_commits,
    "updated_at": now.isoformat(),
    "includes_private_contributions": includes_private
}

os.makedirs("data", exist_ok=True)

with open("data/commits.json", "w", encoding="utf-8") as file:
    json.dump(output, file, indent=2, ensure_ascii=False)
    file.write("\n")

print(f"Total commits: {total_commits}")
print(f"Private contributions included: {includes_private}")
