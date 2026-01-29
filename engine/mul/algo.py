from __future__ import annotations
from typing import Dict, Any

def compute_egel_multiplication(a: int, b: int) -> Dict[str, Any]:
    if a < 0 or b < 0:
        raise ValueError("A and B must be non-negative integers.")
    return {"op":"mul","a":int(a),"b":int(b),"result":int(a)*int(b)}
