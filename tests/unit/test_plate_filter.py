"""Deterministic tests for plate filtering and no-guess OCR behavior."""

from collections import Counter
import unittest

import cv2
import numpy as np

from plate.plate_reader import CONFIRMED, NOT_READABLE, UNCERTAIN, PlateReader


class FakeTrack:
    def __init__(self, track_id=150, box=(10, 10, 210, 130)):
        self.id = track_id
        self.current_box = box
        self.plate_votes = Counter()


class FakeOCR:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def readtext(self, image, detail=1, paragraph=False):
        self.calls += 1
        height, width = image.shape[:2]
        box = [[0, 0], [width, 0], [width, height], [0, height]]
        return [(box, self.text, 0.90)]


class PlateFilterTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.clear_crop = rng.integers(0, 256, (30, 70, 3), dtype=np.uint8)
        self.track = FakeTrack()

    @staticmethod
    def detection(box, confidence, crop):
        return {
            "box": box,
            "confidence": confidence,
            "crop": crop,
            "text": None,
            "ocr_confidence": 0.0,
            "status": NOT_READABLE,
            "accepted": False,
            "reason": "NOT_FILTERED",
            "track": None,
        }

    def test_1_clear_near_plate_can_confirm(self):
        fake_ocr = FakeOCR("51D-57579")
        reader = PlateReader(detector=object(), ocr_reader=fake_ocr)
        detection = self.detection((60, 70, 130, 100), 0.80, self.clear_crop)
        reader.filter_detection(detection, [self.track])
        self.assertTrue(detection["accepted"])

        result = None
        for frame_idx in (1, 2, 3):
            result = reader.process_crop(
                self.track.id,
                self.clear_crop,
                frame_idx,
                run_ocr=frame_idx == 3,
                vote_counter=self.track.plate_votes,
                plate_confidence=detection["confidence"],
                quality_metrics=detection["metrics"],
            )
        self.assertEqual(result["text"], "51D57579")
        self.assertEqual(result["status"], CONFIRMED)

    def test_2_slight_blur_is_buffered_when_quality_is_sufficient(self):
        slightly_blurred = cv2.GaussianBlur(self.clear_crop, (5, 5), 0)
        reader = PlateReader(detector=object(), ocr_reader=FakeOCR("51D57579"))
        detection = self.detection((60, 70, 130, 100), 0.72, slightly_blurred)
        reader.filter_detection(detection, [self.track])
        self.assertTrue(detection["accepted"])
        reader.process_crop(
            self.track.id,
            slightly_blurred,
            1,
            plate_confidence=detection["confidence"],
            quality_metrics=detection["metrics"],
        )
        self.assertEqual(len(reader.track_states[self.track.id].crops), 1)

    def test_3_too_blurry_plate_is_not_sent_to_ocr(self):
        fake_ocr = FakeOCR("51D57579")
        reader = PlateReader(detector=object(), ocr_reader=fake_ocr)
        unreadable = np.full((30, 70, 3), 128, dtype=np.uint8)
        detection = self.detection((60, 70, 130, 100), 0.80, unreadable)
        reader.filter_detection(detection, [self.track])
        self.assertFalse(detection["accepted"])
        self.assertEqual(detection["reason"], "LOW_SHARPNESS")
        self.assertEqual(fake_ocr.calls, 0)

    def test_4_sign_outside_vehicle_is_not_sent_to_ocr(self):
        fake_ocr = FakeOCR("SALE50")
        reader = PlateReader(detector=object(), ocr_reader=fake_ocr)
        detection = self.detection((300, 200, 370, 230), 0.90, self.clear_crop)
        reader.filter_detection(detection, [self.track])
        self.assertFalse(detection["accepted"])
        self.assertEqual(detection["reason"], "OUTSIDE_VEHICLE")
        self.assertEqual(fake_ocr.calls, 0)

    def test_partial_text_is_never_completed(self):
        fake_ocr = FakeOCR("57579")
        reader = PlateReader(detector=object(), ocr_reader=fake_ocr)
        votes = Counter()
        result = None
        for frame_idx in (1, 2, 3):
            result = reader.process_crop(
                151,
                self.clear_crop,
                frame_idx,
                run_ocr=frame_idx == 3,
                vote_counter=votes,
                plate_confidence=0.80,
            )
        self.assertEqual(result["text"], "57579")
        self.assertEqual(result["status"], UNCERTAIN)
        self.assertNotIn("51D", result["text"])


if __name__ == "__main__":
    unittest.main()
