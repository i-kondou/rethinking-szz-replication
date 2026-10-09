#!/usr/bin/env python3
"""Generate compact English RQ2 displays from the pinned aggregate.

Display-only revision: preserve raw logs, classification and earlier figures.
Uses Python/ReportLab for vector PDFs with embedded Arial; no model calls.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import median
import sys

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from common import ROOT, data as input_data, english
TABLE_DIR = ROOT / 'outputs/analysis/rq2'

STEM = "rq2-compact-20260916"
BLUE, ORANGE, INK, GRID = map(HexColor, ["#27658B", "#B96530", "#182A36", "#DFE3E5"])
ALL_GRAY = HexColor("#818A91")
WIDTH = 252
GROUPS = ("all", "success", "failure")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_data():
    return english(input_data('rq2'))


def runs(data, group):
    return [r for r in data["runs"] if group == "all" or r["exact"] == (group == "success")]


def fonts(directory):
    for name, filename in (("RQ2Arial", "Arial.ttf"), ("RQ2ArialBold", "Arial Bold.ttf")):
        path = directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Provide --font-dir containing {filename}")
        pdfmetrics.registerFont(TTFont(name, str(path)))


def text(c, value, x, y, size=8, bold=False, align="left", color=INK):
    c.setFont("RQ2ArialBold" if bold else "RQ2Arial", size)
    c.setFillColor(color)
    getattr(c, {"left": "drawString", "center": "drawCentredString", "right": "drawRightString"}[align])(x, y, str(value))


def histogram(data, output, compare=False):
    c = canvas.Canvas(str(output), pagesize=(WIDTH, 137), invariant=1)
    c.setTitle("Bash calls per run: " + ("successful and unsuccessful runs" if compare else "all runs"))
    left, bottom, pw, ph = 27, 26, 221, 105
    top = bottom + ph
    for percent in (0, 5, 10, 15, 20):
        y = bottom + ph * percent / 20
        c.setStrokeColor(GRID)
        c.setLineWidth(.3)
        c.line(left, y, left + pw, y)
        text(c, f"{percent}%", left - 4, y - 2.5, 7, align="right")
    groups = ("success", "failure") if compare else ("all",)
    dx = pw / 30
    for key in groups:
        selected = runs(data, key)
        freq = Counter(r["bash_calls"] for r in selected)
        color = {"all": ALL_GRAY, "success": BLUE, "failure": ORANGE}[key]
        for i in range(1, 31):
            x = left + (i - .5) * dx
            bw = dx * (.4 if compare else .76)
            bx = x - bw if key == "success" else x if compare else x - bw / 2
            c.setFillColor(color)
            c.rect(bx, bottom, bw, ph * (freq[i] / len(selected)) / .2, fill=1, stroke=0)
        mid = median(r["bash_calls"] for r in selected)
        mx = left + (mid - .5) * dx
        c.saveState()
        c.setStrokeColor(INK if key == "all" else color)
        c.setLineWidth(1.15)
        c.setDash(3, 2)
        c.line(mx, bottom, mx, top)
        c.restoreState()
    # Keep the statistic label horizontal in the empty upper-right area.
    # Color identifies outcome; the dashed stroke identifies a median.
    legend_x, legend_y = left + pw - 74, top - 10
    if compare:
        for index, (label, color) in enumerate((("Successful", BLUE), ("Unsuccessful", ORANGE))):
            y = legend_y - index * 12
            c.setFillColor(color)
            c.rect(legend_x + 3, y, 5, 5, fill=1, stroke=0)
            text(c, label, legend_x + 16, y, 8)
        legend_y -= 24
    c.saveState()
    c.setStrokeColor(INK)
    c.setLineWidth(1.05)
    c.setDash(3, 2)
    c.line(legend_x, legend_y + 2.5, legend_x + 12, legend_y + 2.5)
    c.restoreState()
    text(c, "Median", legend_x + 16, legend_y, 8)
    median_ticks = {int(median(r["bash_calls"] for r in runs(data, g))):
                    {"all": INK, "success": BLUE, "failure": ORANGE}[g] for g in groups}
    for i in range(1, 31):
        text(c, i, left + (i - .5) * dx, bottom - 9,
             7.5 if i in median_ticks else 6.2, bold=i in median_ticks,
             align="center", color=median_ticks.get(i, INK))
    c.setStrokeColor(INK)
    c.setLineWidth(.45)
    c.line(left, bottom, left + pw, bottom)
    text(c, "Bash calls per run", left + pw / 2, 3, 8, align="center")
    c.save()


def patterns(data, output):
    c = canvas.Canvas(str(output), pagesize=(WIDTH, 169), invariant=1)
    c.setTitle("Investigation patterns in successful and unsuccessful runs")
    left, bottom, pw, ph = 59, 28, 173, 123
    for tick in (0, 25, 50, 75, 100):
        x = left + pw * tick / 100
        c.setStrokeColor(GRID)
        c.setLineWidth(.3)
        c.line(x, bottom, x, bottom + ph)
        text(c, f"{tick}%", x, bottom - 10, 7, align="center")
    labels = [("Starts with AB", "starts_AB"), ("Contains ABA", "has_ABA"),
              ("Contains\nABAB / BABA", "has_four_AB"), ("Includes C", "C")]
    for i, (label, key) in enumerate(labels):
        y = bottom + ph - 15 - i * 29
        lines = label.split("\n")
        for j, line in enumerate(lines):
            text(c, line, left - 5, y - 1 + (len(lines)-1)*4.5 - j*9, 7.6, align="right")
        for group, offset, color in (("success", 1, BLUE), ("failure", -8, ORANGE)):
            summary = data["groups"][group]
            count = summary["activity_runs"]["C"] if key == "C" else summary["patterns"][key]
            value = count / summary["runs"]
            c.setFillColor(color)
            c.rect(left, y + offset, pw * value, 8, fill=1, stroke=0)
            text(c, f"{100*value:.1f}%", left + pw * value + 2, y + offset + 1, 7)
    for group, x, color in (("success", 36, BLUE), ("failure", 139, ORANGE)):
        c.setFillColor(color)
        c.rect(x, 2, 5, 5, fill=1, stroke=0)
        text(c, "Successful" if group == "success" else "Unsuccessful", x + 8, 2, 7.7)
    c.save()


def row(*cells):
    return " & ".join(map(str, cells)) + r" \\"


def write_table(name, rows, columns, compact=False):
    value = "\n".join([
        "% Generated by scripts/build_rq2_compact_displays.py; do not edit values.",
        r"\begingroup", r"\footnotesize" if compact else r"\small",
        *([r"\setlength{\tabcolsep}{3pt}"] if compact else []),
        r"\renewcommand{\arraystretch}{1.12}",
        rf"\begin{{tabular*}}{{\linewidth}}{{@{{\extracolsep{{\fill}}}}{columns}@{{}}}}",
        r"\toprule", *rows, r"\bottomrule", r"\end{tabular*}", r"\endgroup", ""])
    (TABLE_DIR / f"{STEM}-{name}.tex").write_text(value)


def command_rows(data):
    census = input_data('census')
    counts, run_sets = Counter(), {}
    for call in census["calls"]:
        commands = ["git " + c["subcommand"] for c in call["git"]]
        commands += [c["executable"] for c in call["invocations"] if c["executable"] != "git"]
        for command in commands:
            counts[command] += 1
            run_sets.setdefault(command, set()).add(call["slot_id"])
    summary = data["groups"]["all"]
    for entry in summary["ranking"]:
        assert counts[entry["command"]] == entry["occurrences"]
        assert len(run_sets[entry["command"]]) == entry["runs"]
    assert sum(counts.values()) == summary["command_occurrences"] == 3748
    blocks = []
    for is_git, key in ((True, "git_occurrences"), (False, "non_git_occurrences")):
        ranking = [r for r in summary["ranking"] if r["command"].startswith("git ") == is_git]
        total = sum(r["occurrences"] for r in ranking)
        assert total == summary[key]
        block = []
        for entry in ranking[:6]:
            command = entry["command"].removeprefix("git ") if is_git else entry["command"]
            block.append((rf"\texttt{{{command}}}",
                          f"{entry['occurrences']:,} ({100*entry['occurrences']/total:.1f})"))
        omitted = ranking[6:]
        other_count = sum(r["occurrences"] for r in omitted)
        other_runs = len(set().union(*(run_sets[r["command"]] for r in omitted)))
        total_runs = len(set().union(*(run_sets[r["command"]] for r in ranking)))
        assert (other_runs, total_runs) == ((12, 237) if is_git else (55, 228))
        block.append((f"Other ({len(omitted)} types)", f"{other_count:,} ({100*other_count/total:.1f})"))
        block.append((r"\textbf{Total}", rf"\textbf{{{total:,} (100.0)}}"))
        blocks.append(block)
    assert len(blocks[0]) == len(blocks[1]) == 8
    rows = [row("Git command", r"Count (\%)", "Non-Git command", r"Count (\%)"), r"\midrule"]
    for i, (git, non_git) in enumerate(zip(*blocks)):
        if i == 7:
            rows.append(r"\midrule")
        rows.append(row(*git, *non_git))
    rows += [r"\midrule",
             row(rf"\multicolumn{{3}}{{@{{}}l}}{{All commands ({len(counts)} types)}}", f"{sum(counts.values()):,}")]
    return rows


def compact_tables(data):
    write_table("commands", command_rows(data), "lrlr", compact=True)
    summary = data["groups"]["all"]
    rows = [row("First explicit Git request", "Runs", r"\%"), r"\midrule"]
    entries = [
        (r"\textbf{\texttt{log}}", summary["first_git"]["log"]),
        (r"\quad\texttt{--oneline}, no patch", summary["first_log_formats"]["oneline_without_patch"]),
        (r"\qquad List request", summary["first_oneline_no_patch_non_single"]),
        (r"\qquad One-commit request (\texttt{-1})", summary["first_oneline_no_patch_single"]),
        (r"\quad\texttt{--oneline}, with patch", summary["first_log_formats"]["oneline_with_patch"]),
        (r"\quad Standard format, with patch", summary["first_log_formats"]["standard_with_patch"]),
        (r"\texttt{show}", summary["first_git"]["show"]),
    ]
    assert entries[1][1] == entries[2][1] + entries[3][1]
    assert entries[0][1] == sum(entries[i][1] for i in (1, 4, 5))
    assert entries[0][1] + entries[6][1] == 237
    rows += [row(label, count, f"{100*count/237:.1f}") for label, count in entries]
    rows += [r"\midrule", row(r"\textbf{Total}", r"\textbf{237}", r"\textbf{100.0}")]
    write_table("first-git", rows, "lrr")
    cohort = [case for case in data["cases"] if case["same_prediction"]]
    comparison = Counter(case["block_comparison"] for case in cohort)
    assert len(cohort) == 68 and comparison == {"different": 62, "same": 6}
    rows = [row("Comparison", "Cases", r"\%"), r"\midrule"]
    for key, label in (("different", "Different in at least two runs"),
                       ("same", "Same in all three runs")):
        rows.append(row(label, comparison[key], f"{100*comparison[key]/len(cohort):.1f}"))
    rows += [r"\midrule", row(r"\textbf{Total}", r"\textbf{68}", r"\textbf{100.0}")]
    write_table("same-answer", rows, "lrr")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate the source without writing outputs")
    parser.add_argument("--font-dir", type=Path, default=Path("/opt/replication-fonts"))
    args = parser.parse_args()
    data = read_data()
    if args.check:
        print("Pinned source, group counts, medians and sequence rankings verified.")
        return
    fonts(args.font_dir)
    output = ROOT / "results/figures/rq2"
    output.mkdir(parents=True, exist_ok=False)
    TABLE_DIR.mkdir(parents=True, exist_ok=False)
    histogram(data, output / f"{STEM}-a2-all.pdf")
    histogram(data, output / f"{STEM}-a2-outcomes.pdf", compare=True)
    patterns(data, output / f"{STEM}-b1.pdf")
    compact_tables(data)
    print("Generated three vector plots and the three active result-table bodies; source data unchanged.")


if __name__ == "__main__":
    main()
