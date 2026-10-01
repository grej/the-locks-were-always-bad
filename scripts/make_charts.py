"""Render the article's four charts as static SVG + PNG.

Usage (from the repo root):
    python scripts/make_charts.py            # dark theme only -> images/NN-name-dark.{svg,png}
    python scripts/make_charts.py --theme light
    python scripts/make_charts.py --theme all

Requires: pip install playwright && playwright install chromium
"""
import argparse, math, pathlib
from playwright.sync_api import sync_playwright

OUT = pathlib.Path(__file__).resolve().parent.parent / "images"
THEMES = {
    # name: (suffix, background, TXT, SEC, ACC, MUT, GRID)
    "light": ("", "white", "#1a1a1a", "#666666", "#2f6fdb", "#c4c3b8", "#e6e6e6"),
    "dark": ("-dark", "#0d1117", "#e6edf3", "#9198a1", "#5b9bff", "#565d68", "#30363d"),
}
BG = TXT = SEC = ACC = MUT = GRID = None
FONT = "font-family='Inter, Helvetica, Arial, sans-serif'"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def svg(w, h, body, label, fs=13):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' width='{w}' height='{h}' "
            f"role='img' aria-label=\"{esc(label)}\" {FONT} font-size='{fs}'>"
            f"<rect width='{w}' height='{h}' fill='{BG}'/>{body}</svg>")


def title(t, sub, y=30):
    return (f"<text x='20' y='{y}' font-size='17' font-weight='600' fill='{TXT}'>{esc(t)}</text>"
            f"<text x='20' y='{y + 22}' fill='{SEC}'>{esc(sub)}</text>")


def foot(lines, y):
    return "".join(f"<text x='20' y='{y + 20 * i}' font-size='12' fill='{SEC}'>{esc(l)}</text>" for i, l in enumerate(lines))


def chart_slope():
    rows = [("Never-solved tasks", 198, 93, True), ("Other tasks", 700, 7, False)]
    total = sum(r[1] for r in rows)
    xL, xR, y0, y1 = 250, 540, 120, 330
    y = lambda v: y1 - v / 100 * (y1 - y0)
    t = "Never-solved tasks were 22% of the benchmark and 93% of the tasks discussed"
    b = title(t, f"ExploitGym, as OpenAI ran it: 198 of {total} tasks had never been solved by any model")
    b += (f"<text x='{xL}' y='95' text-anchor='middle' font-weight='600' fill='{SEC}'>Share of the benchmark</text>"
          f"<text x='{xR}' y='95' text-anchor='middle' font-weight='600' fill='{SEC}'>Share of tasks discussed on the board</text>"
          f"<line x1='{xL}' x2='{xL}' y1='{y0-8}' y2='{y1+8}' stroke='{GRID}'/><line x1='{xR}' x2='{xR}' y1='{y0-8}' y2='{y1+8}' stroke='{GRID}'/>")
    for name, n, board, hot in rows:
        s = round(n / total * 100); c = ACC if hot else MUT; fw = 600 if hot else 400
        b += (f"<line x1='{xL}' x2='{xR}' y1='{y(s)}' y2='{y(board)}' stroke='{c}' stroke-width='{3.5 if hot else 2.5}'/>"
              f"<circle cx='{xL}' cy='{y(s)}' r='6' fill='{c}'/><circle cx='{xR}' cy='{y(board)}' r='6' fill='{c}'/>"
              f"<text x='{xL-14}' y='{y(s)+5}' text-anchor='end' font-weight='{fw}' fill='{TXT}'>{name}  {s}%</text>"
              f"<text x='{xR+14}' y='{y(board)+5}' font-weight='{fw}' fill='{TXT}'>{board}%  {name.lower()}</text>")
    b += foot(["“Never solved” means no model had produced a correct answer, not that a task was proven impossible.",
               "Source: OpenAI – Hugging Face Incident Technical Report"], 375)
    return svg(760, 410, b, t)


def chart_phases():
    rows = [("Payload staging", 6972, True), ("Reconnaissance", 6191, True), ("Shell commands", 2911, False),
            ("Internal network pivot", 115, False), ("Command and control", 114, False), ("Kubernetes access", 87, False),
            ("Source-control supply chain", 69, False), ("Data exfiltration", 56, False), ("Evasion", 6, False)]
    total = sum(r[1] for r in rows); focus = sum(r[1] for r in rows if r[2]); peak = rows[0][1]
    xs, w, y0, rh = 250, 400, 92, 30
    t = "Most recorded actions were reconnaissance or payload staging"
    b = title(t, f"Hugging Face’s phase table, {total:,} actions. Reconnaissance and staging: {focus:,} ({round(focus/total*100)}%).")
    for i, (name, n, hot) in enumerate(rows):
        bw = max(1.5, n / peak * w); yy = y0 + i * rh
        b += (f"<text x='{xs-12}' y='{yy+15}' text-anchor='end' font-weight='{600 if hot else 400}' fill='{TXT if hot else SEC}'>{name}</text>"
              f"<rect x='{xs}' y='{yy+3}' width='{bw}' height='{rh-10}' fill='{ACC if hot else MUT}'/>"
              f"<text x='{xs+bw+8}' y='{yy+15}' fill='{TXT}'>{n:,}</text>")
    yEnd = y0 + len(rows) * rh
    b += foot(["Phases describe activity, not whether it succeeded. Hugging Face’s headline total of reconstructed actions is about 17,600.",
               "Source: Hugging Face, Anatomy of a Frontier Lab Agent Intrusion"], yEnd + 24)
    return svg(760, yEnd + 70, b, t)


def chart_tripwire():
    series = [("1 in 1,000 actions", 0.001, 1.0), ("1 in 10,000 actions", 0.0001, 0.45)]
    marks = [(200, "200-action example", "start"), (17600, "size of the Hugging Face campaign", "end")]
    ticks = [200, 1000, 5000, 17600]
    lo, hi, x0, x1, y0, y1 = 120, 25000, 130, 590, 90, 300
    lx = lambda n: x0 + (math.log10(n) - math.log10(lo)) / (math.log10(hi) - math.log10(lo)) * (x1 - x0)
    y = lambda v: y1 - v * (y1 - y0)
    prob = lambda p, n: 1 - (1 - p) ** n
    fmt = lambda v: ">99.99%" if v > 0.9999 else f"{round(v*100)}%"
    t = "More actions, more chances to trip a wire (hypothetical)"
    b = title(t, "Chance an attacker sets off at least one tripwire, by number of actions taken", y=32)
    for v in (0, 0.5, 1):
        b += (f"<line x1='{x0}' x2='{x1}' y1='{y(v)}' y2='{y(v)}' stroke='{GRID}'/>"
              f"<text x='{x0-12}' y='{y(v)+4}' text-anchor='end' fill='{SEC}'>{int(v*100)}%</text>")
    for n in ticks:
        b += f"<text x='{lx(n):.1f}' y='{y1+20}' text-anchor='middle' fill='{SEC}'>{n:,}</text>"
    for n, lab, anchor in marks:
        b += f"<text x='{lx(n):.1f}' y='{y1+38}' text-anchor='{anchor}' font-size='12' fill='{SEC}'>{lab}</text>"
    b += f"<text x='{(x0+x1)/2}' y='{y1+62}' text-anchor='middle' fill='{SEC}'>Attacker actions (logarithmic scale)</text>"
    samples = [lo * (hi / lo) ** (k / 60) for k in range(61)]
    for name, p, op in series:
        d = " ".join(f"{'M' if k == 0 else 'L'}{lx(n):.1f},{y(prob(p, n)):.1f}" for k, n in enumerate(samples))
        b += f"<path d='{d}' fill='none' stroke='{ACC}' stroke-opacity='{op}' stroke-width='2.5'/>"
        for n, _, _ in marks:
            b += f"<circle cx='{lx(n):.1f}' cy='{y(prob(p, n)):.1f}' r='5' fill='{ACC}' fill-opacity='{op}'/>"
        nf, nl = marks[0][0], marks[-1][0]
        b += (f"<text x='{lx(nf)-12:.1f}' y='{y(prob(p, nf))+4:.1f}' text-anchor='end' fill='{TXT}'>{fmt(prob(p, nf))}</text>"
              f"<text x='{lx(nl)-10:.1f}' y='{y(prob(p, nl))-10:.1f}' text-anchor='end' font-weight='600' fill='{TXT}'>{esc(fmt(prob(p, nl)))}</text>"
              f"<text x='{x1+14}' y='{y(prob(p, nl))+4:.1f}' fill='{TXT}'>{name}</text>")
    b += foot(["Hypothetical model: every action has the same independent chance of hitting a tripwire. Not measured detection rates.",
               "17,600 is the number of attacker actions Hugging Face reconstructed."], 398)
    return svg(760, 430, b, t)


def chart_timeline():
    rows = [("May 12", "First note in the cache (a training run)", None, False),
            ("May 26", "Agents reach the internet through the cache", "A team sees board activity", False),
            ("Jun 26", "Agents take admin control of the cache", None, False),
            ("Jun 27", None, "Alert traced to the board; run continues", False),
            ("Jul 5", None, "Cache taken offline, credentials revoked", False),
            ("Jul 7", None, "Evaluations resume", False),
            ("Jul 8", "New board, new way out", None, False),
            ("Jul 9–13", "Hugging Face break-in", None, True),
            ("Jul 19–20", None, "New alert; link to Hugging Face found", False)]
    y0, rh, xA, xO = 122, 34, 130, 450
    yr = lambda i: y0 + i * rh
    yEnd = yr(len(rows) - 1)
    t = "Warning signs preceded the July intrusion, and containment didn’t hold"
    b = title(t, "OpenAI’s evaluation environment, 2026. Rows are in date order, not to scale.")
    b += (f"<text x='{xA-6}' y='92' font-weight='600' fill='{SEC}'>What the agents did</text>"
          f"<text x='{xO-6}' y='92' font-weight='600' fill='{ACC}'>What OpenAI saw and did</text>"
          f"<line x1='{xA}' x2='{xA}' y1='{y0-14}' y2='{yEnd+10}' stroke='{GRID}'/><line x1='{xO}' x2='{xO}' y1='{y0-14}' y2='{yEnd+10}' stroke='{GRID}'/>")
    for i, (d, ag, oa, emph) in enumerate(rows):
        b += f"<text x='20' y='{yr(i)+4}' font-weight='600' fill='{SEC}'>{d}</text>"
        if ag:
            b += (f"<circle cx='{xA}' cy='{yr(i)}' r='{7 if emph else 5.5}' fill='{TXT if emph else MUT}'/>"
                  f"<text x='{xA+14}' y='{yr(i)+4}' font-weight='{600 if emph else 400}' fill='{TXT if emph else SEC}'>{esc(ag)}</text>")
        if oa:
            b += (f"<circle cx='{xO}' cy='{yr(i)}' r='5.5' fill='{ACC}'/>"
                  f"<text x='{xO+14}' y='{yr(i)+4}' fill='{TXT}'>{esc(oa)}</text>")
    b += foot(["Source: OpenAI – Hugging Face Incident Technical Report; Hugging Face technical timeline"], yEnd + 50)
    return svg(760, yEnd + 76, b, t, fs=12.5)


def render(theme, pg):
    global BG, TXT, SEC, ACC, MUT, GRID
    suffix, BG, TXT, SEC, ACC, MUT, GRID = THEMES[theme]
    charts = {"01-never-solved-tasks": chart_slope(), "02-actions-by-phase": chart_phases(),
              "03-tripwire-odds": chart_tripwire(), "04-warning-signs": chart_timeline()}
    for name, s in charts.items():
        (OUT / f"{name}{suffix}.svg").write_text(s)
        w, h = [float(v) for v in s.split("viewBox='0 0 ")[1].split("'")[0].split()]
        pg.set_viewport_size({"width": int(w), "height": int(h)})
        pg.set_content(f"<html><body style='margin:0'>{s}</body></html>")
        pg.screenshot(path=str(OUT / f"{name}{suffix}.png"), clip={"x": 0, "y": 0, "width": w, "height": h})
        print("wrote", OUT / f"{name}{suffix}.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", choices=["dark", "light", "all"], default="dark")
    themes = ["light", "dark"] if (t := ap.parse_args().theme) == "all" else [t]
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(device_scale_factor=2)
        for th in themes:
            render(th, pg)
        br.close()
