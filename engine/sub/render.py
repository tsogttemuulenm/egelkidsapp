from __future__ import annotations

from typing import Dict, Any, Tuple, List

from engine.sub.algo import compute_egel_subtraction

def _esc(s: str) -> str:
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
             .replace('"',"&quot;").replace("'","&apos;"))

def render_svg(
    a: int,
    b: int,
    unit: int = 56,
    stage: int = 3,
    show_grid: bool = True,
    show_marks: bool = True,
) -> Tuple[str, Dict[str, Any]]:
    """Render subtraction (completion method) as SVG.

    Unified stage:
      0: grid only
      1: show A,B and '-' sign
      2: + borrowed row + underline (if show_marks)
      3: + result row
    """
    trace = compute_egel_subtraction(a, b)
    n = trace["digits"]

    # Layout similar to addition: one sign column + n digit columns
    cols = n + 1
    # rows: A, B, borrowed, result
    # (User request) Move both input numbers up by one cell, and put the
    # borrowed ("zээлсэн") digits in the cells directly below the inputs.
    rows = 4
    pad = int(unit * 0.45)
    width = pad*2 + cols*unit
    height = pad*2 + rows*unit

    def X(c: int) -> int:
        return pad + c*unit
    def Y(r: int) -> int:
        return pad + r*unit

    def text(x: float, y: float, s: str, size: int, weight: str="800", fill: str="#000", anchor: str="middle"):
        return f"<text x='{x:.2f}' y='{y:.2f}' text-anchor='{anchor}' dominant-baseline='middle' font-family='ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial' font-size='{size}' font-weight='{weight}' fill='{fill}'>" + _esc(s) + "</text>"

    parts: List[str]=[]
    parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>")
    parts.append(f"<rect x='0' y='0' width='{width}' height='{height}' fill='white'/>")

    if show_grid and stage >= 0:
        x0,y0 = pad,pad
        w,h = cols*unit, rows*unit
        parts.append(f"<rect x='{x0}' y='{y0}' width='{w}' height='{h}' fill='none' stroke='#b3d1ff' stroke-width='2'/>")
        for c in range(1, cols):
            parts.append(f"<line x1='{X(c)}' y1='{y0}' x2='{X(c)}' y2='{y0+h}' stroke='#cfe3ff' stroke-width='1.5'/>")
        for r in range(1, rows):
            parts.append(f"<line x1='{x0}' y1='{Y(r)}' x2='{x0+w}' y2='{Y(r)}' stroke='#cfe3ff' stroke-width='1.5'/>")

    font_big = int(unit*0.50)
    font_small = int(unit*0.36)

    # digit columns mapping: place 0 (units) at rightmost digit column (cols-1)
    def col_for_place(place: int) -> int:
        return cols-1 - place

    if stage >= 1:
        # '-' sign in sign column, aligned with B row (row 1)
        parts.append(text(X(0)+unit*0.5, Y(1)+unit*0.5, "−", size=font_big, weight="900"))
        # A digits on row 0, B digits on row 1
        a_p = trace["a_padded"]
        b_p = trace["b_padded"]
        for i,ch in enumerate(reversed(a_p)):  # units first
            c = col_for_place(i)
            parts.append(text(X(c)+unit*0.5, Y(0)+unit*0.5, ch, size=font_big))
        for i,ch in enumerate(reversed(b_p)):
            c = col_for_place(i)
            parts.append(text(X(c)+unit*0.5, Y(1)+unit*0.5, ch, size=font_big))

    if stage >= 2 and show_marks:
        # Borrowed/carry digits:
        # (User request) Put them in the cells directly below the input numbers,
        # i.e., in the dedicated "borrowed" row (row 2).
        carries = trace["carries_in"]
        for pos,cv in enumerate(carries):
            if cv:
                place = (n-1) - pos
                c = col_for_place(place)
                parts.append(text(
                    X(c)+unit*0.5,
                    Y(2)+unit*0.5,   # borrowed row center
                    str(cv),
                    size=font_small,
                    weight="800",
                    fill="#e53935",
                ))
        # underline between borrowed and result (under borrowed row)
        x1 = X(0)
        x2 = X(cols)
        y = Y(3)  # top of result row
        parts.append(f"<line x1='{x1}' y1='{y}' x2='{x2}' y2='{y}' stroke='#1e88e5' stroke-width='{max(2,int(unit*0.06))}'/>")

    if stage >= 3:
        # result digits row 3
        res_digits = trace["result_digits"]
        for i,d in enumerate(reversed(res_digits)):
            c = col_for_place(i)
            parts.append(text(X(c)+unit*0.5, Y(3)+unit*0.5, str(d), size=font_big, fill="#0b5d1e"))
    # warning if final_carry == 1 (a < b)
    if trace.get("final_carry",0)==1:
        parts.append(text(width - pad, pad*0.55, "⚠ A < B байж магадгүй", size=int(unit*0.28), weight="700", fill="#cc0000", anchor="end"))

    parts.append("</svg>")
    return "\n".join(parts), {"trace": trace}
