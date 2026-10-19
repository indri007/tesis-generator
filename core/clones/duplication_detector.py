"""Code & Data Duplication Detection Clones (jscpd, Simian, SonarQube, DataComPy, Dedupe, pandas).

Zero-cloud, deterministic offline implementations:
1. jscpd & Simian: Token-level code block duplication detection.
2. SonarQube: Cognitive complexity calculation, code smell identification, and duplicate line tracking.
3. DataComPy: Tabular dataset comparison, reporting row mismatches, schema differences, and value drifts.
4. Dedupe: Fuzzy entity resolution and deduplication on academic metadata.
5. PandasDuplication: Row-level duplicate finding with custom subsets.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Optional


# ==============================================================================
# 1. JSCPD & SIMIAN CLONES (Token-Based Duplicate Code Detection)
# ==============================================================================
@dataclass
class DuplicateCloneBlock:
    source_a: str
    line_start_a: int
    source_b: str
    line_start_b: int
    lines_count: int
    tokens_count: int
    duplicated_snippet: str


class JscpdClone:
    """Clones jscpd & Simian: Finds duplicate code blocks across files or strings."""

    def __init__(self, min_tokens: int = 20, min_lines: int = 4):
        self.min_tokens = min_tokens
        self.min_lines = min_lines

    def find_code_duplicates(self, files: dict[str, str]) -> list[DuplicateCloneBlock]:
        """Scans code files and identifies identical token sequences."""
        duplicates: list[DuplicateCloneBlock] = []
        file_items = list(files.items())

        for i in range(len(file_items)):
            name_a, content_a = file_items[i]
            lines_a = [line.strip() for line in content_a.splitlines() if line.strip() and not line.strip().startswith("#")]

            for j in range(i, len(file_items)):
                name_b, content_b = file_items[j]
                lines_b = [line.strip() for line in content_b.splitlines() if line.strip() and not line.strip().startswith("#")]

                # Sliding window of min_lines
                for idx_a in range(len(lines_a) - self.min_lines + 1):
                    chunk_a = lines_a[idx_a : idx_a + self.min_lines]
                    start_b = idx_a + 1 if i == j else 0

                    for idx_b in range(start_b, len(lines_b) - self.min_lines + 1):
                        chunk_b = lines_b[idx_b : idx_b + self.min_lines]
                        if chunk_a == chunk_b:
                            tokens = sum(len(re.findall(r"\w+", line)) for line in chunk_a)
                            if tokens >= self.min_tokens:
                                duplicates.append(
                                    DuplicateCloneBlock(
                                        source_a=name_a,
                                        line_start_a=idx_a + 1,
                                        source_b=name_b,
                                        line_start_b=idx_b + 1,
                                        lines_count=self.min_lines,
                                        tokens_count=tokens,
                                        duplicated_snippet="\n".join(chunk_a[:2]) + "\n...",
                                    )
                                )
        return duplicates


# Simian duplicate detector alias
SimianClone = JscpdClone


# ==============================================================================
# 2. SONARQUBE CLONE (Quality, Complexity & Duplication Metrics)
# ==============================================================================
class SonarQubeClone:
    """Clones SonarQube: Calculates cognitive complexity, code smell density, and duplicate line %."""

    def audit_code_quality(self, code: str) -> dict[str, Any]:
        lines = code.splitlines()
        total_lines = max(1, len(lines))

        # Cognitive complexity: indentations, nested loops, branching
        cognitive_complexity = 0
        code_smells = []
        seen_lines: set[str] = set()
        dup_lines = 0

        for idx, line in enumerate(lines, 1):
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue

            # Check duplicate non-trivial lines
            if len(clean) > 15:
                if clean in seen_lines:
                    dup_lines += 1
                seen_lines.add(clean)

            # Complexity points
            if any(k in clean for k in ("if ", "elif ", "for ", "while ", "except ")):
                indent = len(line) - len(clean)
                nesting = max(1, indent // 4)
                cognitive_complexity += nesting

            # Code smell checks
            if len(clean) > 120:
                code_smells.append(f"Line {idx}: Line exceeds 120 characters")
            if "print(" in clean:
                code_smells.append(f"Line {idx}: Direct print statement found instead of logging")

        dup_pct = round((dup_lines / total_lines) * 100, 2)
        rating = "A" if cognitive_complexity < 15 and dup_pct < 5.0 else "B" if cognitive_complexity < 30 else "C"

        return {
            "total_lines": total_lines,
            "cognitive_complexity": cognitive_complexity,
            "code_smell_count": len(code_smells),
            "code_smells": code_smells,
            "duplicated_line_percentage": dup_pct,
            "maintainability_rating": rating,
        }


# ==============================================================================
# 3. DATACOMPY CLONE (Dataset Comparison & Drift Analysis)
# ==============================================================================
class DataComPyClone:
    """Clones DataComPy: Compares two tabular datasets and detects schema/value differences."""

    def compare(
        self,
        df1: list[dict[str, Any]],
        df2: list[dict[str, Any]],
        join_columns: list[str],
    ) -> dict[str, Any]:
        cols1 = set(df1[0].keys()) if df1 else set()
        cols2 = set(df2[0].keys()) if df2 else set()

        col_intersection = cols1 & cols2
        col_diff1 = cols1 - cols2
        col_diff2 = cols2 - cols1

        dict1 = {tuple(str(r.get(c)) for c in join_columns): r for r in df1}
        dict2 = {tuple(str(r.get(c)) for c in join_columns): r for r in df2}

        shared_keys = set(dict1.keys()) & set(dict2.keys())
        only_in_df1 = len(dict1) - len(shared_keys)
        only_in_df2 = len(dict2) - len(shared_keys)

        value_mismatches = 0
        for k in shared_keys:
            r1, r2 = dict1[k], dict2[k]
            for c in col_intersection:
                if str(r1.get(c)) != str(r2.get(c)):
                    value_mismatches += 1

        matches = (len(shared_keys) == len(df1) == len(df2)) and value_mismatches == 0
        return {
            "datasets_match": matches,
            "rows_in_df1": len(df1),
            "rows_in_df2": len(df2),
            "intersect_rows": len(shared_keys),
            "only_in_df1_count": only_in_df1,
            "only_in_df2_count": only_in_df2,
            "column_mismatch_count": len(col_diff1) + len(col_diff2),
            "value_mismatches": value_mismatches,
        }


# ==============================================================================
# 4. DEDUPE CLONE (Fuzzy Entity Resolution & Deduplication)
# ==============================================================================
class DedupeClone:
    """Clones Dedupe: Entity deduplication and fuzzy clustering on bibliographic records."""

    def deduplicate(
        self,
        records: list[dict[str, Any]],
        key_field: str = "title",
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        clusters = []
        seen_indices = set()

        for i, rec1 in enumerate(records):
            if i in seen_indices:
                continue
            val1 = str(rec1.get(key_field, "")).lower()
            current_cluster = [rec1]
            seen_indices.add(i)

            for j in range(i + 1, len(records)):
                if j in seen_indices:
                    continue
                val2 = str(records[j].get(key_field, "")).lower()
                sim = difflib.SequenceMatcher(None, val1, val2).ratio()
                if sim >= threshold:
                    current_cluster.append(records[j])
                    seen_indices.add(j)

            clusters.append({
                "canonical_record": current_cluster[0],
                "duplicate_count": len(current_cluster) - 1,
                "cluster_records": current_cluster,
            })

        return clusters


# ==============================================================================
# 5. PANDAS DUPLICATION CLONE (Row Duplicate Identification)
# ==============================================================================
class PandasDuplicationClone:
    """Clones pandas.DataFrame.duplicated: Finds and marks duplicate records."""

    @staticmethod
    def identify_duplicates(
        records: list[dict[str, Any]],
        subset: Optional[list[str]] = None,
        keep: str = "first",
    ) -> list[dict[str, Any]]:
        seen_keys: set[str] = set()
        annotated: list[dict[str, Any]] = []

        for rec in records:
            if subset:
                key_items = [str(rec.get(c, "")) for c in subset]
            else:
                key_items = [f"{k}:{v}" for k, v in sorted(rec.items())]
            key_hash = hashlib.sha256("||".join(key_items).encode("utf-8")).hexdigest()

            is_dup = key_hash in seen_keys
            seen_keys.add(key_hash)

            rec_copy = dict(rec)
            rec_copy["is_duplicate"] = is_dup
            annotated.append(rec_copy)

        return annotated
