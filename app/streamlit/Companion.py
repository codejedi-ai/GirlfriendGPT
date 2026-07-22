import sys
from pathlib import Path
import json

import streamlit as st
import streamlit.components.v1 as components

sys.path.append(str((Path(__file__) / "..").resolve()))
st.set_page_config(
    page_title="GirlfriendGPT Companion",
    page_icon="🤗",
    layout="wide",
    initial_sidebar_state="expanded",
)
from utils.data import get_companions, get_companion_attributes, add_resource
from utils.ux import sidebar, show_response, create_instance, invoke_prompt, talk_embed_url

CONFIG_FILE = Path.home() / ".gfgpt" / "config.json"


def _load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


st.title("🤗 GirlfriendGPT Companion")
st.write("Select a character in the left bar — voice companions open the LiveKit talk UI.")

selected = sidebar()

# --- Voice companion: embed the new Vite Talk UI ---
if selected and selected.voice and selected.agent_id:
    st.header(f"🎙 Voice talk with {selected.name}")
    st.caption(
        "Embedded from app/frontend → app/backend `/api/token` → LiveKit → app/agent. "
        "Keep Vite (:5173), backend (:8080), and the voice worker running."
    )
    embed = talk_embed_url(selected)
    st.markdown(f"[Open in new tab]({embed})")
    components.iframe(embed, height=720, scrolling=True)
    st.stop()

# --- Legacy text companion flow ---
if not st.session_state.get("instance"):
    col1, col2 = st.columns(2)

    col1.subheader("Attributes")
    default_template = selected.name if selected and not selected.voice else "<none>"
    options = ["<none>", *get_companions()]
    try:
        default_index = options.index(default_template) if default_template in options else 0
    except ValueError:
        default_index = 0
    companion_template = col2.selectbox(
        "Templates (Optional)",
        options=options,
        index=default_index,
    )
    if companion_template != "<none>":
        companion = get_companion_attributes(companion_template.lower())
        if not companion:
            companion = get_companion_attributes(companion_template)
    else:
        companion = selected.attrs if selected else {}

    personality = st.text_input(
        "Name",
        value=companion.get("name", ""),
        placeholder="The name of your companion",
    )
    byline = st.text_input(
        "Byline",
        value=companion.get("byline", ""),
        placeholder="The byline of your companion",
    )
    identity = st.text_area(
        "Identity",
        value=companion.get("identity", ""),
        placeholder="The identity of your companion",
    )
    behavior = st.text_area(
        "Behavior",
        value=companion.get("behavior", ""),
        placeholder="The behavior of your companion",
    )
    st.session_state.companion_profile_img = st.text_input(
        "Profile picture",
        value=companion.get("profile_image", ""),
        placeholder="The profile picture of your companion",
    )

    st.session_state.companion_first_message = st.text_input(
        label="First message",
        placeholder="The first message your companion sends when a new conversation starts.",
    )

    st.subheader("Long term memory")
    youtube_video_url = st.text_input("Youtube Video URL")

    if st.button("🤗 Spin up your companion"):
        existing = _load_config()
        existing.update(
            {
                "name": personality,
                "byline": byline,
                "identity": identity,
                "behavior": behavior,
            }
        )
        _save_config(existing)

        create_instance(
            {
                "name": personality,
                "byline": byline,
                "identity": identity,
                "behavior": behavior,
            }
        )

        if youtube_video_url:
            with st.spinner("Companion is watching the video 👀..."):
                add_resource(youtube_video_url)

        st.balloons()
        st.rerun()

else:
    instance = st.session_state.instance
    companion_name = instance["config"]["name"]

    if st.button("+ New bot"):
        st.session_state.instance = None
        st.rerun()

    st.header(f"Start chatting with {companion_name}")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": st.session_state.companion_first_message or "Hi ☺️",
            }
        ]

    companion_img = st.session_state.get("companion_profile_img")
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            with st.chat_message(msg["role"], avatar=companion_img or None):
                for response in (
                    [msg["content"]] if isinstance(msg["content"], str) else msg["content"]
                ):
                    show_response(response)
        else:
            st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = invoke_prompt(instance, prompt)
            show_response(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
