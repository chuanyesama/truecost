import pandas as pd

from src import costs
from tests.test_costbasis import trades


def test_mergeable_orders():
    t = trades((0, 10, 10), (0, 10, 10), (0, -5, 11))
    t.loc[1, "time"] += pd.Timedelta(minutes=3)   # same side, 3 min later -> mergeable
    t.loc[2, "time"] += pd.Timedelta(minutes=4)   # opposite side -> not
    m = costs._mergeable(t, 10)
    assert m.tolist() == [False, True, False]


def test_mergeable_respects_window():
    t = trades((0, 10, 10), (0, 10, 10))
    t.loc[1, "time"] += pd.Timedelta(minutes=30)
    assert costs._mergeable(t, 10).tolist() == [False, False]
