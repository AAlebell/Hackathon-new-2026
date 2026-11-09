"""System core map drawn as SVG. This is the only HTML the app builds, every label is escaped."""

import math
from html import escape
from textwrap import wrap

SIZE = 360
CENTRE = SIZE / 2
MARGIN = 6
CORE_SHARE = 0.25  # the core disc takes this share of the radius
FULL_TURN = 2 * math.pi
RING_ORDER = ("core", "sensitive", "inner", "outer")  # from the centre outwards
# Each ring is a step of one blue ramp: the closer to the centre, the darker, the more it is worth.
RING_FILL = {"outer": ("--t0", "#dce9f7"), "inner": ("--t1", "#afcbee"),
             "sensitive": ("--t2", "#5f93d6"), "core": ("--t3", "#1f4f92")}
DARK_RINGS = ("sensitive", "core")  # these get white text
LINE_HEIGHT = 12
LABEL_WIDTH = 11
FONT_SIZE = 10.5
LOST_MARK = {"outer": "⊘ refused"}  # a lost outer zone is a refused customer
SECRET_LOST_MARK = "✕ leaked"  # a lost inner, sensitive or core zone is a leaked secret
SERVED_MARK = "✓ served"
SAFE_MARK = "✓ safe"
FOCUS_COLOR = {"target": ("--bad", "#b4302a"), "asking": ("--accent", "#1a5da8")}
Geometry = tuple[float, float, float, float]  # r_in, r_out, start angle, end angle


def _var(token: tuple[str, str]) -> str:
    """Return a CSS colour that follows the theme variable and falls back to a fixed colour."""
    return f"var({token[0]},{token[1]})"


def _point(radius: float, angle: float) -> tuple[float, float]:
    """Return the x, y position of a polar coordinate around the centre."""
    return CENTRE + radius * math.cos(angle), CENTRE + radius * math.sin(angle)


def _circle_path(radius: float, sweep: int) -> str:
    """Return a closed circle path made of two half arcs."""
    left, right = CENTRE - radius, CENTRE + radius
    return (f"M {right:.2f} {CENTRE:.2f} A {radius:.2f} {radius:.2f} 0 1 {sweep} {left:.2f} {CENTRE:.2f} "
            f"A {radius:.2f} {radius:.2f} 0 1 {sweep} {right:.2f} {CENTRE:.2f} Z")


def _sector_path(geometry: Geometry) -> str:
    """Return the path of one ring sector, a full ring or a disc when it spans 360 degrees."""
    r_in, r_out, start, end = geometry
    if end - start >= FULL_TURN - 1e-6:
        return _circle_path(r_out, 1) + (f" {_circle_path(r_in, 0)}" if r_in > 0 else "")
    large = 1 if end - start > math.pi else 0
    x0, y0 = _point(r_out, start)
    x1, y1 = _point(r_out, end)
    if r_in <= 0:
        return (f"M {CENTRE:.2f} {CENTRE:.2f} L {x0:.2f} {y0:.2f} "
                f"A {r_out:.2f} {r_out:.2f} 0 {large} 1 {x1:.2f} {y1:.2f} Z")
    x2, y2 = _point(r_in, end)
    x3, y3 = _point(r_in, start)
    return (f"M {x0:.2f} {y0:.2f} A {r_out:.2f} {r_out:.2f} 0 {large} 1 {x1:.2f} {y1:.2f} "
            f"L {x2:.2f} {y2:.2f} A {r_in:.2f} {r_in:.2f} 0 {large} 0 {x3:.2f} {y3:.2f} Z")


def _layout(zones: list[dict]) -> list[tuple[dict, Geometry]]:
    """Give every zone a ring band and an equal sector, skipping rings without zones."""
    unknown = {zone["ring"] for zone in zones} - set(RING_ORDER)
    if unknown:
        raise ValueError(f"Unknown ring name: {sorted(unknown)[0]}")
    rings = [ring for ring in RING_ORDER if any(zone["ring"] == ring for zone in zones)]
    radius = SIZE / 2 - MARGIN
    core_radius = radius * CORE_SHARE if "core" in rings else 0
    bands = [ring for ring in rings if ring != "core"]
    band = (radius - core_radius) / max(len(bands), 1)
    placed: list[tuple[dict, Geometry]] = []
    for ring in rings:
        members = [zone for zone in zones if zone["ring"] == ring]
        index = bands.index(ring) if ring != "core" else 0
        r_in, r_out = (0.0, core_radius) if ring == "core" else (core_radius + index * band, core_radius + (index + 1) * band)
        span = FULL_TURN / len(members)
        for slot, zone in enumerate(members):
            start = -math.pi / 2 + slot * span
            placed.append((zone, (r_in, r_out, start, start + span)))
    return placed


def _label_anchor(geometry: Geometry) -> tuple[float, float]:
    """Return where the label text is centred for a sector."""
    r_in, r_out, start, end = geometry
    full = end - start >= FULL_TURN - 1e-6
    if full and r_in <= 0:
        return CENTRE, CENTRE
    if full:
        return _point((r_in + r_out) / 2, start)
    radius = (r_in + r_out) / 2 if r_in > 0 else r_out * 0.6
    return _point(radius, (start + end) / 2)


def _lost_mark(zone: dict) -> str:
    """Return the marker text of a lost zone: refused for a customer zone, leaked for a secret."""
    return LOST_MARK.get(zone["ring"], SECRET_LOST_MARK)


def _mark_text(zone: dict, lost: bool, mark: str | None) -> str | None:
    """Return the marker words of a zone, or None when it has none: words, never colour alone."""
    if lost:
        return _lost_mark(zone)
    return {"served": SERVED_MARK, "safe": SAFE_MARK}.get(mark or "")


def _label_lines(zone: dict, marker: str | None) -> list[str]:
    """Return the text lines shown in a zone: label, points and, when it has one, a marker with words."""
    lines = wrap(str(zone["label"]), width=LABEL_WIDTH)[:3]
    lines.append(f"{zone['points']} pts")
    if marker:
        lines.append(marker)
    return lines


def _fill(zone: dict, lost: bool, mark: str | None) -> tuple[str, str]:
    """Return the fill and the text colour of a zone for its state."""
    if lost and zone["ring"] == "outer":
        return "url(#hatch)", _var(("--warn", "#8f5e0e"))  # a turned-away customer
    if lost:
        return _var(("--breach", "#1e252c")), _var(("--breach-ink", "#f2766d"))  # a breached secret
    if mark == "served":
        return _var(("--good-soft", "#dff1e8")), _var(("--ink", "#12202b"))
    ink = "#ffffff" if zone["ring"] in DARK_RINGS else _var(("--ink", "#12202b"))
    return _var(RING_FILL[zone["ring"]]), ink


def _outline(path: str, kind: str) -> str:
    """Return a flashing outline for the zone being attacked or asked about."""
    color = _var(FOCUS_COLOR[kind])
    return (f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4" data-focus="{kind}">'
            '<animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite"/></path>')


def _zone_svg(zone: dict, geometry: Geometry, lost: bool, mark: str | None, focus: str | None) -> str:
    """Return the SVG group of one zone."""
    fill, ink = _fill(zone, lost, mark)
    marker = _mark_text(zone, lost, mark)
    status = "lost" if lost else "safe"
    x, y = _label_anchor(geometry)
    lines = _label_lines(zone, marker)
    top = y - (len(lines) - 1) * LINE_HEIGHT / 2
    spans = "".join(f'<tspan x="{x:.1f}" y="{top + i * LINE_HEIGHT:.1f}">{escape(line)}</tspan>'
                    for i, line in enumerate(lines))
    spoken = marker.split()[1] if marker else status
    title = escape(f"{zone['label']}, {zone['points']} points, {spoken}")
    path = _sector_path(geometry)
    # text on the hatching gets a light outline so it stays readable
    halo = ';stroke:var(--warn-soft,#faefd9);stroke-width:3px;paint-order:stroke' if fill.startswith('url(') else ''
    ring_stroke = _var(("--surface", "#ffffff"))
    return (f'<g data-zone="{escape(str(zone["id"]), quote=True)}" data-state="{status}" '
            f'data-mark="{escape(mark or "", quote=True)}">'
            f"<title>{title}</title>"
            f'<path d="{path}" style="fill:{fill};stroke:{ring_stroke}" stroke-width="2" fill-rule="evenodd"/>'
            f'<text text-anchor="middle" font-family="system-ui,sans-serif" font-size="{FONT_SIZE}" '
            f'font-weight="600" style="fill:{ink}{halo}">{spans}</text>'
            f'{_outline(path, focus) if focus else ""}</g>')


HATCH = ('<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="7" height="7" style="fill:var(--warn-soft,#faefd9)"/>'
         '<line x1="0" y1="0" x2="0" y2="7" style="stroke:var(--warn,#8f5e0e)" stroke-width="3"/></pattern></defs>')


def build_map_svg(zones: list[dict], state: dict | None = None, marks: dict | None = None,
                  focus: tuple[str, str] | None = None) -> str:
    """Return the system core map as an SVG string.

    state maps zone id to "safe" or "lost" (missing means safe). marks maps zone id to "served" or "safe",
    the good outcomes. focus is (zone id, "target" or "asking"): that zone gets a flashing outline and is drawn
    last so the outline is not covered by its neighbours.
    """
    state, marks = state or {}, marks or {}
    focus_id, focus_kind = focus if focus else (None, None)
    placed = sorted(_layout(zones), key=lambda item: item[0]["id"] == focus_id)
    body = "".join(_zone_svg(zone, geometry, state.get(zone["id"]) == "lost", marks.get(zone["id"]),
                             focus_kind if zone["id"] == focus_id else None)
                   for zone, geometry in placed)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" role="img" '
            f'aria-label="System core map" '
            f'style="width:100%;max-width:{SIZE + 40}px;height:auto;display:block;margin:0 auto">{HATCH}{body}</svg>')


RING_LEGEND = {"outer": "Public: customers ask", "inner": "Internal secret", "sensitive": "Sensitive secret",
               "core": "Core: lose if breached"}
LEGEND_ROW_HEIGHT = 20


def legend_svg(rings: list[str]) -> str:
    """Return a small legend for the rings on a map and for the breached and turned away markers."""
    items = [(ring, RING_LEGEND[ring], _var(RING_FILL[ring])) for ring in ("outer", "inner", "sensitive", "core")
             if ring in rings]
    items += [("breached", "Breached: points lost", _var(("--breach", "#1e252c"))),
              ("refused", "Customer turned away", "url(#hatch)")]
    rows = math.ceil(len(items) / 2)
    cells = ""
    for index, (_, text, fill) in enumerate(items):
        x, y = (index % 2) * (SIZE / 2), (index // 2) * LEGEND_ROW_HEIGHT + 4
        cells += (f'<rect x="{x:.0f}" y="{y}" width="12" height="12" rx="3" style="fill:{fill}"/>'
                  f'<text x="{x + 18:.0f}" y="{y + 10}" font-family="system-ui,sans-serif" font-size="11" '
                  f'style="fill:var(--muted,#56687a)">{escape(text)}</text>')
    height = rows * LEGEND_ROW_HEIGHT + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {height}" role="img" '
            f'aria-label="Map legend" style="width:100%;max-width:{SIZE + 40}px;height:auto;display:block;margin:0 auto">'
            f"{HATCH}{cells}</svg>")
