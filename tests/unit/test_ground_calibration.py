import pytest
from modules.ground_calibration import GroundCalibration


def test_measured_ground_distance_is_resolution_independent():
    calibration = GroundCalibration(
        [(0, 0), (1, 0), (1, 1), (0, 1)],
        [(0, 0), (20, 0), (20, 40), (0, 40)],
    )
    assert calibration.project((40, 20, 60, 50), 100, 100) == pytest.approx((10, 20))
    assert calibration.project((80, 40, 120, 100), 200, 200) == pytest.approx((10, 20))


def test_do_not_extrapolate_speed_outside_calibrated_area():
    calibration = GroundCalibration(
        [(.2, .2), (.8, .2), (.8, .8), (.2, .8)],
        [(0, 0), (20, 0), (20, 40), (0, 40)],
    )
    assert calibration.project((0, 0, 10, 10), 100, 100) is None


def test_reject_collinear_points():
    with pytest.raises(ValueError):
        GroundCalibration([(0, 0), (.2, .2), (.4, .4), (.6, .6)], [(0, 0), (1, 0), (1, 1), (0, 1)])
