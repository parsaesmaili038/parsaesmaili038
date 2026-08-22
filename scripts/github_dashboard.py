import os
import requests
from datetime import datetime, timezone

USERNAME = os.getenv("GITHUB_USERNAME", "parsaesmaili038")
TOKEN = os.getenv("GITHUB_TOKEN")

API = "https://api.github.com"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
}


def github_get(url, params=None):
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def get_user():
    return github_get(f"{API}/users/{USERNAME}")


def get_repositories():
    repos = []

    page = 1

    while True:
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

        repos.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repos


def calculate_stats(user, repos):
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)

    forks = sum(repo.get("forks_count", 0) for repo in repos)

    return {
        "stars": stars,
        "repositories": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "forks": forks,
    }


def escape_xml(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def create_svg(stats):
    now = datetime.now(timezone.utc)

    updated = now.strftime("%Y-%m-%d")

    stars = stats["stars"]
    repositories = stats["repositories"]
    followers = stats["followers"]
    following = stats["following"]
    forks = stats["forks"]

    width = 1100
    height = 620

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


<!-- Background -->

<rect
    x="0"
    y="0"
    width="{width}"
    height="{height}"
    rx="28"
    fill="url(#background)"
/>


<!-- Border -->

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


<!-- Header -->

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


<!-- Card 1 -->

<rect
    x="60"
    y="140"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="210"
    y="180"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    ⭐ STARS
</text>

<text
    x="210"
    y="235"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial"
    font-size="42"
    font-weight="700"
>
    {stars}
</text>


<!-- Card 2 -->

<rect
    x="400"
    y="140"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="550"
    y="180"
    text-anchor="middle"
    fill="#7C3AED"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    📦 REPOSITORIES
</text>

<text
    x="550"
    y="235"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial"
    font-size="42"
    font-weight="700"
>
    {repositories}
</text>


<!-- Card 3 -->

<rect
    x="740"
    y="140"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="890"
    y="180"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    👥 FOLLOWERS
</text>

<text
    x="890"
    y="235"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial"
    font-size="42"
    font-weight="700"
>
    {followers}
</text>


<!-- Card 4 -->

<rect
    x="60"
    y="315"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="210"
    y="355"
    text-anchor="middle"
    fill="#7C3AED"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    🔀 FORKS
</text>

<text
    x="210"
    y="410"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial"
    font-size="42"
    font-weight="700"
>
    {forks}
</text>


<!-- Card 5 -->

<rect
    x="400"
    y="315"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="550"
    y="355"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    👤 FOLLOWING
</text>

<text
    x="550"
    y="410"
    text-anchor="middle"
    fill="#FFFFFF"
    font-family="Arial"
    font-size="42"
    font-weight="700"
>
    {following}
</text>


<!-- Activity -->

<rect
    x="740"
    y="315"
    width="300"
    height="145"
    rx="20"
    fill="#161B22"
    stroke="#30363D"
    stroke-width="1"
/>

<text
    x="890"
    y="355"
    text-anchor="middle"
    fill="#7C3AED"
    font-family="Arial"
    font-size="18"
    font-weight="700"
>
    ⚡ STATUS
</text>

<text
    x="890"
    y="407"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial"
    font-size="24"
    font-weight="700"
>
    ACTIVE DEVELOPER
</text>


<!-- Footer -->

<text
    x="550"
    y="520"
    text-anchor="middle"
    fill="#8B949E"
    font-family="Arial"
    font-size="15"
>
    LIVE DATA • GENERATED AUTOMATICALLY
</text>

<text
    x="550"
    y="555"
    text-anchor="middle"
    fill="#58A6FF"
    font-family="Arial"
    font-size="15"
>
    LAST UPDATED: {escape_xml(updated)} UTC
</text>

</svg>
"""

    return svg


def main():
    print("Fetching GitHub data...")

    user = get_user()
    repos = get_repositories()

    stats = calculate_stats(user, repos)

    print("Statistics:")
    print(stats)

    svg = create_svg(stats)

    output = "dist/github-stats/overview.svg"

    os.makedirs(os.path.dirname(output), exist_ok=True)

    with open(output, "w", encoding="utf-8") as file:
        file.write(svg)

    print(f"Generated: {output}")


if __name__ == "__main__":
    main()
