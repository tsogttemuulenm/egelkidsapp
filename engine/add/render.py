from __future__ import annotations

from dataclasses import asdict
from typing import List, Dict, Any, Tuple

from engine.add.algo import EgelAddTrace, Underline, compute_egel_addition


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _palette(idx: int) -> str:
    # A small repeating palette (pleasant, high contrast for kids)
    colors = [
        "#e53935",  # red
        "#43a047",  # green
        "#1e88e5",  # blue
        "#8e24aa",  # purple
        "#fb8c00",  # orange
        "#00897b",  # teal
    ]
    return colors[idx % len(colors)]


def render_svg(
    addends: List[int],
    cell: int = 42,
    pad: int = 18,
    show_grid: bool = True,
    show_underlines: bool = True,
    show_carry: bool = True,
    stage: int = 5,
) -> Tuple[str, Dict[str, Any]]:
    """Return (svg_string, debug_data).

    stage:
      1 -> only grid
      2 -> + numbers
      3 -> + underline marks
      4 -> + carry row digits
      5 -> + result row digits
    """

    trace: EgelAddTrace = compute_egel_addition(addends)
    n_add = len(addends)

    # Layout
    # Columns: trace.max_digits (includes possible extra carry column)
    cols = trace.max_digits + 1  # +1 for a left margin column (for '+')
    # Rows: addend rows + carry row (placed just above the separator) + separator + result
    # NOTE: In this “Эгэл нэмэх” visualization, carry is intentionally written
    # on the row right above the long separator line (instead of the very top),
    # matching the TeX layout you shared.
    r_first_add = 0
    r_carry = r_first_add + n_add
    r_sep = r_carry + 1
    r_result = r_sep + 1
    rows = r_result + 1

    width = pad * 2 + cols * cell
    height = pad * 2 + rows * cell

    def cell_xy(col_idx: int, row_idx: int) -> Tuple[int, int]:
        x = pad + col_idx * cell
        y = pad + row_idx * cell
        return x, y

    # Rightmost digit column index in the grid (excluding the left sign column)
    digit_right_col = cols - 1

    def digit_col_for_place(place: int) -> int:
        # place 0 (units) sits at rightmost digit column
        return digit_right_col - place

    # Begin SVG
    parts: List[str] = []
    parts.append(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>"
    )

    # Background
    parts.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='white'/>")

    # Grid
    if show_grid and stage >= 1:
        # outer
        x0, y0 = pad, pad
        w, h = cols * cell, rows * cell
        parts.append(
            f"<rect x='{x0}' y='{y0}' width='{w}' height='{h}' fill='none' stroke='#b3d1ff' stroke-width='2'/>"
        )
        # vertical lines
        for c in range(1, cols):
            x = x0 + c * cell
            parts.append(f"<line x1='{x}' y1='{y0}' x2='{x}' y2='{y0+h}' stroke='#cfe3ff' stroke-width='2' />")
        # horizontal lines
        for r in range(1, rows):
            y = y0 + r * cell
            parts.append(f"<line x1='{x0}' y1='{y}' x2='{x0+w}' y2='{y}' stroke='#cfe3ff' stroke-width='2' />")

    # Column color bands (very light)
    for place in range(trace.max_digits):
        col = digit_col_for_place(place)
        x, y = cell_xy(col, 0)
        parts.append(
            f"<rect x='{x}' y='{pad}' width='{cell}' height='{rows*cell}' fill='{_palette(place)}' opacity='0.06'/>"
        )

    # Helper: draw centered text in a cell
    def draw_text(col_idx: int, row_idx: int, text: str, size: int = 22, color: str = "#111"):
        x, y = cell_xy(col_idx, row_idx)
        cx = x + cell / 2
        cy = y + cell / 2 + 8
        parts.append(
            f"<text x='{cx}' y='{cy}' text-anchor='middle' font-family='ui-sans-serif, system-ui, Segoe UI, Arial' font-size='{size}' fill='{color}'>{_xml_escape(text)}</text>"
        )

    # '+' sign (aligned with the last addend row)
    if stage >= 2:
        plus_row = r_first_add + (n_add - 1) if n_add >= 1 else r_first_add
        draw_text(0, plus_row, "+", size=26, color="#111")

    # Addend digits
    if stage >= 2:
        for r, n in enumerate(addends):
            digs = _int_to_digits(n)
            for place, dig in enumerate(digs):
                col = digit_col_for_place(place)
                draw_text(col, r_first_add + r, str(dig), size=24, color=_palette(place))

    # Separator line
    if stage >= 2:
        x1, y1 = cell_xy(0, r_sep)
        x2 = pad + cols * cell
        y = y1
        parts.append(f"<line x1='{x1}' y1='{y}' x2='{x2}' y2='{y}' stroke='#222' stroke-width='3'/>")

    # Underlines (10-completion marks)
    if show_underlines and stage >= 3:
        for ct in trace.columns:
            place = ct.col
            if place >= trace.max_digits:
                continue
            col = digit_col_for_place(place)
            for ul in ct.underlines:
                if ul.row == -1:
                    row = r_carry
                else:
                    row = r_first_add + ul.row
                x, y = cell_xy(col, row)
                y_ul = y + cell - 10
                parts.append(
                    f"<line x1='{x+8}' y1='{y_ul}' x2='{x+cell-8}' y2='{y_ul}' stroke='{_palette(place)}' stroke-width='5' stroke-linecap='round'/>"
                )

    # Carry digits (carry_out goes to next column)
    if show_carry and stage >= 4:
        for ct in trace.columns:
            place = ct.col
            if place + 1 >= trace.max_digits:
                continue
            carry = ct.carry_out
            if carry == 0:
                continue
            col = digit_col_for_place(place + 1)
            draw_text(col, r_carry, str(carry), size=18, color=_palette(place + 1))

    # Result digits (use actual sum for correctness)
    if stage >= 5:
        res = sum(addends)
        digs = _int_to_digits(res)
        for place, dig in enumerate(digs):
            col = digit_col_for_place(place)
            draw_text(col, r_result, str(dig), size=26, color=_palette(place))

    # Warnings
    if trace.warnings:
        msg = " | ".join(trace.warnings)
        parts.append(
            f"<text x='{pad}' y='{height - 10}' text-anchor='start' font-family='ui-sans-serif, system-ui, Segoe UI, Arial' font-size='14' fill='#b71c1c'>{_xml_escape(msg)}</text>"
        )

    parts.append("</svg>")

    data = {
        "trace": asdict(trace),
        "layout": {
            "cell": cell,
            "pad": pad,
            "cols": cols,
            "rows": rows,
            "row_index": {
                "carry": r_carry,
                "first_add": r_first_add,
                "sep": r_sep,
                "result": r_result,
            },
        },
    }

    return "".join(parts), data


def _int_to_digits(n: int) -> List[int]:
    if n == 0:
        return [0]
    out: List[int] = []
    while n > 0:
        out.append(n % 10)
        n //= 10
    return out
