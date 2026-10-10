"""UI-facing state populated by the existing AI pipeline."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

import config


SAFE = "SAFE"
WARNING = "WARNING"
DANGER = "DANGER"


@dataclass
class PlateEvent:
    time: str
    track_id: int
    text: str
    confidence: float
    status: str
    crop: object = None


@dataclass
class HistoryEvent:
    time: str
    track_id: int | None
    license_plate: str
    confidence: float | None
    event: str


class SystemState:
    """Small in-memory result store; it never runs detection or OCR."""

    def __init__(self, source):
        self.online = True
        self.source = str(source)
        self.source_type = self._source_type(source)
        self.frame_index = 0
        self.fps = 0.0

        self.safety_status = SAFE
        self.collision_risk = "LOW"
        self.collision_message = "Road clear"
        self.warning_track_ids = set()

        self.vehicle_count = 0
        self.tracking_count = 0
        self.total_vehicle_tracks = set()
        self.warning_events = 0
        self.danger_events = 0

        self.last_plate = None
        self.last_plate_confidence = 0.0
        self.last_plate_status = "NOT_READABLE"
        self.last_plate_crop = None
        self.plate_history = deque(maxlen=config.UI_PLATE_HISTORY_LIMIT)
        self.history = deque(maxlen=config.UI_HISTORY_LIMIT)
        self._plate_event_keys = set()
        self._previous_safety_status = SAFE

    @staticmethod
    def _source_type(source):
        value = str(source).lower()
        if value.isdigit():
            return "WEBCAM"
        if value.startswith("rtsp://") or value.startswith("rtsps://"):
            return "RTSP"
        if value.startswith("http://") or value.startswith("https://"):
            return "STREAM"
        return "VIDEO"

    @staticmethod
    def _now():
        return datetime.now().strftime("%H:%M:%S")

    def set_offline(self):
        self.online = False

    def update_frame(self, vehicle_tracks, warnings, fps, frame_index):
        self.frame_index = frame_index
        self.fps = float(fps)
        self.vehicle_count = len(vehicle_tracks)
        self.tracking_count = len(vehicle_tracks)
        self.warning_track_ids = {track.id for track, _ in warnings}
        self.total_vehicle_tracks.update(track.id for track in vehicle_tracks)

        if not warnings:
            status = SAFE
            risk = "LOW"
            message = "Road clear"
        else:
            max_rate = max(rate for _, rate in warnings)
            danger_threshold = (
                config.COLLISION_GROWTH_RATE_THRESHOLD
                * config.UI_DANGER_RATE_MULTIPLIER
            )
            if max_rate >= danger_threshold:
                status = DANGER
                risk = "HIGH"
                message = "COLLISION WARNING - BRAKE!"
            else:
                status = WARNING
                risk = "MEDIUM"
                message = "Vehicle too close"

        self.safety_status = status
        self.collision_risk = risk
        self.collision_message = message
        if status != self._previous_safety_status and status != SAFE:
            self.warning_events += 1
            if status == DANGER:
                self.danger_events += 1
            warning_track = next(iter(self.warning_track_ids), None)
            self.history.appendleft(
                HistoryEvent(
                    time=self._now(),
                    track_id=warning_track,
                    license_plate="-",
                    confidence=None,
                    event=status.title(),
                )
            )
        self._previous_safety_status = status

    def record_plate(self, track_id, text, confidence, status, crop=None):
        """Record exactly the OCR text supplied by the pipeline, without edits."""
        if not text:
            return
        confidence = float(confidence)
        self.last_plate = text
        self.last_plate_confidence = confidence
        self.last_plate_status = status
        self.last_plate_crop = crop.copy() if crop is not None else None

        key = (int(track_id), text, status)
        if key in self._plate_event_keys:
            return
        self._plate_event_keys.add(key)
        event = PlateEvent(
            time=self._now(),
            track_id=int(track_id),
            text=text,
            confidence=confidence,
            status=status,
            crop=crop.copy() if crop is not None else None,
        )
        self.plate_history.appendleft(event)
        self.history.appendleft(
            HistoryEvent(
                time=event.time,
                track_id=event.track_id,
                license_plate=event.text,
                confidence=event.confidence,
                event="Detected" if status == "CONFIRMED" else "Partial OCR",
            )
        )

        # Keep the deduplication set bounded with the same lifetime as history.
        if len(self._plate_event_keys) > config.UI_HISTORY_LIMIT * 2:
            active_keys = {
                (item.track_id, item.text, item.status) for item in self.plate_history
            }
            self._plate_event_keys = active_keys

    @property
    def total_vehicles(self):
        return len(self.total_vehicle_tracks)

    @property
    def plates_detected(self):
        return len(self.plate_history)
