try:
    from ai_engine.modules.eyes_closed_monitor import EyesClosedMonitor, EyeState
except ImportError:
    from eyes_closed_monitor import EyesClosedMonitor, EyeState


OPEN_EAR, CLOSED_EAR = 0.30, 0.02


def make(fps=15):
    return EyesClosedMonitor(baseline_ear=OPEN_EAR), fps


def run(m, fps, segments):
    """segments: list[(giây, ear|None, face_found)] -> (events, trạng thái cuối)"""
    t, dt, events, last = 100.0, 1.0 / fps, [], None
    for secs, ear, face in segments:
        for _ in range(int(secs * fps)):
            last = m.update(t, face, ear, quality=0.9)
            events += last.events
            t += dt
    return events, last


def types(events):
    return [e["type"] for e in events]


def test_close_5s_critical_once():
    for fps in (5, 15, 30):  # kết quả không phụ thuộc FPS
        m, _ = make(fps)
        ev, last = run(m, fps, [(1, OPEN_EAR, True), (5.5, CLOSED_EAR, True)])
        assert types(ev).count("eyes_closed_prolonged") == 1, fps
        assert types(ev).count("eyes_closed_warning") == 1, fps
        assert last.state == EyeState.CLOSED_CRITICAL


def test_normal_blinks_no_alert():
    m, fps = make()
    seg = [(1, OPEN_EAR, True)] + [(0.3, CLOSED_EAR, True), (0.7, OPEN_EAR, True)] * 10
    ev, _ = run(m, fps, seg)
    assert ev == []


def test_close_4s_only_warning():
    m, fps = make()
    ev, last = run(m, fps, [(1, OPEN_EAR, True), (4, CLOSED_EAR, True), (1, OPEN_EAR, True)])
    assert types(ev) == ["eyes_closed_warning"]
    assert last.state == EyeState.OPEN


def test_face_lost_resets():
    m, fps = make()
    ev, _ = run(m, fps, [(3, CLOSED_EAR, True), (1, None, False), (3, CLOSED_EAR, True)])
    assert "eyes_closed_prolonged" not in types(ev)


def test_short_gap_tolerated():
    m, fps = make()
    ev, _ = run(m, fps, [(3, CLOSED_EAR, True), (0.2, OPEN_EAR, True), (2.5, CLOSED_EAR, True)])
    assert "eyes_closed_prolonged" in types(ev)


def test_cooldown_repeat_and_reopen():
    m, fps = make()
    ev, _ = run(m, fps, [(17, CLOSED_EAR, True), (1, OPEN_EAR, True)])
    t = types(ev)
    assert t.count("eyes_closed_prolonged") == 2  # ~5s và ~15s
    assert t[-1] == "eyes_reopened"


def test_low_quality_is_unknown():
    m, _ = make()
    r = m.update(1.0, True, CLOSED_EAR, quality=0.2)
    assert r.state == EyeState.UNKNOWN and r.events == []


def test_calibration_then_detect():
    m = EyesClosedMonitor()  # chưa có baseline
    fps, t = 15, 0.0
    for _ in range(12 * fps):
        r = m.update(t, True, OPEN_EAR, 0.9); t += 1 / fps
        assert r.events == []
    assert m.baseline is not None and abs(m.baseline - OPEN_EAR) < 1e-6
    ev = []
    for _ in range(int(5.5 * fps)):
        ev += m.update(t, True, CLOSED_EAR, 0.9).events; t += 1 / fps
    assert "eyes_closed_prolonged" in types(ev)


def test_calibrating_never_alerts():
    m = EyesClosedMonitor()
    ev = []
    for i in range(100):
        ev += m.update(i / 15, True, CLOSED_EAR, 0.9).events
    assert ev == [] and m.baseline is None
