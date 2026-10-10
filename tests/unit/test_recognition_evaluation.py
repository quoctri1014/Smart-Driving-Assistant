from scripts.evaluate_recognition import evaluate


def test_missing_second_vehicle_reduces_recall():
    result = evaluate([{"truth": [{"class": "car", "box": [0, 0, 10, 10]}, {"class": "car", "box": [20, 0, 30, 10]}],
                        "predictions": [{"class": "car", "box": [0, 0, 10, 10]}]}])
    assert result["per_class"]["car"]["recall"] == .5


def test_empty_evaluation_never_claims_perfect_accuracy():
    result = evaluate([])
    assert result["plate_exact_match_on_matched_objects"] is None
    assert result["speed_mae_kmh"] is None


def test_duplicate_detection_counts_as_false_positive():
    item = {"class": "car", "box": [0, 0, 10, 10]}
    result = evaluate([{"truth": [item], "predictions": [item, item]}])
    assert result["per_class"]["car"]["precision"] == .5
