#!/usr/bin/env python3
"""
LEGACY — NOT THE BUILD STEP. Superseded 2026-08-22 by build_neural_map.js.

This file carries its own hardcoded node/edge tables (21 nodes, data state 2026-08-10).
It does NOT read map_source.json, and it does NOT write neural_svg.frag or
neural_data.json — it emits a standalone HTML sheet to an absolute path that does not
exist outside the machine it was written on. Running it will not update the site and
will leave the map silently stale.

To regenerate the map:  node src/build_neural_map.js

Kept only as the transcription of record for the original design tokens and the
canonical coordinates, which map_source.json inherited.

THE ARCHITECTURE — Neural Map renderer (original).

Rebuilt from the canonical DATA STATE recorded in Google Drive file
1ivWJ7K_26TdoBF0FSXTANMpeXuj2vVge
("network_map_2026-08-10_GENERATOR (build_map3.py - regenerates PNG+HTML exactly)").

Node coordinates, node subtitles, the full edge list with evidence grades and
labels, the footer text, and the colour/stroke design tokens are transcribed
verbatim from that record. Node radii and the typeface were not present in the
retrievable portion of that record and are reconstructed here.
"""

import math

# ----------------------------------------------------------------------------
# DESIGN TOKENS - verbatim from the canonical record
# ----------------------------------------------------------------------------
BG      = "#141210"
INK     = "#e9e3d6"
SOFT    = "#b9b0a0"
FAINT   = "#8a8172"
AMBER   = "#d98a2b"
AMBER_HI= "#e9a94e"
RED     = "#c0562f"
RULE    = "#3a352d"
RULE_2  = "#2a2620"

# Edge treatments - verbatim: [A] solid amber 3.0 | [B] solid faint 2.2
#                             [C] dashed 9,7 red  | [O] dotted 2,7 faint
GRADE = {
    "A": dict(stroke=AMBER, width=3.0, dash=None,    label="documented"),
    "B": dict(stroke=FAINT, width=2.2, dash=None,    label="reported"),
    "C": dict(stroke=RED,   width=2.0, dash="9,7",   label="alleged / denied"),
    "O": dict(stroke=FAINT, width=2.0, dash="2,7",   label="adjacency"),
}

CURRENT_THROUGH = "2026-08-10"

# ----------------------------------------------------------------------------
# NODES - (x, y) and subtitle verbatim from the canonical record.
# radius reconstructed: tiered by structural role.
# ----------------------------------------------------------------------------
NODES = {
    "TRUMP":    (850,  790,  84, "THE PRINCIPAL", ""),
    "WLF":      (545,  505,  60, "WLF", "family crypto · $1.4B+ 2025 income"),
    "SONS":     (1170, 505,  60, "SONS", "1789 · ABTC · 9 new Form D vehicles (Jun)"),
    "KUSHNER":  (395,  720,  56, "KUSHNER", "envoy · $4.8B Gulf money"),
    "WITKOFF":  (505,  985,  56, "WITKOFF", "envoy father · WLF sons · $130M"),
    "UAE":      (255,  360,  48, "UAE", "49% WLF pre-inauguration · chips"),
    "SAUDI":    (150,  590,  48, "SAUDI", "Affinity base · 123 nuclear approved"),
    "QATAR":    (205,  880,  48, "QATAR", "$400M jet · $5.5B golf"),
    "PAKISTAN": (330,  1135, 48, "PAKISTAN", "WLF deal Jan 2026 · war mediator"),
    "ZHAO":     (640,  265,  48, "ZHAO", "$2B in USD1 → pardon"),
    "POLY":     (1030, 250,  48, "POLYMARKET", "98% win rate · unidentified"),
    "VAULT":    (1330, 275,  54, "PROJECT VAULT", "demand floor · shielded reserve · DPA 101"),
    "PENTAGON": (1490, 480,  52, "PENTAGON", "11/15 defense startups = 1789"),
    "DOJ":      (1435, 700,  54, "DOJ", "BLANCHE AG · confirmed 50–49 · Comey/James dismissed"),
    "PULTE":    (1400, 945,  50, "PULTE", "FHFA · referrals stand · DNI stint → Clayton 51–47"),
    "ICE":      (1185, 1120, 50, "ICE", "$45B · no-bid · Palantir layer"),
    "SCOTUS":   (925,  1210, 52, "SCOTUS", "obeyed twice · Callais gutted VRA"),
    "IRAN":     (655,  1205, 52, "IRAN", "Senate check collapsed 47–49 · 49–50"),
    "VZ":       (860,  300,  48, "VENEZUELA", "US-controlled revenue"),
    "RUSSIA":   (355,  245,  48, "RUSSIA", "plan co-drafted · sanctions passed 86–11"),
    "P2025":    (1085, 905,  50, "PROJECT 2025", "53% executed · Vought"),
}

# Nodes new or updated in this window - drawn with a highlight ring
NEW_NODES     = {"VAULT"}
UPDATED_NODES = {"DOJ", "PULTE", "IRAN", "RUSSIA"}

# ----------------------------------------------------------------------------
# EDGES - (source, target, grade, label) verbatim from the canonical record
# ----------------------------------------------------------------------------
EDGES = [
    ("TRUMP", "WLF",      "A", "75% of coin revenue"),
    ("UAE",   "WLF",      "A", "$2B MGX in USD1"),
    ("UAE",   "WLF",      "B", "49%/$500M secret"),
    ("SAUDI", "KUSHNER",  "A", "fund base + leverage"),
    ("SAUDI", "KUSHNER",  "O", "123 ↔ Affinity adjacency"),
    ("TRUMP", "SAUDI",    "A", "123 pact · PD 2026-18"),
    ("KUSHNER","IRAN",    "A", "US negotiator"),
    ("WITKOFF","WLF",     "A", "co-founders"),
    ("WITKOFF","RUSSIA",  "A", "28-pt co-draft"),
    ("WITKOFF","RUSSIA",  "C", "coached Ushakov"),
    ("PAKISTAN","WLF",    "A", "Jan 2026 deal"),
    ("PAKISTAN","IRAN",   "O", "mediator adjacency"),
    ("QATAR", "TRUMP",    "A", "jet → library 2029"),
    ("ZHAO",  "WLF",      "A", "boosted"),
    ("TRUMP", "ZHAO",     "A", "pardon Oct 23"),
    ("ZHAO",  "TRUMP",    "C", "quid pro quo (denied)"),
    ("POLY",  "IRAN",     "A", "$1M pre-strike bets"),
    ("POLY",  "TRUMP",    "O", "holders unknown"),
    ("SONS",  "PENTAGON", "A", "defense portfolio"),
    ("TRUMP", "PENTAGON", "A", "$1.5T request"),
    ("TRUMP", "VAULT",    "A", "EO 14415 + DPA 101"),
    ("SONS",  "VAULT",    "O", "no position located · tickers: EMAT / REEMF"),
    ("TRUMP", "DOJ",      "A", "directed cases"),
    ("DOJ",   "SCOTUS",   "A", "dismissals upheld*"),
    ("TRUMP", "PULTE",    "A", "acting-DNI stint → superseded"),
    ("PULTE", "DOJ",      "A", "referrals: Schiff/James/Cook"),
    ("TRUMP", "ICE",      "A", "$45B build-out"),
    ("ICE",   "SONS",     "O", "patronage adjacency"),
    ("TRUMP", "IRAN",     "A", "war past Congress"),
    ("TRUMP", "VZ",       "A", "Maduro seized · oil"),
    ("P2025", "TRUMP",    "A", "blueprint 53%"),
    ("SCOTUS","TRUMP",    "A", "checked: tariffs/birthright"),
    ("TRUMP", "SONS",     "A", "family"),
    ("TRUMP", "KUSHNER",  "A", "family envoy"),
    ("TRUMP", "WITKOFF",  "A", "friend envoy"),
]

FOOTER_NOTE = (
    '* “dismissals upheld” reflects district rulings; DOJ appeals pending. '
    'A propagandist draws the dotted edges solid. An investigator marks them '
    'dotted — and names who could make them solid.'
)
FOOTER_UNDRAWN = (
    'UN-DRAWN BY DESIGN: wallet identities, WLFI stake buyers, any envoy market '
    'position, any family/1789 position in EMAT or REEMF. Identification would '
    'reprice the entire map.'
)
FOOTER_LEDGER = (
    'SINCE 2026-07-19 (Briefs 1–2, all primary-record): Senate war check collapsed '
    '(47–49 · 49–50) · Blanche confirmed AG 50–49 · Clayton confirmed DNI 51–47 · '
    'Saudi 123 approved · EO 14415 / Project Vault + DPA 101 (tickers now on the '
    'dotted edge) · federal photo-ID mandate blocked 52–46 · Russia sanctions 86–11 · '
    'no shutdown this cycle (CR 90–6).'
)

# ----------------------------------------------------------------------------
# Geometry helpers
# ----------------------------------------------------------------------------
PAD_X, PAD_TOP, PAD_BOT = 210, 150, 150
xs = [n[0] for n in NODES.values()]
ys = [n[1] for n in NODES.values()]
MIN_X, MAX_X = min(xs), max(xs)
MIN_Y, MAX_Y = min(ys), max(ys)
VB_X = MIN_X - PAD_X
VB_Y = MIN_Y - PAD_TOP
VB_W = (MAX_X - MIN_X) + PAD_X * 2
VB_H = (MAX_Y - MIN_Y) + PAD_TOP + PAD_BOT


def trim_to_rims(x1, y1, r1, x2, y2, r2, extra=4):
    """Shorten a segment so it starts and ends at the node rims, not the centres."""
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy) or 1.0
    ux, uy = dx / d, dy / d
    return (x1 + ux * (r1 + extra), y1 + uy * (r1 + extra),
            x2 - ux * (r2 + extra), y2 - uy * (r2 + extra))


def parallel_offset(pairs):
    """Assign a perpendicular offset to each edge in a duplicated node pair."""
    seen = {}
    out = []
    for i, (s, t, g, lab) in enumerate(pairs):
        key = tuple(sorted((s, t)))
        seen.setdefault(key, []).append(i)
    offsets = [0.0] * len(pairs)
    for key, idxs in seen.items():
        if len(idxs) == 1:
            continue
        spread = 34.0
        start = -spread * (len(idxs) - 1) / 2.0
        for k, i in enumerate(idxs):
            offsets[i] = start + k * spread
    return offsets


def node_obstacles():
    """Fixed boxes the edge labels must not sit on: node discs + their subtitles."""
    obs = []
    for key, (x, y, r, name, sub) in NODES.items():
        obs.append(dict(x=x, y=y, w=2 * r + 10, h=2 * r + 10))
        lines = wrap(sub, 30)
        if lines:
            w = max(len(l) for l in lines) * 5.6 + 14
            h = len(lines) * 14 + 8
            obs.append(dict(x=x, y=y + r + 19 + (len(lines) - 1) * 7 - 4, w=w, h=h))
    return obs


def resolve_label_collisions(labels, iterations=400):
    """
    Relax label positions on both axes: repel from each other and from the fixed
    node/subtitle boxes, while a spring holds each label near its edge midpoint.
    400 iterations, per the canonical record.
    """
    obs = node_obstacles()

    def overlap(a, b, padx=9.0, pady=7.5):
        dx = b["x"] - a["x"]
        dy = b["y"] - a["y"]
        ox = (a["w"] + b["w"]) / 2 + padx - abs(dx)
        oy = (a["h"] + b["h"]) / 2 + pady - abs(dy)
        if ox > 0 and oy > 0:
            return dx, dy, ox, oy
        return None

    for it in range(iterations):
        moved = False
        cool = 1.0 - (it / iterations) * 0.55

        # label <-> label
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = labels[i], labels[j]
                hit = overlap(a, b)
                if not hit:
                    continue
                dx, dy, ox, oy = hit
                if oy <= ox:                       # cheaper to separate vertically
                    push = (oy * 0.62 + 1.0) * cool
                    s = 1.0 if dy >= 0 else -1.0
                    a["y"] -= push * s
                    b["y"] += push * s
                else:
                    push = (ox * 0.62 + 1.0) * cool
                    s = 1.0 if dx >= 0 else -1.0
                    a["x"] -= push * s
                    b["x"] += push * s
                moved = True

        # label <-> fixed node / subtitle boxes
        for L in labels:
            for O in obs:
                hit = overlap(L, O, padx=9.0, pady=8.0)
                if not hit:
                    continue
                dx, dy, ox, oy = hit
                if oy <= ox:
                    s = 1.0 if dy >= 0 else -1.0
                    L["y"] -= (oy * 1.15 + 1.2) * cool * s
                else:
                    s = 1.0 if dx >= 0 else -1.0
                    L["x"] -= (ox * 1.15 + 1.2) * cool * s
                moved = True

        # spring back toward the edge midpoint so labels stay near their edge
        for L in labels:
            L["x"] += (L["ax"] - L["x"]) * 0.022
            L["y"] += (L["ay"] - L["y"]) * 0.022

        if not moved and it > 40:
            break
    return labels


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def wrap(text, width):
    """Naive word wrap into a list of lines."""
    if not text:
        return []
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------------------
# Build SVG
# ----------------------------------------------------------------------------
def build_svg():
    parts = []
    offsets = parallel_offset(EDGES)

    # --- edges -------------------------------------------------------------
    label_specs = []
    edge_paths = []
    for i, (s, t, g, lab) in enumerate(EDGES):
        x1, y1, r1 = NODES[s][0], NODES[s][1], NODES[s][2]
        x2, y2, r2 = NODES[t][0], NODES[t][1], NODES[t][2]
        sx, sy, ex, ey = trim_to_rims(x1, y1, r1, x2, y2, r2)

        dx, dy = ex - sx, ey - sy
        d = math.hypot(dx, dy) or 1.0
        px, py = -dy / d, dx / d          # perpendicular unit vector
        off = offsets[i]
        mx = (sx + ex) / 2 + px * off
        my = (sy + ey) / 2 + py * off

        st = GRADE[g]
        dash = f' stroke-dasharray="{st["dash"]}"' if st["dash"] else ""
        if abs(off) > 0.01:
            path = f'M {sx:.1f} {sy:.1f} Q {mx:.1f} {my:.1f} {ex:.1f} {ey:.1f}'
        else:
            path = f'M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}'
        edge_paths.append(
            f'<path d="{path}" fill="none" stroke="{st["stroke"]}" '
            f'stroke-width="{st["width"]}" stroke-linecap="round"{dash} '
            f'opacity="{0.95 if g == "A" else 0.8}"/>'
        )

        # label anchor sits at the curve midpoint
        lx = (sx + ex) / 2 + px * off * 0.5
        ly = (sy + ey) / 2 + py * off * 0.5
        w = len(lab) * 5.9 + 20
        label_specs.append(dict(x=lx, y=ly, ax=lx, ay=ly, w=w, h=20,
                                text=lab, grade=g))

    parts.extend(edge_paths)

    # --- edge labels (pills, horizontal) -----------------------------------
    label_specs = resolve_label_collisions(label_specs)
    for L in label_specs:
        colour = AMBER_HI if L["grade"] == "A" else (RED if L["grade"] == "C" else SOFT)
        drift = math.hypot(L["x"] - L["ax"], L["y"] - L["ay"])
        if drift > 16:
            parts.append(
                f'<line x1="{L["ax"]:.1f}" y1="{L["ay"]:.1f}" '
                f'x2="{L["x"]:.1f}" y2="{L["y"]:.1f}" stroke="{RULE}" '
                f'stroke-width="0.9" stroke-dasharray="1,4" opacity="0.75"/>'
            )
        parts.append(
            f'<g><rect x="{L["x"] - L["w"]/2:.1f}" y="{L["y"] - 10:.1f}" '
            f'width="{L["w"]:.1f}" height="20" rx="10" fill="{BG}" '
            f'stroke="{RULE}" stroke-width="1" opacity="0.94"/>'
            f'<text x="{L["x"]:.1f}" y="{L["y"] + 4:.1f}" text-anchor="middle" '
            f'font-size="11.5" fill="{colour}" letter-spacing="0.02em">'
            f'{esc(L["text"])}</text></g>'
        )

    # --- nodes -------------------------------------------------------------
    for key, (x, y, r, name, sub) in NODES.items():
        is_core = key == "TRUMP"
        ring = AMBER_HI if key in NEW_NODES else (AMBER if key in UPDATED_NODES else RULE)
        ring_w = 2.6 if (key in NEW_NODES or key in UPDATED_NODES) else 1.6
        fill = AMBER if is_core else BG

        if key in NEW_NODES:
            parts.append(
                f'<circle cx="{x}" cy="{y}" r="{r + 9}" fill="none" '
                f'stroke="{AMBER_HI}" stroke-width="1" stroke-dasharray="3,5" opacity="0.55"/>'
            )
        parts.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
            f'stroke="{ring}" stroke-width="{ring_w}"/>'
        )

        # node name inside the circle
        name_lines = wrap(name, 11)
        n_fs = 15 if is_core else 13
        start_y = y - (len(name_lines) - 1) * (n_fs * 0.58)
        for li, line in enumerate(name_lines):
            parts.append(
                f'<text x="{x}" y="{start_y + li * (n_fs + 2) + n_fs * 0.35:.1f}" '
                f'text-anchor="middle" font-size="{n_fs}" font-weight="700" '
                f'letter-spacing="0.09em" fill="{BG if is_core else INK}">'
                f'{esc(line)}</text>'
            )

        # subtitle beneath the circle, on an opaque backing so edges don't cut it
        sub_lines = wrap(sub, 30)
        for li, line in enumerate(sub_lines):
            ty = y + r + 19 + li * 14
            bw = len(line) * 5.6 + 12
            parts.append(
                f'<rect x="{x - bw/2:.1f}" y="{ty - 10:.1f}" width="{bw:.1f}" '
                f'height="14" fill="{BG}" opacity="0.92"/>'
                f'<text x="{x}" y="{ty}" text-anchor="middle" '
                f'font-size="11" fill="{FAINT}">{esc(line)}</text>'
            )

    return "\n".join(parts)


# ----------------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------------
def build_html():
    svg_body = build_svg()

    legend = "".join(
        f'<div class="lg-item">'
        f'<svg width="46" height="12">'
        f'<line x1="2" y1="6" x2="44" y2="6" stroke="{v["stroke"]}" '
        f'stroke-width="{v["width"]}" '
        f'{f"stroke-dasharray=\"{v['dash']}\"" if v["dash"] else ""} '
        f'stroke-linecap="round"/></svg>'
        f'<span class="lg-k">[{k}]</span>'
        f'<span class="lg-v">{v["label"]}</span></div>'
        for k, v in GRADE.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>THE ARCHITECTURE — Neural Map — current through {CURRENT_THROUGH}</title>
<style>
  @page {{ size: 1700px 1500px; margin: 0; }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0; padding: 0; background: {BG}; color: {INK};
    font-family: Georgia, "Times New Roman", "DejaVu Serif", serif;
    -webkit-font-smoothing: antialiased;
  }}
  .sheet {{ width: 1700px; margin: 0 auto; padding: 46px 58px 40px; background: {BG}; }}

  .eyebrow {{
    font-size: 11.5px; letter-spacing: .22em; text-transform: uppercase;
    color: {AMBER}; font-weight: 700; margin-bottom: 16px;
  }}
  h1 {{
    margin: 0; font-size: 60px; line-height: .96; letter-spacing: -.02em;
    font-weight: 700; color: {INK};
  }}
  .deck {{
    margin-top: 12px; font-size: 17px; color: {SOFT}; max-width: 900px;
    line-height: 1.45; font-style: italic;
  }}
  .rule {{ height: 1px; background: {RULE}; margin: 26px 0 0; }}

  .legend {{
    display: flex; gap: 34px; align-items: center;
    padding: 16px 0 18px; border-bottom: 1px solid {RULE_2};
    flex-wrap: wrap;
  }}
  .lg-item {{ display: flex; align-items: center; gap: 9px; }}
  .lg-k {{ font-size: 11px; font-weight: 700; color: {SOFT}; letter-spacing: .1em; }}
  .lg-v {{ font-size: 12px; color: {FAINT}; letter-spacing: .04em; }}
  .lg-spacer {{ flex: 1; }}
  .lg-note {{ font-size: 11px; color: {FAINT}; letter-spacing: .12em; text-transform: uppercase; }}

  .map {{ width: 100%; display: block; margin: 8px 0 0; }}

  footer {{ border-top: 1px solid {RULE}; margin-top: 10px; padding-top: 20px; }}
  .f-note {{ font-size: 12.5px; color: {SOFT}; line-height: 1.6; max-width: 1180px; }}
  .f-undrawn {{
    font-size: 11.5px; color: {FAINT}; line-height: 1.6; margin-top: 12px;
    max-width: 1180px; letter-spacing: .02em;
  }}
  .f-ledger {{
    font-size: 11.5px; color: {AMBER}; line-height: 1.65; margin-top: 16px;
    padding-top: 14px; border-top: 1px solid {RULE_2};
  }}
  .stamp {{
    margin-top: 18px; font-size: 10.5px; letter-spacing: .2em;
    text-transform: uppercase; color: {FAINT};
  }}
</style>
</head>
<body>
<div class="sheet">

  <div class="eyebrow">
    Updated weekly · Current through {CURRENT_THROUGH} · Research series since spring 2026
    · This synthesis first compiled 2026-07-19
  </div>

  <h1>THE ARCHITECTURE</h1>
  <div class="deck">
    The neural map — power, money, and ideology in the second Trump era.
    Every solid edge resolves to a primary record. Every dotted edge is an
    adjacency that the record has not yet closed.
  </div>

  <div class="rule"></div>

  <div class="legend">
    {legend}
    <div class="lg-spacer"></div>
    <div class="lg-note">21 nodes · {len(EDGES)} edges</div>
  </div>

  <svg class="map" viewBox="{VB_X} {VB_Y} {VB_W} {VB_H}"
       xmlns="http://www.w3.org/2000/svg">
    {svg_body}
  </svg>

  <footer>
    <div class="f-note">{esc(FOOTER_NOTE)}</div>
    <div class="f-undrawn">{esc(FOOTER_UNDRAWN)}</div>
    <div class="f-ledger">{esc(FOOTER_LEDGER)}</div>
    <div class="stamp">
      THE ARCHITECTURE · Neural Map · Data state {CURRENT_THROUGH} ·
      Kirk Musick, MS, MBA · ZINC Digital
    </div>
  </footer>

</div>
</body>
</html>"""


if __name__ == "__main__":
    html = build_html()
    out = "/home/claude/THE_ARCHITECTURE_CURRENT_neural_map.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out} ({len(html):,} bytes)")
