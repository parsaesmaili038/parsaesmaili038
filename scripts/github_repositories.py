import os
import time
from datetime import datetime, timezone

import requests


# =========================
# Configuration
# =========================

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "the-pa3a",
)

TOKEN = os.getenv("GITHUB_TOKEN")

API = "https://api.github.com"

REQUEST_DELAY = 20


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
    """
    Fetch the list of repositories owned by the user.

    This request is only used to discover repositories.
    """

    repositories = []

    for page in range(1, 100):
        data = github_get(
            f"{API}/users/{USERNAME}/repos",
            params={
                "per_page": 100,
                "page": page,
                "type": "owner",
                "sort": "updated",
            },
        )

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

    return repositories


def get_repository_details(repository_name):
    """Fetch detailed information for one repository."""

    return github_get(
        f"{API}/repos/{USERNAME}/{repository_name}"
    )


def get_repositories():
    """
    Fetch detailed repository information.

    Exactly one API request is made for each repository,
    with a 20-second delay between repository requests.
    """

    repository_list = get_repository_list()

    repositories = []

    total = len(repository_list)

    print(
        f"Found {total} repositories."
    )

    print(
        f"Fetching repository details "
        f"with a {REQUEST_DELAY}-second delay..."
    )

    for index, repository in enumerate(
        repository_list,
        start=1,
    ):
        name = repository.get("name")

        if not name:
            continue

        print(
            f"[{index}/{total}] "
            f"Requesting repository: {name}"
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

        print(
            "  → Repository received successfully."
        )

        if index < total:
            print(
                f"  → Waiting {REQUEST_DELAY} seconds "
                "before the next request..."
            )

            time.sleep(
                REQUEST_DELAY
            )

    return repositories


# =========================
# Statistics
# =========================

def calculate_statistics(user, repositories):
    """Calculate detailed repository statistics."""

    total_stars = sum(
        repo.get("stargazers_count", 0)
        for repo in repositories
    )

    total_forks = sum(
        repo.get("forks_count", 0)
        for repo in repositories
    )

    total_watchers = sum(
        repo.get("watchers_count", 0)
        for repo in repositories
    )

    total_open_issues = sum(
        repo.get("open_issues_count", 0)
        for repo in repositories
    )

    total_size_kb = sum(
        repo.get("size", 0)
        for repo in repositories
    )

    total_topics = sum(
        len(repo.get("topics", []))
        for repo in repositories
    )

    languages = {}

    for repo in repositories:
        language = repo.get("language")

        if language:
            languages[language] = (
                languages.get(language, 0) + 1
            )

    language_count = len(languages)

    archived = sum(
        1
        for repo in repositories
        if repo.get("archived")
    )

    forks = sum(
        1
        for repo in repositories
        if repo.get("fork")
    )

    original_repositories = (
        len(repositories) - forks
    )

    repositories_with_description = sum(
        1
        for repo in repositories
        if repo.get("description")
    )

    repositories_with_website = sum(
        1
        for repo in repositories
        if repo.get("homepage")
    )

    total_size_mb = total_size_kb / 1024

    return {
        "repositories": user.get(
            "public_repos",
            0,
        ),
        "stars": total_stars,
        "forks": total_forks,
        "watchers": total_watchers,
        "open_issues": total_open_issues,
        "languages": language_count,
        "original": original_repositories,
        "archived": archived,
        "size_mb": total_size_mb,
        "descriptions": repositories_with_description,
        "websites": repositories_with_website,
        "topics": total_topics,
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
    """Generate the GitHub repository analytics SVG."""

    width = 1100
    height = 760

    updated = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    cards = [
        (
            "📦",
            "REPOSITORIES",
            stats["repositories"],
            "#58A6FF",
        ),
        (
            "⭐",
            "TOTAL STARS",
            stats["stars"],
            "#F7DF1E",
        ),
        (
            "🔀",
            "TOTAL FORKS",
            stats["forks"],
            "#7C3AED",
        ),
        (
            "👀",
            "WATCHERS",
            stats["watchers"],
            "#58A6FF",
        ),
        (
            "🐛",
            "OPEN ISSUES",
            stats["open_issues"],
            "#F78166",
        ),
        (
            "💻",
            "LANGUAGES",
            stats["languages"],
            "#58A6FF",
        ),
        (
            "🧩",
            "ORIGINAL",
            stats["original"],
            "#7C3AED",
        ),
        (
            "📁",
            "ARCHIVED",
            stats["archived"],
            "#8B949E",
        ),
        (
            "💾",
            "TOTAL SIZE",
            f'{stats["size_mb"]:.1f} MB',
            "#58A6FF",
        ),
        (
            "📝",
            "DESCRIPTIONS",
            stats["descriptions"],
            "#7C3AED",
        ),
        (
            "🌐",
            "WEBSITES",
            stats["websites"],
            "#58A6FF",
        ),
        (
            "🏷️",
            "TOPICS",
            stats["topics"],
            "#7C3AED",
        ),
    ]

    positions = [
        (60, 140),
        (400, 140),
        (740, 140),
        (60, 310),
        (400, 310),
        (740, 310),
        (60, 480),
        (400, 480),
        (740, 480),
        (60, 650),
        (400, 650),
        (740, 650),
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
    📦 PARSA ESMAILI — REPOSITORY ANALYTICS
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
    ), (
        x,
        y,
    ) in zip(cards, positions):

        svg += f"""

<rect
    x="{x}"
    y="{y}"
    width="300"
    height="135"
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
    font-size="17"
    font-weight="700"
>
    {escape_xml(icon)} {escape_xml(label)}
</text>


<text
    x="{x + 150}"
    y="{y + 100}"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="38"
    font-weight="700"
>
    {escape_xml(value)}
</text>
"""

    svg += f"""

<text
    x="550"
    y="730"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    LIVE DATA • GENERATED AUTOMATICALLY
</text>


<text
    x="550"
    y="752"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="13"
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

    print(
        "Fetching repository list..."
    )

    repositories = get_repositories()

    print(
        f"Successfully fetched details for "
        f"{len(repositories)} repositories."
    )

    stats = calculate_statistics(
        user,
        repositories,
    )

    print("Repository statistics:")

    for key, value in stats.items():
        print(
            f"{key}: {value}"
        )

    svg = create_svg(stats)

    output = (
        "dist/github-stats/"
        "repositories.svg"
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
