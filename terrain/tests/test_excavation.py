"""Hand-checked excavation volumes."""

import pytest

from terrain.core import excavation, house
from terrain.core.excavation import Area
from terrain.core.survey import Point

# A 40 m square sloping up 0.1 m per metre eastward: z = 270 + 0.1 x.
PLANE = (
    Point(1, 0.0, 0.0, 270.0),
    Point(2, 40.0, 0.0, 274.0),
    Point(3, 40.0, 40.0, 274.0),
    Point(4, 0.0, 40.0, 270.0),
)
TRIANGLES = ((0, 1, 2), (0, 2, 3))
START, END = (0.0, 20.0), (40.0, 20.0)


def test_cut_and_fill_meet_where_the_ground_crosses_the_formation() -> None:
    """x 10-20 by 10 m against 271.5: ground crosses it at x = 15, leaving 0.5 m
    average over 5 m on each side, so 12.5 m³ cut and 12.5 m³ fill."""
    cut, fill = excavation.volumes(
        PLANE, TRIANGLES, START, END, Area(10.0, 20.0, -5.0, 5.0), 271.5, cell=1.0
    )
    assert (cut, fill) == pytest.approx((12.5, 12.5))


def test_pits_add_working_space_and_footings() -> None:
    """Garage level x 9-19 by 12 m (1 m working space) down to 269.5: ground is 0.5
    + 0.1 x above it, 1.9 m on average, so 228 m³. Its 36 m of footings at 0.6 x
    0.8 m are 17.28 m³. The rest of the house starts after the working space."""
    spec = house.HouseSpec(
        start=10.0,
        offset=0.0,
        length=20.0,
        width=10.0,
        lower_depth=8.0,
        garage_floor=270.0,
        lower_height=3.0,
        upper_height=3.0,
        pitch_deg=45.0,
    )
    shed = house.ShedSpec(
        start=30.0, offset=0.0, depth=2.0, length=10.0, floor=273.0, height=2.5
    )
    dig = excavation.DigSpec(
        floor_buildup=0.5, footing_width=0.6, footing_depth=0.8, working_space=1.0
    )
    garage, rest, shed_pit = excavation.pits(
        PLANE, TRIANGLES, START, END, spec, shed, dig, cell=1.0
    )

    assert garage.area == Area(9.0, 19.0, -6.0, 6.0)
    assert garage.formation == pytest.approx(269.5)
    assert garage.cut == pytest.approx(228.0)
    assert (garage.footing_length, garage.footings) == pytest.approx((36.0, 17.28))
    assert rest.area == Area(19.0, 30.0, -5.0, 5.0)
    assert rest.footing_length == pytest.approx(34.0)
    assert shed_pit.area == Area(30.0, 33.0, -6.0, 6.0)
    cut, fill = excavation.totals((garage, rest, shed_pit))
    assert cut == pytest.approx(
        sum(p.cut + p.footings for p in (garage, rest, shed_pit))
    )
    assert fill == pytest.approx(garage.fill + rest.fill + shed_pit.fill)
