from __future__ import annotations

from typing import Dict, Any, List

def compute_egel_subtraction(a: int, b: int) -> Dict[str, Any]:
    """Completion-based subtraction ("гүйцээх" логик) producing a trace.

    This follows the same rules as the user's existing egel_hasah_web:
      sub_val = b_digit + carry
      if sub_val > a_digit:
          comp = 10 - sub_val
          res  = comp + a_digit
          carry_out = 1
      else:
          res = a_digit - sub_val
          carry_out = 0

    Note: Classroom usage usually assumes a >= b. If final_carry==1, it indicates mismatch.
    """
    if a < 0 or b < 0:
        raise ValueError("A and B must be non-negative integers.")
    a_str=str(a)
    b_str=str(b)
    n=max(len(a_str), len(b_str))
    a_p=a_str.zfill(n)
    b_p=b_str.zfill(n)

    carry=0
    result=[0]*n
    carries_in=[0]*n
    raw_steps: List[Dict[str, Any]]=[]
    for pos in range(n-1, -1, -1):
        ad=int(a_p[pos]); bd=int(b_p[pos])
        carries_in[pos]=carry
        sub_val=bd+carry
        if sub_val>ad:
            comp=10-sub_val
            res=comp+ad
            carry_out=1
            rule="complete"
        else:
            comp=None
            res=ad-sub_val
            carry_out=0
            rule="fit"
        result[pos]=res
        raw_steps.append({
            "pos": pos,
            "a": ad,
            "b": bd,
            "carry_in": carry,
            "sub_val": sub_val,
            "rule": rule,
            "comp": comp,
            "res": res,
            "carry_out": carry_out,
        })
        carry=carry_out

    result_str="".join(str(d) for d in result).lstrip("0") or "0"
    steps_lr=list(reversed(raw_steps))
    return {
        "op": "sub",
        "a": a,
        "b": b,
        "a_padded": a_p,
        "b_padded": b_p,
        "digits": n,
        "carries_in": carries_in,
        "steps": steps_lr,
        "result_digits": result,
        "result": int(result_str),
        "result_str": result_str,
        "final_carry": carry,
    }
