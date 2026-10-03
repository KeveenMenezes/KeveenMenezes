#!/usr/bin/env python3
"""Generates the animated SVGs used by the profile README, in the look of Keveen's own
"Prometheus Dark" VS Code theme.

- hero.svg     : banner with the title, the "patterns, not hype" quote, a faint blueprint of an
                 event-driven AWS workload with traces in flight, and the AWS badges.
- stats.svg    : GitHub numbers for the last 12 months and languages by code size.
- activity.svg : contributions per month (a pixel-art astronaut duck hops across the bars), contribution mix
                 and busiest weekdays.

Only uses the standard library; reads GITHUB_TOKEN / GH_TOKEN from the env. Fonts and badges
are embedded from assets/ (fonts are built by scripts/build_fonts.py).
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
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
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
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}
"""

# Prometheus Dark 2026: black and graphite first; among the accents blue leads, then purple, then orange.
P = {
    "bg": "#080808", "panel": "#121212", "border": "#242424", "hair": "#1f1f1f", "dot": "#232323",
    "text": "#ececec", "body": "#8c8c8c", "muted": "#6b6b6b", "faint": "#4a4a4a", "comment": "#5c5c5c",
    "bar": "#222222", "purple": "#a579c3", "cyan": "#23d8ea", "blue": "#3b8eea", "orange": "#ff9e3b",
    "green": "#98c379",
}
SANS = "Geist,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
FONTS = {
    "sans": ("Geist", "100 900", "geist.woff2"),
    "mono": ("JetBrains Mono", "400", "jetbrains-mono.woff2"),
}


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


# ---------------------------------------------------------------- shared bits
def asset_b64(path):
    with open(os.path.join(ASSETS, path), "rb") as f:
        return base64.b64encode(f.read()).decode()


def font_css(*keys):
    """GitHub shows README images as <img>, which can't fetch fonts, so they travel inside the SVG."""
    return "".join(
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-display:block;"
        f"src:url(data:font/woff2;base64,{asset_b64('fonts/' + file)}) format('woff2')}}"
        for family, weight, file in (FONTS[k] for k in keys)
    )


BASE_CSS = (
    f".sans{{font-family:{SANS}}}.mono{{font-family:{MONO}}}"
    # entrance effects only: the resting state is the visible one, so renderers that don't
    # animate still show everything
    ".in{animation:in .7s ease-out backwards}@keyframes in{from{opacity:0;transform:translateY(6px)}}"
)


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(width, height, css, body, radius=14, title=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<title>{esc(title)}</title>
<style>{css}</style>
<clipPath id="card"><rect width="{width}" height="{height}" rx="{radius}"/></clipPath>
<g clip-path="url(#card)">
<rect width="{width}" height="{height}" fill="{P['bg']}"/>
{body}
</g>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="{radius - .5}" fill="none" stroke="{P['border']}"/>
</svg>"""


# ---------------------------------------------------------------- pixel sprites
# Pixel-art ducks as ASCII frames (one char per pixel, "." is transparent). The astronaut lives
# in the activity chart; the three lab-coat ducks keep editing the blueprint in the banner.
SCI_BUILDER = {
    "walk0": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "walk1": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T...T.....",
        ".....TT...TT....",
        "................",
    ],
    "walk2": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "walk3": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        ".....T...T......",
        "....TT...TT.....",
        "................",
    ],
    "stand": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "aim": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOOOO..",
        "...OlLLLkLLLLGGC",
        "...OlLpbkLOOOO..",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "aim2": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWWcWO....",
        "....ODqDCCDO....",
        "....OWWWWWWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOOOO..",
        "...OlLLLkLLLLGGc",
        "...OlLpbkLOOOO..",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
}

SCI_PLATFORM = {
    "walk0": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWvvvvO....",
        "....OVVVVVVO....",
        "....OWVVVVWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "walk1": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWvvvvO....",
        "....OVVVVVVO....",
        "....OWVVVVWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T...T.....",
        ".....TT...TT....",
        "................",
    ],
    "walk2": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWvvvvO....",
        "....OVVVVVVO....",
        "....OWVVVVWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "walk3": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWvvvvO....",
        "....OVVVVVVO....",
        "....OWVVVVWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        ".....T...T......",
        "....TT...TT.....",
        "................",
    ],
    "carry0": [
        ".....QQQQQQ.....",
        ".....QRRRRQ.....",
        ".....QRrRRQ.....",
        ".....QRRRRQ.....",
        ".....QQQQQQ.....",
        "...w........w...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "carry1": [
        ".....QQQQQQ.....",
        ".....QRRRRQ.....",
        ".....QRrRRQ.....",
        ".....QRRRRQ.....",
        ".....QQQQQQ.....",
        "...w........w...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T...T.....",
        ".....TT...TT....",
        "................",
    ],
    "carry2": [
        ".....QQQQQQ.....",
        ".....QRRRRQ.....",
        ".....QRrRRQ.....",
        ".....QRRRRQ.....",
        ".....QQQQQQ.....",
        "...w........w...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "carry3": [
        ".....QQQQQQ.....",
        ".....QRRRRQ.....",
        ".....QRrRRQ.....",
        ".....QRRRRQ.....",
        ".....QQQQQQ.....",
        "...w........w...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        ".....T...T......",
        "....TT...TT.....",
        "................",
    ],
    "stand": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWvvvvO....",
        "....OVVVVVVO....",
        "....OWVVVVWYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "carry": [
        ".....QQQQQQ.....",
        ".....QRRRRQ.....",
        ".....QRrRRQ.....",
        ".....QRRRRQ.....",
        ".....QQQQQQ.....",
        "...w........w...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "cheer": [
        "................",
        "................",
        "................",
        "..w..........w..",
        "..Lw........wL..",
        "...L........L...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWvvvvOL...",
        "...LOVVVVVVOL...",
        "...LOWVVVVWYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
}

SCI_SRE = {
    "stand": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWZZZO....",
        "....OZZZzEZO....",
        "....OWWWZZZYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "blink": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWZZZO....",
        "....OZZZzzZO....",
        "....OWWWZZZYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLwwO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "type1": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWZZZO....",
        "....OZZZzEZO....",
        "....OWWWZZZYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkKKKKKK.",
        "...OlLpbkKnNNNK.",
        "...OllLLKKKKKKKK",
        "...OllLLLLwLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "type2": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWZZZO....",
        "....OZZZzEZO....",
        "....OWWWZZZYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkKKKKKK.",
        "...OlLpbkKNNnNK.",
        "...OllLLKKKKKKKK",
        "...OllLLLLLLw...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "typeblink": [
        "................",
        "................",
        "................",
        "................",
        "................",
        "................",
        "......OOOO......",
        ".....OWWWWO.....",
        "....OWWWZZZO....",
        "....OZZZzzZO....",
        "....OWWWZZZYYO..",
        "....OwWWWWWyyO..",
        ".....OwwWWO.....",
        "......OwwO......",
        ".....OLkkLO.....",
        "....OLLLkLOO....",
        "...OlLLLkKKKKKK.",
        "...OlLpbkKNNnNK.",
        "...OllLLKKKKKKKK",
        "...OllLLLLLLw...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
    "cheer": [
        "................",
        "................",
        "................",
        "..w..........w..",
        "..Lw........wL..",
        "...L........L...",
        "......OOOO......",
        ".....OWWWWO.....",
        "...LOWWWZZZOL...",
        "...LOZZZzEZOL...",
        "...LOWWWZZZYLO..",
        "...LOwWWWWWyLO..",
        "...L.OwwWWO.L...",
        "...L..OwwO..L...",
        "...O.OLkkLO.O...",
        "...LOLLLkLLOL...",
        "...OlLLLkLLLO...",
        "...OlLpbkLLLO...",
        "...OllLLkLLLO...",
        "...OllLLLLLLO...",
        "....OOOOOOOO....",
        "......T..T......",
        ".....TT..TT.....",
        "................",
    ],
}

ASTRO = {
    "stand": [
        ".....l.................",
        "......A..OOOOO.........",
        ".......OOWWWWWOO.......",
        "......oWhWWWWWWWO......",
        ".....oWhWWvhVVVVWO.....",
        ".....ohWWWvVFFFVVO.....",
        "....oWWWWvVFFFeFVVO....",
        "....oWWWWVFFFEFFVVO....",
        "....owWWWVFFFFFYYYO....",
        "....owwWWVfFFFFyyVO....",
        "....owwwWWVfFFFVVWo....",
        ".....owwwWWVVVVVWo.....",
        ".....oSwwwWWWWWWWo.....",
        "......oSwwwWWWWWo......",
        ".oooo..oowwwWWoo.......",
        "oBBBB..oCccCCCCo.......",
        "oBLBB.oWWWWWWWWWOwO....",
        "obBBBoSwWPPPPPWWWwO....",
        "obBBBoSwWP123PWWWwO....",
        "oBBBBoSwwwwwwwwwWGG....",
        "oBBBB.ooooooooooo......",
        ".oooo...ooooooo........",
        "........ww...ww........",
        ".......TTTt..TTTt......",
    ],
    "crouch": [
        ".....l.................",
        "......A..OOOOO.........",
        ".......OOWWWWWOO.......",
        "......oWhWWWWWWWO......",
        ".....oWhWWvhVVVVWO.....",
        ".....ohWWWvVFFFVVO.....",
        "....oWWWWvVFFFeFVVO....",
        "....oWWWWVFFFEFFVVO....",
        "....owWWWVFFFFFYYYO....",
        "....owwWWVfFFFFyyVO....",
        "....owwwWWVfFFFVVWo....",
        ".....owwwWWVVVVVWo.....",
        ".....oSwwwWWWWWWWo.....",
        "......oSwwwWWWWWo......",
        ".oooo..oowwwWWoo.......",
        "oBBBB..oCccCCCCo.......",
        "oBLBB.oWWWWWWWWWOwO....",
        "obBBBoSwWPPPPPWWWwO....",
        "obBBBoSwWP123PWWWwO....",
        "oBBBBoSwwwwwwwwwWGG....",
        "oBBBB.ooooooooooo......",
        ".oooo...ooooooo........",
        ".......................",
        "......TTTTt.TTTTt......",
    ],
    "tuck": [
        ".....l.................",
        "......A..OOOOO.........",
        ".......OOWWWWWOO.......",
        "......oWhWWWWWWWO......",
        ".....oWhWWvhVVVVWO.....",
        ".....ohWWWvVFFFVVO.....",
        "....oWWWWvVFFFeFVVO....",
        "....oWWWWVFFFEFFVVO....",
        "....owWWWVFFFFFYYYO....",
        "....owwWWVfFFFFyyVO....",
        "....owwwWWVfFFFVVWo....",
        ".....owwwWWVVVVVWo.....",
        ".....oSwwwWWWWWWWoGG...",
        "......oSwwwWWWWWo.wO...",
        ".oooo..oowwwWWoo..wO...",
        "oBBBB..oCccCCCCo.wO....",
        "oBLBB.oWWWWWWWWWOwO....",
        "obBBBoSwWPPPPPWWWO.....",
        "obBBBoSwWP123PWWWO.....",
        "oBBBBoSwwwwwwwwwWo.....",
        "oBBBB.ooooooooooo......",
        ".oooo...ooooooo........",
        "........wT...wT........",
        ".......................",
    ],
    "blink": [
        ".....l.................",
        "......A..OOOOO.........",
        ".......OOWWWWWOO.......",
        "......oWhWWWWWWWO......",
        ".....oWhWWvhVVVVWO.....",
        ".....ohWWWvVFFFVVO.....",
        "....oWWWWvVFFFFFVVO....",
        "....oWWWWVFFFFFFVVO....",
        "....owWWWVFFFFFYYYO....",
        "....owwWWVfFFFFyyVO....",
        "....owwwWWVfFFFVVWo....",
        ".....owwwWWVVVVVWo.....",
        ".....oSwwwWWWWWWWo.....",
        "......oSwwwWWWWWo......",
        ".oooo..oowwwWWoo.......",
        "oBBBB..oCccCCCCo.......",
        "oBLBB.oWWWWWWWWWOwO....",
        "obBBBoSwWPPPPPWWWwO....",
        "obBBBoSwWP123PWWWwO....",
        "oBBBBoSwwwwwwwwwWGG....",
        "oBBBB.ooooooooooo......",
        ".oooo...ooooooo........",
        "........ww...ww........",
        ".......TTTt..TTTt......",
    ],
}

SCI_COLORS = {'o': '#2e2e2e', 'O': '#5a5a5a', 'W': '#f2f2f2', 'w': '#d9d9d9', 'S': '#b4b4b4', 'E': '#101010', 'Y': '#ff9e3b', 'y': '#c8661a', 'L': '#d5dae1', 'l': '#aeb4bd', 'k': '#ffffff', 'p': '#a579c3', 'b': '#3b8eea', 'T': '#ff9e3b', 't': '#c8661a', 'H': '#ff9e3b', 'h': '#ffc680', 'q': '#ff9e3b', 'D': '#1c1c1c', 'C': '#23d8ea', 'c': '#b8f6fc', 'P': '#a579c3', 'M': '#6f4f8c', 'm': '#cfcfcf', 'G': '#9a9a9a', 'g': '#d0d0d0', 'K': '#1c1c1c', 'N': '#23d8ea', 'n': '#0e4d55', 'Q': '#2a2a2a', 'R': '#3a3a3a', 'r': '#98c379', 'V': '#5a4a78', 'v': '#a99bd0', 'Z': '#a8a8a8', 'z': '#d8f8fb'}
ASTRO_COLORS = {'O': '#5c5c5c', 'o': '#363636', 'W': '#f2f2f2', 'w': '#d6d6d6', 'S': '#a9a9a9', 's': '#7f7f7f', 'V': '#1b2232', 'v': '#3a4a6a', 'h': '#ffffff', 'F': '#d4d4d4', 'f': '#b2b2b2', 'E': '#0d0d0d', 'e': '#ffffff', 'Y': '#ff9e3b', 'y': '#c8661a', 'C': '#9a9a9a', 'c': '#d9d9d9', 'P': '#1b1b1b', '1': '#23d8ea', '2': '#a579c3', '3': '#98c379', 'B': '#262626', 'b': '#3a3a3a', 'L': '#a579c3', 'A': '#8a8a8a', 'l': '#23d8ea', 'G': '#c2c2c2', 'T': '#ff9e3b', 't': '#c8661a'}

# jetpack flame under the astronaut's backpack, two flicker frames
JET = [
    [".offo.", "eoffoe", ".offo.", "..oo..", "..ee.."],
    [".offo.", ".offo.", "e.oo.e", "..ee..", "......"],
]
JET_COLORS = {"f": "#ffe7a3", "o": P["orange"], "e": "#ff7d4d"}
WALK = ["walk0", "walk1", "walk2", "walk3"]


def pixels(rows, px, colors, dy=0):
    """Rows of colour keys -> merged <rect> runs."""
    out = []
    for y, row in enumerate(rows):
        x = 0
        while x < len(row):
            c = row[x]
            if c == ".":
                x += 1
                continue
            run = 1
            while x + run < len(row) and row[x + run] == c:
                run += 1
            out.append(f'<rect x="{x * px:g}" y="{(y + dy) * px:g}" width="{run * px:g}" height="{px:g}" fill="{colors[c]}"/>')
            x += run
    return "".join(out)


def sprite(frames, px, colors, cls):
    """Pixels shared by every frame are drawn once; each frame's differences get their own
    group (class f"{cls}-{name}") so CSS can flip between them cheaply."""
    names = list(frames)
    first = frames[names[0]]
    h, w = len(first), len(first[0])
    base = ["".join(first[y][x] if all(frames[n][y][x] == first[y][x] for n in names) else "." for x in range(w))
            for y in range(h)]
    out = [pixels(base, px, colors)]
    for n in names:
        diff = ["".join(frames[n][y][x] if frames[n][y][x] != base[y][x] else "." for x in range(w)) for y in range(h)]
        out.append(f'<g class="{cls}-{n}">{pixels(diff, px, colors)}</g>')
    return "".join(out), w * px, h * px


def actor(cls, frames, colors, period, script, px=2, rest="stand"):
    """Animates a sprite along a script of
    (t0, t1, (x0, y0), (x1, y1), frame cycle, seconds per frame, facing[, opacity at t0, opacity at t1]).

    Returns (css, svg). Positions are the sprite's top-left corner. The resting state (no CSS) is
    the `rest` frame at the script's first visible stop, facing right."""
    body, w, h = sprite(frames, px, colors, cls)
    pct = lambda t: f"{t / period * 100:.3f}%"
    moves, faces, fades, changes = [], [], [], []
    for step in script:
        t0, t1, (x0, y0), (x1, y1), cycle, dt, face = step[:7]
        a0, a1 = step[7:9] if len(step) > 7 else (1, 1)
        moves += [f"{pct(t0)}{{transform:translate({x0}px,{y0}px)}}", f"{pct(t1)}{{transform:translate({x1}px,{y1}px)}}"]
        fades += [f"{pct(t0)}{{opacity:{a0}}}", f"{pct(t1)}{{opacity:{a1}}}"]
        faces.append(f"{pct(t0)}{{transform:scaleX({face})}}")
        t, k = t0, 0
        while t < t1 - 1e-6:
            changes.append((t, cycle[k % len(cycle)]))
            t, k = t + dt, k + 1
    css = (f".{cls}-mv{{animation:{cls}-mv {period}s linear infinite}}@keyframes {cls}-mv{{{''.join(moves)}}}"
           f".{cls}-op{{animation:{cls}-op {period}s linear infinite}}@keyframes {cls}-op{{{''.join(fades)}}}"
           f".{cls}-fc{{transform-box:fill-box;transform-origin:center;animation:{cls}-fc {period}s steps(1) infinite}}"
           f"@keyframes {cls}-fc{{{''.join(faces)}100%{{transform:scaleX({script[-1][6]})}}}}")
    for name in frames:
        keys, shown = [], None
        for t, frame in changes:
            on = frame == name
            if on != shown:
                keys.append(f"{pct(t)}{{opacity:{1 if on else 0}}}")
                shown = on
        keys.append(f"100%{{opacity:{1 if shown else 0}}}")
        base = "" if name == rest else "opacity:0;"
        css += f".{cls}-{name}{{{base}animation:{cls}-{name} {period}s steps(1) infinite}}@keyframes {cls}-{name}{{{''.join(keys)}}}"
    stop = next((st[2] for st in script if st[2] == st[3] and st[2][0] < 1000 and (len(st) < 8 or st[7] == 1)),
                script[0][2])
    svg = (f'<g class="{cls}-mv" transform="translate({stop[0]} {stop[1]})"><g class="{cls}-op"><g class="{cls}-fc" shape-rendering="crispEdges">'
           f'{body}</g></g></g>')
    return css, svg


# ---------------------------------------------------------------- lab ducks at work (hero)
OFF = 1112  # just past the right edge


SCHEDULE = 180.0  # seconds; the ducks take turns, never on screen together
SLOTS = {"bd": 0.0, "pf": 60.0, "sr": 120.0}


def retime(markup, local, offset, period=SCHEDULE):
    """Stretches a scene written for a `local`-second loop into its slot of the shared schedule:
    CSS keyframes and durations, plus SMIL dur/keyTimes. Each keyframes block is pinned to its
    first/last state outside the slot so the scene rests (hidden) the rest of the time."""
    import re
    scale = lambda pct: (offset + float(pct) / 100 * local) / period * 100

    def block(m):
        steps = re.findall(r'([\d.%,\s]+)\{([^{}]*)\}', m.group(2))
        out = []
        for sel, props in steps:
            sel = ",".join(f"{scale(v.strip().rstrip('%')):.3f}%" for v in sel.split(",") if v.strip())
            out.append(f"{sel}{{{props}}}")
        return f"@keyframes {m.group(1)}{{0%{{{steps[0][1]}}}{''.join(out)}100%{{{steps[-1][1]}}}}}"

    markup = re.sub(r'@keyframes ([\w-]+)\{((?:[^{}]*\{[^{}]*\})*)\}', block, markup)
    markup = re.sub(rf'(\s|:){local:g}(?:\.0)?s\b', rf'\g<1>{period:g}s', markup)
    markup = markup.replace(f'dur="{local}s"', f'dur="{period:g}s"')

    def keytimes(m):
        vals = [float(v) for v in m.group(1).split(";")]
        mid = [f"{(offset + v * local) / period:.4f}" for v in vals[1:-1]]
        return 'keyTimes="0;' + ";".join(mid) + ';1"'
    return re.sub(r'keyTimes="([\d.;]+)"', keytimes, markup)


def builder_scene():
    """Smart-glasses duck beams in next to checkout, builds notify-λ with a laser pen, wires it
    up, then walks off to the right."""
    T, top, stop = 16.0, 262 - 46, 896
    here = (stop, top)
    css, duck = actor("bd", SCI_BUILDER, SCI_COLORS, T, [
        (0, 1.1, here, here, ["stand"], 1, 1, 0, 0),
        (1.1, 1.6, here, here, ["stand"], 1, 1, 0, 1),
        (1.6, 3.7, here, here, ["stand"], 1, 1),
        (3.7, 5.6, here, here, ["aim", "aim2"], .1, 1),
        (5.6, 12.6, here, here, ["stand"], 1, 1),
        (12.6, 15.0, here, (OFF, top), WALK, .12, 1),
        (15.0, T, (OFF, top), (OFF, top), ["stand"], 1, 1),
    ])
    q = lambda s: f"{s / T * 100:.2f}%"
    css += (f".beam{{opacity:0;animation:beam {T}s infinite}}@keyframes beam{{0%,{q(.9)}{{opacity:0}}{q(1.2)}{{opacity:.55}}"
            f"{q(1.8)},100%{{opacity:0}}}}")
    laser = ["0%{opacity:0}"]
    t = 3.8
    while t + .14 <= 5.5:  # flicker while the outline is drawn, then off for the rest of the loop
        laser += [f"{t / T * 100:.2f}%{{opacity:.85}}", f"{(t + .07) / T * 100:.2f}%{{opacity:.35}}"]
        t += .14
    laser.append(f"{t / T * 100:.2f}%{{opacity:0}}")
    css += f".laser{{opacity:0;animation:laser {T}s steps(1) infinite}}@keyframes laser{{{''.join(laser)}}}"
    beam = (f'<rect class="beam" x="{stop + 2}" y="{top - 30}" width="28" height="{262 - top + 30}" fill="url(#beamfill)"/>'
            f'<line class="laser" x1="928" y1="249" x2="939" y2="237" stroke="{P["cyan"]}" stroke-width="1.2"/>')
    pct = lambda s: f"{s / T * 100:.2f}%"
    css += (
        f".nsvc{{animation:nsvc {T}s infinite}}@keyframes nsvc{{0%,{pct(3.7)}{{opacity:0}}{pct(3.8)},{pct(14)}{{opacity:1}}{pct(15.2)},100%{{opacity:0}}}}"
        f".nso{{stroke-dasharray:1;animation:nso {T}s infinite}}@keyframes nso{{0%,{pct(3.8)}{{stroke-dashoffset:1}}{pct(5.2)},100%{{stroke-dashoffset:0}}}}"
        f".nsf{{animation:nsf {T}s infinite}}@keyframes nsf{{0%,{pct(5.2)}{{opacity:0}}{pct(5.5)},100%{{opacity:1}}}}"
        f".nsl{{animation:nsl {T}s infinite}}@keyframes nsl{{0%,{pct(5.5)}{{opacity:0}}{pct(5.9)},100%{{opacity:1}}}}"
        f".nw1{{stroke-dasharray:1;animation:nw1 {T}s infinite}}@keyframes nw1{{0%,{pct(6.0)}{{stroke-dashoffset:1}}{pct(6.7)},100%{{stroke-dashoffset:0}}}}"
        f".nw2{{stroke-dasharray:1;animation:nw2 {T}s infinite}}@keyframes nw2{{0%,{pct(6.9)}{{stroke-dashoffset:1}}{pct(7.9)},100%{{stroke-dashoffset:0}}}}"
        f".ah1{{animation:ah1 {T}s infinite}}@keyframes ah1{{0%,{pct(6.7)}{{opacity:0}}{pct(6.8)},100%{{opacity:1}}}}"
        f".ah2{{animation:ah2 {T}s infinite}}@keyframes ah2{{0%,{pct(7.9)}{{opacity:0}}{pct(8.0)},100%{{opacity:1}}}}"
    )
    sparks = []
    for k in range(6):  # bursts where the laser hits the outline
        t = 3.92 + k * .26
        dx, dy = ((-8, -7), (8, -9), (10, 5), (-7, 6), (6, -11), (-10, -2))[k]
        color = (P["orange"], P["cyan"])[k % 2]
        css += (f".spk{k}{{opacity:0;animation:spk{k} {T}s infinite}}@keyframes spk{k}{{0%,{pct(t)}{{opacity:0;transform:none}}"
                f"{pct(t + .05)}{{opacity:1}}{pct(t + .45)},100%{{opacity:0;transform:translate({dx}px,{dy}px)}}}}")
        sparks.append(f'<rect class="spk{k}" x="943" y="235" width="2" height="2" fill="{color}"/>')

    def event(path, start, end, color):
        a, b = start / T, end / T
        return (f'<circle r="1.8" fill="{color}" opacity="0">'
                f'<animateMotion path="{path}" dur="{T}s" repeatCount="indefinite" calcMode="linear" '
                f'keyPoints="0;0;1;1" keyTimes="0;{a:.3f};{b:.3f};1"/>'
                f'<animate attributeName="opacity" dur="{T}s" repeatCount="indefinite" values="0;0;.9;.9;0;0" '
                f'keyTimes="0;{a:.3f};{a + .005:.3f};{b - .005:.3f};{b:.3f};1"/></circle>')

    service = f"""<g class="nsvc">
<path class="nw1" pathLength="1" d="M944 196V224" fill="none" stroke="{A['wire']}"/>
<path class="ah1" d="M940.8 221.2L944 225.5L947.2 221.2Z" fill="#383838"/>
<path class="nw2" pathLength="1" d="M890 244H932" fill="none" stroke="{A['wire']}"/>
<path class="ah2" d="M929.2 240.8L933.5 244L929.2 247.2Z" fill="#383838"/>
<path class="nso" pathLength="1" d="M939 226H949A5 5 0 0 1 954 231V241A5 5 0 0 1 949 246H939A5 5 0 0 1 934 241V231A5 5 0 0 1 939 226Z" fill="none" stroke="{A['edge']}"/>
<g class="nsf"><rect x="934" y="226" width="20" height="20" rx="5" fill="{A['node']}" stroke="{A['edge']}"/>
<text x="944" y="239.5" font-size="10" text-anchor="middle" fill="{A['glyph']}" class="mono">λ</text></g>
<text class="nsl mono" x="944" y="257" font-size="7.5" text-anchor="middle" fill="{A['label']}">notify-λ</text>
{''.join(sparks)}
{event("M944 196V225", 8.6, 9.4, P["purple"])}{event("M890 244H933", 10.4, 11.2, P["orange"])}
</g>"""
    return css, service, beam + duck


def platform_scene():
    """AR-visor duck walks in from the left along the event bus carrying a new pod, slots it into
    the EKS cluster (hpa 2→3), then steps right and leaves through a black door that folds away."""
    T, top, stop = 18.0, 186 - 46, 802
    here, up = (stop, top), (stop, top - 5)
    carry = ["carry0", "carry1", "carry2", "carry3"]
    left, porch, inside = 668, 840, 884
    css, duck = actor("pf", SCI_PLATFORM, SCI_COLORS, T, [
        (0, 1.0, (left, top), (left, top), ["carry"], 1, 1, 0, 0),
        (1.0, 1.4, (left, top), (left + 20, top), carry, .12, 1, 0, 1),
        (1.4, 4.6, (left + 20, top), here, carry, .12, 1),
        (4.6, 5.0, here, here, ["carry"], 1, 1),
        (5.0, 5.25, here, up, ["carry"], 1, 1),
        (5.25, 5.55, up, here, ["cheer"], 1, 1),
        (5.55, 6.8, here, here, ["stand"], 1, 1),
        (6.8, 7.6, here, (porch, top), WALK, .12, 1),
        (7.6, 8.4, (porch, top), (porch, top), ["stand"], 1, 1),
        (8.4, 9.2, (porch, top), (inside, top), WALK, .12, 1),
        (9.2, 9.21, (inside, top), (inside, top), ["stand"], 1, 1, 1, 0),
        (9.21, T, (inside, top), (inside, top), ["stand"], 1, 1, 0, 0),
    ])
    q = lambda s: f"{s / T * 100:.2f}%"
    # the door rises out of the bus, opens, swallows the duck, closes and folds back down
    css += (
        f".door{{opacity:0;animation:door {T}s infinite}}@keyframes door{{0%,{q(6.95)}{{opacity:0}}{q(7.0)},{q(10.55)}{{opacity:1}}{q(10.6)},100%{{opacity:0}}}}"
        f".doorbox{{transform-box:fill-box;transform-origin:bottom;animation:doorbox {T}s infinite}}"
        f"@keyframes doorbox{{0%,{q(7.0)}{{transform:scaleY(0)}}{q(7.6)},{q(10.0)}{{transform:none}}{q(10.6)},100%{{transform:scaleY(0)}}}}"
        f".leaf{{transform-box:fill-box;transform-origin:left;animation:leaf {T}s infinite}}"
        f"@keyframes leaf{{0%,{q(7.7)}{{transform:none}}{q(8.2)},{q(9.3)}{{transform:scaleX(.12)}}{q(9.8)},100%{{transform:none}}}}"
    )
    dx, dy, dw, dh = 880, 144, 30, 42
    door = (f'<g class="door"><g class="doorbox">'
            f'<rect x="{dx - 2}" y="{dy - 2}" width="{dw + 4}" height="{dh + 2}" rx="2" fill="#050505" stroke="#2f2f2f"/>'
            f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="#000000"/>'
            f'<g class="leaf"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="#151515" stroke="#262626"/>'
            f'<rect x="{dx + 4}" y="{dy + 4}" width="{dw - 8}" height="{dh / 2 - 6}" fill="none" stroke="#202020"/>'
            f'<rect x="{dx + dw - 6}" y="{dy + dh / 2}" width="2" height="3" fill="#5a5a5a"/></g>'
            f'</g></g>')
    duck += door
    pct = lambda s: f"{s / T * 100:.2f}%"
    css += (
        f".podp{{animation:podp {T}s steps(1) infinite}}@keyframes podp{{0%{{opacity:1}}{pct(5.25)}{{opacity:0}}{pct(16.8)}{{opacity:1}}}}"
        f".podr{{opacity:0;animation:podr {T}s steps(1) infinite}}@keyframes podr{{0%{{opacity:0}}{pct(5.25)}{{opacity:1}}{pct(16.8)}{{opacity:0}}}}"
        f".hpa{{animation:hpa {T}s infinite}}@keyframes hpa{{0%,{pct(5.2)}{{fill:{A['note']}}}{pct(5.4)},{pct(7)}{{fill:{P['cyan']}}}{pct(8)},100%{{fill:{A['note']}}}}}"
    )
    return css, duck


def sre_scene():
    """Round-glasses duck lives at the trace waterfall: types, gets the slow span from 182 ms to
    96 ms, celebrates, and goes back to typing (the span regresses so the loop can repeat)."""
    T, top, stop = 20.0, 314 - 46, 1052
    here, hop = (stop, top), (stop, top - 5)
    typing = ["type1", "type2"]
    css, duck = actor("sr", SCI_SRE, SCI_COLORS, T, [
        (0, .3, (OFF, top), (OFF, top), ["stand"], 1, -1),
        (.3, 1.6, (OFF, top), here, WALK, .12, -1),
        (1.6, 3.1, here, here, typing, .14, -1),
        (3.1, 3.25, here, here, ["typeblink"], 1, -1),
        (3.25, 6.2, here, here, typing, .14, -1),
        (6.2, 6.45, here, hop, ["cheer"], 1, -1),
        (6.45, 6.7, hop, here, ["cheer"], 1, -1),
        (6.7, 6.95, here, hop, ["cheer"], 1, -1),
        (6.95, 7.2, hop, here, ["cheer"], 1, -1),
        (7.2, 8.4, here, here, ["stand"], 1, -1),
        (8.4, 8.55, here, here, ["blink"], 1, -1),
        (8.55, 9.4, here, here, ["stand"], 1, -1),
        (9.4, 13.6, here, here, typing, .14, -1),
        (13.6, 13.75, here, here, ["typeblink"], 1, -1),
        (13.75, 17.6, here, here, typing, .14, -1),
        (17.6, 19.0, here, (OFF, top), WALK, .12, 1),
        (19.0, T, (OFF, top), (OFF, top), ["stand"], 1, 1),
    ], rest="type1")
    pct = lambda s: f"{s / T * 100:.2f}%"
    css += (
        f".crit{{transform-box:fill-box;transform-origin:left;animation:crit {T}s infinite}}"
        f"@keyframes crit{{0%,{pct(4.4)}{{transform:none}}{pct(5.6)},{pct(18.4)}{{transform:scaleX(.5)}}{pct(19.4)},100%{{transform:none}}}}"
        f".after{{animation:after {T}s infinite}}"
        f"@keyframes after{{0%,{pct(4.4)}{{transform:none}}{pct(5.6)},{pct(18.4)}{{transform:translateX(-15px)}}{pct(19.4)},100%{{transform:none}}}}"
        f".root{{transform-box:fill-box;transform-origin:left;animation:root {T}s infinite}}"
        f"@keyframes root{{0%,{pct(4.4)}{{transform:none}}{pct(5.6)},{pct(18.4)}{{transform:scaleX(.85)}}{pct(19.4)},100%{{transform:none}}}}"
        f".slow{{animation:slow {T}s infinite}}@keyframes slow{{0%,{pct(5.4)}{{opacity:1}}{pct(5.7)},{pct(18.6)}{{opacity:0}}{pct(19)},100%{{opacity:1}}}}"
        f".fast{{opacity:0;animation:fast {T}s infinite}}@keyframes fast{{0%,{pct(5.6)}{{opacity:0}}{pct(5.9)},{pct(18.4)}{{opacity:1}}{pct(18.7)},100%{{opacity:0}}}}"
    )
    return css, duck


# ---------------------------------------------------------------- hero banner
TITLE = ".NET Specialist · Solution Architecture · Distributed Systems · AWS"
BADGES = ["sap", "saa", "dva"]
# architecture blueprint: graphite first, colour only on the moving traces
A = {"frame": "#242424", "vpc": "#1e1e1e", "wire": "#2b2b2b", "node": "#111111", "edge": "#2c2c2c",
     "glyph": "#5a5a5a", "label": "#434343", "note": "#353535"}


def node(x, y, kind, label=None, above=False):
    """A 20px service node with a tiny line icon."""
    s = f'fill="none" stroke="{A["glyph"]}" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"'
    t = f'text-anchor="middle" fill="{A["glyph"]}" class="mono"'
    cyl = f'<ellipse cx="{x}" cy="{y - 4}" rx="5" ry="1.8"/><path d="M{x - 5} {y - 4}v8c0 1 2.2 1.8 5 1.8s5-.8 5-1.8v-8"/>'
    icon = {
        "dns": f'<text x="{x}" y="{y + 3}" font-size="7.5" {t}>53</text>',
        "cdn": f'<g {s}><circle cx="{x}" cy="{y}" r="5.5"/><ellipse cx="{x}" cy="{y}" rx="2.3" ry="5.5"/><path d="M{x - 5.5} {y}h11"/></g>',
        "api": f'<text x="{x}" y="{y + 3}" font-size="8.5" {t}>{{}}</text>',
        "auth": f'<path {s} d="M{x} {y - 6}l5 2v3.6c0 3-2.2 5-5 6.2c-2.8-1.2-5-3.2-5-6.2v-3.6z"/>',
        "fn": f'<text x="{x}" y="{y + 3.5}" font-size="10" {t}>λ</text>',
        "queue": f'<path {s} d="M{x - 5} {y - 3.5}h10M{x - 5} {y}h10M{x - 5} {y + 3.5}h10"/>',
        "db": f'<g {s}>{cyl}</g>',
        "sql": f'<g {s}>{cyl}<path d="M{x - 5} {y}c0 1 2.2 1.8 5 1.8s5-.8 5-1.8"/></g>',
        "cache": f'<path {s} d="M{x} {y - 5.5}l5.5 5.5-5.5 5.5-5.5-5.5z"/>',
        "bucket": f'<g {s}><path d="M{x - 5.5} {y - 3.5}h11l-1.8 8.5h-7.4z"/><ellipse cx="{x}" cy="{y - 3.5}" rx="5.5" ry="1.4"/></g>',
        "otel": f'<g {s}><circle cx="{x}" cy="{y}" r="5.5"/><circle cx="{x}" cy="{y}" r="2.1"/></g>',
        "prom": (f'<path d="M{x} {y - 6}c3.6 3.2 5 5.6 3.6 8.6c-.8 1.8-2.2 2.8-3.6 2.8s-2.8-1-3.6-2.8'
                 f'c-.9-2.2.1-4 1.6-5.6c.1 1.6.9 2.6 1.9 2.8c.4-2 .4-3.6.1-5.8z" fill="{P["orange"]}" opacity=".85"/>'),
        "tempo": f'<path {s} d="M{x - 5.5} {y - 3.5}h8M{x - 3} {y}h8.5M{x - 1} {y + 3.5}h4"/>',
    }[kind]
    out = f'<rect x="{x - 10}" y="{y - 10}" width="20" height="20" rx="5" fill="{A["node"]}" stroke="{A["edge"]}"/>{icon}'
    if label:
        out += f'<text x="{x}" y="{y - 15 if above else y + 19}" font-size="7.5" text-anchor="middle" fill="{A["label"]}" class="mono">{label}</text>'
    return out


def wire(d, dashed=False, arrow=True, dotted=False):
    dash = ' stroke-dasharray="3 3"' if dashed else ' stroke-dasharray="1 3"' if dotted else ""
    end = ' marker-end="url(#arr)"' if arrow else ""
    return f'<path d="{d}" fill="none" stroke="{A["wire"]}" stroke-width="1"{dash}{end}/>'


def trace(d, color, dur, begin, r=2):
    """A request/event/span dot travelling along a wire."""
    return (f'<circle r="{r}" fill="{color}" opacity="0">'
            f'<animateMotion path="{d}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;.9;.9;0" keyTimes="0;.08;.88;1" dur="{dur}s" begin="{begin}s" '
            f'repeatCount="indefinite"/></circle>')


def pill(x, y, w, label):
    return (f'<rect x="{x - w / 2}" y="{y - 7}" width="{w}" height="14" rx="7" fill="{A["node"]}" stroke="{A["edge"]}"/>'
            f'<text x="{x}" y="{y + 2.5}" font-size="7" text-anchor="middle" fill="#515151" class="mono">{label}</text>')


def architecture():
    """Blueprint of an event-driven AWS workload (DuckStore-like), kept faint behind the text."""
    lab = f'font-size="7.5" fill="{A["label"]}" class="mono"'
    note = f'font-size="6.5" fill="{A["note"]}" class="mono"'
    parts = [
        # region + vpc
        f'<rect x="626" y="20" width="470" height="298" rx="12" fill="none" stroke="{A["frame"]}" stroke-dasharray="4 4"/>',
        f'<rect x="640" y="32" width="5" height="5" rx="1" fill="{P["orange"]}" opacity=".85"/>',
        f'<text x="651" y="37" font-size="8" letter-spacing="1.4" fill="#4b4b4b" class="mono">AWS · SA-EAST-1</text>',
        f'<text x="1082" y="37" font-size="7.5" text-anchor="end" fill="{A["note"]}" class="mono">duckstore · prod · vpc 10.0.0.0/16</text>',
        f'<rect x="640" y="46" width="332" height="262" rx="8" fill="none" stroke="{A["vpc"]}"/>',
        # edge row
        wire("M674 80H710"), wire("M730 80H766"), wire("M786 80H822", dashed=True),
        wire("M776 90V106", arrow=False), wire("M723 106H944", arrow=False),
        wire("M888 106V91"), wire("M944 106V91"), wire("M723 106V115"),
        f'<text x="796" y="102" {note}>https · jwt</text>',
        node(664, 80, "dns", "route53", above=True), node(720, 80, "cdn", "cloudfront", above=True),
        node(776, 80, "api", "api-gw", above=True), node(832, 80, "auth", "cognito", above=True),
        node(888, 80, "fn", "orders-λ", above=True), node(944, 80, "fn", "payments-λ", above=True),
        # compute: eks cluster with pods, one of them scaling out
        f'<rect x="690" y="116" width="178" height="54" rx="6" fill="none" stroke="{A["edge"]}" stroke-dasharray="3 3"/>',
        f'<text x="698" y="128" font-size="7" fill="{A["note"]}" class="mono">eks · 2 services</text>',
    ]
    for k in range(3):
        parts.append(f'<rect x="{704 + k * 12}" y="138" width="9" height="9" rx="2" fill="#141414" stroke="#363636"/>')
    parts.append(f'<rect x="711" y="139" width="2" height="2" fill="{P["green"]}"/>')
    for k in range(2):
        parts.append(f'<rect x="{790 + k * 12}" y="138" width="9" height="9" rx="2" fill="#141414" stroke="#363636"/>')
    parts += [
        f'<rect class="podp" x="814" y="138" width="9" height="9" rx="2" fill="none" stroke="#363636" stroke-dasharray="2 2"/>',
        f'<g class="podr"><rect x="814" y="138" width="9" height="9" rx="2" fill="#141414" stroke="#363636"/>'
        f'<rect x="821" y="139" width="2" height="2" fill="{P["green"]}"/></g>',
        f'<text x="721" y="162" {lab} text-anchor="middle">catalog</text>',
        f'<text x="806" y="162" {lab} text-anchor="middle">cart</text>',
        f'<text class="hpa mono" x="830" y="146" font-size="6.5" fill="{A["note"]}">hpa 2→3</text>',
        wire("M868 143H919"), node(930, 143, "queue"),
        f'<text x="930" y="162" {lab} text-anchor="middle">orders.fifo</text>',
        # event bus
        wire("M808 170V185", dashed=True), wire("M941 143H952V185", dashed=True),
        f'<text x="676" y="181" {lab}>eventbridge · duckstore.bus</text>',
        f'<rect x="676" y="186" width="286" height="10" rx="5" fill="{A["node"]}" stroke="{A["edge"]}"/>',
    ]
    for k in range(3):
        parts.append(f'<rect class="evt" style="animation-delay:{k * 2.4:.1f}s" x="680" y="188.5" width="5" height="5" rx="1" fill="{P["purple"]}"/>')
    # step functions: checkout state machine
    parts += [
        f'<text x="676" y="214" {lab}>step functions · checkout</text>',
        wire("M704 196V225"), wire("M726 233H739"), wire("M784 233H808"),
        wire("M823 233H836V222H849"), wire("M836 233V244H849", dashed=True),
        pill(704, 233, 44, "reserve"), pill(762, 233, 44, "charge"),
        f'<path d="M816 226l7 7-7 7-7-7z" fill="{A["node"]}" stroke="{A["edge"]}"/>',
        pill(870, 222, 40, "ship"), pill(870, 244, 40, "refund"),
        # data
        wire("M704 240V273"), wire("M762 240V273"), wire("M890 222H904V284H889"),
        node(704, 284, "db", "orders-ddb"), node(762, 284, "sql", "aurora-pg"),
        node(820, 284, "cache", "redis"), node(878, 284, "bucket", "s3"),
        f'<text x="834" y="268" {note}>p99 42ms</text>',
        # observability column, right of the vpc
        wire("M972 84H993", dotted=True), f'<text x="975" y="79" {note}>otlp</text>',
        wire("M1004 94V129"), wire("M994 88H988V196H993", dashed=True),
        node(1004, 84, "otel"), node(1004, 140, "prom"), node(1004, 196, "tempo"),
        f'<text x="1019" y="87" {lab}>otel</text>', f'<text x="1019" y="143" {lab}>prometheus</text>',
        f'<text x="1019" y="199" {lab}>tempo</text>',
        # trace waterfall: the sre duck gets the slow (orange) span from 182 ms down to 96 ms
        f'<text class="slow mono" x="984" y="232" font-size="6.5" fill="{A["note"]}">trace 7f3a…e1 · 182 ms</text>',
        f'<text class="fast mono" x="984" y="232" font-size="6.5" fill="{A["note"]}">trace 7f3a…e1 · 96 ms <tspan fill="{P["green"]}">✓</tspan></text>',
        f'<rect class="root" x="984" y="238" width="100" height="3" rx="1.5" fill="#2c2c2c"/>',
        f'<rect x="991" y="244" width="44" height="3" rx="1.5" fill="{P["blue"]}" opacity=".7"/>',
        f'<rect class="crit" x="1000" y="250" width="30" height="3" rx="1.5" fill="{P["orange"]}" opacity=".75"/>',
        f'<g class="after"><rect x="1032" y="256" width="38" height="3" rx="1.5" fill="#2c2c2c"/>'
        f'<rect x="1038" y="262" width="20" height="3" rx="1.5" fill="{P["purple"]}" opacity=".7"/></g>',
        f'<rect class="scan" x="984" y="235" width="1" height="32" fill="{P["cyan"]}" opacity=".45"/>',
    ]
    # traces in flight: requests in blue/cyan, events in purple, the checkout path in orange
    parts += [
        trace("M664 80H776V106H888V91", P["cyan"], 5.5, .4),
        trace("M776 80V106H723V138", P["blue"], 3.6, 2.2),
        trace("M808 170V191H704V226", P["purple"], 4.6, 1.2),
        trace("M704 233H816H836V222H870", P["orange"], 4.2, .8, r=1.8),
        trace("M972 84H994", P["purple"], 1.6, .2, r=1.6),
        trace("M1004 94V130", P["blue"], 2.2, 1.0, r=1.6),
    ]
    return "".join(parts)


DESCRIPTION = [
    'Backend engineer and software architect specialized in <tspan fill="#cfcfcf" font-weight="500">.NET</tspan>',
    "(C#, ASP.NET Core, .NET Aspire), designing event-driven,",
    'distributed systems on <tspan fill="#cfcfcf" font-weight="500">AWS</tspan>.',
]
DESCRIPTION_PLAIN = [
    "Backend engineer and software architect specialized in .NET",
    "(C#, ASP.NET Core, .NET Aspire), designing event-driven,",
    "distributed systems on AWS.",
]
# the same sentence, as C# in the theme's syntax colours: (text, kind)
CSHARP = [
    [("var", "kw"), (" me", "var"), (" = ", "op"), ("new", "kw"), (" Engineer", "type"), ("(", "punct"),
     ("Role", "type"), (".", "punct"), ("Backend", "enum"), (" | ", "bit"), ("Role", "type"), (".", "punct"),
     ("Architect", "enum"), (");", "punct")],
    [("me", "var"), (".", "punct"), ("Specialize", "method"), ("(", "punct"), ('".NET"', "str"), (", ", "punct"),
     ("Stack", "type"), (".", "punct"), ("AspNetCore", "enum"), (", ", "punct"), ("Stack", "type"), (".", "punct"),
     ("Aspire", "enum"), (");", "punct")],
    [("await", "kw"), (" me", "var"), (".", "punct"), ("DesignAsync", "method"), ("(", "punct"), ("Arch", "type"),
     (".", "punct"), ("EventDriven", "enum"), (", ", "punct"), ("on", "param"), (": ", "punct"), ("Cloud", "type"),
     (".", "punct"), ("Aws", "enum"), (");", "punct")],
]
SYNTAX = {"kw": "#ff7d4d", "type": "#ff9e3b", "enum": "#ff9e3b", "method": "#23d8ea", "var": "#e0e0e0",
          "punct": "#888888", "op": "#888888", "bit": "#ff9e3b", "param": "#888888", "str": "#98c379"}

# Engineer-style runes (a nod to the Prometheus film): 6x11 cells, words joined by a top bar
RUNES = [
    ("M3 0V11", [(3, 3.2, 1.6)], []),
    ("M1 0V11M1 5.5H5", [], []),
    ("M3 0V7M.5 7.5a2.5 2.5 0 0 0 5 0", [], []),
    ("M1 0V11M5 0V6", [], [(5, 9)]),
    ("M3 0V2.9M3 8.1V11", [(3, 5.5, 2.6)], []),
    ("M3 0V11M3 3L6 0", [], [(.8, 8)]),
    ("M.5 0V11H5", [], [(4, 4.5)]),
    ("M5.5 0V11M5.5 4H1", [(1.6, 8.5, 1.3)], []),
    ("M3 0L.5 11M3 0L5.5 11M1.4 7H4.6", [], []),
    ("M3 0V11", [], [(.8, 3), (5.2, 3), (.8, 8), (5.2, 8)]),
    ("M.5 0a2.5 2.5 0 0 0 5 0M3 2.5V11", [], []),
    ("M1 0V11M5 0V11M1 5.5H5", [], []),
]


def runes(text, x, baseline, adv=7.6):
    strokes, rings, dots = [], [], []
    top = baseline - 11
    cx = x
    for word in text.split(" "):
        start = cx
        for ch in word:
            path, circles, points = RUNES[(ord(ch) * 7 + int(cx) // 3) % len(RUNES)]
            strokes.append(f'<path transform="translate({cx:.1f} {top})" d="{path}"/>')
            rings += [f'<circle cx="{cx + a:.1f}" cy="{top + b:.1f}" r="{r}"/>' for a, b, r in circles]
            dots += [f'<circle cx="{cx + a:.1f}" cy="{top + b:.1f}" r=".9"/>' for a, b in points]
            cx += adv
        if word:
            strokes.append(f'<path d="M{start - .5:.1f} {top}H{cx - 1.1:.1f}"/>')
        cx += adv
    return "".join(strokes + rings), "".join(dots)


def translation():
    """The description arrives in an alien script, is translated to C#, then to English.

    Plays once (SMIL, so it also runs inside <img>). Every animated value starts at t=0 and the
    resting attributes are the final state, so a renderer without animation just shows the text."""
    x0, x1, top, h = 50, 600, 182, 74
    T, w1s, w1e, w2s, w2e = 4.0, .9, 1.7, 2.6, 3.4
    k = lambda t: f"{t / T:.3f}"
    spline = 'calcMode="spline" keySplines="0 0 1 1;.6 0 .4 1;0 0 1 1"'

    def anim(attr, a, b, start, end):
        return (f'<animate attributeName="{attr}" values="{a};{a};{b};{b}" keyTimes="0;{k(start)};{k(end)};1" '
                f'dur="{T}s" begin="0s" fill="freeze" {spline}/>')

    baselines = [198, 222, 246]
    alien = [runes(line, 56, y) for line, y in zip(DESCRIPTION_PLAIN, baselines)]
    alien_svg = (f'<g fill="none" stroke="#4a4a4a" stroke-width="1.25" stroke-linecap="round">'
                 + "".join(s for s, _ in alien) + '</g><g fill="#4a4a4a">' + "".join(d for _, d in alien) + "</g>")
    code = "".join(
        f'<text x="56" y="{y}" font-size="13" class="mono">'
        + "".join(f'<tspan fill="{SYNTAX[kind]}">{esc(text)}</tspan>' for text, kind in line) + "</text>"
        for line, y in zip(CSHARP, baselines)
    )
    english = "".join(f'<text x="56" y="{y}">{line}</text>' for line, y in zip(DESCRIPTION, baselines))

    def scan(color, start, end):
        return (f'<rect x="{x0}" y="{top}" width="1.5" height="{h}" fill="{color}" opacity="0">'
                f'<animate attributeName="x" values="{x0};{x0};{x1};{x1}" keyTimes="0;{k(start)};{k(end)};1" dur="{T}s" '
                f'begin="0s" fill="freeze" {spline}/>'
                f'<animate attributeName="opacity" values="0;0;.9;.9;0;0" keyTimes="0;{k(start)};{k(start + .1)};{k(end - .1)};{k(end)};1" '
                f'dur="{T}s" begin="0s" fill="freeze"/></rect>')

    return f"""<defs>
<clipPath id="tAlien"><rect x="{x1}" y="{top}" width="{x1 - x0}" height="{h}">{anim("x", x0, x1, w1s, w1e)}</rect></clipPath>
<clipPath id="tCodeL"><rect x="{x0}" y="{top}" width="0" height="{h}">{anim("width", 0, x1 - x0, w1s, w1e)}</rect></clipPath>
<clipPath id="tCodeR"><rect x="{x1}" y="{top}" width="{x1 - x0}" height="{h}">{anim("x", x0, x1, w2s, w2e)}</rect></clipPath>
<clipPath id="tText"><rect x="{x0}" y="{top}" width="{x1 - x0}" height="{h}">{anim("width", 0, x1 - x0, w2s, w2e)}</rect></clipPath>
</defs>
<g clip-path="url(#tAlien)" opacity="0"><animate attributeName="opacity" values="0;1" dur=".5s" begin="0s" fill="freeze"/>{alien_svg}</g>
<g clip-path="url(#tCodeL)"><g clip-path="url(#tCodeR)">{code}</g></g>
<g clip-path="url(#tText)" class="sans" font-size="16.2" fill="{P['body']}">{english}</g>
{scan(P["cyan"], w1s, w1e)}{scan(P["orange"], w2s, w2e)}"""


HEX = ((.5, .013), (.922, .257), (.922, .743), (.5, .987), (.078, .743), (.078, .257))  # hexagon inside a badge


def badge_cluster(cx, cy, size=84, gap=6):
    """The AWS badges as an interlocking honeycomb (SAP on top, the associates tucked under it).
    The cluster floats as one piece and a single light band sweeps across all three hexagons.
    Returns (css, svg)."""
    w = .844 * size  # flat-to-flat width of the hexagon
    step = w + gap
    spots = [("sap", cx, cy), ("saa", cx - step / 2, cy + .866 * step), ("dva", cx + step / 2, cy + .866 * step)]
    images, hexes = [], []
    for key, x, y in spots:
        x0, y0 = x - size / 2, y - size / 2
        images.append(f'<image href="data:image/png;base64,{asset_b64(f"badges/{key}.png")}" '
                      f'x="{x0:.1f}" y="{y0:.1f}" width="{size}" height="{size}"/>')
        hexes.append(f'<polygon points="{" ".join(f"{x0 + size * a:.1f},{y0 + size * b:.1f}" for a, b in HEX)}"/>')
    left, top = cx - step / 2 - w / 2, cy - size / 2
    width, height = step + w, .866 * step + size
    slant, band = .32 * height, 22
    x = left - band - slant
    glint = (f'<polygon class="glint" points="{x:.1f},{top + height:.1f} {x + band:.1f},{top + height:.1f} '
             f'{x + band + slant:.1f},{top:.1f} {x + slant:.1f},{top:.1f}" fill="url(#shine)"/>')
    travel = width + 2 * band + slant
    css = (".cluster{animation:bob 3.4s ease-in-out infinite alternate}"
           f".glint{{animation:glint 6s ease-in-out infinite}}@keyframes glint{{0%,55%{{transform:none}}85%,100%{{transform:translateX({travel:.0f}px)}}}}")
    svg = (f'<clipPath id="hexes">{"".join(hexes)}</clipPath>'
           f'<g class="cluster">{"".join(images)}<g clip-path="url(#hexes)">{glint}</g></g>')
    return css, svg


def hero(user):
    width, height = 1000, 420
    css = font_css("sans", "mono") + BASE_CSS + (
        ".cur{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        ".evt{opacity:0;animation:evt 7.2s linear infinite}"
        "@keyframes evt{0%{opacity:0;transform:none}6%{opacity:.85}90%{opacity:.85}100%{opacity:0;transform:translateX(272px)}}"
        ".scan{animation:scan 7s ease-in-out infinite}@keyframes scan{0%,15%{transform:none}60%,100%{transform:translateX(100px)}}"
        "@keyframes bob{to{transform:translateY(-3px)}}"
    )
    badges_css, badges = badge_cluster(582, 166, size=88)
    css += badges_css
    bd_css, bd_service, bd_duck = (retime(x, 16.0, SLOTS["bd"]) for x in builder_scene())
    pf_css, pf_duck = (retime(x, 18.0, SLOTS["pf"]) for x in platform_scene())
    sr_css, sr_duck = (retime(x, 20.0, SLOTS["sr"]) for x in sre_scene())
    css += bd_css + pf_css + sr_css
    dot = '<tspan fill="#474747">·</tspan>'
    text = f"""<g class="in">
<text x="56" y="62" font-size="12" letter-spacing="1.9" fill="#737373" class="mono">5+ YEARS BUILDING SOFTWARE · BELO HORIZONTE, BR<tspan class="cur" fill="{P['orange']}"> ▍</tspan></text>
</g>
<g class="in sans" style="animation-delay:.1s" font-size="34" font-weight="620" letter-spacing="-0.7" fill="{P['text']}">
<text x="54" y="112"><tspan fill="{P['purple']}">.NET</tspan> Specialist {dot} Solution Architecture</text>
<text x="54" y="154">Distributed Systems {dot} <tspan fill="{P['orange']}">AWS</tspan></text>
</g>
{translation()}
<g class="in" style="animation-delay:.35s">
<rect x="56" y="270" width="3" height="27" rx="1.5" fill="url(#quotebar)"/>
<text x="72" y="291" font-size="22.5" font-weight="520" letter-spacing="-0.3" fill="#bdbdbd" class="sans">I pick patterns for the problem, <tspan fill="#ffffff" font-weight="600">not the hype.</tspan></text>
<text x="56" y="320" font-size="12.5" fill="{P['comment']}" class="mono">// weighing scalability, cost, maintainability and business needs</text>
<text x="56" y="339" font-size="12.5" fill="{P['comment']}" class="mono">// trade-offs documented, so the next person inherits the reasoning</text>
</g>"""
    defs = f"""<linearGradient id="quotebar" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{P['blue']}"/><stop offset="1" stop-color="{P['purple']}"/></linearGradient>
<linearGradient id="beamfill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{P['cyan']}" stop-opacity="0"/><stop offset=".6" stop-color="{P['cyan']}" stop-opacity=".45"/><stop offset="1" stop-color="{P['cyan']}" stop-opacity=".15"/></linearGradient>
<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<marker id="arr" viewBox="0 0 6 6" refX="5.5" refY="3" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L6 3L0 6z" fill="#383838"/></marker>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#121212"/></pattern>"""
    # left half: the words, on a transparent background (one file per GitHub theme)
    ax, ay, aw, ah = 46, 44, 622, 306
    about = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{aw}" height="{ah}" viewBox="{ax} {ay} {aw} {ah}">'
             f'<title>{esc(TITLE)}</title><style>{css}</style><defs>{defs}</defs>{text}'
             f'<g class="in" style="animation-delay:.6s">{badges}</g></svg>')
    # right half: the blueprint with the lab ducks, as a dark card
    dx, dy, dw, dh = 616, 10, 490, 318
    diagram = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{dw}" height="{dh}" viewBox="{dx} {dy} {dw} {dh}">'
               f'<title>Event-driven AWS blueprint</title><style>{css}</style><defs>{defs}'
               f'<clipPath id="card"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" rx="14"/></clipPath></defs>'
               f'<g clip-path="url(#card)"><rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="{P["bg"]}"/>'
               f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="url(#grid)"/>{architecture()}{bd_service}'
               f'{pf_duck}{bd_duck}{sr_duck}</g>'
               f'<rect x="{dx + .5}" y="{dy + .5}" width="{dw - 1}" height="{dh - 1}" rx="13.5" fill="none" stroke="{P["border"]}"/></svg>')
    light = about
    for dark_c, light_c in LIGHT_TEXT.items():
        light = light.replace(dark_c, light_c)
    diagram_light = diagram
    for dark_c, light_c in LIGHT_DIAGRAM.items():
        diagram_light = diagram_light.replace(dark_c, light_c)
    return {"about-dark": about, "about-light": light, "diagram-dark": diagram, "diagram-light": diagram_light}


# dark blueprint -> white blueprint with yellow ducks (light theme)
LIGHT_DIAGRAM = {
    P["bg"]: "#ffffff", "#121212": "#f5f6f8", "#242424": "#d0d7de", "#1e1e1e": "#e1e4e8", "#2b2b2b": "#c3c9d0",
    "#111111": "#f6f8fa", "#2c2c2c": "#cfd5dc", "#5a5a5a": "#6e7781", "#434343": "#6e7781", "#353535": "#8c959f",
    "#4b4b4b": "#6e7781", "#383838": "#9aa3ad", "#363636": "#b6bdc5", "#141414": "#f6f8fa", "#151515": "#d0d7de",
    "#050505": "#24292f", "#000000": "#24292f", "#2f2f2f": "#8c959f", "#262626": "#c3c9d0", "#202020": "#57606a",
    # duck feathers turn yellow; lab coats and suits stay light grey
    "#f2f2f2": "#ffd84d", "#d9d9d9": "#f5c02e", "#b4b4b4": "#d99a1e",
}
# dark-theme text colours -> light-theme equivalents for the transparent "about" image
LIGHT_TEXT = {"#ececec": "#1f2328", "#8c8c8c": "#57606a", "#cfcfcf": "#1f2328", "#bdbdbd": "#424a53",
              "#ffffff": "#1f2328", "#5c5c5c": "#8c959f", "#737373": "#6e7781", "#474747": "#afb8c1",
              "#4a4a4a": "#b8bec5", "#e0e0e0": "#24292f", "#888888": "#6e7781", "#23d8ea": "#0e8fa3"}


# ---------------------------------------------------------------- stats card
LANG_COLORS = {"C#": P["blue"], "CSS": P["purple"], "TypeScript": P["orange"], "SCSS": P["green"], "HTML": P["cyan"]}
LANG_FALLBACK = ["#666666", "#4f4f4f", "#3d3d3d", "#2f2f2f"]


def stats_card(user):
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
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    lang_total = sum(v for _, v in top) or 1

    stats = [
        ("contributions", cc["contributionCalendar"]["totalContributions"]),
        ("commits", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
        ("pull requests", cc["totalPullRequestContributions"]),
        ("pr reviews", cc["totalPullRequestReviewContributions"]),
        ("repositories", repos["totalCount"]),
        ("longest streak · days", best),
        ("years on github", years),
        ("active days", active),
    ]

    width, height = 820, 256
    css = font_css("sans", "mono") + BASE_CSS + (
        ".bar{transform-box:fill-box;transform-origin:left;"
        "animation:grow 1.2s cubic-bezier(.2,.8,.2,1) backwards}@keyframes grow{from{transform:scaleX(0)}}"
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [
        f'<text x="28" y="36" font-size="10.5" letter-spacing="1.7" fill="{P["muted"]}" class="mono">GITHUB · LAST 12 MONTHS</text>',
        f'<text x="{width - 28}" y="36" font-size="10" fill="{P["faint"]}" text-anchor="end" class="mono">updated {today}</text>',
    ]
    col_w = (width - 56) / 4
    for k, (label, value) in enumerate(stats):
        x = 28 + (k % 4) * col_w
        y = 82 + (k // 4) * 62
        if k % 4:
            parts.append(f'<line x1="{x - 14}" y1="{y - 26}" x2="{x - 14}" y2="{y + 12}" stroke="{P["hair"]}"/>')
        parts.append(
            f'<g class="in" style="animation-delay:{0.08 + k * 0.06:.2f}s">'
            f'<text x="{x}" y="{y}" font-size="27" font-weight="600" letter-spacing="-0.6" fill="{P["text"]}" class="sans">{value:,}</text>'
            f'<text x="{x}" y="{y + 19}" font-size="10.5" fill="{P["muted"]}" class="mono">{label}</text></g>'
        )

    bar_y, bar_w = 206, width - 56
    parts.append(f'<text x="28" y="{bar_y - 10}" font-size="10" letter-spacing="1.5" fill="{P["muted"]}" class="mono in" style="animation-delay:.6s">LANGUAGES · BY CODE SIZE</text>')
    parts.append(f'<clipPath id="lang"><rect x="28" y="{bar_y}" width="{bar_w}" height="6" rx="3"/></clipPath>')
    fallback = iter(LANG_FALLBACK * 2)
    colors = [LANG_COLORS.get(name) or next(fallback) for name, _ in top]
    seg, offset = [], 28.0
    for k, (name, size) in enumerate(top):
        w = size / lang_total * bar_w
        seg.append(f'<rect x="{offset:.1f}" y="{bar_y}" width="{w + 0.5:.1f}" height="6" fill="{colors[k]}"/>')
        offset += w
    parts.append(f'<g clip-path="url(#lang)"><g class="bar" style="animation-delay:.7s">{"".join(seg)}</g></g>')
    lx = 28.0
    for k, (name, size) in enumerate(top):
        label = f"{name} {size / lang_total * 100:.1f}%"
        parts.append(
            f'<g class="in" style="animation-delay:{0.9 + k * 0.06:.2f}s">'
            f'<rect x="{lx}" y="{bar_y + 19}" width="7" height="7" rx="1.5" fill="{colors[k]}"/>'
            f'<text x="{lx + 13}" y="{bar_y + 26}" font-size="10.5" fill="#9a9a9a" class="mono">{esc(label)}</text></g>'
        )
        lx += 13 + len(label) * 6.32 + 20
    return svg(width, height, css, "".join(parts), radius=12, title="GitHub activity")


# ---------------------------------------------------------------- activity card
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
WEEKDAYS = "Mon Tue Wed Thu Fri Sat Sun".split()


def activity_card(user):
    cc = user["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    monthly, weekday = {}, [0] * 7
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["contributionCount"]
        weekday[datetime.fromisoformat(d["date"]).weekday()] += d["contributionCount"]
    months = sorted(monthly.items())[-12:]
    mix = [
        ("commits", cc["totalCommitContributions"] + cc["restrictedContributionsCount"], "#8c8c8c"),
        ("pull requests", cc["totalPullRequestContributions"], P["blue"]),
        ("code reviews", cc["totalPullRequestReviewContributions"], P["orange"]),
        ("issues", cc["totalIssueContributions"], P["purple"]),
    ]

    width, height = 820, 300
    cycle = 13.0
    css = font_css("sans", "mono") + BASE_CSS + (
        ".gy{transform-box:fill-box;transform-origin:bottom;"
        "animation:gy .9s cubic-bezier(.2,.8,.2,1) backwards}@keyframes gy{from{transform:scaleY(0)}}"
        ".gx{transform-box:fill-box;transform-origin:left;"
        "animation:gx .9s cubic-bezier(.2,.8,.2,1) backwards}@keyframes gx{from{transform:scaleX(0)}}"
    )
    label = f'font-size="10.5" letter-spacing="1.5" fill="{P["muted"]}" class="mono"'
    parts = [
        f'<text x="28" y="36" {label}>CONTRIBUTIONS / MONTH</text>',
        f'<text x="566" y="36" {label}>CONTRIBUTION MIX</text>',
        f'<text x="566" y="196" {label}>BUSIEST WEEKDAYS</text>',
        f'<line x1="544" y1="24" x2="544" y2="{height - 24}" stroke="{P["hair"]}"/>',
    ]

    # monthly bars; the duck hops from the top of one bar to the next
    left, chart_w, base, chart_h = 28, 494, 252, 160
    pitch = chart_w / len(months)
    bar_w = pitch - 14
    peak = max(v for _, v in months) or 1
    best_ym, best_v = max(months, key=lambda kv: kv[1])
    tops = []
    for i, (ym, v) in enumerate(months):
        h = max(2, v / peak * chart_h)
        x = left + i * pitch + 7
        tops.append((x + bar_w / 2, base - h))
        fill = "url(#hot)" if ym == best_ym else "url(#cold)"
        parts.append(
            f'<rect class="gy" style="animation-delay:{i * 0.05:.2f}s" x="{x:.1f}" y="{base - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="3" fill="{fill}"><title>{v} contributions</title></rect>'
            f'<text x="{x + bar_w / 2:.1f}" y="{base + 18}" font-size="10" text-anchor="middle" fill="#575757" class="mono">'
            f'{MONTHS[int(ym[5:]) - 1]}</text>'
        )
        if ym == best_ym:  # thin purple cap marks the peak month, once the bar has grown
            parts.append(f'<rect class="in" style="animation-delay:{i * 0.05 + 0.8:.2f}s" x="{x:.1f}" y="{base - h:.1f}" '
                         f'width="{bar_w:.1f}" height="2" rx="1" fill="{P["purple"]}"/>')
    parts.append(f'<text x="{left + chart_w}" y="36" font-size="10" text-anchor="end" fill="{P["faint"]}" class="mono">'
                 f'peak: {MONTHS[int(best_ym[5:]) - 1].lower()} · {best_v}</text>')

    px = 2.4
    duck_svg, duck_w, duck_h = sprite(ASTRO, px, ASTRO_COLORS, "as")
    flame = "".join(f'<g class="jet{i}">{pixels(frame, px, JET_COLORS, dy=22)}</g>' for i, frame in enumerate(JET))
    leds = (f'<rect class="ledoff" x="{5 * px:g}" y="0" width="{px:g}" height="{px:g}" fill="#1a3c40"/>'
            f'<rect class="ledoff" style="animation-delay:-.8s" x="{2 * px:g}" y="{16 * px:g}" width="{px:g}" height="{px:g}" fill="#3a2a4a"/>')
    duck_svg = f'<g shape-rendering="crispEdges">{duck_svg}{leds}<g class="jet" opacity="0">{flame}</g></g>'
    css += (".jet0{animation:flick .16s steps(1) infinite}.jet1{animation:flick .16s -.08s steps(1) infinite}"
            "@keyframes flick{0%{opacity:1}50%{opacity:0}}"
            ".ledoff{opacity:0;animation:ledoff 1.6s steps(1) infinite}@keyframes ledoff{50%{opacity:1}}")
    anchor_x, anchor_y = duck_w / 2, duck_h + 1  # feet, centred
    seg = 0.9 / len(tops)  # last 10% of the cycle the duck fades out and resets
    frames = []
    for i, (cx, top) in enumerate(tops):
        x, y = cx - anchor_x, top - anchor_y
        p = i * seg * 100
        frames.append(f"{p:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        frames.append(f"{p + seg * 50:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}")
        if i + 1 < len(tops):
            nx, ny = tops[i + 1][0] - anchor_x, tops[i + 1][1] - anchor_y
            frames.append(f"{p + seg * 75:.2f}%{{transform:translate({(x + nx) / 2:.1f}px,{min(y, ny) - 22:.1f}px);opacity:1}}")
    lx, ly = tops[-1][0] - anchor_x, tops[-1][1] - anchor_y
    frames.append(f"95%{{transform:translate({lx:.1f}px,{ly:.1f}px);opacity:0}}")
    frames.append(f"100%{{transform:translate({tops[0][0] - anchor_x:.1f}px,{tops[0][1] - anchor_y:.1f}px);opacity:0}}")
    css += f"#duck{{animation:hop {cycle}s ease-in-out infinite}}@keyframes hop{{{''.join(frames)}}}"
    jet = ["0%{opacity:0}"]
    for i in range(len(tops) - 1):
        p = i * seg * 100
        jet += [f"{p + seg * 50 + .2:.2f}%{{opacity:1}}", f"{p + seg * 100 - .3:.2f}%{{opacity:0}}"]
    jet.append("100%{opacity:0}")
    css += f".jet{{animation:jet {cycle}s steps(1) infinite}}@keyframes jet{{{''.join(jet)}}}"
    changes = []  # pose per moment: stand (with an occasional blink), crouch before take-off, tucked in the air
    for i in range(len(tops)):
        p = i * seg * 100
        changes.append((p, "stand"))
        if i % 3 == 1:
            changes += [(p + seg * 20, "blink"), (p + seg * 26, "stand")]
        if i + 1 < len(tops):
            changes += [(p + seg * 40, "crouch"), (p + seg * 50, "tuck")]
    for name in ASTRO:
        keys, shown = [], None
        for t, frame in changes:
            if (frame == name) != shown:
                shown = frame == name
                keys.append(f"{t:.2f}%{{opacity:{1 if shown else 0}}}")
        keys.append(f"100%{{opacity:{1 if shown else 0}}}")
        base = "" if name == "stand" else "opacity:0;"
        css += f".as-{name}{{{base}animation:as-{name} {cycle}s steps(1) infinite}}@keyframes as-{name}{{{''.join(keys)}}}"

    # contribution mix: donut + legend
    total = sum(v for _, v, _ in mix) or 1
    cx, cy, r = 606, 110, 40
    circ = 2 * math.pi * r
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{P["bar"]}" stroke-width="10"/>')
    offset = 0.0
    for k, (name, v, color) in enumerate(mix):
        length = v / total * circ
        if length:
            parts.append(
                f'<circle class="in" style="animation-delay:{0.2 + k * 0.15:.2f}s" cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{color}" stroke-width="10" stroke-dasharray="{max(length - 2, 0.5):.1f} {circ:.1f}" '
                f'stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>'
            )
        offset += length
        ty = 76 + k * 24
        parts.append(
            f'<g class="in" style="animation-delay:{0.2 + k * 0.15:.2f}s">'
            f'<rect x="664" y="{ty - 7}" width="7" height="7" rx="1.5" fill="{color}"/>'
            f'<text x="678" y="{ty}" font-size="10.5" fill="#b5b5b5" class="mono">{name}</text>'
            f'<text x="{width - 28}" y="{ty}" font-size="10.5" text-anchor="end" fill="{P["muted"]}" class="mono">{v / total * 100:.0f}%</text></g>'
        )
    parts.append(f'<text x="{cx}" y="{cy + 6}" font-size="17" font-weight="600" text-anchor="middle" fill="{P["text"]}" class="sans">{total}</text>')

    # weekdays: horizontal bars, the busiest one in purple
    wd_peak = max(weekday) or 1
    for k, name in enumerate(WEEKDAYS):
        y = 212 + k * 11.5
        w = weekday[k] / wd_peak * 190
        color = P["blue"] if weekday[k] == wd_peak else "#363636"
        parts.append(
            f'<text x="566" y="{y + 7}" font-size="9.5" fill="#575757" class="mono">{name}</text>'
            f'<rect x="600" y="{y}" width="190" height="7" rx="3.5" fill="{P["bar"]}"/>'
            f'<rect class="gx" style="animation-delay:{0.3 + k * 0.06:.2f}s" x="600" y="{y}" width="{max(w, 1):.1f}" '
            f'height="7" rx="3.5" fill="{color}"><title>{weekday[k]} contributions</title></rect>'
        )

    body = f"""<defs>
<linearGradient id="cold" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2c2c2c"/><stop offset="1" stop-color="#1a1a1a"/></linearGradient>
<linearGradient id="hot" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#8a8a8a"/><stop offset="1" stop-color="#3a3a3a"/></linearGradient>
</defs>
{''.join(parts)}
<g id="duck">{duck_svg}</g>"""
    return svg(width, height, css, body, radius=12, title="Contributions per month, contribution mix and busiest weekdays")


def main():
    user = fetch()
    os.makedirs(OUT, exist_ok=True)
    files = hero(user)
    files.update({"stats": stats_card(user), "activity": activity_card(user)})
    for name, content in files.items():
        with open(os.path.join(OUT, f"{name}.svg"), "w") as f:
            f.write(content)
    print(f"wrote SVGs to {OUT}/")


if __name__ == "__main__":
    main()
