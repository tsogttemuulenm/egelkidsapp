from __future__ import annotations

from typing import Any
import math

TIKZ_TO_HEX = {
    "red": "#cc0000",
    "blue": "#005bbb",
    "green!50!black": "#0b5d1e",
    "green!60!black": "#0b5d1e",
    "orange": "#d97706",
    "orange!90!black": "#8a4b00",
    "purple": "#6a0dad",
    "teal": "#0f766e",
    "teal!70!black": "#006a6a",
    "black": "#000000",
    "gray!20": "#d1d5db",
    "blue!70!black": "#1e3a8a",
}

STEP_COLORS = ["red", "blue", "teal", "orange", "purple"]


def css_color(token: str) -> str:
    token = (token or "").strip()
    if token in TIKZ_TO_HEX:
        return TIKZ_TO_HEX[token]
    if token.startswith("#") or token.startswith("rgb(") or token.startswith("rgba("):
        return token
    return token if token else "#000000"


# =========================
# Algorithm (matches TeX Lua)
# =========================
def calculate_egel_huvaah(dividend: int, divisor: int) -> dict[str, Any]:
    """Python port of calculate_egel_huvaah() from EGEL HUVAAH 4_0 OK.tex."""
    if divisor <= 0:
        raise ValueError("divisor must be positive")
    if dividend < 0:
        raise ValueError("dividend must be non-negative")

    steps: list[dict[str, Any]] = []
    remainder = int(dividend)
    q_list: list[int] = []
    div_str = str(int(divisor))

    # helper "hürd"
    sub_vals = [
        {"k": 1, "val": int(divisor)},
        {"k": 2, "val": int(divisor) * 2},
        {"k": 5, "val": int(divisor) * 5},
    ]

    while remainder >= divisor:
        r_val = int(remainder)
        r_str = str(r_val)

        factor = 0
        multiplier = 1
        p10 = 0
        read_digits = ""

        # find earliest prefix >= divisor, set multiplier=10^p10
        for i in range(1, len(r_str) + 1):
            read_digits = r_str[:i]
            if int(read_digits) >= divisor:
                p10 = len(r_str) - i
                multiplier = 10 ** p10
                break

        # choose 5/2/1
        if remainder >= divisor * 5 * multiplier:
            factor = 5
        elif remainder >= divisor * 2 * multiplier:
            factor = 2
        else:
            factor = 1

        subtract_val = int((divisor * factor) * multiplier)
        current_q = int(factor * multiplier)

        msg = f"Уншсан тоо {read_digits}-д {div_str} нь {factor} удаа багтана. "
        if p10 > 0:
            msg += f"{p10} тэгээр орон гүйцээж {current_q} болов."

        steps.append(
            {
                "rem_before": r_val,
                "sub": subtract_val,
                "factor": current_q,  # this is the step quotient chunk (factor*10^p10)
                "msg": msg,
            }
        )
        remainder = remainder - subtract_val
        q_list.append(current_q)

        # safety: avoid infinite loop if something goes wrong
        if len(steps) > 200:
            break

    total_q = int(sum(q_list))
    final_rem = int(remainder)
    return {
        "dividend": int(dividend),
        "divisor": int(divisor),
        "steps": steps,
        "q_list": q_list,
        "total_q": total_q,
        "final_rem": final_rem,
        "sub_vals": sub_vals,
    }


# =========================
# SVG primitives
# =========================
def svg_text(x, y, s, size=22, weight="700", fill="#000", anchor="middle", family="Times New Roman, serif"):
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-family="{family}" '
        f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{s}</text>'
    )


def svg_line(x1, y1, x2, y2, stroke="#000", width=2, opacity=1.0):
    return (
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}"/>'
    )


def svg_rect(x, y, w, h, fill="none", stroke="none", width=1, opacity=1.0, rx=0.0, ry=0.0):
    return (
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{width}" opacity="{opacity}" rx="{rx:.2f}" ry="{ry:.2f}"/>'
    )


def svg_grid(x0, y0, cols, rows, unit, stroke="#35b7c8", width=1, opacity=0.22):
    parts = []
    for c in range(cols + 1):
        x = x0 + c * unit
        parts.append(svg_line(x, y0, x, y0 + rows * unit, stroke=stroke, width=width, opacity=opacity))
    for r in range(rows + 1):
        y = y0 + r * unit
        parts.append(svg_line(x0, y, x0 + cols * unit, y, stroke=stroke, width=width, opacity=opacity))
    return "\n".join(parts)


# =========================
# Renderer (grid layout inspired by TeX)
# =========================
def render_division_svg(
    dividend: int,
    divisor: int,
    unit: int = 56,
    stage: int = 3,
    show_grid: bool = True,
    color_mode: int = 1,
    align_mode: str = "right",  # left|right for step quotient chunks on right side
    sub_pos: str = "top",      # top|side|none
    black: bool = False,
    show_remainder: bool = True,
):
    data = calculate_egel_huvaah(dividend, divisor)
    steps = data["steps"]

    s_dividend = str(int(dividend))
    s_divisor = str(int(divisor))
    s_total_q = str(int(data["total_q"]))
    s_final_rem = str(int(data["final_rem"]))

    max_digits = len(s_dividend)
    right_side_width = max(len(s_divisor), len(s_total_q))
    cols = max_digits + 1 + right_side_width
    rows = len(steps) * 2 + 3  # header + (2 per step) + footer

    # paddings to allow minus sign on left
    pad_x = int(unit * 1.2)
    pad_y = int(unit * 1.4)

    def X(col: float) -> float:
        return pad_x + col * unit

    def Y(row: float) -> float:
        return pad_y + row * unit

    def XR(col: float, pad: float = 0.88) -> float:
        """Right-align x inside a grid cell with a small inner padding."""
        return X(col) + unit * pad

    width = int(pad_x * 2 + cols * unit + (unit * 5 if sub_pos == "side" else 0))
    height = int(pad_y * 2 + rows * unit + (unit * 2.2 if (stage >= 3 and show_remainder) else 0))

    ink = "#000" if black else "#111827"
    grid_stroke = "#000000" if black else "#35b7c8"
    main_line = css_color("black" if black else "green!50!black")

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append(svg_rect(0, 0, width, height, fill="white", opacity=0.0))

    # subtle rounded "paper"
    parts.append(svg_rect(pad_x * 0.55, pad_y * 0.55, cols * unit + pad_x * 0.9, rows * unit + pad_y * 0.6,
                          fill="#ffffff", stroke="#e5e7eb" if not black else "#111111", width=1, opacity=1.0, rx=18, ry=18))

    # helper hürd (top)
    if stage >= 1 and sub_pos == "top":
        box_w = cols * unit
        box_h = unit * 0.72
        bx = X(0) - unit * 0.0
        by = Y(-1.05)
        parts.append(svg_rect(bx, by, box_w, box_h,
                              fill="#ffffff", stroke=main_line, width=2, opacity=1.0, rx=12, ry=12))
        txt = f"Туслах хүрд: {s_divisor}×1={data['sub_vals'][0]['val']}, {s_divisor}×2={data['sub_vals'][1]['val']}, {s_divisor}×5={data['sub_vals'][2]['val']}"
        parts.append(svg_text(bx + 10, by + box_h * 0.62, txt, size=int(unit * 0.26), weight="800", fill=ink, anchor="start",
                              family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif"))

    # grid
    if show_grid:
        parts.append(svg_grid(X(0), Y(0), cols, rows, unit, stroke=grid_stroke, width=1, opacity=0.22 if not black else 0.28))

    # main vertical line
    parts.append(svg_line(X(max_digits), Y(0), X(max_digits), Y(rows), stroke=main_line, width=3, opacity=1.0))

    # header line under divisor
    parts.append(svg_line(X(max_digits), Y(1), X(cols), Y(1), stroke=main_line, width=3, opacity=1.0))

    # header numbers
    if stage >= 1:
        # dividend digits (right-aligned within left area)
        for i, ch in enumerate(s_dividend):
            col = max_digits - (len(s_dividend) - i)
            parts.append(svg_text(X(col) + unit * 0.5, Y(0) + unit * 0.72, ch, size=int(unit * 0.44), weight="800", fill=ink))

        # divisor digits (left area of right side)
        for i, ch in enumerate(s_divisor):
            col = max_digits + 1 + i
            parts.append(svg_text(X(col) + unit * 0.5, Y(0) + unit * 0.72, ch, size=int(unit * 0.44), weight="800", fill=ink))

    # side helper box
    if stage >= 1 and sub_pos == "side":
        bx = X(cols) + unit * 0.45
        by = Y(0)
        bw = unit * 3.4
        bh = unit * 2.6
        parts.append(svg_rect(bx, by, bw, bh, fill="#ffffff", stroke="#111827" if black else main_line, width=2, rx=16, ry=16))
        parts.append(svg_text(bx + bw * 0.5, by + unit * 0.6, "Туслах", size=int(unit * 0.34), weight="900", fill=ink,
                              family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif"))
        for r, item in enumerate(data["sub_vals"]):
            parts.append(svg_text(bx + unit * 0.28, by + unit * (1.15 + r * 0.55),
                                  f"{s_divisor}×{item['k']}={item['val']}",
                                  size=int(unit * 0.28), weight="800", fill=ink, anchor="start",
                                  family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif"))

    # steps (subtract rows + remainder rows)
    if stage >= 2:
        for idx, st in enumerate(steps):
            color = ink if (black or color_mode == 0) else css_color(STEP_COLORS[idx % len(STEP_COLORS)])

            # subtract row
            sub_row = 1 + 2 * idx
            # minus sign outside grid (like TeX x=-0.4)
            parts.append(svg_text(X(-0.7) + unit * 0.5, Y(sub_row) + unit * 0.72, "−", size=int(unit * 0.52), weight="900", fill=color))

            s_sub = str(int(st["sub"]))
            for j, ch in enumerate(s_sub):
                col = max_digits - (len(s_sub) - j)
                parts.append(svg_text(X(col) + unit * 0.5, Y(sub_row) + unit * 0.72, ch, size=int(unit * 0.44), weight="800", fill=color))

            # step quotient chunk on right side
            q_s = str(int(st["factor"]))
            for j, ch in enumerate(q_s):
                if align_mode == "left":
                    col = max_digits + 1 + j
                else:
                    col = max_digits + 1 + right_side_width - (len(q_s) - j)
                parts.append(svg_text(XR(col), Y(sub_row) + unit * 0.72, ch, size=int(unit * 0.44), weight="800", fill=color, anchor="end"))

            # line under subtract row across left side
            line_y = Y(sub_row + 1)
            parts.append(svg_line(X(0), line_y, X(max_digits), line_y, stroke="#111827" if black else "#111827", width=2, opacity=0.95))

            # remainder row
            rem_val = int(st["rem_before"]) - int(st["sub"])
            s_rem = str(rem_val)
            rem_row = sub_row + 1
            for j, ch in enumerate(s_rem):
                col = max_digits - (len(s_rem) - j)
                parts.append(svg_text(X(col) + unit * 0.5, Y(rem_row) + unit * 0.72, ch, size=int(unit * 0.44), weight="800", fill=ink))

    # footer: total quotient
    if stage >= 3:
        footer_y = 1 + 2 * len(steps) + 1
        parts.append(svg_line(X(max_digits), Y(footer_y), X(cols), Y(footer_y), stroke=main_line, width=3, opacity=1.0))

        for j, ch in enumerate(s_total_q):
            col = max_digits + 1 + right_side_width - (len(s_total_q) - j)
            parts.append(svg_text(XR(col), Y(footer_y) + unit * 0.72, ch, size=int(unit * 0.46), weight="900", fill=ink, anchor="end"))

        # remainder badge
        if show_remainder:
            rx = X(0)
            ry = Y(rows) + unit * 0.35
            parts.append(svg_rect(rx, ry, unit * 4.8, unit * 0.86, fill="#ffffff", stroke=main_line, width=2, rx=14, ry=14))
            parts.append(svg_text(rx + unit * 0.28, ry + unit * 0.58, f"Үлдэгдэл: {s_final_rem}", size=int(unit * 0.30),
                                  weight="900", fill=ink, anchor="start",
                                  family="ui-sans-serif, system-ui, Segoe UI, Roboto, Arial, sans-serif"))

    parts.append("</svg>")
    return "\n".join(parts), data


# =========================
