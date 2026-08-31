import os
from datetime import datetime, timezone

import requests


# =========================
# Configuration
# =========================

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "the-par3a",
)

TOKEN = os.getenv("GITHUB_TOKEN")

API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


# =========================
# HTTP Client
# =========================

if not TOKEN:
    raise RuntimeError(
        "GITHUB_TOKEN is not available. "
        "Please set the GITHUB_TOKEN environment variable."
    )


SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def github_get(url, params=None):
    """Send a GET request to the GitHub API."""

    try:
        response = SESSION.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as error:
        raise RuntimeError(
            f"GitHub API request failed: {error}"
        ) from error

    return response.json()


# =========================
# GitHub API
# =========================

def get_user():
    """Fetch the GitHub profile."""

    return github_get(
        f"{API}/users/{USERNAME}"
    )


def get_events():
    """Fetch recent public GitHub events."""

    events = []

    for page in range(1, 4):
        data = github_get(
            f"{API}/users/{USERNAME}/events/public",
            params={
                "per_page": 100,
                "page": page,
            },
        )

        if not data:
            break

        events.extend(data)

        if len(data) < 100:
            break

    return events


# =========================
# Statistics
# =========================

def calculate_activity(user, events):
    """Calculate activity statistics."""

    stats = {
        "public_repositories": user.get(
            "public_repos",
            0,
        ),
        "followers": user.get(
            "followers",
            0,
        ),
        "following": user.get(
            "following",
            0,
        ),
        "push_events": 0,
        "pull_requests": 0,
        "issues": 0,
        "stars": 0,
        "forks": 0,
    }

    for event in events:
        event_type = event.get("type", "")

        if event_type == "PushEvent":
            stats["push_events"] += 1

        elif event_type == "PullRequestEvent":
            stats["pull_requests"] += 1

        elif event_type == "IssuesEvent":
            stats["issues"] += 1

        elif event_type == "WatchEvent":
            stats["stars"] += 1

        elif event_type == "ForkEvent":
            stats["forks"] += 1

    stats["events"] = len(events)

    return stats


# =========================
# SVG Utilities
# =========================

def escape_xml(value):
    """Escape text for safe use inside SVG/XML."""

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def create_svg(stats):
    """Generate the GitHub activity SVG."""

    width = 1100
    height = 620

    updated = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    cards = [
        (
            "⚡",
            "PUSH EVENTS",
            stats["push_events"],
            "#58A6FF",
        ),
        (
            "🔀",
            "PULL REQUESTS",
            stats["pull_requests"],
            "#7C3AED",
        ),
        (
            "💬",
            "ISSUES",
            stats["issues"],
            "#58A6FF",
        ),
        (
            "⭐",
            "STAR EVENTS",
            stats["stars"],
            "#F7DF1E",
        ),
        (
            "🍴",
            "FORK EVENTS",
            stats["forks"],
            "#7C3AED",
        ),
        (
            "📡",
            "PUBLIC EVENTS",
            stats["events"],
            "#58A6FF",
        ),
    ]

    positions = [
        (60, 145),
        (400, 145),
        (740, 145),
        (60, 330),
        (400, 330),
        (740, 330),
    ]

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
>

<defs>

    <linearGradient
        id="background"
        x1="0"
        y1="0"
        x2="1"
        y2="1"
    >
        <stop offset="0%" stop-color="#0D1117"/>
        <stop offset="55%" stop-color="#111827"/>
        <stop offset="100%" stop-color="#17113A"/>
    </linearGradient>

    <linearGradient
        id="accent"
        x1="0"
        y1="0"
        x2="1"
        y2="0"
    >
        <stop offset="0%" stop-color="#58A6FF"/>
        <stop offset="100%" stop-color="#7C3AED"/>
    </linearGradient>

</defs>

<rect
    x="0"
    y="0"
    width="{width}"
    height="{height}"
    rx="28"
    fill="url(#background)"
/>

<rect
    x="2"
    y="2"
    width="{width - 4}"
    height="{height - 4}"
    rx="28"
    fill="none"
    stroke="#30363D"
    stroke-width="2"
/>

<text
    x="550"
    y="68"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="28"
    font-weight="700"
>
    ⚡ PARSA ESMAILI — ACTIVITY ANALYTICS
</text>

<rect
    x="180"
    y="92"
    width="740"
    height="3"
    rx="2"
    fill="url(#accent)"
/>
"""

    for (
        icon,
        label,
        value,
        accent,
    ), (x, y) in zip(cards, positions):

        svg += f"""

<rect
    x="{x}"
    y="{y}"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="{x + 150}"
    y="{y + 42}"
    text-anchor="middle"
    fill="{accent}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="18"
    font-weight="700"
>
    {escape_xml(icon)} {escape_xml(label)}
</text>

<text
    x="{x + 150}"
    y="{y + 103}"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="42"
    font-weight="700"
>
    {escape_xml(value)}
</text>
"""

    svg += f"""

<text
    x="550"
    y="535"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    RECENT PUBLIC ACTIVITY • GENERATED AUTOMATICALLY
</text>

<text
    x="550"
    y="570"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    LAST UPDATED: {escape_xml(updated)} UTC
</text>

</svg>
"""

    return svg


# =========================
# Main
# =========================

def main():
    print(
        f"Fetching GitHub profile for @{USERNAME}..."
    )

    user = get_user()

    print("Fetching public activity...")

    events = get_events()

    print(
        f"Found {len(events)} public events."
    )

    stats = calculate_activity(
        user,
        events,
    )

    print("Activity statistics:")

    for key, value in stats.items():
        print(f"{key}: {value}")

    svg = create_svg(stats)

    output = (
        "dist/github-stats/"
        "activity.svg"
    )

    os.makedirs(
        os.path.dirname(output),
        exist_ok=True,
    )

    with open(
        output,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(svg)

    print(
        f"Generated: {output}"
    )


if __name__ == "__main__":
    main()
