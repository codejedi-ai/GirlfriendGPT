import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict

import requests
import streamlit as st
import websockets

CONFIG_FILE = Path.home() / ".gfgpt" / "config.json"


def _load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "name": "Luna",
        "gateway_host": "127.0.0.1",
        "gateway_port": 18789,
    }


def _save_config(config: Dict[str, Any]):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def sidebar():
    config = _load_config()

    with st.sidebar:
        st.subheader("Gateway")
        host = st.text_input("Host", value=config.get("gateway_host", "127.0.0.1"))
        port = st.number_input("Port", min_value=1, max_value=65535, value=int(config.get("gateway_port", 18789)))

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
        # Consume greeting frame first.
        _ = await asyncio.wait_for(websocket.recv(), timeout=8.0)
        await websocket.send(json.dumps({
            "role": "user",
            "content": prompt,
            "type": "text",
            "metadata": None,
        }))

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
