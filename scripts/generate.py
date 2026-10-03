#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README.

- activity-{dark,light}.svg : contributions per month (a pixel duck hops across
                           the bars), contribution mix and busiest weekdays.
- hero-{dark,light}.svg  : see-through pixel-art space header with the flying astronaut duck and AWS badges.
- stats-{dark,light}.svg : animated activity card (contributions, commits, PRs,
                           streaks, years on GitHub and top languages).

Only uses the standard library; reads GITHUB_TOKEN / GH_TOKEN from the env.
"""
import base64
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


# ---------------------------------------------------------------- duck frames
# The flying astronaut duck is drawn by scripts/duck_frames.py (needs Pillow) into
# assets/duck/{big,small}; here we only embed those PNGs and flip through them with CSS.
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")


def duck_meta():
    with open(os.path.join(ASSETS, "duck", "meta.json")) as f:
        return json.load(f)


def duck_frames(size_dir, x, y, size, cls):
    """Returns (css, svg) showing one frame at a time."""
    meta = duck_meta()
    n, ms = meta["frames"], meta["frame_ms"]
    css = (f".{cls}{{opacity:0;image-rendering:pixelated;animation:{cls} {n * ms}ms steps(1) infinite}}"
           f"@keyframes {cls}{{0%{{opacity:1}}{100 / n:.3f}%,100%{{opacity:0}}}}")
    images = []
    for i in range(n):
        with open(os.path.join(ASSETS, "duck", size_dir, f"{i:02d}.png"), "rb") as f:
            data = base64.b64encode(f.read()).decode()
        images.append(f'<image class="{cls}" style="animation-delay:{i * ms}ms" href="data:image/png;base64,{data}" '
                      f'x="{x}" y="{y}" width="{size}" height="{size}"/>')
    return css, "".join(images)


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
    cycle = 13.0
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
    ]
    parts = [
        f'<text x="24" y="32" font-size="15" font-weight="600">Contributions per month</text>',
        f'<text x="560" y="32" font-size="15" font-weight="600">Contribution mix</text>',
        f'<text x="560" y="198" font-size="15" font-weight="600">Busiest weekdays</text>',
    ]

    # monthly bars; the duck flies from the top of one bar to the next
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

    duck_css, duck_svg = duck_frames("small", 0, 0, 64, "fs")
    style.append(duck_css)
    anchor_x, anchor_y = 38, 50  # body centre / feet on the 64px canvas
    seg = 0.9 / len(tops)  # last 10% of the cycle the duck fades out and resets
    frames = []
    for i, (cx, top) in enumerate(tops):
        x, y = cx - anchor_x, top - anchor_y
        p = i * seg * 100
        frames.append(f"{p:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        frames.append(f"{p + seg * 50:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        if i + 1 < len(tops):
            nx, ny = tops[i + 1][0] - anchor_x, tops[i + 1][1] - anchor_y
            hop = min(y, ny) - 22
            frames.append(f"{p + seg * 75:.2f}%{{transform:translate({(x + nx) / 2:.1f}px,{hop:.1f}px);opacity:1}}")
    lx, ly = tops[-1][0] - anchor_x, tops[-1][1] - anchor_y
    frames.append(f"95%{{transform:translate({lx:.1f}px,{ly:.1f}px);opacity:0}}")
    frames.append(f"100%{{transform:translate({tops[0][0] - anchor_x:.1f}px,{tops[0][1] - anchor_y:.1f}px);opacity:0}}")
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
<g id="duck">{duck_svg}</g>
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


def wrap(text, limit):
    lines, line = [], ""
    for word in text.split():
        if line and len((line + " " + word).replace("**", "")) > limit:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line]


HERO_THEMES = {
    "dark": {
        "tint": "#7355dd", "tint_opacity": ".07", "border": "#30363d",
        "title": "#ffffff", "sub": "#a8a3d6", "body": "#d6d3ee", "bold": "#ffffff",
        "core": ["#ffffff", "#f1ecff", "#d9ceff"],
        "arms": ["#c4b5fd", "#9b82f3", "#7355dd", "#5b9bf0", "#3178c6"],
        "stars": ["#ffffff", "#e9e3ff", "#c4b5fd", "#9fc5ff"],
    },
    "light": {
        "tint": "#7355dd", "tint_opacity": ".05", "border": "#d0d7de",
        "title": "#1f2328", "sub": "#6a5bb5", "body": "#3d3a55", "bold": "#1f2328",
        "core": ["#4a2fb0", "#5a3fc0", "#7355dd"],
        "arms": ["#7355dd", "#8b6cf0", "#5568d6", "#3178c6", "#9b82f3"],
        "stars": ["#7355dd", "#5568d6", "#3178c6", "#9b82f3"],
    },
}
ACCENTS = ["#ff8a1f", "#39d353"]  # a pinch of orange and green


def galaxy(width, height, rng, t):
    """Pixel-art space on a see-through background: a few galaxies and stars."""
    P = 2
    px = {}

    def put(x, y, color):
        gx, gy = int(x // P), int(y // P)
        if 0 <= gx * P < width and 0 <= gy * P < height:
            px[(gx, gy)] = color

    def accent_or(color, chance=0.04):
        return rng.choice(ACCENTS) if rng.random() < chance else color

    def spiral(cx, cy, scale, tilt, n, turns=3.0):
        for arm in range(2):
            for i in range(n):
                f = i / n
                ang = f * turns * 2.1 + arm * math.pi
                rad = scale * (0.12 + f)
                x = cx + math.cos(ang) * rad * 1.4 + rng.gauss(0, 1.5 + f * scale * 0.06)
                y = cy + math.sin(ang) * rad * tilt + rng.gauss(0, 1 + f * scale * 0.03)
                arms = t["arms"]
                put(x, y, accent_or(arms[min(len(arms) - 1, int(f * len(arms) + rng.random() * .8))], .03))
        for _ in range(n // 2):
            put(cx + rng.gauss(0, scale * .09), cy + rng.gauss(0, scale * .05), rng.choice(t["core"]))

    def elliptical(cx, cy, rx, ry, n):
        for _ in range(n):
            a, d = rng.uniform(0, 6.283), abs(rng.gauss(0, .45))
            put(cx + math.cos(a) * d * rx, cy + math.sin(a) * d * ry,
                rng.choice(t["core"]) if d < .25 else accent_or(rng.choice(t["arms"][:3]), .06))

    spiral(860, 120, 90, .5, 700)
    elliptical(470, 338, 26, 12, 160)
    spiral(640, 330, 30, .45, 160, turns=2.4)
    elliptical(960, 330, 12, 7, 60)

    rects = "".join(f'<rect x="{x * P}" y="{y * P}" width="{P}" height="{P}" fill="{c}"/>' for (x, y), c in px.items())

    stars = []
    for _ in range(70):
        x, y = rng.randrange(0, width, P), rng.randrange(0, height, P)
        behind_text = x < 700 and 36 < y < 300
        color = accent_or(rng.choice(t["stars"]), .1)
        twinkle = f' class="tw" style="animation-delay:{rng.uniform(0, 4):.2f}s;animation-duration:{rng.uniform(2, 5):.2f}s"'
        if not behind_text and rng.random() < 0.3:  # sparkle: plus with a bright center
            s = P
            stars.append(
                f'<g{twinkle} fill="{color}"><rect x="{x}" y="{y - 3 * s}" width="{s}" height="{7 * s}" opacity=".55"/>'
                f'<rect x="{x - 3 * s}" y="{y}" width="{7 * s}" height="{s}" opacity=".55"/>'
                f'<rect x="{x - s}" y="{y - s}" width="{3 * s}" height="{3 * s}"/></g>'
            )
        elif behind_text:
            stars.append(f'<rect x="{x}" y="{y}" width="{P}" height="{P}" fill="{color}" opacity=".35"/>')
        else:
            stars.append(f'<rect{twinkle} x="{x}" y="{y}" width="{P * 2}" height="{P * 2}" fill="{color}"/>')
    return rects + "".join(stars)


DUCK_X, DUCK_Y, DUCK_SIZE = 716, 16, 256  # 128px canvas shown at 2x


def exhaust(theme, rng):
    """Sparks and smoke puffs streaming out of the jetpack, animated in CSS so they move smoothly."""
    meta = duck_meta()
    k = DUCK_SIZE / meta["canvas"]
    nx, ny = DUCK_X + meta["nozzle"][0] * k, DUCK_Y + meta["nozzle"][1] * k
    dx, dy = meta["exhaust_dir"]
    lift = math.radians(-12)  # let the trail drift a bit flatter than the nozzle
    dx, dy = dx * math.cos(lift) - dy * math.sin(lift), dx * math.sin(lift) + dy * math.cos(lift)
    px, py = -dy, dx
    sparks = {"dark": ["#ffffff", "#ffd23f", "#ff8a1f", "#ffb347"],
              "light": ["#ff8a1f", "#ffb347", "#f05a28", "#7355dd"]}[theme]
    smoke, smoke_alpha = {"dark": ("#c9c0ff", .3), "light": ("#c4bdf0", .45)}[theme]
    css, els = [], []
    for j in range(24):
        puff = j % 3 == 0
        dur = rng.uniform(1.2, 1.9) if puff else rng.uniform(.55, 1.05)
        dist = rng.uniform(55, 95) if puff else rng.uniform(35, 75)
        side = rng.gauss(0, 9 if puff else 6)
        size = 8 if puff else rng.choice([3, 4, 4, 5])
        sx, sy = nx + dx * 34, ny + dy * 34
        tx, ty = dx * dist + px * side, dy * dist + py * side + rng.uniform(-4, 6)
        css.append(f"@keyframes x{j}{{0%{{transform:translate(0,0) scale(1);opacity:{smoke_alpha if puff else 1}}}"
                   f"100%{{transform:translate({tx:.1f}px,{ty:.1f}px) scale({2.0 if puff else .3});opacity:0}}}}")
        els.append(f'<rect x="{sx - size / 2:.1f}" y="{sy - size / 2:.1f}" width="{size}" height="{size}" '
                   f'fill="{smoke if puff else rng.choice(sparks)}" style="transform-box:fill-box;transform-origin:center;'
                   f'animation:x{j} {dur:.2f}s ease-out {-rng.uniform(0, dur):.2f}s infinite"/>')
    return "".join(css), "".join(els)


def hero(theme):
    import base64
    import random

    t = HERO_THEMES[theme]
    rng = random.Random(7)
    duck_css, duck_svg = duck_frames("big", DUCK_X, DUCK_Y, DUCK_SIZE, "fb")
    fx_css, fx_svg = exhaust(theme, random.Random(11))
    width, height = 1000, 380
    style = [
        f"text{{font-family:{FONT}}}",
        ".tw{animation:tw 3s ease-in-out infinite alternate}",
        "@keyframes tw{from{opacity:1}to{opacity:.2}}",
        ".drift{animation:drift 5.2s ease-in-out infinite alternate}",
        "@keyframes drift{from{transform:translateX(-6px)}to{transform:translateX(8px)}}",
        f".float{{transform-origin:{DUCK_X + DUCK_SIZE * 76 / 128:.0f}px {DUCK_Y + DUCK_SIZE * 64 / 128:.0f}px;"
        "animation:float 3.4s ease-in-out infinite alternate}",
        "@keyframes float{from{transform:translateY(7px) rotate(-2.5deg)}to{transform:translateY(-9px) rotate(2deg)}}",
        ".badge{animation:bf 3s ease-in-out infinite alternate}",
        "@keyframes bf{from{transform:translateY(0)}to{transform:translateY(-6px)}}",
        ".glint{animation:glint 5s ease-in-out infinite}",
        "@keyframes glint{0%,60%{transform:translateX(-140px)}85%,100%{transform:translateX(140px)}}",
    ]

    def rich(line):
        out = []
        for k, chunk in enumerate(line.split("**")):
            chunk = chunk.replace("&", "&amp;").replace("<", "&lt;")
            out.append(f'<tspan font-weight="700" fill="{t["bold"]}">{chunk}</tspan>' if k % 2 else chunk)
        return "".join(out)

    text = [
        f'<text x="40" y="66" font-size="24" font-weight="700" fill="{t["title"]}">{TITLE}</text>',
        f'<text x="40" y="94" font-size="14" fill="{t["sub"]}">{SUBTITLE}</text>',
        '<rect x="40" y="112" width="56" height="4" fill="#7355dd"/><rect x="96" y="112" width="20" height="4" fill="#3178c6"/>'
        '<rect x="116" y="112" width="6" height="4" fill="#ff8a1f"/><rect x="122" y="112" width="6" height="4" fill="#39d353"/>',
    ]
    y = 152
    for para in ABOUT:
        for line in wrap(para, 76):
            text.append(f'<text x="40" y="{y}" font-size="15.5" fill="{t["body"]}">{rich(line)}</text>')
            y += 25
        y += 12

    badges = []
    size, bx0, by = 88, 712, 266
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
<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<clipPath id="frame"><rect width="{width}" height="{height}" rx="14"/></clipPath>
</defs>
<style>{''.join(style)}{duck_css}{fx_css}</style>
<g clip-path="url(#frame)">
<rect width="{width}" height="{height}" fill="{t['tint']}" opacity="{t['tint_opacity']}"/>
{galaxy(width, height, rng, t)}
<g shape-rendering="auto">{''.join(text)}</g>
<g class="drift"><g class="float">{fx_svg}{duck_svg}</g></g>
<g shape-rendering="auto">{''.join(badges)}</g>
</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="none" stroke="{t['border']}"/>
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
        for name, fn in (("activity", activity_card), ("stats", stats_card), ("hero", lambda _, th: hero(th))):
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w") as f:
                f.write(fn(user, theme))
    print(f"wrote SVGs to {OUT}/")


if __name__ == "__main__":
    main()
