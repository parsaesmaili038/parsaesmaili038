import os
import urllib.request
import json
from datetime import datetime, timezone


USERNAME = os.environ.get("GITHUB_USERNAME", "parsaesmaili038")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

OUTPUT_DIR = "dist/github-stats"

BLUE = "#58A6FF"
PURPLE = "#7C3AED"
BG = "#0D1117"
TEXT = "#E6EDF3"
MUTED = "#8B949E"
CARD = "#161B22"
BORDER = "#30363D"


def github_api(endpoint):
    url = f"https://api.github.com/{endpoint}"

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-profile-stats"
        }
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def svg_start(width, height):
    return f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}">
    <rect width="100%" height="100%" rx="18" fill="{BG}"/>
'''


def svg_end():
    return "</svg>"


def text(x, y, value, size=16, color=TEXT, weight="400"):
    safe = (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    return (
        f'<text x="{x}" y="{y}" '
        f'fill="{color}" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="{size}px" font-weight="{weight}">'
        f'{safe}</text>'
    )


def gradient():
    return f'''
    <defs>
        <linearGradient id="purpleBlue" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="{PURPLE}"/>
            <stop offset="100%" stop-color="{BLUE}"/>
        </linearGradient>

        <linearGradient id="bluePurple" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="{BLUE}"/>
            <stop offset="100%" stop-color="{PURPLE}"/>
        </linearGradient>
    </defs>
    '''


def card(x, y, width, height):
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
        f'rx="14" fill="{CARD}" stroke="{BORDER}"/>'
    )


def generate_stats(user):
    width = 900
    height = 330

    repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    following = user.get("following", 0)

    svg = svg_start(width, height)
    svg += gradient()

    svg += text(35, 45, "GitHub Statistics", 25, TEXT, "700")
    svg += text(
        35,
        70,
        f"@{USERNAME}",
        14,
        MUTED
    )

    boxes = [
        (35, 100, "Public Repositories", repos),
        (325, 100, "Followers", followers),
        (615, 100, "Following", following),
    ]

    for x, y, label, value in boxes:
        svg += card(x, y, 250, 170)

        svg += text(
            x + 25,
            y + 45,
            label,
            14,
            MUTED,
            "500"
        )

        svg += text(
            x + 25,
            y + 100,
            value,
            36,
            BLUE,
            "700"
        )

        svg += (
            f'<rect x="{x + 25}" y="{y + 125}" '
            f'width="200" height="5" rx="3" '
            f'fill="url(#purpleBlue)"/>'
        )

    svg += text(
        35,
        305,
        "Generated automatically with GitHub Actions",
        12,
        MUTED
    )

    svg += svg_end()

    save("stats.svg", svg)


def generate_streak(events):
    width = 900
    height = 300

    dates = []

    for event in events:
        created = event.get("created_at")

        if created:
            try:
                dt = datetime.fromisoformat(
                    created.replace("Z", "+00:00")
                )
                dates.append(dt.date())
            except ValueError:
                pass

    dates = sorted(set(dates))

    streak = 0
    best = 0

    if dates:
        current = dates[-1]

        for date in reversed(dates):
            if date == current:
                streak += 1
                current = current.fromordinal(
                    current.toordinal() - 1
                )
            else:
                break

        running = 1

        for i in range(1, len(dates)):
            difference = (
                dates[i] - dates[i - 1]
            ).days

            if difference == 1:
                running += 1
            else:
                running = 1

            best = max(best, running)

        best = max(best, streak)

    svg = svg_start(width, height)
    svg += gradient()

    svg += text(
        35,
        45,
        "GitHub Streak",
        25,
        TEXT,
        "700"
    )

    svg += card(35, 80, 400, 160)
    svg += card(465, 80, 400, 160)

    svg += text(
        65,
        120,
        "Current Streak",
        15,
        MUTED,
        "500"
    )

    svg += text(
        65,
        180,
        f"{streak} days",
        38,
        BLUE,
        "700"
    )

    svg += text(
        495,
        120,
        "Longest Streak",
        15,
        MUTED,
        "500"
    )

    svg += text(
        495,
        180,
        f"{best} days",
        38,
        PURPLE,
        "700"
    )

    svg += text(
        35,
        275,
        "Contribution activity detected from GitHub events",
        12,
        MUTED
    )

    svg += svg_end()

    save("streak.svg", svg)


def generate_languages(repositories):
    languages = {}

    for repo in repositories:
        language = repo.get("language")

        if language:
            languages[language] = languages.get(language, 0) + 1

    sorted_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True
    )[:8]

    total = sum(languages.values()) or 1

    width = 900
    row_height = 42
    height = 100 + row_height * len(sorted_languages)

    svg = svg_start(width, height)
    svg += gradient()

    svg += text(
        35,
        45,
        "Top Languages",
        25,
        TEXT,
        "700"
    )

    y = 85

    for index, (language, count) in enumerate(sorted_languages):
        percentage = (count / total) * 100

        svg += text(
            40,
            y,
            language,
            15,
            TEXT,
            "600"
        )

        svg += text(
            780,
            y,
            f"{percentage:.1f}%",
            14,
            MUTED,
            "500"
        )

        svg += (
            f'<rect x="40" y="{y + 10}" '
            f'width="800" height="8" rx="4" '
            f'fill="{BORDER}"/>'
        )

        bar_width = max(
            10,
            800 * percentage / 100
        )

        svg += (
            f'<rect x="40" y="{y + 10}" '
            f'width="{bar_width:.1f}" height="8" rx="4" '
            f'fill="url(#bluePurple)"/>'
        )

        y += row_height

    svg += svg_end()

    save("top-langs.svg", svg)


def save(filename, content):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"Generated: {path}")


def main():
    print(f"Generating statistics for @{USERNAME}")

    user = github_api(
        f"users/{USERNAME}"
    )

    repositories = github_api(
        f"users/{USERNAME}/repos?per_page=100&sort=updated"
    )

    events = github_api(
        f"users/{USERNAME}/events/public?per_page=100"
    )

    generate_stats(user)
    generate_streak(events)
    generate_languages(repositories)

    print("All SVG files generated successfully.")


if __name__ == "__main__":
    main()
