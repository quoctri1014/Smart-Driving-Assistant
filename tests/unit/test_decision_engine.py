"""
test_decision_engine.py
-----------------------
Unit tests kiểm thử Decision Engine, EventNoiseFilter, AdasEvent, VoiceGenerator.
"""

import time
import pytest
from backend.app.schemas.adas_event import AdasEvent, DecisionResult
from backend.app.core.noise_filter import EventNoiseFilter
from backend.app.core.voice_generator import VietnameseVoiceGenerator
from backend.app.core.decision_engine import DecisionEngine


def test_adas_event_schema_creation():
    ev = AdasEvent(
        module="ttc",
        type="collision_imminent",
        severity="critical",
        confidence=0.92,
        payload={"ttc_seconds": 1.2, "distance_m": 8.5}
    )
    assert ev.event_id is not None
    assert ev.module == "ttc"
    assert ev.severity == "critical"
    assert ev.confidence == 0.92
    assert ev.payload["ttc_seconds"] == 1.2


def test_noise_filter_confidence_gating():
    flt = EventNoiseFilter()
    
    # Event có confidence thấp (0.4 < 0.65) -> phải bị chặn
    low_conf_ev = AdasEvent(
        module="ttc",
        type="collision_imminent",
        severity="critical",
        confidence=0.40
    )
    assert flt.filter_event(low_conf_ev) is None

    # Event có confidence đạt yêu cầu
    high_conf_ev = AdasEvent(
        module="ttc",
        type="collision_imminent",
        severity="critical",
        confidence=0.85
    )
    # Chưa đủ 3 frame -> vẫn là None ở frame 1 và 2
    assert flt.filter_event(high_conf_ev) is None
    assert flt.filter_event(high_conf_ev) is None
    # Đến frame 3 -> được chấp nhận
    res = flt.filter_event(high_conf_ev)
    assert res is not None
    assert res.type == "collision_imminent"


def test_voice_generator_prompts():
    gen = VietnameseVoiceGenerator()
    
    ttc_ev = AdasEvent(module="ttc", type="collision_imminent", severity="critical")
    prompt = gen.generate_prompt(ttc_ev)
    assert "Nguy hiểm" in prompt and "va chạm" in prompt
    
    drowsy_ev = AdasEvent(module="drowsiness", type="drowsy", severity="critical")
    prompt = gen.generate_prompt(drowsy_ev)
    assert "ngủ gật" in prompt
    
    speed_sign_ev = AdasEvent(
        module="sign", 
        type="speed_sign", 
        severity="info", 
        payload={"speed_limit": 60}
    )
    prompt = gen.generate_prompt(speed_sign_ev)
    assert "60" in prompt and "giới hạn tốc độ" in prompt


def test_decision_engine_priority_arbitration():
    engine = DecisionEngine()
    
    # 2 sự kiện đồng thời: biển báo (priority thấp) và va chạm TTC (priority cao)
    sign_ev = AdasEvent(module="sign", type="speed_sign", severity="info", confidence=0.9, payload={"speed_limit": 50})
    ttc_ev = AdasEvent(module="ttc", type="collision_imminent", severity="critical", confidence=0.9)
    
    # Kiểm tra điểm ưu tiên của TTC phải cao hơn biển báo
    assert engine._calculate_event_score(ttc_ev) > engine._calculate_event_score(sign_ev)

    # Đưa sự kiện vào: TTC có min_frames=3, nên ở frame 3 TTC sẽ trigger
    res_list = []
    for _ in range(3):
        res = engine.process_events([sign_ev, ttc_ev])
        if res.primary_event is not None:
            res_list.append(res)
        
    assert len(res_list) > 0
    # Sự kiện đầu tiên kích hoạt là TTC
    first_trigger = res_list[0]
    assert first_trigger.primary_event.module == "ttc"
    assert first_trigger.ui_theme == "critical"
    assert first_trigger.sound_alert == "alarm_critical"
    assert first_trigger.should_record_violation is True
    assert "Nguy hiểm" in first_trigger.speech_prompt
