"""Regression: local stack must resist speaker→mic false barge-ins mid-utterance."""

from __future__ import annotations

from voice_agent import turn_handling_for_local_stack


def test_interruption_requires_real_speech_not_echo_blips() -> None:
    opts = turn_handling_for_local_stack()
    interruption = opts["interruption"]
    # Defaults are 0.5s / 0 words — too easy for loudspeaker echo to cut TTS.
    assert interruption["min_duration"] >= 1.2
    assert interruption["min_words"] >= 2
    assert interruption["enabled"] is True


def test_false_interruption_resume_stays_enabled() -> None:
    opts = turn_handling_for_local_stack()
    interruption = opts["interruption"]
    assert interruption["resume_false_interruption"] is True
    assert interruption["false_interruption_timeout"] is not None
