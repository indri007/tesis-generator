"""Mathematical formula parser, symbol extractor, and equation structure detector."""

from __future__ import annotations

import re
from typing import Any


class FormulaParser:
    """Extracts mathematical models, regression equations, variables, and calculation cases."""

    def __init__(self, raw_text: str):
        self.raw_text = raw_text

    def extract_equations(self) -> list[dict[str, Any]]:
        """Extracts candidate regression or algebraic formulas from document."""
        # Common patterns:
        # Y = a + bX + e
        # Y = 2,5 + 0,4X
        # Y = \beta_0 + \beta_1 X_1 + ...
        # Persamaan 3.1: Y = ...
        pattern = re.compile(
            r"(?:(?:Persamaan|Rumus)\s+(\d+\.\d+)[\s:=-]+)?([A-Z]\w*)\s*=\s*([0-9a-zA-Z\s\+\-\*\/\^\,\.\(\)\_]+)",
            re.IGNORECASE
        )

        equations = []
        for line in self.raw_text.splitlines():
            line_str = line.strip()
            # Must contain an equality sign and regression/formula characteristics
            if "=" in line_str and any(sym in line_str for sym in ["+", "-", "*", "/", "X", "Y", "e", "β", "beta"]):
                m = pattern.search(line_str)
                if m:
                    eq_id = m.group(1) or ""
                    dep_var = m.group(2).strip()
                    body = m.group(3).strip()

                    # Avoid capturing normal text sentences containing "="
                    if len(body) > 60 or " " in dep_var or any(w in body.lower() for w in ["adalah", "karena", "sebagaimana"]):
                        continue

                    # Extract variable symbols inside body
                    var_symbols = re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\b", body)
                    # Filter out purely numeric or common words
                    filtered_vars = [
                        v for v in var_symbols
                        if not v.isdigit() and v.lower() not in ["dan", "or", "log", "exp", "sin", "cos"]
                    ]

                    equations.append({
                        "id": eq_id,
                        "raw_line": line_str,
                        "dependent_var": dep_var,
                        "body": body,
                        "variables": filtered_vars
                    })
        return equations

    def extract_recalculation_cases(self) -> list[dict[str, Any]]:
        """Finds instances where a formula with coefficients is accompanied by input and claimed output.
        E.g.:
        Y = 2,5 + 0,4X
        X = 10
        Y = 7,5 (or claimed Y = 6,5)
        """
        cases = []
        text_lines = [l.strip() for l in self.raw_text.splitlines() if l.strip()]

        for i in range(len(text_lines) - 2):
            l1, l2, l3 = text_lines[i], text_lines[i + 1], text_lines[i + 2]

            # Look for Y = num + num X
            m_formula = re.search(r"\b([A-Z])\s*=\s*([0-9.,]+)\s*([\+\-])\s*([0-9.,]+)\s*([A-Z]\w*)", l1)
            # Look for input variable: X = 10
            m_input = re.search(r"\b([A-Z]\w*)\s*=\s*([0-9.,]+)", l2)
            # Look for claimed result: Y = 7,5
            m_result = re.search(r"\b([A-Z])\s*=\s*([0-9.,]+)", l3)

            if m_formula and m_input and m_result:
                dep_f = m_formula.group(1)
                const_a = m_formula.group(2)
                op = m_formula.group(3)
                coeff_b = m_formula.group(4)
                var_x = m_formula.group(5)

                input_var = m_input.group(1)
                input_val = m_input.group(2)

                res_dep = m_result.group(1)
                claimed_val = m_result.group(2)

                if var_x.upper() == input_var.upper() and dep_f.upper() == res_dep.upper():
                    formula_str = f"{const_a} {op} {coeff_b}{var_x}"
                    cases.append({
                        "dependent_var": dep_f,
                        "formula_body": formula_str,
                        "input_var": var_x,
                        "input_value": input_val,
                        "claimed_result": claimed_val,
                        "context": f"{l1}\n{l2}\n{l3}"
                    })
        return cases
