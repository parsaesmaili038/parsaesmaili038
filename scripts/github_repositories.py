import os
import sys
import time
from datetime import datetime, timezone

import requests


# =========================================================
# Configuration
# =========================================================

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "the-par3a",
)

TOKEN = os.getenv("GITHUB_TOKEN")

API = "https://api.github.com"

# Delay between expensive per-repository API requests.
# Set to 0 to disable the delay.
REQUEST_DELAY = 2


# =========================================================
# UTF-8 Console Support
# =========================================================

# GitHub Actions Windows runners may use cp1252 by default.
# Force UTF-8 so Unicode characters such as arrows and emoji
# do not cause UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace",
    )

if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace",
    )


# =========================================================
# HTTP Client
# =========================================================

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


def github_get_count(url, params=None):
    """
    Fetch a paginated GitHub API endpoint and count all returned items.

    This is used for repositories where the API does not expose
    a direct total count.
    """

    total = 0

    for page in range(1, 100):
        current_params = dict(params or {})
        current_params["per_page"] = 100
        current_params["page"] = page

        data = github_get(
            url,
            params=current_params,
        )

        if not data:
            break

        total += len(data)

        if len(data) < 100:
            break

    return total


# =========================================================
# GitHub Profile
# =========================================================

def get_user():
    """Fetch the GitHub user profile."""

    return github_get(
        f"{API}/users/{USERNAME}"
    )


# =========================================================
# Repository Discovery
# =========================================================

def get_repository_list():
    """
    Fetch repositories owned by the target user.

    The public user endpoint is used because the workflow is
    primarily intended for public GitHub profile statistics.
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
    Fetch detailed information for every discovered repository.

    Repository details are requested individually because the
    repository list endpoint does not contain every field required
    by the dashboard.
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
            "  -> Repository received successfully."
        )

        if (
            REQUEST_DELAY > 0
            and index < total
        ):
            print(
                f"  -> Waiting {REQUEST_DELAY} seconds..."
            )

            time.sleep(
                REQUEST_DELAY
            )

    return repositories


# =========================================================
# Repository Statistics
# =========================================================

def calculate_repository_statistics(
    user,
    repositories,
):
    """Calculate statistics that can be derived from repository data."""

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

    open_issues = sum(
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

    archived = sum(
        1
        for repo in repositories
        if repo.get("archived")
    )

    forked = sum(
        1
        for repo in repositories
        if repo.get("fork")
    )

    original = (
        len(repositories) - forked
    )

    descriptions = sum(
        1
        for repo in repositories
        if repo.get("description")
    )

    websites = sum(
        1
        for repo in repositories
        if repo.get("homepage")
    )

    licenses = sum(
        1
        for repo in repositories
        if repo.get("license")
    )

    public_repositories = sum(
        1
        for repo in repositories
        if not repo.get("private", False)
    )

    private_repositories = sum(
        1
        for repo in repositories
        if repo.get("private", False)
    )

    languages = {}

    for repo in repositories:
        language = repo.get("language")

        if language:
            languages[language] = (
                languages.get(language, 0) + 1
            )

    language_count = len(languages)

    total_repositories = len(repositories)

    fork_percentage = (
        (forked / total_repositories) * 100
        if total_repositories
        else 0
    )

    total_issues = sum(
        repo.get("open_issues_count", 0)
        for repo in repositories
    )

    total_size_mb = (
        total_size_kb / 1024
    )

    oldest = None
    newest = None
    latest_push = None

    for repo in repositories:
        created_at = repo.get("created_at")
        pushed_at = repo.get("pushed_at")

        if created_at:
            if (
                oldest is None
                or created_at < oldest.get("created_at", "")
            ):
                oldest = repo

            if (
                newest is None
                or created_at > newest.get("created_at", "")
            ):
                newest = repo

        if pushed_at:
            if (
                latest_push is None
                or pushed_at > latest_push.get("pushed_at", "")
            ):
                latest_push = repo

    return {
        "repositories": user.get(
            "public_repos",
            total_repositories,
        ),
        "stars": total_stars,
        "forks": total_forks,
        "watchers": total_watchers,
        "open_issues": open_issues,
        "languages": language_count,
        "original": original,
        "archived": archived,
        "forked": forked,
        "fork_percentage": fork_percentage,
        "size_mb": total_size_mb,
        "descriptions": descriptions,
        "websites": websites,
        "topics": total_topics,
        "licenses": licenses,
        "public": public_repositories,
        "private": private_repositories,
        "oldest": (
            oldest.get("name", "N/A")
            if oldest
            else "N/A"
        ),
        "newest": (
            newest.get("name", "N/A")
            if newest
            else "N/A"
        ),
        "latest_push": (
            latest_push.get("name", "N/A")
            if latest_push
            else "N/A"
        ),
    }


# =========================================================
# Global GitHub Statistics
# =========================================================

def get_global_statistics():
    """
    Fetch account-level statistics using GitHub's search API.

    These counts are useful for activity metrics that cannot be
    calculated reliably from repository metadata alone.
    """

    print("")
    print("Fetching global GitHub statistics...")

    # Pull requests authored by the user.
    pull_requests = github_get(
        f"{API}/search/issues",
        params={
            "q": f"author:{USERNAME} type:pr",
            "per_page": 1,
        },
    ).get(
        "total_count",
        0,
    )

    print(
        f"  -> Pull requests: {pull_requests}"
    )

    # Issues authored by the user.
    authored_issues = github_get(
        f"{API}/search/issues",
        params={
            "q": f"author:{USERNAME} type:issue",
            "per_page": 1,
        },
    ).get(
        "total_count",
        0,
    )

    print(
        f"  -> Authored issues: {authored_issues}"
    )

    # Closed issues authored by the user.
    closed_issues = github_get(
        f"{API}/search/issues",
        params={
            "q": f"author:{USERNAME} type:issue state:closed",
            "per_page": 1,
        },
    ).get(
        "total_count",
        0,
    )

    print(
        f"  -> Closed issues: {closed_issues}"
    )

    # Open issues authored by the user.
    open_issues = github_get(
        f"{API}/search/issues",
        params={
            "q": f"author:{USERNAME} type:issue state:open",
            "per_page": 1,
        },
    ).get(
        "total_count",
        0,
    )

    print(
        f"  -> Open issues: {open_issues}"
    )

    return {
        "pull_requests": pull_requests,
        "authored_issues": authored_issues,
        "closed_issues": closed_issues,
        "open_issues": open_issues,
    }


# =========================================================
# Commit Statistics
# =========================================================

def get_commit_count(repositories):
    """
    Count commits in the user's repositories.

    The GitHub commits endpoint is queried for every repository.
    """

    total_commits = 0

    print("")
    print("Counting repository commits...")

    for index, repo in enumerate(
        repositories,
        start=1,
    ):
        name = repo.get("name")

        if not name:
            continue

        print(
            f"[{index}/{len(repositories)}] "
            f"Counting commits: {name}"
        )

        try:
            commits = github_get(
                f"{API}/repos/{USERNAME}/{name}/commits",
                params={
                    "per_page": 1,
                },
            )
        except RuntimeError as error:
            print(
                f"  -> Failed to count commits: {error}"
            )
            continue

        # The commits endpoint itself does not expose total_count.
        # Read the Link header through a lightweight direct request.
        try:
            response = SESSION.get(
                f"{API}/repos/{USERNAME}/{name}/commits",
                params={
                    "per_page": 1,
                },
                timeout=30,
            )

            response.raise_for_status()

            link = response.headers.get(
                "Link",
                "",
            )

            last_page = 1

            if 'rel="last"' in link:
                for part in link.split(","):
                    if 'rel="last"' in part:
                        url_part = part.split(";")[0]
                        url_part = (
                            url_part
                            .strip()
                            .strip("<>")
                        )

                        if "page=" in url_part:
                            last_page = int(
                                url_part.split("page=")[-1]
                            )

            total_commits += last_page

        except (
            requests.RequestException,
            ValueError,
        ) as error:
            print(
                f"  -> Failed to determine commit count: {error}"
            )

        if (
            REQUEST_DELAY > 0
            and index < len(repositories)
        ):
            time.sleep(
                REQUEST_DELAY
            )

    print(
        f"Total commits: {total_commits}"
    )

    return total_commits


# =========================================================
# Release Statistics
# =========================================================

def get_release_count(repositories):
    """Count releases across all repositories."""

    total_releases = 0

    print("")
    print("Counting releases...")

    for index, repo in enumerate(
        repositories,
        start=1,
    ):
        name = repo.get("name")

        if not name:
            continue

        try:
            releases = github_get(
                f"{API}/repos/{USERNAME}/{name}/releases",
                params={
                    "per_page": 100,
                },
            )

            count = len(releases)

            total_releases += count

            if count:
                print(
                    f"[{index}/{len(repositories)}] "
                    f"{name}: {count} releases"
                )

        except RuntimeError as error:
            print(
                f"Failed to count releases for {name}: {error}"
            )

        if (
            REQUEST_DELAY > 0
            and index < len(repositories)
        ):
            time.sleep(
                REQUEST_DELAY
            )

    print(
        f"Total releases: {total_releases}"
    )

    return total_releases


# =========================================================
# SVG Utilities
# =========================================================

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


def create_card(
    x,
    y,
    icon,
    label,
    value,
    accent,
):
    """Create one dashboard statistic card."""

    return f"""
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
    font-size="36"
    font-weight="700"
>
    {escape_xml(value)}
</text>
"""


def create_svg(stats):
    """Generate the GitHub repository analytics SVG."""

    width = 1100
    height = 1270

    updated = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

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
            "📝",
            "COMMITS",
            stats["commits"],
            "#3FB950",
        ),
        (
            "🔀",
            "PULL REQUESTS",
            stats["pull_requests"],
            "#A371F7",
        ),
        (
            "📦",
            "RELEASES",
            stats["releases"],
            "#F0883E",
        ),
        (
            "🐛",
            "OPEN ISSUES",
            stats["open_issues"],
            "#F78166",
        ),
        (
            "✅",
            "CLOSED ISSUES",
            stats["closed_issues"],
            "#3FB950",
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
            "🌿",
            "FORKED REPOS",
            stats["forked"],
            "#A371F7",
        ),
        (
            "📈",
            "FORK PERCENTAGE",
            f'{stats["fork_percentage"]:.1f}%',
            "#F0883E",
        ),
        (
            "📁",
            "ARCHIVED",
            stats["archived"],
            "#8B949E",
        ),
        (
            "📜",
            "WITH LICENSE",
            stats["licenses"],
            "#3FB950",
        ),
        (
            "🌐",
            "PUBLIC",
            stats["public"],
            "#58A6FF",
        ),
        (
            "🔒",
            "PRIVATE",
            stats["private"],
            "#F78166",
        ),
        (
            "💾",
            "TOTAL SIZE",
            f'{stats["size_mb"]:.1f} MB',
            "#58A6FF",
        ),
        (
            "🏷️",
            "TOPICS",
            stats["topics"],
            "#7C3AED",
        ),
        (
            "📝",
            "DESCRIPTIONS",
            stats["descriptions"],
            "#A371F7",
        ),
        (
            "🌍",
            "WEBSITES",
            stats["websites"],
            "#58A6FF",
        ),
        (
            "📊",
            "TOTAL ISSUES",
            stats["authored_issues"],
            "#F0883E",
        ),
    ]

    positions = []

    start_y = 140
    row_height = 155

    for row in range(
        (len(cards) + 2) // 3
    ):
        y = start_y + (
            row * row_height
        )

        positions.extend(
            [
                (60, y),
                (400, y),
                (740, y),
            ]
        )

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
    📊 PARSA ESMAILI — GITHUB ANALYTICS
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
        card,
        position,
    ) in zip(
        cards,
        positions,
    ):
        (
            icon,
            label,
            value,
            accent,
        ) = card

        x, y = position

        svg += create_card(
            x,
            y,
            icon,
            label,
            value,
            accent,
        )

    # Determine the bottom of the card grid.
    last_card_y = positions[
        len(cards) - 1
    ][1]

    footer_y = last_card_y + 175

    svg += f"""

<text
    x="550"
    y="{footer_y}"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="14"
>
    LIVE DATA • GENERATED AUTOMATICALLY
</text>

<text
    x="550"
    y="{footer_y + 25}"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial, Helvetica, sans-serif"
    font-size="13"
>
    LAST UPDATED: {escape_xml(updated)}
</text>

<text
    x="550"
    y="{footer_y + 55}"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="12"
>
    Latest push: {escape_xml(stats["latest_push"])}
</text>

<text
    x="550"
    y="{footer_y + 78}"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial, Helvetica, sans-serif"
    font-size="12"
>
    Oldest repository: {escape_xml(stats["oldest"])}
    •
    Newest repository: {escape_xml(stats["newest"])}
</text>

</svg>
"""

    return svg


# =========================================================
# Main
# =========================================================

def main():
    print(
        f"Fetching GitHub profile for @{USERNAME}..."
    )

    user = get_user()

    print(
        "Fetching repository list..."
    )

    repositories = get_repositories()

    print("")
    print(
        f"Successfully fetched details for "
        f"{len(repositories)} repositories."
    )

    print("")
    print("Calculating repository statistics...")

    stats = calculate_repository_statistics(
        user,
        repositories,
    )

    global_stats = get_global_statistics()

    print("")
    print("Collecting commit statistics...")

    commits = get_commit_count(
        repositories
    )

    print("")
    print("Collecting release statistics...")

    releases = get_release_count(
        repositories
    )

    stats.update(
        global_stats
    )

    stats.update(
        {
            "commits": commits,
            "releases": releases,
        }
    )

    print("")
    print("======================================")
    print("GitHub Repository Statistics")
    print("======================================")

    for key, value in stats.items():
        print(
            f"{key}: {value}"
        )

    print("======================================")

    svg = create_svg(
        stats
    )

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

    print("")
    print(
        f"Generated: {output}"
    )


if __name__ == "__main__":
    main()

