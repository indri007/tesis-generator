"""Number parsing and mathematical calculation utilities."""

from __future__ import annotations

import ast
import re
from typing import Any


def parse_id_number(raw_str: str) -> float | None:
    """Parse Indonesian/English formatted numbers.
    e.g. '2,5' -> 2.5, '2.5' -> 2.5, '42.381' -> 42381, '120' -> 120.0
    """
    if raw_str is None:
        return None
    cleaned = str(raw_str).strip()
    # Remove currency or label prefixes
    cleaned = re.sub(r"^[^\d\-+]+", "", cleaned)
    cleaned = re.sub(r"[^\d\-+.,]+$", "", cleaned)

    if not cleaned:
        return None

    # Check Indonesian format: 42.381,50 or 42.381 (thousands dot)
    if re.search(r"^\d{1,3}(\.\d{3})+(,\d+)?$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    # Or Indonesian decimal without thousands: 2,5 or 0,032
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    # Or English thousands with comma: 42,381.50 or 42,381
    elif re.search(r"^\d{1,3}(,\d{3})+(\.\d+)?$", cleaned):
        cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_formula_expression(expr: str) -> str:
    """Normalize mathematical formula string into python-evaluable expression.
    e.g. '2,5 + 0,4X' -> '2.5 + 0.4 * X'
    'a + b1X1 + b2X2 + e' -> 'a + b1*X1 + b2*X2 + e'
    """
    # Replace Indonesian decimal comma preceded and followed by digits with dot
    res = re.sub(r"(\d+),(\d+)", r"\1.\2", expr)

    # Insert multiplication between number and variable, e.g. 0.4X -> 0.4 * X
    res = re.sub(r"(\d+(\.\d+)?)\s*([A-Za-z]\w*)", r"\1 * \3", res)

    # Convert ^ to **
    res = res.replace("^", "**")
    return res.strip()


def safe_evaluate_formula(
    formula_body: str,
    variable_values: dict[str, float]
) -> tuple[float | None, str | None]:
    """Safely evaluate a mathematical expression given variable inputs.
    Returns (result, error_message).
    """
    try:
        normalized = normalize_formula_expression(formula_body)
        # Parse AST to verify only safe mathematical operations
        node = ast.parse(normalized, mode="eval")

        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.Call, ast.Import, ast.ImportFrom, ast.Attribute)):
                return None, f"Operasi tidak diizinkan dalam ekspresi: {ast.dump(subnode)}"

        compiled = compile(node, "<formula>", "eval")
        # Build local scope from variable_values
        scope: dict[str, Any] = {k: v for k, v in variable_values.items()}
        val = eval(compiled, {"__builtins__": {}}, scope)
        return float(val), None
    except Exception as e:
        return None, f"Gagal mengevaluasi rumus: {e}"


def check_formula_recalculation(
    dependent_var: str,
    formula_body: str,
    inputs: dict[str, float],
    claimed_result: float,
    tolerance: float = 0.05
) -> dict[str, Any]:
    """Performs deterministic recalculation check as per Requirement #23.
    Returns audit dictionary with expected, claimed, delta, and status.
    """
    computed, err = safe_evaluate_formula(formula_body, inputs)
    if err or computed is None:
        return {
            "status": "UNVERIFIED",
            "reason": err or "Ekspresi tidak dapat dihitung otomatis",
            "expected": None,
            "claimed": claimed_result,
            "delta": None,
            "is_match": False
        }

    delta = abs(computed - claimed_result)
    is_match = delta <= tolerance

    return {
        "status": "PASS" if is_match else "ERROR",
        "dependent_var": dependent_var,
        "formula_body": formula_body,
        "inputs": inputs,
        "expected": round(computed, 4),
        "claimed": round(claimed_result, 4),
        "delta": round(delta, 4),
        "is_match": is_match,
        "message": (
            f"Hasil hitung valid ({claimed_result})"
            if is_match
            else f"Hasil perhitungan tidak konsisten: Ekspektasi {computed:.2f}, pada teks {claimed_result:.2f} (selisih {delta:.2f})"
        )
    }


def evaluate_hypothesis_significance(
    p_value: float,
    alpha: float = 0.05,
    claimed_significant: bool | None = None
) -> dict[str, Any]:
    """Evaluates statistical consistency of p-value against alpha and claimed decision."""
    is_significant = p_value < alpha
    result: dict[str, Any] = {
        "p_value": p_value,
        "alpha": alpha,
        "is_significant": is_significant,
        "expected_conclusion": "Signifikan" if is_significant else "Tidak Signifikan",
        "status": "PASS"
    }

    if claimed_significant is not None:
        if is_significant != claimed_significant:
            result["status"] = "ERROR"
            result["message"] = (
                f"Kesimpulan statistik bertentangan! Dengan p={p_value} dan alpha={alpha}, "
                f"data seharusnya {'Signifikan' if is_significant else 'Tidak Signifikan'}, "
                f"tetapi diklaim {'Signifikan' if claimed_significant else 'Tidak Signifikan'}."
            )
        else:
            result["status"] = "PASS"
            result["message"] = "Kesimpulan statistik konsisten dengan p-value dan alpha."

    return result
