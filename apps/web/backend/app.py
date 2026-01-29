from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path (so `engine` can be imported when running from apps/web/backend)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from engine.add.render import render_svg as render_add_svg
from engine.div.core import render_division_svg, calculate_egel_huvaah
from engine.sub.render import render_svg as render_sub_svg
from engine.sub.algo import compute_egel_subtraction
from engine.mul.render import render_svg as render_mul_svg
from engine.mul.algo import compute_egel_multiplication

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR.parent / "static"

app = FastAPI(title="Egel Engine Unified v2 (ADD + SUB + MUL + DIV)")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def _bool(v: bool) -> bool:
    return bool(v)


@app.get("/api/render")
def api_render(
    op: Literal["add", "sub", "mul", "div"] = Query("add"),
    a: int = Query(8541, ge=0),
    b: int = Query(1973, ge=0),
    unit: int = Query(56, ge=28, le=96),
    stage: int = Query(3, ge=0, le=3),
    show_grid: bool = Query(True),
    show_marks: bool = Query(True),
    color_mode: int = Query(1, ge=0, le=3),
    align: Literal["left", "right"] = Query("right"),
    sub_pos: Literal["top", "side", "none"] = Query("top"),
    show_remainder: bool = Query(True),
):
    """
    Unified SVG renderer.

    - add: a+b using "Эгэл нэмэх" (stage is mapped to add-stage 1..5)
    - div: a/b using "Эгэл багтаах" (a=dividend, b=divisor)
    """
    try:
        if op == "add":
            # map unified stage 0..3 => add stage 2..5 (so it always reveals useful parts)
            add_stage = max(1, min(5, stage + 2))
            svg, _data = render_add_svg(
                addends=[int(a), int(b)],
                cell=int(unit),
                pad=int(unit * 0.42),
                show_grid=_bool(show_grid),
                show_underlines=_bool(show_marks),
                show_carry=_bool(show_marks),
                stage=int(add_stage),
            )
            return Response(content=svg, media_type="image/svg+xml")


        if op == "sub":
            svg, _data = render_sub_svg(
                a=int(a),
                b=int(b),
                unit=int(unit),
                stage=int(stage),
                show_grid=_bool(show_grid),
                show_marks=_bool(show_marks),
            )
            return Response(content=svg, media_type="image/svg+xml")

        if op == "mul":
            svg, _data = render_mul_svg(
                a=int(a),
                b=int(b),
                unit=int(unit),
                stage=int(stage),
                show_grid=_bool(show_grid),
                show_marks=_bool(show_marks),
                color_mode=int(color_mode),
            )
            return Response(content=svg, media_type="image/svg+xml")

        # div
        if int(b) <= 0:
            return JSONResponse({"error": "Divisor (b) must be >= 1 for division."}, status_code=400)

        svg, _data = render_division_svg(
            dividend=int(a),
            divisor=int(b),
            unit=int(unit),
            stage=int(stage),
            show_grid=_bool(show_grid),
            color_mode=int(color_mode),
            align_mode=str(align),
            sub_pos=str(sub_pos),
            black=False,
            show_remainder=_bool(show_remainder),
        )
        return Response(content=svg, media_type="image/svg+xml")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/trace")
def api_trace(
    op: Literal["add", "sub", "mul", "div"] = Query("add"),
    a: int = Query(8541, ge=0),
    b: int = Query(1973, ge=0),
):
    """
    Unified trace endpoint (JSON).
    """
    try:
        if op == "add":
            # use renderer to produce trace in same format as original add app
            _svg, data = render_add_svg(addends=[int(a), int(b)])
            return JSONResponse(data["trace"])


        if op == "sub":
            return JSONResponse(compute_egel_subtraction(int(a), int(b)))

        if op == "mul":
            return JSONResponse(compute_egel_multiplication(int(a), int(b)))

        if int(b) <= 0:
            return JSONResponse({"error": "Divisor (b) must be >= 1 for division."}, status_code=400)

        return JSONResponse(calculate_egel_huvaah(int(a), int(b)))
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
