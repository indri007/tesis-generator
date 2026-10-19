"""Formula Auditor: Performs deterministic recalculations, notation checks, and model consistency."""

from __future__ import annotations

import re
from typing import Any

from models.document_model import ParsedDocument
from parsers.formula_parser import FormulaParser
from utils.number_utils import check_formula_recalculation, parse_id_number


class FormulaAuditor:
    """Audits mathematical models, notation consistency, and arithmetic recalculation."""

    def __init__(self, document: ParsedDocument):
        self.doc = document
        self.text = document.get_text()
        self.parser = FormulaParser(self.text)

    def audit(self) -> list[dict[str, Any]]:
        findings = []

        # 1. Recalculation Check (Requirement #23: e.g. Y = 2,5 + 0,4X with X=10 -> expected 6,5, claimed 7,5)
        cases = self.parser.extract_recalculation_cases()
        for case in cases:
            dep_var = case["dependent_var"]
            f_body = case["formula_body"]
            input_v = case["input_var"]
            input_num = parse_id_number(case["input_value"])
            claimed_num = parse_id_number(case["claimed_result"])

            if input_num is not None and claimed_num is not None:
                eval_res = check_formula_recalculation(
                    dep_var, f_body, {input_v: input_num}, claimed_num
                )

                if eval_res["status"] == "ERROR":
                    findings.append({
                        "rule_id": "FORMULA_RECALCULATION_001",
                        "category": "Formula",
                        "status": "ERROR",
                        "field": "formulas.arithmetic_error_count",
                        "actual": f"{dep_var} = {claimed_num}",
                        "expected": f"{dep_var} = {eval_res['expected']} (berdasarkan {dep_var} = {f_body} pada {input_v} = {input_num})",
                        "message": (
                            f"Hasil perhitungan tidak konsisten: Ekspektasi {eval_res['expected']}, "
                            f"pada naskah tertulis {claimed_num} (selisih {eval_res['delta']})."
                        ),
                        "evidence_query": f"{dep_var} = {case['claimed_result']}",
                        "recommendation": (
                            f"Koreksi hasil perhitungan {dep_var} menjadi {eval_res['expected']} "
                            f"atau periksa kembali angka input dan koefisien model."
                        ),
                        "source": {
                            "document": "Ketepatan Kalkulasi Aritmetika Matematis",
                            "page": None,
                            "verified": True
                        }
                    })

        # 2. Check symbol definitions
        equations = self.parser.extract_equations()
        for eq in equations:
            variables = eq["variables"]
            for var in variables:
                if var in ["X", "Y", "X1", "X2", "Z", "M"]:
                    # Check if variable is defined anywhere in the text
                    var_def_pattern = re.compile(rf"\b{re.escape(var)}\b\s*(?:=|adalah|merupakan|yakni|yaitu)", re.IGNORECASE)
                    if not var_def_pattern.search(self.text):
                        findings.append({
                            "rule_id": "FORMULA_SYMBOL_DEF_001",
                            "category": "Formula",
                            "status": "WARNING",
                            "field": "formulas.symbol_definitions",
                            "actual": f"Variabel {var} belum ditemukan definisinya",
                            "expected": "Setiap simbol variabel memiliki definisi operasional",
                            "message": f"Variabel '{var}' pada persamaan {eq.get('id', '')} belum memiliki definisi yang jelas.",
                            "evidence_query": eq["raw_line"],
                            "recommendation": f"Berikan keterangan definisi operasional untuk variabel '{var}'.",
                            "source": {"document": "Kaidah Notasi Matematis", "page": None, "verified": True}
                        })

        return findings
