from __future__ import annotations

import math
from typing import Tuple, Dict, Any, List

TIKZ_TO_HEX = {
    "red": "#cc0000",
    "blue": "#005bbb",
    "green!60!black": "#0b5d1e",
    "yellow!80!black": "#6b5a00",
    "orange!90!black": "#8a4b00",
    "purple": "#6a0dad",
    "teal!70!black": "#006a6a",
    "brown": "#7a3b00",
    "magenta": "#b000b0",
    "black": "#000000",
}

# A-digit default palette (matches Lua's palette(idx))
A_PALETTE = ["red","blue","green!60!black","yellow!80!black","purple","orange!90!black","teal!70!black","brown"]

# Place-value palette for Egel-add marks (matches Lua default_colors)
PV_COLORS = ["red","blue","green!60!black","orange!90!black","purple","teal!70!black","brown","magenta"]

def css_color(token: str) -> str:
    """Accept TikZ-ish tokens, CSS named colors, or hex."""
    token = (token or "").strip()
    if token in TIKZ_TO_HEX:
        return TIKZ_TO_HEX[token]
    if token.startswith("#") or token.startswith("rgb(") or token.startswith("rgba(") or token.startswith("hsl("):
        return token
    # fall back to CSS named colors
    return token if token else "#000000"

def col_color(total_cols: int, col_index: int) -> str:
    # col_index: 1..total_cols (left->right)
    # rightmost is ones place
    ones_index = total_cols - col_index + 1  # rightmost=1
    return PV_COLORS[(ones_index - 1) % len(PV_COLORS)]

def ndigits(v: int) -> int:
    v = abs(int(v))
    if v == 0:
        return 1
    return int(math.floor(math.log10(v))) + 1

def digits_rev(v: int):
    v = int(v)
    if v == 0:
        return [0]
    out = []
    while v > 0:
        out.append(v % 10)
        v //= 10
    return out  # least->most


def parse_digits_units_first(x: int):
    x = abs(int(x))
    if x == 0:
        return [0]
    ds = []
    while x > 0:
        ds.append(x % 10)
        x //= 10
    return ds  # units first

def multiply_digits(A, B):
    # A,B: units-first
    m = len(A)
    n = len(B)
    P = [0] * (m + n + 2)
    for i in range(m):
        for j in range(n):
            P[i + j] += A[i] * B[j]
    carry = 0
    for k in range(len(P)):
        total = P[k] + carry
        P[k] = total % 10
        carry = total // 10
    while len(P) > 1 and P[-1] == 0:
        P.pop()
    return P  # units-first

def acolor(i: int, Acolors: list[str] | None):
    # i is 0-based index over A units->... like Lua
    if Acolors and i < len(Acolors) and Acolors[i].strip():
        return Acolors[i].strip()
    return A_PALETTE[i % len(A_PALETTE)]

def checker_digit_color(x_int: int, y_int: int, Ccolors: tuple[str,str]):
    c1, c2 = Ccolors[0] or "red", Ccolors[1] or "blue"
    bx = math.floor(x_int / 2)
    by = y_int
    return c1 if ((bx + by) % 2) == 0 else c2

# ---------- SVG primitives ----------
def svg_text(x, y, s, size=22, weight="bold", fill="#000", anchor="middle", family="Times New Roman, serif"):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-family="{family}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{s}</text>'

def svg_line(x1, y1, x2, y2, stroke="#000", width=2, opacity=1.0):
    return f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'

def svg_rect(x, y, w, h, fill="none", stroke="none", width=1, opacity=1.0, rx=0.0, ry=0.0):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" rx="{rx:.2f}" ry="{ry:.2f}"/>'

def svg_grid(x0, y0, x1, y1, step, stroke="#35b7c8", width=1, opacity=0.22):
    parts = []
    x = x0
    while x <= x1 + 1e-9:
        parts.append(svg_line(x, y0, x, y1, stroke=stroke, width=width, opacity=opacity))
        x += step
    y = y0
    while y <= y1 + 1e-9:
        parts.append(svg_line(x0, y, x1, y, stroke=stroke, width=width, opacity=opacity))
        y += step
    return "\n".join(parts)

def highlight_cell_svg(X, Y, unit, x_int, y_int, col_token):
    # matches TikZ: (x+0.10, y+0.10) to (x+0.90, y+0.90), opacity=0.20, rounded corners
    fill = css_color(col_token)
    x = X(x_int) + 0.10 * unit
    y = Y(y_int) + 0.10 * unit
    w = 0.80 * unit
    h = 0.80 * unit
    r = 0.18 * unit
    return svg_rect(x, y, w, h, fill=fill, opacity=0.20, rx=r, ry=r)

def highlight_block2_svg(X, Y, unit, x_int, y_int, col_token):
    # matches TikZ: (x+0.08, y+0.08) to (x+1.92, y+0.92)
    fill = css_color(col_token)
    x = X(x_int) + 0.08 * unit
    y = Y(y_int) + 0.08 * unit
    w = 1.84 * unit
    h = 0.84 * unit
    r = 0.18 * unit
    return svg_rect(x, y, w, h, fill=fill, opacity=0.20, rx=r, ry=r)

# ---------- renderer ----------
def render_svg_lua_match(
    a: int, b: int,
    unit: int = 56,
    show_grid: bool = True,
    add_mode: str = "egel",
    show_marks: bool = True,
    show_carry: bool = True,
    carry_scale: float = 1.0,
    mark_len_factor: float = 0.70,
    mark_stack_step: float = 0.08,
    color_mode: int = 0,
    reveal_stage: int = 3,
    Acolors: list[str] | None = None,
    Ccolors: tuple[str,str] = ("red","blue"),
):
    """
    Lua-match layout:
      A digits at (-2-i, i)
      dot-times-dot at (-1,0),(0,0),(1,0)
      B digits at (2+j, j) with Bms (most->least)
      blocks: x=j-i, y=2+i+j, tens at (x,y), ones at (x+1,y)
    Color modes:
      0: all digits black
      1: byA MARKER (background markers on A digits + corresponding blocks)
      2: byA COLOR (A digits + corresponding block digits colored)
      3: CHECKER COLOR (block digits colored by checkerboard using Ccolors)
    """
    A = parse_digits_units_first(a)  # units->...
    B = parse_digits_units_first(b)
    m = len(A)
    n = len(B)

    # B placement order: MS->LS
    Bms = [B[n - 1 - j] for j in range(n)]
    show_digits = (reveal_stage >= 1)
    show_blocks = (reveal_stage >= 2)
    show_egel   = (reveal_stage >= 3)

    # blocks + ranges
    blocks = []
    yMax = -10**9
    xMin = 10**9
    xMax = -10**9
    for i in range(m):
        for j in range(n):
            ad = A[i]
            bd = Bms[j]
            p = ad * bd
            t = p // 10
            u = p % 10
            x_int = j - i
            y_int = 2 + i + j
            yMax = max(yMax, y_int)
            xMin = min(xMin, x_int)
            xMax = max(xMax, x_int + 1)
            blocks.append({"i": i, "x": x_int, "y": y_int, "t": t, "u": u})

    # rows
    if add_mode == "egel":
        yCarry = yMax + 2
        yRes = yCarry + 1
    else:
        yCarry = None
        yRes = yMax + 3
    yLine = yRes

    # product digits
    P = multiply_digits(A, B)  # units-first
    chars = [str(d) for d in reversed(P)]
    while len(chars) > 1 and chars[0] == "0":
        chars.pop(0)

    xRight = n
    startX = xRight - (len(chars) - 1)

    # bbox
    xmin, xmax, ymin, ymax = 10**9, -10**9, 10**9, -10**9
    def upd(x, y):
        nonlocal xmin, xmax, ymin, ymax
        xmin = min(xmin, x)
        xmax = max(xmax, x)
        ymin = min(ymin, y)
        ymax = max(ymax, y)

    for i in range(m): upd(-2 - i, i)
    upd(-1, 0); upd(0, 0); upd(1, 0)
    for j in range(n): upd(2 + j, j)
    for b0 in blocks:
        upd(b0["x"], b0["y"])
        upd(b0["x"] + 1, b0["y"])
    for k in range(len(chars)): upd(startX + k, yRes)
    upd(startX, yLine); upd(xRight + 1, yLine)

    # egel add computations (underline + carry row)
    underline = {}  # underline[y][x]=count
    carry_at = {}
    carry_src = {}
    if add_mode == "egel":
        add_xMin, add_xMax = xMin, xMax
        add_cols = add_xMax - add_xMin + 1

        def x_to_colindex(x): return (x - add_xMin + 1)

        digits_by_col = {x: [] for x in range(add_xMin, add_xMax + 1)}
        for b0 in blocks:
            digits_by_col[b0["x"]].append({"x": b0["x"], "y": b0["y"], "d": b0["t"]})
            digits_by_col[b0["x"] + 1].append({"x": b0["x"] + 1, "y": b0["y"], "d": b0["u"]})

        carry_in = 0
        for x in range(add_xMax, add_xMin - 1, -1):
            u = carry_in
            tens_counter = 0
            col_list = digits_by_col.get(x, [])
            col_list.sort(key=lambda it: it["y"])  # top->bottom
            for it in col_list:
                u += it["d"]
                if u >= 10:
                    produced = u // 10
                    tens_counter += produced
                    u = u % 10
                    underline.setdefault(it["y"], {})
                    underline[it["y"]][it["x"]] = underline[it["y"]].get(it["x"], 0) + produced
            if tens_counter > 0:
                carry_at[x - 1] = tens_counter
                carry_src[x - 1] = x
            carry_in = tens_counter

        # bbox expand for multi-digit carry
        extra_left = xmin
        for tx, v in carry_at.items():
            k = ndigits(v)
            leftmost = tx - (k - 1)
            extra_left = min(extra_left, leftmost)
        if extra_left < xmin:
            xmin = extra_left - 1

        # allow a bit for carry row
        upd(add_xMin - ndigits(999), yCarry)
        upd(add_xMax, yCarry)

    # pad bbox
    xmin -= 1; xmax += 1; ymin -= 1; ymax += 1

    # map integer grid to SVG pixels
    pad = int(unit * 0.6)
    W = (xmax - xmin + 1) * unit + pad * 2
    H = (ymax - ymin + 1) * unit + pad * 2

    def X(x): return pad + (x - xmin) * unit
    def Y(y): return pad + (y - ymin) * unit
    def Cx(x): return pad + (x - xmin + 0.5) * unit
    def Cy(y): return pad + (y - ymin + 0.5) * unit

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # grid (cyan)
    if show_grid:
        parts.append(svg_grid(X(xmin), Y(ymin), X(xmax + 1), Y(ymax + 1), step=unit, stroke="#35b7c8", width=1, opacity=0.22))

    # --- color=1 markers (background) ---
    if color_mode == 1:
        # A digit markers
        if show_digits:
            for i in range(m):
                col = acolor(i, Acolors)
                parts.append(highlight_cell_svg(X, Y, unit, -2 - i, i, col))
        # Block markers for each block, colored by its A digit index (i)
        if show_blocks:
            for b0 in blocks:
                col = acolor(b0["i"], Acolors)
                parts.append(highlight_block2_svg(X, Y, unit, b0["x"], b0["y"], col))

    if show_digits:
        # A digits (color=2 -> colored; otherwise black)
        for i in range(m):
            x = -2 - i
            y = i
            d = A[i]
            fill = "#000000"
            if color_mode == 2:
                fill = css_color(acolor(i, Acolors))
            parts.append(svg_text(Cx(x), Cy(y) + 8, d, size=26, weight="bold", fill=fill))

        # • × •
        parts.append(svg_text(Cx(-1), Cy(0) + 8, "·", size=28, weight="bold", fill="#000"))
        parts.append(svg_text(Cx(0),  Cy(0) + 8, "×", size=28, weight="bold", fill="#000"))
        parts.append(svg_text(Cx(1),  Cy(0) + 8, "·", size=28, weight="bold", fill="#000"))

        # B digits (always black, matching engine)
        for j in range(n):
            x = 2 + j
            y = j
            d = Bms[j]
            parts.append(svg_text(Cx(x), Cy(y) + 8, d, size=26, weight="bold", fill="#000000"))

    if show_blocks:
        # Block digits
        for b0 in blocks:
            tcol = "#000000"
            if color_mode == 2:
                tcol = css_color(acolor(b0["i"], Acolors))
            elif color_mode == 3:
                tcol = css_color(checker_digit_color(b0["x"], b0["y"], Ccolors))
            parts.append(svg_text(Cx(b0["x"]),   Cy(b0["y"]) + 8, b0["t"], size=26, weight="bold", fill=tcol))
            parts.append(svg_text(Cx(b0["x"]+1), Cy(b0["y"]) + 8, b0["u"], size=26, weight="bold", fill=tcol))

    if show_egel:
        # Egel underlines (place-value coloring)
        if add_mode == "egel" and show_marks:
            add_xMin, add_xMax = xMin, xMax
            add_cols = add_xMax - add_xMin + 1
            def x_to_colindex(x): return (x - add_xMin + 1)

            for y, row in underline.items():
                for x, cnt in row.items():
                    colidx = x_to_colindex(x)
                    color_name = col_color(add_cols, colidx)
                    stroke = css_color(color_name)
                    if cnt > 8:
                        parts.append(svg_text(Cx(x), Cy(y) - 6, cnt, size=14, weight="bold", fill=stroke))
                        continue
                    y_bottom = Y(y + 1)  # exact grid line
                    x1 = Cx(x) - (mark_len_factor * unit) / 2
                    x2 = Cx(x) + (mark_len_factor * unit) / 2
                    for k in range(cnt):
                        yy = y_bottom - (mark_stack_step * unit) * (k)
                        parts.append(svg_line(x1, yy, x2, yy, stroke=stroke, width=3, opacity=1.0))

        # Carry-count row (place-value coloring)
        if add_mode == "egel" and show_carry:
            add_xMin, add_xMax = xMin, xMax
            add_cols = add_xMax - add_xMin + 1
            def x_to_colindex(x): return (x - add_xMin + 1)

            for tx, v in carry_at.items():
                src = carry_src.get(tx, tx + 1)
                src_colidx = x_to_colindex(src)
                color_name = col_color(add_cols, src_colidx)
                fill = css_color(color_name)
                digs = digits_rev(v)  # least->most
                for i, d in enumerate(digs):
                    x = tx - i
                    parts.append(svg_text(Cx(x), Cy(yCarry) + 8, d, size=int(22 * carry_scale), weight="bold", fill=fill))

        # underline above answer row
        y_line = Y(yLine)
        parts.append(svg_line(X(startX), y_line, X(xRight + 1), y_line, stroke="#000", width=3, opacity=1.0))

        # result row
        for k, ch in enumerate(chars):
            x = startX + k
            parts.append(svg_text(Cx(x), Cy(yRes) + 10, ch, size=28, weight="bold", fill="#000"))

    parts.append("</svg>")
    return "\n".join(parts)



def render_svg(
    a: int,
    b: int,
    unit: int = 56,
    stage: int = 3,
    show_grid: bool = True,
    show_marks: bool = True,
    color_mode: int = 0,
) -> Tuple[str, Dict[str, Any]]:
    """Unified wrapper around Lua-match multiplication renderer.

    Unified stage:
      0: grid only
      1: show digits
      2: show blocks
      3: full (includes Egel-add integration)
    """
    reveal_stage = max(0, min(3, int(stage)))
    svg = render_svg_lua_match(
        a=int(a),
        b=int(b),
        unit=int(unit),
        show_grid=bool(show_grid),
        add_mode="egel",
        show_marks=bool(show_marks),
        show_carry=bool(show_marks),
        color_mode=int(color_mode),
        reveal_stage=reveal_stage,
    )
    # basic trace
    return svg, {"trace": {"op": "mul", "a": int(a), "b": int(b), "result": int(a)*int(b)}}
