"""System core map drawn as SVG. This is the only HTML the app builds, every label is escaped."""

import math
from html import escape
from textwrap import wrap

SIZE = 480
MARGIN = 8
CENTRE = SIZE / 2
FULL_TURN = 2 * math.pi
RING_ORDER = ("core", "sensitive", "inner", "outer")  # from the centre outwards
RING_FILL = {"core": "#e4d4f4", "sensitive": "#f7d2c4", "inner": "#fbe7bf", "outer": "#d7ecf6"}
LOST_FILL = "#2b2b36"
TEXT_COLOR = "#14202b"
LOST_TEXT_COLOR = "#ffffff"
ATTACK_STROKE = "#d62828"
LINE_HEIGHT = 14
LABEL_WIDTH = 14
Geometry = tuple[float, float, float, float]  # r_in, r_out, start angle, end angle


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
    band = (SIZE / 2 - MARGIN) / max(len(rings), 1)
    placed: list[tuple[dict, Geometry]] = []
    for index, ring in enumerate(rings):
        members = [zone for zone in zones if zone["ring"] == ring]
        span = FULL_TURN / len(members)
        for slot, zone in enumerate(members):
            start = -math.pi / 2 + slot * span
            placed.append((zone, (index * band, (index + 1) * band, start, start + span)))
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


def _label_lines(zone: dict, lost: bool) -> list[str]:
    """Return the text lines shown in a zone: label, points and, when lost, a cross and the word lost."""
    lines = wrap(str(zone["label"]), width=LABEL_WIDTH)[:3]
    lines.append(f"{zone['points']} pts")
    if lost:
        lines.append("✕ lost")
    return lines


def _zone_svg(zone: dict, geometry: Geometry, lost: bool, attacked: bool) -> str:
    """Return the SVG group of one zone."""
    fill = LOST_FILL if lost else RING_FILL[zone["ring"]]
    color = LOST_TEXT_COLOR if lost else TEXT_COLOR
    stroke, width = (ATTACK_STROKE, 5) if attacked else ("#ffffff", 2)
    status = "lost" if lost else "safe"
    x, y = _label_anchor(geometry)
    lines = _label_lines(zone, lost)
    top = y - (len(lines) - 1) * LINE_HEIGHT / 2
    spans = "".join(f'<tspan x="{x:.1f}" y="{top + i * LINE_HEIGHT:.1f}">{escape(line)}</tspan>'
                    for i, line in enumerate(lines))
    title = escape(f"{zone['label']}, {zone['points']} points, {status}")
    return (f'<g data-zone="{escape(str(zone["id"]), quote=True)}" data-state="{status}">'
            f"<title>{title}</title>"
            f'<path d="{_sector_path(geometry)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" fill-rule="evenodd"/>'
            f'<text text-anchor="middle" font-family="sans-serif" font-size="12" '
            f'font-weight="600" fill="{color}">{spans}</text></g>')


def build_map_svg(zones: list[dict], state: dict | None = None, attacked: str | None = None) -> str:
    """Return the system core map as an SVG string.

    state maps zone id to "safe" or "lost" (missing means safe). The attacked zone gets a
    red outline and is drawn last so the outline is not covered by its neighbours.
    """
    state = state or {}
    placed = sorted(_layout(zones), key=lambda item: item[0]["id"] == attacked)
    body = "".join(_zone_svg(zone, geometry, state.get(zone["id"]) == "lost", zone["id"] == attacked)
                   for zone, geometry in placed)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" role="img" '
            f'aria-label="System core map" '
            f'style="width:100%;max-width:{SIZE}px;height:auto;display:block;margin:0 auto">{body}</svg>')
