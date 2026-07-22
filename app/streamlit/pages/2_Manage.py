import pandas as pd
import streamlit as st
from pytube import YouTube

from utils.data import index_youtube_video, get_indexed_resources
from utils.ux import sidebar

st.title("Manage your chatbot")

sidebar()


def _get_video_info(youtube_url: str):
    yt = YouTube(youtube_url)
    return {
        "title": yt.title or "Unknown",
        "description": yt.description or "Unknown",
        "view_count": yt.views or 0,
        "thumbnail_url": yt.thumbnail_url or "Unknown",
        "publish_date": yt.publish_date.strftime("%Y-%m-%d %H:%M:%S")
        if yt.publish_date
        else "Unknown",
        "length": yt.length or 0,
        "author": yt.author or "Unknown",
    }


def load_and_show_videos():
    resources = get_indexed_resources()
    documents = []
    for source_url in resources:
        video_info = _get_video_info(source_url)
        documents.append(
            {
                "Title": video_info.get("title"),
                "source": source_url,
                "thumbnail_url": video_info.get("thumbnail_url"),
                "Status": "indexed",
            }
        )
    df = pd.DataFrame(documents)
    table.dataframe(
        df,
        column_config={
            "Title": st.column_config.LinkColumn("source"),
            "thumbnail_url": st.column_config.ImageColumn(label="Thumbnail"),
        },
        column_order=["thumbnail_url", "Title", "Status"],
    )

    return documents


table = st.empty()

youtube_url = st.text_input("Youtube video url")
if st.button("Add video"):
    index_youtube_video(youtube_url)

if st.button("Refresh table"):
    table.text("Loading videos...")
    load_and_show_videos()

# Initial load
table.text("Loading videos...")
load_and_show_videos()
