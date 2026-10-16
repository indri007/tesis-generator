"""Unit tests for Quality, Testing & CI/CD Clones (Tools 21–30)."""

import pytest
from core.clones.quality_and_testing import (
    CoverageClone,
    HypothesisClone,
    MypyPyrightClone,
    MutmutClone,
    PreCommitClone,
    PytestClone,
    RuffBanditClone,
)


def test_pytest_clone_test_runner():
    runner = PytestClone()

    def test_pass_1():
        assert 1 + 1 == 2

    def test_pass_2():
        assert "a".upper() == "A"

    def test_fail():
        assert 1 == 2, "1 is not 2"

    res = runner.run_tests([test_pass_1, test_pass_2, test_fail])
    assert res["total_tests"] == 3
    assert res["passed"] == 2
    assert res["failed"] == 1
    assert res["all_passed"] is False


def test_hypothesis_clone_property_testing():
    hyp = HypothesisClone()

    # Invariant: x + 0 == x for all integers
    def property_addition_identity(x: int):
        assert x + 0 == x

    success = hyp.given_integers(property_addition_identity, trials=15)
    assert success is True


def test_mutmut_clone_mutation_audit():
    mut = MutmutClone()

    def add(a: int, b: int) -> int:
        return a + b

    def test_add(fn):
        return fn(2, 3) == 5

    res = mut.run_mutation_audit(add, test_add)
    assert res["total_mutants"] == 3
    assert res["killed_mutants"] == 3
    assert res["mutation_score_pct"] == 100.0


def test_coverage_clone_percentage():
    cov = CoverageClone()
    res = cov.measure_coverage(total_statements=100, executed_statements=88)
    assert res["coverage_percentage"] == 88.0
    assert res["meets_mikom_threshold"] is True
    assert res["missed_statements"] == 12


def test_ruff_bandit_clone_security_audit():
    scanner = RuffBanditClone()

    bad_code = """
def run_query(user_input):
    api_token = "secret_12345678"
    eval(user_input)
    try:
        x = 1 / 0
    except:
        pass
"""
    res = scanner.audit_python_code(bad_code)
    assert res["syntax_valid"] is True
    assert res["high_severity_count"] >= 2
    assert res["clean_code"] is False

    clean_code = """
def safe_addition(a: int, b: int) -> int:
    return a + b
"""
    res_clean = scanner.audit_python_code(clean_code)
    assert res_clean["clean_code"] is True
    assert res_clean["total_issues"] == 0


def test_mypy_pyright_clone_type_hints():
    checker = MypyPyrightClone()

    def fully_typed(a: int, b: str) -> bool:
        return len(b) == a

    res_typed = checker.check_type_hints(fully_typed)
    assert res_typed["is_fully_typed"] is True

    def untyped(a, b):
        return a + b

    res_untyped = checker.check_type_hints(untyped)
    assert res_untyped["is_fully_typed"] is False
    assert len(res_untyped["missing_param_annotations"]) == 2
    assert res_untyped["missing_return_annotation"] is True


def test_pre_commit_clone_orchestration():
    pre = PreCommitClone()
    pre.add_hook("ruff_lint", lambda: True)
    pre.add_hook("unit_tests", lambda: True)
    pre.add_hook("security_scan", lambda: True)

    res = pre.run_all_hooks()
    assert res["all_passed"] is True
    assert res["total_hooks"] == 3
    assert res["passed_count"] == 3
