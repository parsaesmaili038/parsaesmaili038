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


# =========================
# HTTP Client
# =========================

if not TOKEN:
    raise RuntimeError(
        "GITHUB_TOKEN is not available. "
        "Please set the GITHUB_TOKEN environment variable."
    )


HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


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
    """Fetch the GitHub user profile."""

    return github_get(
        f"{API}/users/{USERNAME}"
    )


def get_repository_list():
    """Fetch the list of repositories owned by the user."""

    repositories = []

    for page in range(1, 100):
        data = github_get(
            f"{API}/users/{USERNAME}/repos",
            params={
                "per_page": 100,
                "page": page,
                "type": "owner",
            },
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

    return repositories


def get_repository_details(repository_name):
    """
    Fetch complete information for one repository.

    This makes one API request per repository.
    """

    return github_get(
        f"{API}/repos/{USERNAME}/{repository_name}"
    )


def get_repositories():
    """
    Fetch all repositories and then request
    detailed information for every repository.
    """

    repository_list = get_repository_list()

    repositories = []

    print(
        f"Found {len(repository_list)} repositories."
    )

    print(
        "Fetching repository details..."
    )

    for index, repository in enumerate(
        repository_list,
        start=1,
    ):
        name = repository.get("name")

        if not name:
            continue

        print(
            f"[{index}/{len(repository_list)}] "
            f"Fetching: {name}"
        )

        try:
            details = get_repository_details(
                name
            )

        except RuntimeError as error:
            print(
                f"Skipping {name}: {error}"
            )
            continue

        repositories.append(details)

    return repositories


# =========================
# Statistics
# =========================

def calculate_stats(user, repositories):
    """Calculate GitHub profile statistics."""

    stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repositories
    )

    forks = sum(
        repo.get("forks_count", 0)
        for repo in repositories
    )

    return {
        "stars": stars,
        "repositories": user.get(
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
        "forks": forks,
    }


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
    """Generate the GitHub analytics SVG."""

    width = 1100
    height = 620

    updated = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    cards = [
        (
            "⭐",
            "STARS",
            stats["stars"],
            "#58A6FF",
        ),
        (
            "📦",
            "REPOSITORIES",
            stats["repositories"],
            "#7C3AED",
        ),
        (
            "👥",
            "FOLLOWERS",
            stats["followers"],
            "#58A6FF",
        ),
        (
            "🔀",
            "FORKS",
            stats["forks"],
            "#7C3AED",
        ),
        (
            "👤",
            "FOLLOWING",
            stats["following"],
            "#58A6FF",
        ),
        (
            "⚡",
            "STATUS",
            "ACTIVE",
            "#7C3AED",
        ),
    ]

    positions = [
        (60, 140),
        (400, 140),
        (740, 140),
        (60, 315),
        (400, 315),
        (740, 315),
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
        <stop
            offset="0%"
            stop-color="#0D1117"
        />

        <stop
            offset="55%"
            stop-color="#111827"
        />

        <stop
            offset="100%"
            stop-color="#17113A"
        />
    </linearGradient>

    <linearGradient
        id="accent"
        x1="0"
        y1="0"
        x2="1"
        y2="0"
    >
        <stop
            offset="0%"
            stop-color="#58A6FF"
        />

        <stop
            offset="100%"
            stop-color="#7C3AED"
        />
    </linearGradient>

    <filter id="glow">

        <feGaussianBlur
            stdDeviation="5"
            result="blur"
        />

        <feMerge>
            <feMergeNode in="blur"/>
            <feMergeNode in="SourceGraphic"/>
        </feMerge>

    </filter>

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
    y="70"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="28"
    font-weight="700"
>
    🚀 PARSA ESMAILI — GITHUB ANALYTICS
</text>


<rect
    x="180"
    y="92"
    width="740"
    height="3"
    rx="2"
    fill="url(#accent)"
    filter="url(#glow)"
/>
"""

    for (
        icon,
        label,
        value,
        accent,
    ), (
        x,
        y,
    ) in zip(cards, positions):

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
    y="{y + 40}"
    text-anchor="middle"
    fill="{accent}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="18"
    font-weight="700"
>
    {escape_xml(icon)}
    {escape_xml(label)}
</text>

<text
    x="{x + 150}"
    y="{y + 100}"
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
    y="520"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
>
    LIVE DATA • GENERATED AUTOMATICALLY
</text>

<text
    x="550"
    y="555"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
>
    LAST UPDATED: {escape_xml(updated)}
</text>

</svg>
"""

    return svg


# =========================
# Main
# =========================

def main():
    print(
        f"Fetching GitHub data for @{USERNAME}..."
    )

    user = get_user()

    repositories = get_repositories()

    stats = calculate_stats(
        user,
        repositories,
    )

    print("Statistics:")

    for key, value in stats.items():
        print(
            f"{key}: {value}"
        )

    output = (
        "dist/github-stats/"
        "overview.svg"
    )

    os.makedirs(
        os.path.dirname(output),
        exist_ok=True,
    )

    svg = create_svg(stats)

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
