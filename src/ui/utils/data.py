import concurrent
import itertools
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import scrapetube
import streamlit as st

RESOURCE_FILE = Path.home() / ".gfgpt" / "ui_resources.json"


def _load_resources():
    if RESOURCE_FILE.exists():
        with open(RESOURCE_FILE, "r") as f:
            return json.load(f)
    return []


def _save_resources(resources):
    RESOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESOURCE_FILE, "w") as f:
        json.dump(resources, f, indent=2)


def add_resource(url: str):
    resources = _load_resources()
    if url not in resources:
        resources.append(url)
        _save_resources(resources)
        return "Added"
    return "Already added"


def index_youtube_channel(
    channel_url: str, offset: Optional[int] = 0, count: Optional[int] = 10
):
    videos = scrapetube.get_channel(channel_url=channel_url)

    future_to_url = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        for video in itertools.islice(videos, offset, offset + count + 1):
            video_url = f"https://www.youtube.com/watch?v={video['videoId']}"
            future_to_url[executor.submit(add_resource, video_url)] = video_url

    for ix, future in enumerate(concurrent.futures.as_completed(future_to_url)):
        url = future_to_url[future]
        try:
            data = future.result()
            if data.lower().contains("added"):
                st.write(f"Added {url}")
        except Exception as e:
            st.error(f"Loading {url} generated an exception: {e}")


def index_youtube_video(youtube_url: str):
    data = add_resource(youtube_url)

    if "added" in data.lower():
        st.write(f"Added {youtube_url}")
    else:
        print("error", data)


def get_indexed_resources():
    return _load_resources()


# Personalities are now stored as templates under the agent example. We
# look relative to this file so both the UI and the example scripts can
# access them regardless of where the repo is installed.
COMPANION_DIR = (
    Path(__file__) / ".." / ".." / ".." / "src" / "templates" / "personalities"
).resolve()


def get_companions():
    return [
        companion.stem
        for companion in COMPANION_DIR.iterdir()
        if companion.suffix == ".json"
    ]


def get_companion_attributes(companion_name: str):
    companion = json.load((COMPANION_DIR / f"{companion_name}.json").open())
    return {
        "name": companion["name"],
        "byline": companion["byline"],
        "identity": companion["identity"] if isinstance(companion["identity"], str) else "\n".join(companion["identity"]),
        "behavior": companion["behavior"] if isinstance(companion["behavior"], str) else "\n".join(companion["behavior"]),
        "profile_image": companion.get("profile_image", ""),
        "description": companion.get("description", ""),
    }
