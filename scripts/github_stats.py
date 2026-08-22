import os
import requests
from datetime import datetime

USERNAME = "parsaesmaili038"

TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError("GITHUB_TOKEN is not available")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}


def github_get(url, params=None):
    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_user():
    return github_get(
        f"https://api.github.com/users/{USERNAME}"
    )


def get_repositories():
    repositories = []

    page = 1

    while True:
        data = github_get(
            f"https://api.github.com/users/{USERNAME}/repos",
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

        page += 1

    return repositories


def calculate_statistics(user, repositories):
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
        "repositories": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "forks": forks,
    }


def escape_xml(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def create_svg(stats):
    width = 1100
    height = 520

    cards = [
        ("⭐", "STARS", stats["stars"]),
        ("🔥", "CONTRIBUTIONS", stats["contributions"]),
        ("📦", "REPOSITORIES", stats["repositories"]),
        ("👥", "FOLLOWERS", stats["followers"]),
        ("🍴", "FORKS", stats["forks"]),
        ("➡️", "FOLLOWING", stats["following"]),
    ]

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
>
    <defs>
        <linearGradient id="background" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0D1117"/>
            <stop offset="100%" stop-color="#161B22"/>
        </linearGradient>

        <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#58A6FF"/>
            <stop offset="100%" stop-color="#7C3AED"/>
        </linearGradient>
    </defs>

    <rect
        width="1100"
        height="520"
        rx="24"
        fill="url(#background)"
    />

    <rect
        x="2"
        y="2"
        width="1096"
        height="516"
        rx="22"
        fill="none"
        stroke="url(#accent)"
        stroke-width="2"
    />

    <text
        x="550"
        y="58"
        text-anchor="middle"
        fill="#FFFFFF"
        font-family="Arial, sans-serif"
        font-size="28"
        font-weight="700"
    >
        🚀 PARSA • GITHUB ANALYTICS
    </text>

    <text
        x="550"
        y="88"
        text-anchor="middle"
        fill="#8B949E"
        font-family="Arial, sans-serif"
        font-size="14"
    >
        Live statistics generated automatically
    </text>
'''

    positions = [
        (40, 120),
        (380, 120),
        (720, 120),
        (40, 300),
        (380, 300),
        (720, 300),
    ]

    for (icon, label, value), (x, y) in zip(cards, positions):
        svg += f'''
    <rect
        x="{x}"
        y="{y}"
        width="300"
        height="140"
        rx="18"
        fill="#161B22"
        stroke="#30363D"
        stroke-width="1"
    />

    <text
        x="{x + 25}"
        y="{y + 42}"
        fill="#FFFFFF"
        font-family="Arial, sans-serif"
        font-size="25"
    >
        {escape_xml(icon)}
    </text>

    <text
        x="{x + 65}"
        y="{y + 39}"
        fill="#58A6FF"
        font-family="Arial, sans-serif"
        font-size="14"
        font-weight="700"
    >
        {escape_xml(label)}
    </text>

    <text
        x="{x + 25}"
        y="{y + 95}"
        fill="#FFFFFF"
        font-family="Arial, sans-serif"
        font-size="32"
        font-weight="700"
    >
        {escape_xml(value)}
    </text>
'''

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    svg += f'''
    <text
        x="550"
        y="485"
        text-anchor="middle"
        fill="#8B949E"
        font-family="Arial, sans-serif"
        font-size="12"
    >
        Last updated: {now}
    </text>

</svg>
'''

    return svg


def main():
    print("Fetching GitHub data...")

    user = get_user()
    repositories = get_repositories()

    stats = calculate_statistics(
        user,
        repositories,
    )

    # Temporary contribution value.
    # We will replace this with GitHub GraphQL
    # contribution data in the next step.
    stats["contributions"] = 0

    print("Statistics:")
    print(stats)

    output_directory = "dist/github-stats"

    os.makedirs(
        output_directory,
        exist_ok=True,
    )

    svg = create_svg(stats)

    output_file = os.path.join(
        output_directory,
        "overview.svg",
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(svg)

    print(f"Generated: {output_file}")


if __name__ == "__main__":
    main()
