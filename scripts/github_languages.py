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

def get_repositories():
    """Fetch all repositories owned by the user."""

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


def get_language_bytes(repository):
    """Fetch language byte counts for a repository."""

    return github_get(
        f"{API}/repos/{USERNAME}/{repository}/languages"
    )


def collect_languages(repositories):
    """Collect language byte counts from all repositories."""

    totals = {}

    for repository in repositories:
        name = repository.get("name")

        if not name:
            continue

        print(f"Reading languages: {name}")

        try:
            languages = get_language_bytes(name)

        except RuntimeError as error:
            print(
                f"Skipping {name}: {error}"
            )
            continue

        for language, byte_count in languages.items():
            totals[language] = (
                totals.get(language, 0)
                + byte_count
            )

    return totals


# =========================
# Statistics
# =========================

def calculate_percentages(totals):
    """Convert language byte counts into percentages."""

    total_bytes = sum(totals.values())

    if total_bytes == 0:
        return []

    languages = []

    for language, byte_count in totals.items():
        percentage = (
            byte_count / total_bytes
        ) * 100

        languages.append(
            {
                "name": language,
                "bytes": byte_count,
                "percentage": percentage,
            }
        )

    languages.sort(
        key=lambda item: item["bytes"],
        reverse=True,
    )

    return languages


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


def create_svg(languages):
    """Generate the language analytics SVG."""

    width = 1100
    height = 620

    updated = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    visible_languages = languages[:8]

    if not visible_languages:
        visible_languages = [
            {
                "name": "No data",
                "bytes": 0,
                "percentage": 0,
            }
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
    y="70"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="28"
    font-weight="700"
>
    💻 PARSA ESMAILI — LANGUAGE ANALYTICS
</text>


<rect
    x="180"
    y="92"
    width="740"
    height="3"
    rx="2"
    fill="url(#accent)"
/>


<text
    x="550"
    y="135"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    Programming languages used across public repositories
</text>
"""

    start_y = 175
    row_height = 42

    for index, language in enumerate(
        visible_languages
    ):
        y = start_y + (
            index * row_height
        )

        name = escape_xml(
            language["name"]
        )

        percentage = language[
            "percentage"
        ]

        bar_width = max(
            5,
            min(
                720,
                percentage * 7.2,
            ),
        )

        svg += f"""

<text
    x="90"
    y="{y}"
    fill="#FFFFFF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="16"
    font-weight="700"
>
    {name}
</text>


<rect
    x="230"
    y="{y - 16}"
    width="720"
    height="20"
    rx="10"
    fill="#21262D"
/>


<rect
    x="230"
    y="{y - 16}"
    width="{bar_width:.2f}"
    height="20"
    rx="10"
    fill="url(#accent)"
/>


<text
    x="975"
    y="{y}"
    text-anchor="end"
    fill="#58A6FF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="15"
    font-weight="700"
>
    {percentage:.1f}%
</text>
"""

    svg += f"""

<text
    x="550"
    y="560"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    LIVE DATA • GENERATED AUTOMATICALLY
</text>


<text
    x="550"
    y="590"
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
        f"Fetching GitHub repositories for @{USERNAME}..."
    )

    repositories = get_repositories()

    print(
        f"Found {len(repositories)} repositories."
    )

    print(
        "Collecting language statistics..."
    )

    totals = collect_languages(
        repositories
    )

    languages = calculate_percentages(
        totals
    )

    print("Language statistics:")

    for language in languages:
        print(
            f'{language["name"]}: '
            f'{language["percentage"]:.2f}%'
        )

    svg = create_svg(languages)

    output = (
        "dist/github-stats/"
        "languages.svg"
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
