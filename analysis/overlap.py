#!/usr/bin/env python3
"""Render Figure 8 at one-column print size from the pinned overlap aggregate.

Display-only: no model calls, new scoring, or modification of source artifacts.
PDF and editable SVG share the same vector drawing and source-derived labels.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from reportlab.graphics import renderPDF, renderSVG
from reportlab.graphics.shapes import Circle, Drawing, Line, Path as VectorPath, String
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results/reference/llm4szz-original-rerun-20261001/pairwise-overlap.json"
SOURCE_SHA = "579edd03d3e84c713eeaeed8a660bf78ed5cb66daae2c92c1421dd1763e29ec9"
STEM = "claude-vs-llm-pairwise-compact-20261001"
REVISED_SOURCE = ROOT / "results/reference/revised-oracle-overlap-20261001/analysis.json"
REVISED_SHA = "a25b145d34746f0dc01bc9fd2d3c48d8079d365918a9b9af7de6e832bac2a7e7"
REVISED_STEM = "claude-vs-llm-revised-oracle-20261001"
WIDTH, HEIGHT = 252, 186
ORANGE, BLUE, INK = map(HexColor, ("#D98C00", "#0072B2", "#253B4B"))
BASELINE_INK, CLAUDE_INK = map(HexColor, ("#B54D12", "#006AA6"))
BASELINE_FILL, CLAUDE_FILL = map(HexColor, ("#FFC38B", "#9BD1EE"))
SHARED_FILL = HexColor("#FFFFFF")
RADIUS, LEFT_CENTER, RIGHT_CENTER = 32, 42, 80


def read_data(revised=False):
    raw = (REVISED_SOURCE if revised else SOURCE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == (REVISED_SHA if revised else SOURCE_SHA), "Review changed aggregate before repinning"
    report = json.loads(raw)
    assert report["sample_count"] == (67 if revised else 79)
    pairs = report["comparisons"]
    assert [p["baseline"] for p in pairs] == ["LLM4SZZ", "AgentSZZ", "SZZ-Agent", "Simple-SZZ-Agent"]
    universe, claude = None, None
    for pair in pairs:
        regions = {key: set(ids) for key, ids in pair["case_ids"].items()}
        assert {key: len(ids) for key, ids in regions.items()} == pair["counts"]
        assert sum(map(len, regions.values())) == report["sample_count"]
        union = set.union(*regions.values())
        assert len(union) == report["sample_count"], "Regions must be disjoint"
        found = regions["both"] | regions["claude_only"]
        if universe is None:
            universe, claude = union, found
        assert union == universe and found == claude
        if not revised:
            assert len(regions["baseline_only"]) == 2
    assert len(claude) == (65 if revised else 63)
    if revised:
        assert [p['counts']['baseline_only'] for p in pairs] == [0,0,0,1]
    else:
        assert len({p["counts"]["neither"] for p in pairs}) == 1
    return report


def intersection_area(r1, r2, distance):
    """Exact area of the intersection of two circles."""
    if distance <= abs(r1-r2):
        return math.pi * min(r1, r2)**2
    if distance >= r1+r2:
        return 0.0
    cos1 = (distance**2+r1**2-r2**2)/(2*distance*r1)
    cos2 = (distance**2+r2**2-r1**2)/(2*distance*r2)
    radicand = (-distance+r1+r2)*(distance+r1-r2)*(distance-r1+r2)*(distance+r1+r2)
    return (r1**2*math.acos(max(-1, min(1, cos1)))
            + r2**2*math.acos(max(-1, min(1, cos2)))
            - math.sqrt(max(0, radicand))/2)


def proportional_geometry(counts):
    """Common area scale across panels; all three regions preserve counts."""
    claude_count = counts['both']+counts['claude_only']
    baseline_count = counts['both']+counts['baseline_only']
    assert claude_count == 65
    unit = math.pi*38**2/65
    rc, rb = math.sqrt(unit*claude_count/math.pi), math.sqrt(unit*baseline_count/math.pi)
    if counts['baseline_only'] == 0:
        # Offset the contained set to collect the small Claude-only region on
        # the right, without changing its area or letting circles intersect.
        cx_c = 56
        cx_b = cx_c - .88*(rc-rb)
    else:
        lo, hi = abs(rc-rb), rc+rb
        for _ in range(100):
            distance = (lo+hi)/2
            if intersection_area(rb, rc, distance) > counts['both']*unit:
                lo = distance
            else:
                hi = distance
        distance = (lo+hi)/2
        cx_b, cx_c = 59-distance/2, 59+distance/2
    overlap = intersection_area(rb, rc, abs(cx_b-cx_c))
    expected = (counts['baseline_only'], counts['both'], counts['claude_only'])
    actual = ((math.pi*rb**2-overlap)/unit, overlap/unit, (math.pi*rc**2-overlap)/unit)
    assert all(math.isclose(a,e,abs_tol=1e-8) for a,e in zip(actual,expected)), (actual,expected)
    assert 0 <= cx_b-rb and cx_c+rc < 122
    return cx_b, rb, cx_c, rc


def shared_region(xb, rb, xc, rc, cy):
    """Opaque shared region prevents blue/orange alpha mixing into gray."""
    distance = xc-xb
    if distance <= rc-rb+1e-10:
        return Circle(xb, cy, rb, fillColor=SHARED_FILL, strokeColor=None)
    x_cross = (rb*rb-rc*rc+distance*distance)/(2*distance)
    angle_b = math.acos(x_cross/rb)
    angle_c = math.acos((x_cross-distance)/rc)
    shape = VectorPath(fillColor=SHARED_FILL, strokeColor=None)
    shape.moveTo(xb+rb*math.cos(angle_b), cy-rb*math.sin(angle_b))

    def arc(cx, radius, start, end):
        pieces = math.ceil((end-start)/(math.pi/2))
        step = (end-start)/pieces
        for i in range(pieces):
            a, b = start+i*step, start+(i+1)*step
            factor = 4/3*math.tan(step/4)
            shape.curveTo(cx+radius*(math.cos(a)-factor*math.sin(a)),
                          cy+radius*(math.sin(a)+factor*math.cos(a)),
                          cx+radius*(math.cos(b)+factor*math.sin(b)),
                          cy+radius*(math.sin(b)-factor*math.cos(b)),
                          cx+radius*math.cos(b), cy+radius*math.sin(b))

    arc(xb, rb, -angle_b, angle_b)
    arc(xc, rc, angle_c, 2*math.pi-angle_c)
    shape.closePath()
    return shape


def drawing(report, font_dir):
    for name, filename in (("Arial", "Arial.ttf"), ("Arial-Bold", "Arial Bold.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    d = Drawing(WIDTH, HEIGHT)

    def text(value, x, y, size=8.5, bold=False, color=INK, anchor="middle"):
        font = "Arial-Bold" if bold else "Arial"
        value = str(value)
        width = pdfmetrics.stringWidth(value, font, size)
        left = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
        assert left >= 0 and left + width <= WIDTH, (value, left, width)
        ascent, descent = pdfmetrics.getAscentDescent(font, size)
        assert y + descent >= 0 and y + ascent <= HEIGHT, (value, y, ascent, descent)
        d.add(String(x, y, value, fontName=font, fontSize=size,
                     fillColor=color, textAnchor=anchor))

    # Keep ordinary-weight counts at the geometric centroids of the regions,
    # rather than pushing exclusive counts toward the outer edges.
    distance = RIGHT_CENTER - LEFT_CENTER
    middle = (LEFT_CENTER + RIGHT_CENTER) / 2
    circle_area = math.pi * RADIUS ** 2
    overlap_area = (2 * RADIUS ** 2 * math.acos(distance / (2 * RADIUS))
                    - distance / 2 * math.sqrt(4 * RADIUS ** 2 - distance ** 2))
    left_centroid = (circle_area * LEFT_CENTER - overlap_area * middle) / (circle_area - overlap_area)
    right_centroid = 2 * middle - left_centroid

    for i, pair in enumerate(report["comparisons"]):
        ox = (i % 2) * 130
        counts = pair["counts"]
        revised = report['sample_count'] == 67
        cy = (132 if i < 2 else 40) if revised else (137 if i < 2 else 41)
        if revised:
            cx_b, rb, cx_c, rc = proportional_geometry(counts)
            d.add(Circle(ox+cx_c, cy, rc, fillColor=CLAUDE_FILL, strokeColor=None))
            d.add(Circle(ox+cx_b, cy, rb, fillColor=BASELINE_FILL, strokeColor=None))
            d.add(shared_region(ox+cx_b, rb, ox+cx_c, rc, cy))
            # Redraw boundaries last: solid blue and dashed orange identify
            # complete sets even where the shared area is white.
            d.add(Circle(ox+cx_c, cy, rc, fillColor=None,
                         strokeColor=CLAUDE_INK, strokeWidth=.8))
            d.add(Circle(ox+cx_b, cy, rb, fillColor=None,
                         strokeColor=BASELINE_INK, strokeWidth=.8, strokeDashArray=[2,1]))
        else:
            for cx, color in ((LEFT_CENTER,ORANGE),(RIGHT_CENTER,BLUE)):
                d.add(Circle(ox+cx, cy, RADIUS, fillColor=color, fillOpacity=.18,
                             strokeColor=HexColor("#606060"), strokeWidth=.45))
        if revised:
            positions = [((cx_b+cx_c)/2,'both'), (112,'claude_only')]
            # The true exclusive regions are too narrow for 12-point counts.
            # Start each short leader strictly inside its exclusive region.
            right_start = (cx_b+rb+cx_c+rc)/2
            assert cx_b+rb < right_start < cx_c+rc
            d.add(Line(ox+right_start, cy, ox+102, cy,
                       strokeColor=CLAUDE_INK, strokeWidth=.65))
            if counts['baseline_only']:
                left_start = (cx_b-rb+cx_c-rc)/2
                assert cx_b-rb < left_start < cx_c-rc
                d.add(Line(ox+16, cy, ox+left_start, cy,
                           strokeColor=BASELINE_INK, strokeWidth=.65))
                positions.insert(0,(8,'baseline_only'))
        else:
            positions = ((left_centroid,'baseline_only'),(middle,'both'),(right_centroid,'claude_only'))
        for x, key in positions:
            ascent, descent = pdfmetrics.getAscentDescent("Arial", 12)
            color = {'both': INK, 'claude_only': CLAUDE_INK, 'baseline_only': BASELINE_INK}[key] if revised else INK
            text(counts[key], ox+x, cy-(ascent+descent)/2, size=12, color=color)
        # A single comparison heading identifies the left and right sets.
        heading = f"{pair['baseline']} vs Claude Code"
        heading_size = min(8, 118 / pdfmetrics.stringWidth(heading, "Arial", 1))
        if revised:
            x = ox+61-pdfmetrics.stringWidth(heading,'Arial',heading_size)/2
            for value, color in ((pair['baseline'],BASELINE_INK), (' vs ',INK), ('Claude Code',CLAUDE_INK)):
                text(value, x, cy+46, size=heading_size, color=color, anchor='start')
                x += pdfmetrics.stringWidth(value,'Arial',heading_size)
        else:
            text(heading, ox+61, cy+39, size=heading_size)

    # Show only identified-set regions. Neither-set cases stay in the aggregate.
    # Revised circle/region areas are proportional; historical mode stays schematic.
    return d


def save_svg(d, output, revised=False):
    # ReportLab's SVG backend omits fillOpacity and uses the PDF font name.
    # Restore pale fills and portable editable text in this generated export.
    svg = renderSVG.drawToString(d)
    svg = svg.replace("font-family: Arial-Bold;", "font-family: Arial, sans-serif; font-weight: bold;")
    svg = svg.replace("font-family: Arial;", "font-family: Arial, sans-serif;")
    root = ET.fromstring(svg)
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    circles = [node for node in root.iter() if node.tag.endswith("}circle")]
    assert len(circles) == (19 if revised else 8)
    # Revised figures use explicit opaque regions; only historical mode needs
    # the missing alpha restored. Do not make the white shared regions transparent.
    if not revised:
        for node in circles:
            node.set("fill-opacity", "0.18")
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--revised", action="store_true", help="Use the reconstructed 67-case dataset")
    parser.add_argument("--font-dir", type=Path, default=Path("/opt/replication-fonts"))
    args = parser.parse_args()
    report = read_data(args.revised)
    d = drawing(report, args.font_dir)
    if not args.check:
        for extension in ("pdf", "svg"):
            stem = REVISED_STEM if args.revised else STEM
            out = ROOT / "results/figures/further_analysis" / f"{stem}.{extension}"
            if out.exists():
                raise FileExistsError(out)
            out.parent.mkdir(parents=True, exist_ok=True)
            if extension == "pdf":
                c = canvas.Canvas(str(out), pagesize=(WIDTH, HEIGHT), invariant=1)
                c.setTitle("Overlap of identified cases: Claude Code and four SZZ baselines")
                renderPDF.draw(d, c, 0, 0)
                c.save()
            else:
                save_svg(d, out, args.revised)
            print(out)
    print("PASS: pinned source, region counts/IDs, membership, text bounds, and revised region-area ratios")


if __name__ == "__main__":
    main()
