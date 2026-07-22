"""Regression: Talk left-bar companions come from templates + personas."""

from companions import list_companions


def test_list_companions_includes_lena_voice() -> None:
    cards = list_companions()
    assert cards, "expected at least one companion from templates/personas"
    lena = next((c for c in cards if "lena" in c["name"].lower()), None)
    assert lena is not None
    assert lena["voice"] is True
    assert lena["agent_id"]
    assert lena["participant_id"]
    assert str(lena["participant_id"]).startswith("agent-")
    assert lena["source"] in {"persona", "template"}


def test_list_companions_no_streamlit_personalities() -> None:
    cards = list_companions()
    assert all(c["source"] != "personality" for c in cards)
