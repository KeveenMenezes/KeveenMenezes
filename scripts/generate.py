#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README.

- activity-{dark,light}.svg : contributions per month (a pixel duck hops across
                           the bars), contribution mix and busiest weekdays.
- hero.svg               : pixel-art galaxy header with the astronaut duck and AWS badges.
- stats-{dark,light}.svg : animated activity card (contributions, commits, PRs,
                           streaks, years on GitHub and top languages).

Only uses the standard library; reads GITHUB_TOKEN / GH_TOKEN from the env.
"""
import json
import math
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
      totalIssueContributions
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
        "accent": ["#9b82f3", "#5b9bf0"],  # C# purple -> TypeScript blue
        "levels": ["#161b22", "#1f2f5c", "#2f5fae", "#5b6ee0", "#9b82f3"],
    },
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "muted": "#656d76",
        "accent": ["#6a46d8", "#2f6fc0"],
        "levels": ["#ebedf0", "#bcd0f5", "#6f9be6", "#5568d6", "#5a3fc0"],
    },
}
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
# Pixel-art astronaut duck, facing right.
#   R helmet rim  H helmet glass  h glass highlight  W duck  E eye  Y beak/feet
#   S suit  s suit shade  P mission patch  J jetpack  B boots  F flame
DUCK = [
    "......RRRRRRRR........",
    "....RRHHHHHHHHRR......",
    "...RHhhWWWWWWHHHR.....",
    "..RHhWWWWWWWWWWHHR....",
    "..RHhWWWWWWWWEWWHR....",
    "..RHWWWWWWWWWWWYYYR...",
    "..RHWWWWWWWWWWYYYYR...",
    "..RHHWWWWWWWWWWHHHR...",
    "...RHHHWWWWWWHHHHR....",
    "....RRRRRRRRRRRRR.....",
    "..JJ.SSSSSSSSSSS......",
    ".JJJSSSSSSSSSSSSs.....",
    ".JJJSSSSSSPPSSSSss....",
    ".JJJSSSSSSPPSSSSss....",
    ".JJJsSSSSSSSSSSSss....",
    ".JJJssSSSSSSSSSss.....",
    "..JJ.ssssssssss.......",
    "......BB....BB........",
    "......BB....BB........",
    ".....YYYY..YYYY.......",
]
FLAME = [(2, 17), (1, 18), (2, 18), (3, 18), (2, 19)]
PALETTE = {
    "R": "#8b93a7", "H": "#2b3a78", "h": "#c9d6ff", "W": "#ffffff", "E": "#1f2328",
    "Y": "#ff8a1f", "S": "#eef1f7", "s": "#b9c0d0", "P": "#7355dd", "J": "#5b6ee0",
    "B": "#6b7385", "F": "#ffb347",
}
OUTLINE = "#14121f"
SPRITE_W, SPRITE_H = len(DUCK[0]), len(DUCK) + 1


def pixels_to_rects(cells, px):
    return "".join(
        f'<rect x="{x * px:g}" y="{y * px:g}" width="{px:g}" height="{px:g}" fill="{PALETTE[c]}"/>'
        for (x, y, c) in cells
    )


def outline_of(cells, px):
    filled = {(x, y) for x, y, _ in cells}
    ring = {
        (x + dx, y + dy)
        for x, y in filled
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if (x + dx, y + dy) not in filled
    }
    return "".join(f'<rect x="{x * px:g}" y="{y * px:g}" width="{px:g}" height="{px:g}" fill="{OUTLINE}"/>' for x, y in ring)


def duck_svg(px):
    """Astronaut duck; animate with .bob, .foot-a, .foot-b and .flame classes."""
    cells = [(x, y, c) for y, row in enumerate(DUCK) for x, c in enumerate(row) if c != "."]
    legs_from = 17
    body = [c for c in cells if c[1] < legs_from]
    back = [c for c in cells if c[1] >= legs_from and c[0] < 10]
    front = [c for c in cells if c[1] >= legs_from and c[0] >= 10]
    flame = [(x, y, "F") for x, y in FLAME]
    group = lambda cls, cs: f'<g class="{cls}">{outline_of(cs, px)}{pixels_to_rects(cs, px)}</g>'
    return group("flame", flame) + group("foot-a", back) + group("foot-b", front) + group("bob", body)


# ------------------------------------------------------------ activity card
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
WEEKDAYS = "Mon Tue Wed Thu Fri Sat Sun".split()


def activity_card(user, theme):
    t = THEMES[theme]
    cc = user["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]

    monthly, weekday = {}, [0] * 7
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["contributionCount"]
        weekday[datetime.fromisoformat(d["date"]).weekday()] += d["contributionCount"]
    months = sorted(monthly.items())[-12:]

    mix = [
        ("Commits", cc["totalCommitContributions"] + cc["restrictedContributionsCount"], t["levels"][4]),
        ("Pull requests", cc["totalPullRequestContributions"], t["accent"][1]),
        ("Code reviews", cc["totalPullRequestReviewContributions"], t["levels"][3]),
        ("Issues", cc["totalIssueContributions"], t["levels"][2]),
    ]

    width, height = 820, 300
    cycle, px = 13.0, 2
    style = [
        f"text{{font-family:{FONT};fill:{t['text']}}}",
        f".muted{{fill:{t['muted']}}}",
        ".gy{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);"
        "animation:gy .9s cubic-bezier(.2,.8,.2,1) forwards}",
        "@keyframes gy{to{transform:scaleY(1)}}",
        ".gx{transform-box:fill-box;transform-origin:left;transform:scaleX(0);"
        "animation:gx .9s cubic-bezier(.2,.8,.2,1) forwards}",
        "@keyframes gx{to{transform:scaleX(1)}}",
        ".in{opacity:0;animation:in .6s ease-out forwards}",
        "@keyframes in{to{opacity:1}}",
        ".bob{animation:bob .3s ease-in-out infinite alternate}",
        "@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-2px)}}",
        ".foot-a{animation:step .3s steps(1) infinite}",
        ".foot-b{animation:step .3s steps(1) infinite reverse}",
        "@keyframes step{0%{transform:translateY(-2px)}50%{transform:translateY(0)}}",
        ".flame{animation:flame .15s steps(1) infinite alternate}",
        "@keyframes flame{from{opacity:1}to{opacity:.35}}",
    ]
    parts = [
        f'<text x="24" y="32" font-size="15" font-weight="600">Contributions per month</text>',
        f'<text x="560" y="32" font-size="15" font-weight="600">Contribution mix</text>',
        f'<text x="560" y="198" font-size="15" font-weight="600">Busiest weekdays</text>',
    ]

    # monthly bars; the duck hops from the top of one bar to the next
    left, chart_w, base, chart_h = 24, 500, 252, 170
    pitch = chart_w / len(months)
    bar_w = pitch - 14
    peak = max(v for _, v in months) or 1
    tops = []
    for i, (ym, v) in enumerate(months):
        h = max(2, v / peak * chart_h)
        x = left + i * pitch + 7
        tops.append((x + bar_w / 2, base - h))
        parts.append(
            f'<rect class="gy" style="animation-delay:{i * 0.05:.2f}s" x="{x:.1f}" y="{base - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="4" fill="url(#bar)"><title>{v} contributions</title></rect>'
            f'<text x="{x + bar_w / 2:.1f}" y="{base + 18}" font-size="11" text-anchor="middle" class="muted">'
            f'{MONTHS[int(ym[5:]) - 1]}</text>'
        )
    best_ym, best_v = max(months, key=lambda kv: kv[1])
    parts.append(
        f'<text x="{left + chart_w}" y="32" font-size="12" text-anchor="end" class="muted">'
        f'best month: {MONTHS[int(best_ym[5:]) - 1]} · {best_v}</text>'
    )

    duck_w, duck_h = SPRITE_W * px, SPRITE_H * px
    seg = 0.9 / len(tops)  # last 10% of the cycle the duck fades out and resets
    frames = []
    for i, (cx, top) in enumerate(tops):
        x, y = cx - duck_w / 2, top - duck_h
        p = i * seg * 100
        frames.append(f"{p:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        frames.append(f"{p + seg * 50:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        if i + 1 < len(tops):
            nx, ny = tops[i + 1][0] - duck_w / 2, tops[i + 1][1] - duck_h
            hop = min(y, ny) - 22
            frames.append(f"{p + seg * 75:.2f}%{{transform:translate({(x + nx) / 2:.1f}px,{hop:.1f}px);opacity:1}}")
    lx, ly = tops[-1][0] - duck_w / 2, tops[-1][1] - duck_h
    frames.append(f"95%{{transform:translate({lx:.1f}px,{ly:.1f}px);opacity:0}}")
    frames.append(f"100%{{transform:translate({tops[0][0] - duck_w / 2:.1f}px,{tops[0][1] - duck_h:.1f}px);opacity:0}}")
    style.append(f"#duck{{animation:hop {cycle}s ease-in-out infinite}}@keyframes hop{{{''.join(frames)}}}")

    # contribution mix: donut + legend
    total = sum(v for _, v, _ in mix) or 1
    cx, cy, r = 610, 108, 44
    circ = 2 * 3.14159265 * r
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["levels"][0]}" stroke-width="14"/>')
    offset = 0.0
    for k, (name, v, color) in enumerate(mix):
        length = v / total * circ
        if length:
            parts.append(
                f'<circle class="in" style="animation-delay:{0.2 + k * 0.15:.2f}s" cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{color}" stroke-width="14" stroke-dasharray="{max(length - 2, 0.5):.1f} {circ:.1f}" '
                f'stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>'
            )
        offset += length
        ty = 70 + k * 26
        parts.append(
            f'<g class="in" style="animation-delay:{0.2 + k * 0.15:.2f}s">'
            f'<rect x="676" y="{ty - 9}" width="10" height="10" rx="2" fill="{color}"/>'
            f'<text x="692" y="{ty}" font-size="12">{name}</text>'
            f'<text x="796" y="{ty}" font-size="12" text-anchor="end" class="muted">{v / total * 100:.0f}%</text></g>'
        )
    parts.append(f'<text x="{cx}" y="{cy + 5}" font-size="15" font-weight="700" text-anchor="middle">{total}</text>')

    # weekdays: horizontal bars
    wd_peak = max(weekday) or 1
    for k, name in enumerate(WEEKDAYS):
        y = 212 + k * 11.5
        w = weekday[k] / wd_peak * 196
        parts.append(
            f'<text x="560" y="{y + 7.5}" font-size="10" class="muted">{name}</text>'
            f'<rect x="590" y="{y}" width="196" height="8" rx="4" fill="{t["levels"][0]}"/>'
            f'<rect class="gx" style="animation-delay:{0.3 + k * 0.06:.2f}s" x="590" y="{y}" width="{max(w, 1):.1f}" '
            f'height="8" rx="4" fill="url(#barx)"><title>{weekday[k]} contributions</title></rect>'
        )

    a0, a1 = t["accent"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs>
<linearGradient id="bar" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{a0}"/><stop offset="1" stop-color="{a1}"/></linearGradient>
<linearGradient id="barx" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{a1}"/><stop offset="1" stop-color="{a0}"/></linearGradient>
</defs>
<style>{''.join(style)}</style>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" fill="{t['bg']}" stroke="{t['border']}"/>
<line x1="540" y1="20" x2="540" y2="{height - 20}" stroke="{t['border']}"/>
{''.join(parts)}
<g id="duck">{duck_svg(px)}</g>
</svg>"""


# ---------------------------------------------------------------- hero banner
TITLE = ".NET Specialist · Solution Architecture · Distributed Systems · AWS"
SUBTITLE = "5+ years building software · Belo Horizonte, Brazil"
ABOUT = [
    "Backend engineer and software architect specialized in **.NET** (C#, ASP.NET Core, "
    ".NET Aspire), designing event-driven, distributed systems on **AWS**.",
    "I pick patterns for the problem, not the hype, weighing scalability, cost, maintainability "
    "and what the business actually needs, and I document the trade-offs so the next person "
    "inherits the reasoning.",
]
BADGES = ["sap", "saa", "dva"]
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def wrap(text, limit):
    lines, line = [], ""
    for word in text.split():
        if line and len((line + " " + word).replace("**", "")) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


def rich(line):
    """**bold** -> tspans."""
    out = []
    for k, chunk in enumerate(line.split("**")):
        chunk = chunk.replace("&", "&amp;").replace("<", "&lt;")
        out.append(f'<tspan font-weight="700" fill="#ffffff">{chunk}</tspan>' if k % 2 else chunk)
    return "".join(out)


def galaxy(width, height, rng):
    """Pixel-art space: nebula dust, a spiral galaxy, twinkling stars, a ringed planet."""
    P = 4
    px = {}

    def put(x, y, color):
        gx, gy = int(x // P), int(y // P)
        if 0 <= gx * P < width and 0 <= gy * P < height:
            px[(gx, gy)] = color

    nebula = ["#1d1846", "#251c5c", "#1b2a63", "#2a1f6b"]
    for cx, cy, r in ((260, 300, 170), (560, 40, 140), (120, 60, 110)):
        for _ in range(int(r * 2.2)):
            a, d = rng.uniform(0, 6.283), abs(rng.gauss(0, r / 2.2))
            put(cx + math.cos(a) * d * 1.6, cy + math.sin(a) * d * 0.7, rng.choice(nebula))

    gx, gy = 830, 150
    arms = ["#7355dd", "#8b6cf0", "#5b6ee0", "#3178c6", "#9b82f3", "#c4b5fd"]
    for arm in range(2):
        for i in range(520):
            t = i / 520 * 3.3
            ang = t * 2.1 + arm * math.pi
            rad = 8 + t * 46
            x = gx + math.cos(ang) * rad * 1.35 + rng.gauss(0, 5 + t * 2)
            y = gy + math.sin(ang) * rad * 0.62 + rng.gauss(0, 3 + t)
            put(x, y, arms[min(len(arms) - 1, int(t / 3.3 * len(arms) + rng.random()))] if t > 0.4 else "#e9e3ff")
    for _ in range(160):
        put(gx + rng.gauss(0, 10), gy + rng.gauss(0, 5), rng.choice(["#ffffff", "#e9e3ff", "#c4b5fd"]))

    rects = "".join(f'<rect x="{x * P}" y="{y * P}" width="{P}" height="{P}" fill="{c}"/>' for (x, y), c in px.items())

    stars = []
    for k in range(110):
        x, y = rng.randrange(0, width, P), rng.randrange(0, height, P)
        behind_text = x < 690 and 36 < y < 300
        big = rng.random() < 0.18 and not behind_text
        color = rng.choice(["#ffffff", "#ffffff", "#c4b5fd", "#9fc5ff", "#ffe8a3"])
        cls = f' class="tw" style="animation-delay:{rng.uniform(0, 4):.2f}s;animation-duration:{rng.uniform(2, 5):.2f}s"' if rng.random() < 0.6 else ""
        if big:  # little plus-shaped star
            stars.append(f'<g{cls} fill="{color}"><rect x="{x}" y="{y - P}" width="{P}" height="{P * 3}"/>'
                         f'<rect x="{x - P}" y="{y}" width="{P * 3}" height="{P}"/></g>')
        else:
            if behind_text:
                cls, color = "", "#8f86c9"
            stars.append(f'<rect{cls} x="{x}" y="{y}" width="{P}" height="{P}" fill="{color}" opacity="{'.45' if behind_text else '.85'}"/>')

    # ringed planet
    planet = []
    pcx, pcy, pr = 640, 300, 22
    for y in range(-pr, pr + 1, P):
        for x in range(-pr, pr + 1, P):
            if x * x + y * y <= pr * pr:
                shade = "#3178c6" if x + y < -8 else "#2a5aa8" if x + y < 12 else "#1f437f"
                planet.append(f'<rect x="{pcx + x}" y="{pcy + y}" width="{P}" height="{P}" fill="{shade}"/>')
    for x in range(-44, 45, P):
        y = round(x * 0.18 / P) * P
        if not (abs(x) < pr and y > -6):
            planet.append(f'<rect x="{pcx + x}" y="{pcy + y}" width="{P}" height="{P}" fill="#9b82f3"/>')
    return rects + "".join(stars) + "".join(planet)


def hero():
    import base64
    import random

    rng = random.Random(42)
    width, height = 1000, 380
    style = [
        f"text{{font-family:{FONT}}}",
        ".tw{animation:tw 3s ease-in-out infinite alternate}",
        "@keyframes tw{from{opacity:1}to{opacity:.15}}",
        ".shoot{animation:shoot 7s linear infinite}",
        "@keyframes shoot{0%,78%{transform:translate(0,0);opacity:0}80%{opacity:1}"
        "92%{transform:translate(-260px,110px);opacity:0}100%{opacity:0}}",
        "#astro{animation:float 4s ease-in-out infinite alternate}",
        "@keyframes float{from{transform:translate(762px,84px) rotate(-3deg)}to{transform:translate(762px,66px) rotate(3deg)}}",
        ".bob{animation:bob .35s ease-in-out infinite alternate}",
        "@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-4px)}}",
        ".foot-a{animation:step .35s steps(1) infinite}",
        ".foot-b{animation:step .35s steps(1) infinite reverse}",
        "@keyframes step{0%{transform:translateY(-5px)}50%{transform:translateY(0)}}",
        ".flame{animation:flame .12s steps(1) infinite alternate}",
        "@keyframes flame{from{opacity:1}to{opacity:.3}}",
        ".badge{animation:bf 3s ease-in-out infinite alternate}",
        "@keyframes bf{from{transform:translateY(0)}to{transform:translateY(-6px)}}",
        ".glint{animation:glint 5s ease-in-out infinite}",
        "@keyframes glint{0%,60%{transform:translateX(-140px)}85%,100%{transform:translateX(140px)}}",
    ]

    text = [
        f'<text x="40" y="66" font-size="25" font-weight="700" fill="#ffffff">{TITLE}</text>',
        f'<text x="40" y="94" font-size="14" fill="#b9b3e6">{SUBTITLE}</text>',
        '<rect x="40" y="112" width="56" height="4" fill="#7355dd"/><rect x="96" y="112" width="28" height="4" fill="#3178c6"/>',
    ]
    y = 152
    for para in ABOUT:
        for line in wrap(para, 76):
            text.append(f'<text x="40" y="{y}" font-size="15.5" fill="#dcd8f5">{rich(line)}</text>')
            y += 25
        y += 12

    badges = []
    size, bx0, by = 92, 700, 262
    for k, name in enumerate(BADGES):
        with open(os.path.join(ASSETS, "badges", f"{name}.png"), "rb") as f:
            data = base64.b64encode(f.read()).decode()
        x = bx0 + k * (size + 6)
        s = size
        hexagon = " ".join(f"{x + s * a:.1f},{by + s * b:.1f}" for a, b in
                           ((.5, .03), (.92, .27), (.92, .73), (.5, .97), (.08, .73), (.08, .27)))
        badges.append(
            f'<clipPath id="hx{k}"><polygon points="{hexagon}"/></clipPath>'
            f'<g class="badge" style="animation-delay:{k * 0.5}s">'
            f'<image href="data:image/png;base64,{data}" x="{x}" y="{by}" width="{s}" height="{s}"/>'
            f'<g clip-path="url(#hx{k})"><rect class="glint" style="animation-delay:{k * 0.4}s" x="{x - 20}" y="{by - 10}" '
            f'width="40" height="{s + 20}" fill="url(#shine)" transform="skewX(-20)"/></g></g>'
        )

    alt_title = "AWS Certified: Solutions Architect Professional, Solutions Architect Associate, Developer Associate"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" shape-rendering="crispEdges">
<title>{TITLE} · {alt_title}</title>
<defs>
<linearGradient id="sky" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#0b0a1f"/><stop offset="1" stop-color="#16123a"/></linearGradient>
<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="frame"><rect width="{width}" height="{height}" rx="14"/></clipPath>
</defs>
<style>{''.join(style)}</style>
<g clip-path="url(#frame)">
<rect width="{width}" height="{height}" fill="url(#sky)"/>
{galaxy(width, height, rng)}
<g class="shoot"><rect x="900" y="24" width="4" height="4" fill="#fff"/><rect x="904" y="20" width="4" height="4" fill="#c4b5fd"/><rect x="908" y="16" width="4" height="4" fill="#7355dd" opacity=".7"/><rect x="912" y="12" width="4" height="4" fill="#3178c6" opacity=".4"/></g>
<g shape-rendering="auto">{''.join(text)}</g>
<g id="astro" style="transform-box:fill-box;transform-origin:center">{duck_svg(7)}</g>
<g shape-rendering="auto">{''.join(badges)}</g>
</g>
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
        ".num{font-size:26px;font-weight:700;fill:url(#accent)}",
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
<defs><linearGradient id="accent" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{t['accent'][0]}"/><stop offset="1" stop-color="{t['accent'][1]}"/></linearGradient></defs>
<text x="24" y="30" font-size="15" font-weight="600" class="in">GitHub activity</text>
{''.join(parts)}
</svg>"""


def main():
    user = fetch()
    os.makedirs(OUT, exist_ok=True)
    for theme in THEMES:
        for name, fn in (("activity", activity_card), ("stats", stats_card)):
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w") as f:
                f.write(fn(user, theme))
    with open(os.path.join(OUT, "hero.svg"), "w") as f:
        f.write(hero())
    print(f"wrote SVGs to {OUT}/")


if __name__ == "__main__":
    main()
