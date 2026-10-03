#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README.

- duck-{dark,light}.svg  : a pixel duck waddles across the contribution graph,
                           revealing each week's squares as it passes.
- stats-{dark,light}.svg : animated activity card (contributions, commits, PRs,
                           streaks, years on GitHub and top languages).

Only uses the standard library; reads GITHUB_TOKEN / GH_TOKEN from the env.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

USER = os.environ.get("GH_USER", "KeveenMenezes")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      totalPullRequestContributions
      totalPullRequestReviewContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount contributionLevel date } }
      }
    }
  }
}
"""

THEMES = {
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "text": "#e6edf3", "muted": "#7d8590",
        "accent": "#39d353",
        "levels": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "muted": "#656d76",
        "accent": "#1a7f37",
        "levels": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}
LEVEL = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GH_TOKEN or GITHUB_TOKEN is required")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        body = json.load(res)
    if "errors" in body:
        sys.exit(json.dumps(body["errors"], indent=2))
    return body["data"]["user"]


# ---------------------------------------------------------------- duck sprite
# Pixel art, facing right. Nod to the old Naruto duck: spiky hair + headband.
#   Y hair  B headband  M plate  W body  E eye  O beak/feet
DUCK = [
    ".....Y.Y.Y....",
    "....YYYYYYY...",
    "...BBBBMMBB...",
    "...WWWWWWWW...",
    "...WWWWWWEW...",
    "...WWWWWWWWOO.",
    "...WWWWWWWOOO.",
    "....WWWWWW....",
    ".WW.WWWWWW....",
    "WWWWWWWWWWW...",
    "WWWWWWWWWWWW..",
    ".WWWWWWWWWW...",
    "..WWWWWWWW....",
]
FEET = {"back": [(4, 13), (3, 14), (4, 14)], "front": [(8, 13), (7, 14), (8, 14)]}
PALETTE = {"Y": "#ffd23f", "B": "#3b4a6b", "M": "#c9d1d9", "W": "#ffffff", "E": "#1f2328", "O": "#ff7a00"}
OUTLINE = "#1f2328"


def pixels_to_rects(cells, px, color_of):
    return "".join(
        f'<rect x="{x * px}" y="{y * px}" width="{px}" height="{px}" fill="{color_of(c)}"/>'
        for (x, y, c) in cells
    )


def outline_of(cells, px):
    filled = {(x, y) for x, y, _ in cells}
    ring = set()
    for x, y in filled:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            if (x + dx, y + dy) not in filled:
                ring.add((x + dx, y + dy))
    return "".join(f'<rect x="{x * px}" y="{y * px}" width="{px}" height="{px}" fill="{OUTLINE}"/>' for x, y in ring)


def duck_svg(px):
    body = [(x, y, c) for y, row in enumerate(DUCK) for x, c in enumerate(row) if c != "."]
    feet = {k: [(x, y, "O") for x, y in v] for k, v in FEET.items()}
    color = lambda c: PALETTE[c]
    return (
        f'<g class="bob">{outline_of(body, px)}{pixels_to_rects(body, px, color)}</g>'
        f'<g class="foot-a">{outline_of(feet["back"], px)}{pixels_to_rects(feet["back"], px, color)}</g>'
        f'<g class="foot-b">{outline_of(feet["front"], px)}{pixels_to_rects(feet["front"], px, color)}</g>'
    )


# ------------------------------------------------------------ duck + graph
def duck_walk(user, theme):
    t = THEMES[theme]
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    cell, gap = 11, 3
    pitch = cell + gap
    left, top = 24, 46
    grid_w = len(weeks) * pitch - gap
    width = left * 2 + grid_w
    height = top + 7 * pitch + 44

    cycle = 14.0          # seconds per loop
    walk_end = 0.62       # fraction of the cycle the duck spends walking
    hold_end = 0.90       # graph stays visible until here, then fades
    px = 3
    duck_w = 16 * px
    duck_y = top + (7 * pitch - gap) / 2 - 15 * px / 2 - 2
    start_x, end_x = -duck_w - 10, width + 10

    def pct(f):
        return round(f * 100, 2)

    style = [
        f"text{{font-family:{FONT};fill:{t['text']}}}",
        f".muted{{fill:{t['muted']}}}",
        f"#duck{{animation:walk {cycle}s linear infinite}}",
        f"@keyframes walk{{0%{{transform:translate({start_x}px,{duck_y}px)}}"
        f"{pct(walk_end)}%{{transform:translate({end_x}px,{duck_y}px)}}"
        f"100%{{transform:translate({end_x}px,{duck_y}px)}}}}",
        ".bob{animation:bob .36s ease-in-out infinite alternate}",
        "@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-3px)}}",
        ".foot-a{animation:step .36s steps(1) infinite}",
        ".foot-b{animation:step .36s steps(1) infinite reverse}",
        "@keyframes step{0%{transform:translateY(-3px)}50%{transform:translateY(0)}}",
        ".c{transform-box:fill-box;transform-origin:center}",
    ]

    cells = []
    for i, week in enumerate(weeks):
        # moment the duck's beak passes over this column
        beak_x = left + i * pitch + cell / 2
        reveal = (beak_x - start_x - duck_w + 6) / (end_x - start_x) * walk_end
        reveal = max(0.0, reveal)
        a, b = pct(reveal), pct(min(reveal + 0.02, hold_end))
        style.append(
            f"@keyframes w{i}{{0%,{a}%{{opacity:0;transform:scale(.2)}}"
            f"{b}%{{opacity:1;transform:scale(1.25)}}"
            f"{pct(min(reveal + 0.04, hold_end))}%,{pct(hold_end)}%{{opacity:1;transform:scale(1)}}"
            f"{pct(hold_end + 0.05)}%,100%{{opacity:0;transform:scale(1)}}}}"
            f".w{i}{{animation:w{i} {cycle}s ease-out infinite}}"
        )
        for day in week["contributionDays"]:
            d = datetime.fromisoformat(day["date"]).weekday()
            row = (d + 1) % 7  # GitHub starts the week on Sunday
            x, y = left + i * pitch, top + row * pitch
            cells.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{t["levels"][0]}"/>')
            lvl = LEVEL.get(day["contributionLevel"], 0)
            if lvl:
                cells.append(
                    f'<rect class="c w{i}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                    f'fill="{t["levels"][lvl]}"><title>{day["contributionCount"]} on {day["date"]}</title></rect>'
                )

    total = cal["totalContributions"]
    legend_x = width - left - 5 * pitch - 70
    legend = "".join(
        f'<rect x="{legend_x + 34 + k * pitch}" y="{height - 26}" width="{cell}" height="{cell}" rx="2" fill="{c}"/>'
        for k, c in enumerate(t["levels"])
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>{''.join(style)}</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t['bg']}" stroke="{t['border']}"/>
<text x="{left}" y="30" font-size="15" font-weight="600">{total:,} contributions in the last year</text>
<text x="{width - left}" y="30" font-size="12" text-anchor="end" class="muted">the duck delivers every commit 🦆</text>
{''.join(cells)}
<text x="{legend_x}" y="{height - 16.5}" font-size="11" class="muted">Less</text>{legend}
<text x="{legend_x + 34 + 5 * pitch + 4}" y="{height - 16.5}" font-size="11" class="muted">More</text>
<g id="duck">{duck_svg(px)}</g>
</svg>"""


# ---------------------------------------------------------------- stats card
def stats_card(user, theme):
    t = THEMES[theme]
    cc = user["contributionsCollection"]
    repos = user["repositories"]
    years = (datetime.now(timezone.utc) - datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))).days // 365
    streak = best = active = 0
    for week in cc["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            streak = streak + 1 if day["contributionCount"] else 0
            best = max(best, streak)
            active += bool(day["contributionCount"])

    langs = {}
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            size, color = langs.get(n, (0, e["node"]["color"] or t["muted"]))
            langs[n] = (size + e["size"], color)
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:6]
    lang_total = sum(v[0] for _, v in top) or 1

    stats = [
        ("Contributions (1y)", cc["contributionCalendar"]["totalContributions"]),
        ("Commits (1y)", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("Pull requests (1y)", cc["totalPullRequestContributions"]),
        ("PR reviews (1y)", cc["totalPullRequestReviewContributions"]),
        ("Repositories", repos["totalCount"]),
        ("Longest streak (days)", best),
        ("Years on GitHub", years),
        ("Active days (1y)", active),
    ]

    width, height = 820, 230
    style = [
        f"text{{font-family:{FONT};fill:{t['text']}}}",
        f".muted{{fill:{t['muted']}}}",
        f".num{{font-size:26px;font-weight:700;fill:{t['accent']}}}",
        ".in{opacity:0;animation:in .6s ease-out forwards}",
        "@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}",
        ".bar{transform-origin:left;transform:scaleX(0);animation:grow 1.2s cubic-bezier(.2,.8,.2,1) forwards}",
        "@keyframes grow{to{transform:scaleX(1)}}",
    ]

    parts = []
    col_w = (width - 48) / 4
    for k, (label, value) in enumerate(stats):
        x = 24 + (k % 4) * col_w
        y = 62 + (k // 4) * 62
        parts.append(
            f'<g class="in" style="animation-delay:{0.1 + k * 0.08:.2f}s">'
            f'<text x="{x}" y="{y}" class="num">{value:,}</text>'
            f'<text x="{x}" y="{y + 20}" font-size="12" class="muted">{label}</text></g>'
        )

    bar_y, bar_w = 178, width - 48
    parts.append(f'<text x="24" y="{bar_y - 10}" font-size="12" font-weight="600" class="in" style="animation-delay:.8s">Languages by code size</text>')
    parts.append(f'<clipPath id="r"><rect x="24" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath>')
    seg, offset = [], 24.0
    for name, (size, color) in top:
        w = size / lang_total * bar_w
        seg.append(f'<rect x="{offset:.1f}" y="{bar_y}" width="{w + 0.5:.1f}" height="10" fill="{color}"/>')
        offset += w
    parts.append(f'<g clip-path="url(#r)"><g class="bar" style="animation-delay:.9s">{"".join(seg)}</g></g>')

    lx = 24.0
    for k, (name, (size, color)) in enumerate(top):
        label = f"{name} {size / lang_total * 100:.1f}%"
        parts.append(
            f'<g class="in" style="animation-delay:{1.2 + k * 0.08:.2f}s">'
            f'<circle cx="{lx + 5}" cy="{bar_y + 30}" r="5" fill="{color}"/>'
            f'<text x="{lx + 15}" y="{bar_y + 34}" font-size="12" class="muted">{label}</text></g>'
        )
        lx += 22 + len(label) * 6.6

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>{''.join(style)}</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t['bg']}" stroke="{t['border']}"/>
<text x="24" y="30" font-size="15" font-weight="600" class="in">GitHub activity</text>
{''.join(parts)}
</svg>"""


def main():
    user = fetch()
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        for name, fn in (("duck", duck_walk), ("stats", stats_card)):
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w") as f:
                f.write(fn(user, theme))
    print(f"wrote SVGs to {OUT}/")


if __name__ == "__main__":
    main()
