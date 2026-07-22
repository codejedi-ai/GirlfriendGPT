import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlencode

import requests
import streamlit as st
import websockets

from utils.data import CompanionCard, get_companion_by_key, list_companions

CONFIG_FILE = Path.home() / ".gfgpt" / "config.json"


def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "name": "Luna",
        "gateway_host": "127.0.0.1",
        "gateway_port": 18789,
        "talk_frontend_url": "http://127.0.0.1:5173",
        "talk_backend_url": "http://127.0.0.1:8080",
    }


def _save_config(config: Dict[str, Any]):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def sidebar() -> CompanionCard | None:
    """Left bar: companion picker + gateway / talk stack settings."""
    config = _load_config()
    companions = list_companions()
    selected: CompanionCard | None = None

    with st.sidebar:
        st.title("Companions")
        st.caption("Pick a character from templates / personas")

        if not companions:
            st.warning("No companions found under templates/ or personalities/")
        else:
            labels = [
                f"{'🎙 ' if c.voice else '💬 '}{c.name}"
                for c in companions
            ]
            keys = [c.key for c in companions]
            default_ix = 0
            for i, c in enumerate(companions):
                if c.name.lower() == "lena van der meer" or c.name.lower() == "lena":
                    default_ix = i
                    break
            choice = st.radio(
                "Characters",
                options=keys,
                format_func=lambda k: labels[keys.index(k)],
                index=default_ix,
                label_visibility="collapsed",
            )
            selected = get_companion_by_key(choice)
            if selected:
                st.session_state["selected_companion_key"] = selected.key
                st.markdown(f"**{selected.name}**")
                if selected.description:
                    st.caption(selected.description[:200])
                st.caption(
                    f"Source: `{selected.source}`"
                    + (" · voice" if selected.voice else " · text")
                )
                if selected.agent_id:
                    st.code(selected.agent_id, language=None)

        st.divider()
        st.subheader("Talk stack (new)")
        talk_fe = st.text_input(
            "Frontend URL",
            value=config.get("talk_frontend_url", "http://127.0.0.1:5173"),
        )
        talk_be = st.text_input(
            "Backend URL",
            value=config.get("talk_backend_url", "http://127.0.0.1:8080"),
        )
        if st.button("Save Talk URLs"):
            config["talk_frontend_url"] = talk_fe.rstrip("/")
            config["talk_backend_url"] = talk_be.rstrip("/")
            _save_config(config)
            st.success("Talk URLs saved")

        if st.button("Check Talk Backend"):
            try:
                response = requests.get(f"{talk_be.rstrip('/')}/api/health", timeout=2)
                if response.status_code == 200:
                    st.success(f"OK — {response.json()}")
                else:
                    st.warning(f"Backend returned {response.status_code}")
            except Exception as e:
                st.error(f"Backend unreachable: {e}")

        st.divider()
        st.subheader("Text gateway (legacy)")
        host = st.text_input("Host", value=config.get("gateway_host", "127.0.0.1"))
        port = st.number_input(
            "Port",
            min_value=1,
            max_value=65535,
            value=int(config.get("gateway_port", 18789)),
        )

        if st.button("Save Gateway Settings"):
            config["gateway_host"] = host
            config["gateway_port"] = int(port)
            _save_config(config)
            st.success("Gateway settings saved")

        base_url = f"http://{host}:{port}"
        ws_url = f"ws://{host}:{port}"
        st.caption(f"HTTP: {base_url}")
        st.caption(f"WS: {ws_url}")

        if st.button("Check Gateway Health"):
            try:
                response = requests.get(f"{base_url}/health", timeout=2)
                if response.status_code == 200:
                    st.success("Gateway is healthy")
                else:
                    st.warning(f"Gateway returned {response.status_code}")
            except Exception as e:
                st.error(f"Gateway unreachable: {e}")

    return selected


def talk_embed_url(companion: CompanionCard) -> str:
    config = _load_config()
    base = str(config.get("talk_frontend_url") or "http://127.0.0.1:5173").rstrip("/")
    params: dict[str, str] = {"name": companion.name}
    if companion.agent_id:
        params["agent_id"] = companion.agent_id
    return f"{base}/talk?{urlencode(params)}"


def get_gateway_urls() -> Dict[str, str]:
    config = _load_config()
    host = config.get("gateway_host", "127.0.0.1")
    port = int(config.get("gateway_port", 18789))
    return {
        "http": f"http://{host}:{port}",
        "ws": f"ws://{host}:{port}",
    }


def create_instance(config: Dict[str, Any]) -> Dict[str, Any]:
    instance = {
        "name": config.get("name", "Companion"),
        "config": config,
        "session_id": str(uuid.uuid4()),
    }
    st.session_state.instance = instance
    return instance


def get_instance() -> Dict[str, Any]:
    instance = st.session_state.get("instance")
    if not instance:
        st.warning("First create your companion on the main page")
        st.stop()
    return instance


async def _send_ws_prompt(session_id: str, prompt: str) -> str:
    urls = get_gateway_urls()
    uri = f"{urls['ws']}/ws/{session_id}"
    async with websockets.connect(uri) as websocket:
        _ = await asyncio.wait_for(websocket.recv(), timeout=8.0)
        await websocket.send(
            json.dumps(
                {
                    "role": "user",
                    "content": prompt,
                    "type": "text",
                    "metadata": None,
                }
            )
        )

        while True:
            response = await asyncio.wait_for(websocket.recv(), timeout=90.0)
            data = json.loads(response)
            if data.get("type") != "ping":
                return data.get("content", "")


def invoke_prompt(instance: Dict[str, Any], prompt: str) -> str:
    try:
        return asyncio.run(_send_ws_prompt(instance["session_id"], prompt))
    except Exception as e:
        return f"Error: {e}"


def show_response(response):
    if isinstance(response, str):
        st.write(response)
    else:
        mime_type = response.get("mimeType")
        if mime_type is None:
            st.write(response.get("text", ""))
        elif "audio" in mime_type:
            st.audio(response.get("url"))
