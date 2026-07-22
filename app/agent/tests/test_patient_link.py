"""Regression: voice worker must bind to the human, not crash on ICE reconnect."""

from __future__ import annotations

from types import SimpleNamespace

from voice_agent import _first_human_participant, _participant_has_mic


def test_first_human_prefers_standard_over_agent() -> None:
    human = SimpleNamespace(identity="user-abc", kind=0)
    agent = SimpleNamespace(identity="agent-AJ_x", kind=4)
    ctx = SimpleNamespace(
        room=SimpleNamespace(remote_participants={"a": agent, "u": human})
    )
    assert _first_human_participant(ctx) is human


def test_first_human_none_when_only_agent() -> None:
    agent = SimpleNamespace(identity="agent-AJ_x", kind=4)
    ctx = SimpleNamespace(room=SimpleNamespace(remote_participants={"a": agent}))
    assert _first_human_participant(ctx) is None


def test_participant_has_mic_detects_audio_kind() -> None:
    human = SimpleNamespace(
        identity="user-abc",
        track_publications={
            "t1": SimpleNamespace(kind=1, source=0, name=""),
        },
    )
    assert _participant_has_mic(human) is True


def test_participant_has_mic_false_without_tracks() -> None:
    human = SimpleNamespace(identity="user-abc", track_publications={})
    assert _participant_has_mic(human) is False


def test_participant_has_mic_detects_microphone_source() -> None:
    human = SimpleNamespace(
        identity="user-abc",
        track_publications={
            "t1": SimpleNamespace(kind=0, source=2, name="microphone"),
        },
    )
    assert _participant_has_mic(human) is True
