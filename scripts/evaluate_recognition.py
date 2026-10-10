"""Evaluate real annotated frames against exported predictions (no bundled data).

Input JSON: {"frames": [{"truth": [{"class": "car", "box": [x1,y1,x2,y2]}],
                          "predictions": [{"class": "car", "box": [...], "confidence": .8}]}]}
Optional plate_text and speed_kmh fields are scored on matched objects only.
Run: python scripts/evaluate_recognition.py --input path/to/results.json
This reports precision/recall, not a fabricated global accuracy or mAP.
"""
import argparse
import json
import math


def overlap(a, b):
    intersection = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area_a = max(0, a[2] - a[0]) * max(0, a[3] - a[1])
    area_b = max(0, b[2] - b[0]) * max(0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


def evaluate(frames, iou_threshold=0.5):
    if not 0 < iou_threshold <= 1:
        raise ValueError("IoU threshold must be in (0, 1]")
    counts = {}
    plate_correct = plate_total = speed_expected = 0
    speed_errors = []
    for frame in frames:
        truth, predictions = frame["truth"], frame["predictions"]
        matched = set()
        for item in truth + predictions:
            if len(item["box"]) != 4 or not all(math.isfinite(x) for x in item["box"]):
                raise ValueError("Bounding boxes must contain four finite coordinates")
            counts.setdefault(item["class"], {"tp": 0, "fp": 0, "fn": 0})
        for prediction in sorted(predictions, key=lambda p: p.get("confidence", 0), reverse=True):
            candidates = [(overlap(prediction["box"], actual["box"]), index)
                          for index, actual in enumerate(truth)
                          if index not in matched and actual["class"] == prediction["class"]]
            score, index = max(candidates, default=(0, -1))
            if score < iou_threshold or index < 0:
                counts[prediction["class"]]["fp"] += 1
                continue
            matched.add(index)
            counts[prediction["class"]]["tp"] += 1
            actual = truth[index]
            if actual.get("plate_text") is not None:
                plate_total += 1
                plate_correct += prediction.get("plate_text") == actual["plate_text"]
            if actual.get("speed_kmh") is not None:
                speed_expected += 1
                speed = prediction.get("speed_kmh")
                if speed is not None and math.isfinite(speed):
                    speed_errors.append(abs(speed - actual["speed_kmh"]))
        for index, actual in enumerate(truth):
            if index not in matched:
                counts[actual["class"]]["fn"] += 1
    for value in counts.values():
        tp, fp, fn = value["tp"], value["fp"], value["fn"]
        value["precision"] = tp / (tp + fp) if tp + fp else None
        value["recall"] = tp / (tp + fn) if tp + fn else None
    return {"per_class": counts, "plate_exact_match_on_matched_objects": plate_correct / plate_total if plate_total else None,
            "plate_samples": plate_total, "speed_mae_kmh": sum(speed_errors) / len(speed_errors) if speed_errors else None,
            "speed_samples": len(speed_errors), "speed_coverage_on_matched_objects": len(speed_errors) / speed_expected if speed_expected else None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    with open(args.input, encoding="utf-8") as source:
        print(json.dumps(evaluate(json.load(source)["frames"]), indent=2))
