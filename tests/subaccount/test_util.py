from greenbudget.app.budget.models import Fringe
from greenbudget.app.subaccount.utils import fringe_value


def test_fringe_value(create_budget, create_fringe):
    budget = create_budget()
    fringes = [
        create_fringe(
            budget=budget, cutoff=50, rate=0.5, unit=Fringe.UNITS.percent),
        create_fringe(budget=budget, rate=None),
        create_fringe(
            budget=budget, cutoff=20, rate=100, unit=Fringe.UNITS.flat),
        create_fringe(budget=budget, rate=100, unit=Fringe.UNITS.flat),
        create_fringe(budget=budget, rate=0.1, unit=Fringe.UNITS.percent)
    ]
    original_value = 100
    value = fringe_value(original_value, fringes[:1])
    assert value == 125.0
    value = fringe_value(original_value, fringes[:2])
    assert value == 125.0
    value = fringe_value(original_value, fringes[:3])
    assert value == 225.0
    value = fringe_value(original_value, fringes[:4])
    assert value == 325.0
    value = fringe_value(original_value, fringes)
    assert value == 335.0

    # Make sure the value is independent of the order in which we apply the
    # fringes.
    fringes.reverse()
    value = fringe_value(100, fringes)
    assert value == 335.0
