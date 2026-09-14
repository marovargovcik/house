"""Every feature names a point the survey measured."""

from pathlib import Path

from terrain.core import features, survey

SURVEY = Path(__file__).resolve().parents[2] / "data" / "terrain.txt"


def test_every_feature_point_is_a_measured_ground_point() -> None:
    measured = {p.number for p in survey.parse(SURVEY.read_text(encoding="utf-8"))}
    named = {n for fence in features.FENCES for n in fence} | {
        *features.BOUNDARY,
        *features.TREES,
        *features.EXISTING_SHED,
    }
    assert named - measured == set()
