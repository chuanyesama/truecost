"""End to end: synthetic statement in several base currencies -> full report
must reconcile to ending NAV - net deposits."""
import importlib.util
from pathlib import Path

import pytest

from src import costs, report, style

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("make_sample", ROOT / "scripts" / "make_sample.py")
make_sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_sample)


@pytest.mark.parametrize("base, source", [("AUD", "rba"), ("AUD", "ecb"), ("USD", "ecb"), ("EUR", "ecb")])
def test_report_reconciles_in_any_base(tmp_path, base, source):
    path = tmp_path / f"sample_{base}.csv"
    make_sample.main(base, path)
    r = report.build(path, fx_source=source)
    assert r.base == base
    assert r.reconciles
    assert style.profile(r).insights
    assert costs.analyse(r, path).total > 0


def test_committed_sample_reconciles():
    r = report.build(ROOT / "data" / "sample" / "sample_statement.csv", fx_source="rba")
    assert r.reconciles and r.base == "AUD"
    assert (r.holdings["diluted_cost"] <= 0).any()  # demo shows a zero-cost holding
