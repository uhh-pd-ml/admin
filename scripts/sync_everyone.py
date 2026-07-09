#!/usr/bin/env python3
"""
Synchronize one GitHub team with all current members of an organization.

Intended use:
  - Organization: uhh-pd-ml
  - Team slug: everyone
  - Repository: uhh-pd-ml/admin

Required environment variables:
  GITHUB_TOKEN_FOR_ORG_ADMIN  A token whose user can manage the target team.

Optional environment variables:
  GITHUB_ORG                 Defaults to "uhh-pd-ml".
  GITHUB_TEAM_SLUG           Defaults to "everyone".
  DRY_RUN                    "true"/"1"/"yes" to only print intended changes.
  REMOVE_STALE_MEMBERS       Defaults to "true". If false, only adds missing members.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"

ORG = os.getenv("GITHUB_ORG", "uhh-pd-ml")
TEAM_SLUG = os.getenv("GITHUB_TEAM_SLUG", "everyone")
TOKEN = os.getenv("GITHUB_TOKEN_FOR_ORG_ADMIN")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes", "y"}
REMOVE_STALE_MEMBERS = os.getenv("REMOVE_STALE_MEMBERS", "true").lower() in {
    "1",
    "true",
    "yes",
    "y",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def github_request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    expected: Iterable[int] = (200,),
) -> Any:
    if not TOKEN:
        fail("GITHUB_TOKEN_FOR_ORG_ADMIN is not set")

    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "uhh-pd-ml-admin-sync-everyone",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            if response.status not in set(expected):
                fail(f"Unexpected HTTP status {response.status} for {method} {path}")
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"GitHub API request failed: {method} {path}: HTTP {exc.code}: {detail}")


def github_paginated(path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1

    while True:
        separator = "&" if "?" in path else "?"
        page_path = f"{path}{separator}per_page=100&page={page}"
        page_items = github_request("GET", page_path, expected=(200,))
        if not page_items:
            break
        items.extend(page_items)
        if len(page_items) < 100:
            break
        page += 1
        time.sleep(0.2)  # Be polite to the API.

    return items


def quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def get_org_members() -> set[str]:
    # role=all includes regular members and organization owners.
    members = github_paginated(f"/orgs/{quote(ORG)}/members?role=all")
    return {member["login"] for member in members}


def get_team_members() -> set[str]:
    members = github_paginated(
        f"/orgs/{quote(ORG)}/teams/{quote(TEAM_SLUG)}/members"
    )
    return {member["login"] for member in members}


def add_to_team(username: str) -> None:
    path = f"/orgs/{quote(ORG)}/teams/{quote(TEAM_SLUG)}/memberships/{quote(username)}"
    if DRY_RUN:
        print(f"DRY-RUN add {username} to {TEAM_SLUG}")
        return
    github_request("PUT", path, body={"role": "member"}, expected=(200, 201))
    print(f"Added {username} to {TEAM_SLUG}")


def remove_from_team(username: str) -> None:
    path = f"/orgs/{quote(ORG)}/teams/{quote(TEAM_SLUG)}/memberships/{quote(username)}"
    if DRY_RUN:
        print(f"DRY-RUN remove {username} from {TEAM_SLUG}")
        return
    github_request("DELETE", path, expected=(204,))
    print(f"Removed {username} from {TEAM_SLUG}")


def main() -> None:
    print(f"Synchronizing team '{TEAM_SLUG}' with all members of organization '{ORG}'")
    print(f"Dry run: {DRY_RUN}")
    print(f"Remove stale team members: {REMOVE_STALE_MEMBERS}")

    org_members = get_org_members()
    team_members = get_team_members()

    missing = sorted(org_members - team_members, key=str.lower)
    stale = sorted(team_members - org_members, key=str.lower)

    print(f"Organization members: {len(org_members)}")
    print(f"Current team members: {len(team_members)}")
    print(f"Missing from team: {len(missing)}")
    print(f"Stale in team: {len(stale)}")

    for username in missing:
        add_to_team(username)

    if REMOVE_STALE_MEMBERS:
        for username in stale:
            remove_from_team(username)
    elif stale:
        print("Stale users were found but not removed:")
        for username in stale:
            print(f"  {username}")

    print("Done.")


if __name__ == "__main__":
    main()
