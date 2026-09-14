"""Survey rows in the plot frame."""

import pytest

from terrain.core import survey

ROWS = """
         1  489191.47  1201769.56  271.42
         3  489172.31  1201775.75  273.58
       122  489205.01  1201727.34    0.00
"""


def test_rows_land_in_the_plot_frame_without_position_only_points() -> None:
    """Point 1 → (24.53, 10.44), point 3 → (43.69, 4.25); 122 has no height."""
    one, three = survey.parse(ROWS)
    assert (one.number, three.number) == (1, 3)
    assert (one.x, one.y, one.z) == pytest.approx((24.53, 10.44, 271.42))
    assert (three.x, three.y, three.z) == pytest.approx((43.69, 4.25, 273.58))
