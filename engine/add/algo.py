from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict


@dataclass(frozen=True)
class Underline:
    """Marks that in column `col` a '10-completion' happened at a given row.

    row:
      - 0..n_addends-1 refers to addend rows (top to bottom as entered)
      - -1 refers to the carry-in cell (when carry-in triggers a new ten)
    col: 0 = units, 1 = tens, ...
    """

    row: int
    col: int


@dataclass(frozen=True)
class ColumnTrace:
    col: int
    digits: List[int]          # digits of each addend in this column
    carry_in: int
    carry_out: int
    result_digit: int
    underlines: List[Underline]


@dataclass(frozen=True)
class EgelAddTrace:
    addends: List[int]
    sum_value: int
    max_digits: int
    columns: List[ColumnTrace]
    warnings: List[str]


def _digits(n: int) -> List[int]:
    if n == 0:
        return [0]
    out: List[int] = []
    while n > 0:
        out.append(n % 10)
        n //= 10
    return out  # least significant first


def compute_egel_addition(addends: List[int]) -> EgelAddTrace:
    """Compute an 'Эгэл нэмэх' trace for the given non-negative integers."""

    if not addends:
        raise ValueError("At least one addend is required")

    if any((not isinstance(x, int)) for x in addends):
        raise TypeError("All addends must be integers")

    if any(x < 0 for x in addends):
        raise ValueError("Only non-negative integers are supported")

    add_digits = [_digits(x) for x in addends]
    max_digits = max(len(d) for d in add_digits)

    warnings: List[str] = []
    columns: List[ColumnTrace] = []

    carry_in = 0

    for col in range(max_digits):
        digits_here = [d[col] if col < len(d) else 0 for d in add_digits]

        s = 0
        carry_out = 0
        underlines: List[Underline] = []

        # Add addend digits from top to bottom.
        for r, dig in enumerate(digits_here):
            s += dig
            if s >= 10:
                underlines.append(Underline(row=r, col=col))
                s -= 10
                carry_out += 1

        # Add carry-in at the end (so it is visible, not hidden).
        if carry_in:
            s += carry_in
            if s >= 10:
                underlines.append(Underline(row=-1, col=col))
                s -= 10
                carry_out += 1

        result_digit = s

        if carry_out >= 10:
            warnings.append(
                f"Column {col} produced carry_out={carry_out} (>=10). "
                "For primary grades, prefer fewer addends / smaller digits."
            )

        columns.append(
            ColumnTrace(
                col=col,
                digits=digits_here,
                carry_in=carry_in,
                carry_out=carry_out,
                result_digit=result_digit,
                underlines=underlines,
            )
        )

        carry_in = carry_out

    # After the last existing digit column, carry_in becomes the most significant part.
    # We keep it as an integer and let renderers decide how to display it.
    sum_value = sum(addends)

    if carry_in:
        # Represent the final carry as an extra synthetic column for better visualization.
        col = max_digits
        digits_here = [0 for _ in addends]
        s = 0
        carry_out = 0
        underlines: List[Underline] = []

        # Only carry-in exists here.
        s += carry_in
        # If carry_in >= 10, it conceptually spans multiple digits. We'll warn and show it.
        if s >= 10:
            warnings.append(
                f"Final carry_in={carry_in} is multi-digit. It will be shown as a number in the carry row."
            )
        # For result digits, we take the ones digit; remaining part stays as 'carry_out' (not typical for grade 1).
        result_digit = s % 10
        carry_out = s // 10

        columns.append(
            ColumnTrace(
                col=col,
                digits=digits_here,
                carry_in=carry_in,
                carry_out=carry_out,
                result_digit=result_digit,
                underlines=underlines,
            )
        )

        max_digits = max_digits + 1

    return EgelAddTrace(
        addends=addends,
        sum_value=sum_value,
        max_digits=max_digits,
        columns=columns,
        warnings=warnings,
    )
