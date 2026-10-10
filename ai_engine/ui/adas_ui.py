"""Modern, minimal OpenCV UI that consumes pipeline result state."""

from __future__ import annotations

import cv2
import numpy as np

import config
from .state import DANGER, WARNING


class ADASUI:
    WINDOW_NAME = "Smart Driver Assistant"
    LIVE_TAB = "LIVE ASSIST"
    PLATES_TAB = "LICENSE PLATES"
    HISTORY_TAB = "HISTORY"

    BG = (18, 20, 25)
    PANEL = (29, 32, 39)
    PANEL_ALT = (35, 38, 46)
    BORDER = (55, 59, 69)
    TEXT = (232, 234, 238)
    MUTED = (145, 150, 160)
    SAFE_COLOR = (88, 196, 113)
    WARNING_COLOR = (42, 190, 236)
    DANGER_COLOR = (70, 70, 235)

    def __init__(self, debug_mode=False):
        self.width = config.UI_WIDTH
        self.height = config.UI_HEIGHT
        self.active_tab = self.LIVE_TAB
        self.debug_mode = bool(debug_mode)
        self.initialized = False
        self.tab_regions = {}
        self.debug_region = None

    def initialize_window(self):
        if self.initialized:
            return
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow(self.WINDOW_NAME, self.width, self.height)
        cv2.setMouseCallback(self.WINDOW_NAME, self._mouse_callback)
        self.initialized = True

    @staticmethod
    def _inside(x, y, region):
        if region is None:
            return False
        x1, y1, x2, y2 = region
        return x1 <= x <= x2 and y1 <= y <= y2

    def _mouse_callback(self, event, x, y, flags, param):
        if event != cv2.EVENT_LBUTTONUP:
            return
        if self._inside(x, y, self.debug_region):
            self.debug_mode = not self.debug_mode
            return
        for tab, region in self.tab_regions.items():
            if self._inside(x, y, region):
                self.active_tab = tab
                return

    def handle_key(self, key):
        if key in (ord("1"),):
            self.active_tab = self.LIVE_TAB
        elif key in (ord("2"),):
            self.active_tab = self.PLATES_TAB
        elif key in (ord("3"),):
            self.active_tab = self.HISTORY_TAB
        elif key in (ord("d"), ord("D")):
            self.debug_mode = not self.debug_mode

    @classmethod
    def _status_color(cls, status):
        if status == DANGER:
            return cls.DANGER_COLOR
        if status == WARNING:
            return cls.WARNING_COLOR
        return cls.SAFE_COLOR

    @staticmethod
    def _text(image, text, position, scale=0.55, color=None, thickness=1):
        cv2.putText(
            image,
            str(text),
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color or ADASUI.TEXT,
            thickness,
            cv2.LINE_AA,
        )

    @classmethod
    def _panel(cls, image, region, color=None, border=True):
        x1, y1, x2, y2 = region
        cv2.rectangle(image, (x1, y1), (x2, y2), color or cls.PANEL, -1)
        if border:
            cv2.rectangle(image, (x1, y1), (x2, y2), cls.BORDER, 1)

    @staticmethod
    def _fit_image(image, width, height, background=(10, 11, 14)):
        canvas = np.full((height, width, 3), background, dtype=np.uint8)
        if image is None or image.size == 0:
            return canvas
        src_h, src_w = image.shape[:2]
        scale = min(width / max(1, src_w), height / max(1, src_h))
        new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        x = (width - new_w) // 2
        y = (height - new_h) // 2
        canvas[y:y + new_h, x:x + new_w] = resized
        return canvas

    @classmethod
    def _draw_labeled_box(cls, frame, box, color, label=None, thickness=2):
        x1, y1, x2, y2 = [int(value) for value in box]
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        if not label:
            return
        (text_w, text_h), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
        )
        label_y1 = max(0, y1 - text_h - 8)
        cv2.rectangle(
            frame,
            (x1, label_y1),
            (min(frame.shape[1] - 1, x1 + text_w + 6), y1),
            color,
            -1,
        )
        cls._text(frame, label, (x1 + 3, max(text_h, y1 - 5)), 0.45, (255, 255, 255))

    def render_camera(self, frame, frame_result, state):
        """Render only pipeline results; never invoke detection/OCR."""
        warned_ids = frame_result.get("warned_ids", set())
        for vehicle in frame_result.get("vehicles", []):
            warned = vehicle["id"] in warned_ids
            color = self._status_color(state.safety_status) if warned else (105, 180, 118)
            label = None
            if self.debug_mode:
                label = (
                    f"{vehicle['class']} #{vehicle['id']} "
                    f"{vehicle['confidence']:.2f}"
                )
            self._draw_labeled_box(frame, vehicle["box"], color, label, 2)

        if self.debug_mode:
            for person in frame_result.get("people", []):
                label = f"person #{person['id']}"
                if person["helmet_status"] is True:
                    label += " helmet"
                elif person["helmet_status"] is False:
                    label += " NO HELMET"
                self._draw_labeled_box(frame, person["box"], self.MUTED, label, 1)

        show_plates = self.active_tab == self.PLATES_TAB or self.debug_mode
        if show_plates and state.safety_status != DANGER:
            for plate in frame_result.get("plates", []):
                if not plate.get("accepted"):
                    # Rejected proposals stay available in PlateReader logs and
                    # statistics, but never clutter the camera view.
                    continue
                text = plate.get("text") or "NOT READABLE"
                label = f"{text} {plate.get('ocr_confidence', 0.0):.0%}"
                if self.debug_mode:
                    track = plate.get("track")
                    track_id = track.id if track is not None else "-"
                    label += f" #{track_id} det={plate['confidence']:.2f}"
                self._draw_labeled_box(frame, plate["box"], self.SAFE_COLOR, label, 2)

        if state.safety_status == DANGER:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 92), self.DANGER_COLOR, -1)
            cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
            self._text(frame, "COLLISION WARNING", (24, 38), 0.9, (255, 255, 255), 2)
            self._text(frame, "BRAKE!", (24, 76), 1.0, (255, 255, 255), 2)
        return frame

    def _draw_header(self, canvas, state):
        header_h = config.UI_HEADER_HEIGHT
        cv2.rectangle(canvas, (0, 0), (self.width, header_h), self.PANEL, -1)
        cv2.line(canvas, (0, header_h), (self.width, header_h), self.BORDER, 1)
        cv2.circle(canvas, (30, header_h // 2), 12, (110, 180, 225), 2)
        self._text(canvas, "SMART DRIVER ASSISTANT", (54, 39), 0.72, self.TEXT, 2)
        self._text(canvas, f"Source: {state.source_type}", (400, 37), 0.48, self.MUTED)

        status_color = self.SAFE_COLOR if state.online else self.DANGER_COLOR
        cv2.circle(canvas, (self.width - 218, header_h // 2), 6, status_color, -1)
        self._text(
            canvas,
            "ONLINE" if state.online else "OFFLINE",
            (self.width - 204, 37),
            0.50,
            status_color,
            1,
        )

        toggle_w, toggle_h = 132, 32
        x2 = self.width - 18
        x1, y1 = x2 - toggle_w, (header_h - toggle_h) // 2
        y2 = y1 + toggle_h
        toggle_color = (64, 96, 78) if self.debug_mode else self.PANEL_ALT
        cv2.rectangle(canvas, (x1, y1), (x2, y2), toggle_color, -1)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), self.BORDER, 1)
        self._text(
            canvas,
            f"DEBUG: {'ON' if self.debug_mode else 'OFF'}",
            (x1 + 14, y1 + 22),
            0.44,
            self.TEXT,
        )
        self.debug_region = (x1, y1, x2, y2)

    def _draw_tabs(self, canvas):
        bottom_h = config.UI_TAB_HEIGHT
        y1 = self.height - bottom_h
        cv2.rectangle(canvas, (0, y1), (self.width, self.height), self.PANEL, -1)
        cv2.line(canvas, (0, y1), (self.width, y1), self.BORDER, 1)
        tabs = [self.LIVE_TAB, self.PLATES_TAB, self.HISTORY_TAB]
        tab_w = min(250, self.width // 3)
        start_x = (self.width - tab_w * len(tabs)) // 2
        self.tab_regions = {}
        for index, tab in enumerate(tabs):
            x1 = start_x + index * tab_w
            x2 = x1 + tab_w
            active = tab == self.active_tab
            if active:
                cv2.rectangle(canvas, (x1, y1), (x2, self.height), self.PANEL_ALT, -1)
                cv2.rectangle(canvas, (x1, y1), (x2, y1 + 3), self.SAFE_COLOR, -1)
            text_color = self.TEXT if active else self.MUTED
            text_size = cv2.getTextSize(tab, cv2.FONT_HERSHEY_SIMPLEX, 0.50, 1)[0]
            self._text(
                canvas,
                tab,
                (x1 + (tab_w - text_size[0]) // 2, y1 + 38),
                0.50,
                text_color,
                1,
            )
            self.tab_regions[tab] = (x1, y1, x2, self.height)

    def _draw_safety_card(self, canvas, region, state):
        color = self._status_color(state.safety_status)
        x1, y1, x2, y2 = region
        self._panel(canvas, region)
        cv2.rectangle(canvas, (x1, y1), (x1 + 5, y2), color, -1)
        self._text(canvas, "SAFETY STATUS", (x1 + 22, y1 + 30), 0.45, self.MUTED)
        cv2.circle(canvas, (x1 + 32, y1 + 67), 9, color, -1)
        self._text(canvas, state.safety_status, (x1 + 52, y1 + 75), 0.82, color, 2)
        self._text(canvas, state.collision_message, (x1 + 22, y1 + 108), 0.48, self.TEXT)
        self._text(canvas, f"Collision Risk: {state.collision_risk}", (x1 + 22, y1 + 137), 0.48, self.MUTED)

    def _draw_last_plate_card(self, canvas, region, state):
        x1, y1, x2, y2 = region
        self._panel(canvas, region)
        self._text(canvas, "LAST DETECTED PLATE", (x1 + 18, y1 + 29), 0.43, self.MUTED)
        text = state.last_plate or "-"
        self._text(canvas, text, (x1 + 18, y1 + 70), 0.78, self.TEXT, 2)
        if state.last_plate:
            self._text(
                canvas,
                f"Confidence: {state.last_plate_confidence:.0%}",
                (x1 + 18, y1 + 101),
                0.48,
                self.MUTED,
            )
            self._text(canvas, state.last_plate_status, (x1 + 18, y1 + 128), 0.42, self.MUTED)

    def _draw_metrics_card(self, canvas, region, state):
        x1, y1, x2, y2 = region
        self._panel(canvas, region)
        self._text(canvas, "LIVE METRICS", (x1 + 18, y1 + 28), 0.43, self.MUTED)
        rows = [
            ("Vehicles", state.vehicle_count),
            ("Tracks total", state.total_vehicles),
            ("FPS", f"{state.fps:.1f}"),
            ("Frame", state.frame_index),
        ]
        for index, (label, value) in enumerate(rows):
            y = y1 + 58 + index * 28
            self._text(canvas, label, (x1 + 18, y), 0.46, self.MUTED)
            value_text = str(value)
            width = cv2.getTextSize(value_text, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)[0][0]
            self._text(canvas, value_text, (x2 - width - 18, y), 0.48, self.TEXT)

    def _draw_live(self, canvas, camera_frame, state, content_region):
        x1, y1, x2, y2 = content_region
        gap = 14
        sidebar_w = int((x2 - x1) * config.UI_SIDEBAR_RATIO)
        camera_region = (x1, y1, x2 - sidebar_w - gap, y2)
        sidebar_region = (camera_region[2] + gap, y1, x2, y2)

        camera = self._fit_image(
            camera_frame,
            camera_region[2] - camera_region[0],
            camera_region[3] - camera_region[1],
        )
        canvas[camera_region[1]:camera_region[3], camera_region[0]:camera_region[2]] = camera
        cv2.rectangle(canvas, camera_region[:2], camera_region[2:], self.BORDER, 1)

        sx1, sy1, sx2, sy2 = sidebar_region
        safety_h = 158
        plate_h = 148
        self._draw_safety_card(canvas, (sx1, sy1, sx2, sy1 + safety_h), state)
        self._draw_last_plate_card(
            canvas,
            (sx1, sy1 + safety_h + gap, sx2, sy1 + safety_h + gap + plate_h),
            state,
        )
        self._draw_metrics_card(
            canvas,
            (sx1, sy1 + safety_h + plate_h + gap * 2, sx2, sy2),
            state,
        )

    def _draw_plate_list(self, canvas, region, state):
        x1, y1, x2, y2 = region
        self._panel(canvas, region)
        self._text(canvas, "DETECTED PLATES", (x1 + 16, y1 + 28), 0.46, self.MUTED)
        row_y = y1 + 60
        for event in list(state.plate_history)[:8]:
            self._text(canvas, event.text, (x1 + 16, row_y), 0.53, self.TEXT, 1)
            confidence = f"{event.confidence:.0%}"
            confidence_w = cv2.getTextSize(confidence, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)[0][0]
            self._text(canvas, confidence, (x2 - confidence_w - 14, row_y), 0.44, self.MUTED)
            self._text(
                canvas,
                f"{event.time}  Track #{event.track_id}  {event.status}",
                (x1 + 16, row_y + 21),
                0.34,
                self.MUTED,
            )
            cv2.line(canvas, (x1 + 14, row_y + 31), (x2 - 14, row_y + 31), self.BORDER, 1)
            row_y += 53
            if row_y + 35 > y2:
                break
        if not state.plate_history:
            self._text(canvas, "No plate result yet", (x1 + 16, y1 + 66), 0.48, self.MUTED)

    def _draw_plate_tab(self, canvas, camera_frame, state, content_region):
        x1, y1, x2, y2 = content_region
        gap = 14
        sidebar_w = int((x2 - x1) * 0.30)
        camera_region = (x1, y1, x2 - sidebar_w - gap, y2)
        sidebar_region = (camera_region[2] + gap, y1, x2, y2)
        camera = self._fit_image(
            camera_frame,
            camera_region[2] - camera_region[0],
            camera_region[3] - camera_region[1],
        )
        canvas[camera_region[1]:camera_region[3], camera_region[0]:camera_region[2]] = camera
        cv2.rectangle(canvas, camera_region[:2], camera_region[2:], self.BORDER, 1)

        sx1, sy1, sx2, sy2 = sidebar_region
        crop_h = 140
        self._panel(canvas, (sx1, sy1, sx2, sy1 + crop_h))
        self._text(canvas, "LAST PLATE CROP", (sx1 + 14, sy1 + 25), 0.42, self.MUTED)
        if state.last_plate_crop is not None:
            crop = self._fit_image(state.last_plate_crop, sx2 - sx1 - 28, 84, self.PANEL)
            canvas[sy1 + 40:sy1 + 124, sx1 + 14:sx2 - 14] = crop
        else:
            self._text(canvas, "No crop", (sx1 + 14, sy1 + 80), 0.48, self.MUTED)
        self._draw_plate_list(canvas, (sx1, sy1 + crop_h + gap, sx2, sy2), state)

    def _draw_stat_card(self, canvas, region, label, value, color=None):
        x1, y1, x2, y2 = region
        self._panel(canvas, region)
        self._text(canvas, label, (x1 + 16, y1 + 28), 0.42, self.MUTED)
        self._text(canvas, value, (x1 + 16, y1 + 68), 0.78, color or self.TEXT, 2)

    def _draw_history(self, canvas, state, content_region):
        x1, y1, x2, y2 = content_region
        gap = 12
        card_h = 88
        card_w = (x2 - x1 - gap * 3) // 4
        cards = [
            ("VEHICLES DETECTED", str(state.total_vehicles), self.TEXT),
            ("PLATES DETECTED", str(state.plates_detected), self.SAFE_COLOR),
            ("WARNINGS", str(state.warning_events), self.WARNING_COLOR),
            ("DANGER EVENTS", str(state.danger_events), self.DANGER_COLOR),
        ]
        for index, (label, value, color) in enumerate(cards):
            cx1 = x1 + index * (card_w + gap)
            self._draw_stat_card(canvas, (cx1, y1, cx1 + card_w, y1 + card_h), label, value, color)

        table_y = y1 + card_h + 16
        self._panel(canvas, (x1, table_y, x2, y2))
        columns = [
            ("TIME", x1 + 18),
            ("TRACK ID", x1 + 150),
            ("LICENSE PLATE", x1 + 310),
            ("CONFIDENCE", x1 + 570),
            ("EVENT", x1 + 780),
        ]
        for label, x in columns:
            self._text(canvas, label, (x, table_y + 32), 0.43, self.MUTED)
        cv2.line(canvas, (x1 + 14, table_y + 46), (x2 - 14, table_y + 46), self.BORDER, 1)

        row_y = table_y + 77
        for event in list(state.history)[:14]:
            confidence = "-" if event.confidence is None else f"{event.confidence:.0%}"
            values = [
                event.time,
                "-" if event.track_id is None else f"#{event.track_id}",
                event.license_plate,
                confidence,
                event.event,
            ]
            for value, (_, x) in zip(values, columns):
                self._text(canvas, value, (x, row_y), 0.46, self.TEXT)
            cv2.line(canvas, (x1 + 14, row_y + 14), (x2 - 14, row_y + 14), self.BORDER, 1)
            row_y += 36
            if row_y + 20 > y2:
                break
        if not state.history:
            self._text(canvas, "No events in this session", (x1 + 18, table_y + 84), 0.50, self.MUTED)

    def compose(self, camera_frame, state):
        canvas = np.full((self.height, self.width, 3), self.BG, dtype=np.uint8)
        self._draw_header(canvas, state)
        self._draw_tabs(canvas)
        content_region = (
            config.UI_MARGIN,
            config.UI_HEADER_HEIGHT + config.UI_MARGIN,
            self.width - config.UI_MARGIN,
            self.height - config.UI_TAB_HEIGHT - config.UI_MARGIN,
        )
        if self.active_tab == self.HISTORY_TAB:
            self._draw_history(canvas, state, content_region)
        elif self.active_tab == self.PLATES_TAB:
            self._draw_plate_tab(canvas, camera_frame, state, content_region)
        else:
            self._draw_live(canvas, camera_frame, state, content_region)
        return canvas
