# Эгэл ENGINE — Unified v2 (ADD + SUB + MUL + DIV)

Энэ нь таны өгсөн `egel_add_web` болон `egel_div_web_game_interactive_viz_FIXED` төслүүдээс
**➕ Нэмэх + ➗ Хуваах**-ыг нэг UI дээр нэгтгэсэн MVP хувилбар.

## Ажиллуулах (Windows / Linux / macOS)

```bash
cd apps/web/backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r ../../../../requirements.txt
python app.py
```

Дараа нь:
- http://127.0.0.1:8000

## API

- `/api/render?op=add|div&a=...&b=...&unit=...&stage=0..3&show_grid=true|false&show_marks=true|false`
- `/api/trace?op=add|div&a=...&b=...`

Тайлбар:
- `div` дээр `a=dividend`, `b=divisor (>=1)`
- `add` дээр `a` ба `b` нь хоёр нэмэгдэхүүн


## Kids UI
- Default opens in **🎮 Тоглох** mode with levels, stars, streak.
- Switch to **📘 Суралцах** for manual inputs and full controls.
