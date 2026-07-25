"""Social media posting tools for AI Influencer Agent."""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base import BaseTool


class InstagramPostTool(BaseTool):
    """Tool to post content to Instagram."""

    name: str = "InstagramPostTool"
    human_description: str = "Post content to Instagram (feed posts, reels, stories). Handles images, videos, captions, and hashtags."
    agent_description: str = "Post to Instagram. Can create feed posts, reels, or stories with images/videos, captions, and hashtags."

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

    def run(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Post to Instagram.

        Args:
            input_data: Caption text
            **kwargs: media_path, media_type, hashtags, schedule_time

        Returns:
            Dictionary with post status and URL
        """
        caption = input_data
        media_path = kwargs.get("media_path", "")
        media_type = kwargs.get("media_type", "image")  # image, video, reel, story
        hashtags = kwargs.get("hashtags", [])
        schedule_time = kwargs.get("schedule_time")

        # Format caption with hashtags
        full_caption = self._format_caption(caption, hashtags)

        if schedule_time:
            return self._schedule_post(media_path, media_type, full_caption, schedule_time)
        else:
            return self._publish_now(media_path, media_type, full_caption)

    def _format_caption(self, caption: str, hashtags: List[str]) -> str:
        """Format caption with hashtags."""
        if hashtags:
            hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
            return f"{caption}\n\n{hashtag_str}"
        return caption

    def _publish_now(self, media_path: str, media_type: str, caption: str) -> Dict[str, Any]:
        """Publish immediately."""
        return {
            "status": "success",
            "platform": "instagram",
            "media_type": media_type,
            "caption": caption,
            "message": f"Posted to Instagram ({media_type})",
            "post_url": "https://instagram.com/p/placeholder",
            "posted_at": datetime.now().isoformat()
        }

    def _schedule_post(self, media_path: str, media_type: str, caption: str, 
                       schedule_time: str) -> Dict[str, Any]:
        """Schedule for later."""
        return {
            "status": "scheduled",
            "platform": "instagram",
            "media_type": media_type,
            "caption": caption,
            "scheduled_for": schedule_time,
            "message": f"Scheduled Instagram {media_type} for {schedule_time}",
        }


class TwitterPostTool(BaseTool):
    """Tool to post content to Twitter/X."""

    name: str = "TwitterPostTool"
    human_description: str = "Post tweets, threads, and media to Twitter/X. Handles text, images, and videos."
    agent_description: str = "Post to Twitter. Can create single tweets, threads, or tweets with media."

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TWITTER_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("TWITTER_API_SECRET", "")

    def run(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Post to Twitter.

        Args:
            input_data: Tweet text
            **kwargs: media_paths, is_thread, schedule_time

        Returns:
            Dictionary with tweet status and URL
        """
        tweet_text = input_data
        media_paths = kwargs.get("media_paths", [])
        is_thread = kwargs.get("is_thread", False)
        schedule_time = kwargs.get("schedule_time")

        if is_thread:
            return self._post_thread(tweet_text, media_paths, schedule_time)
        else:
            return self._post_tweet(tweet_text, media_paths, schedule_time)

    def _post_tweet(self, text: str, media: List[str], schedule: Optional[str]) -> Dict[str, Any]:
        """Post a single tweet."""
        if schedule:
            return {
                "status": "scheduled",
                "platform": "twitter",
                "text": text,
                "media_count": len(media),
                "scheduled_for": schedule,
                "message": f"Scheduled tweet for {schedule}",
            }
        
        return {
            "status": "success",
            "platform": "twitter",
            "text": text,
            "media_count": len(media),
            "message": "Posted to Twitter",
            "tweet_url": "https://twitter.com/status/placeholder",
            "posted_at": datetime.now().isoformat()
        }

    def _post_thread(self, text: str, media: List[str], schedule: Optional[str]) -> Dict[str, Any]:
        """Post a tweet thread."""
        return {
            "status": "success",
            "platform": "twitter",
            "type": "thread",
            "text": text,
            "message": "Posted thread to Twitter",
            "thread_url": "https://twitter.com/status/placeholder",
            "posted_at": datetime.now().isoformat()
        }


class TikTokPostTool(BaseTool):
    """Tool to post content to TikTok."""

    name: str = "TikTokPostTool"
    human_description: str = "Post videos to TikTok. Handles video uploads, captions, hashtags, and sounds."
    agent_description: str = "Post to TikTok. Uploads videos with captions, hashtags, and optional sounds."

    def run(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Post to TikTok.

        Args:
            input_data: Video description/caption
            **kwargs: video_path, hashtags, sound_id, schedule_time

        Returns:
            Dictionary with post status
        """
        caption = input_data
        video_path = kwargs.get("video_path", "")
        hashtags = kwargs.get("hashtags", [])
        sound_id = kwargs.get("sound_id")
        schedule_time = kwargs.get("schedule_time")

        return {
            "status": "success",
            "platform": "tiktok",
            "caption": caption,
            "video_path": video_path,
            "hashtags": hashtags,
            "sound_id": sound_id,
            "message": f"Posted to TikTok: {caption[:50]}...",
            "post_url": "https://tiktok.com/@user/video/placeholder",
            "posted_at": datetime.now().isoformat()
        }


class YouTubePostTool(BaseTool):
    """Tool to post content to YouTube."""

    name: str = "YouTubePostTool"
    human_description: str = "Upload videos to YouTube (regular videos, shorts, premieres). Handles titles, descriptions, tags, and thumbnails."
    agent_description: str = "Upload to YouTube. Can create regular videos, shorts, or premieres with titles, descriptions, tags, thumbnails."

    def run(self, input_data: str, **kwargs) -> Dict[str, Any]:
        """Upload to YouTube.

        Args:
            input_data: Video title
            **kwargs: video_path, description, tags, thumbnail_path, video_type, schedule_time

        Returns:
            Dictionary with upload status
        """
        title = input_data
        video_path = kwargs.get("video_path", "")
        description = kwargs.get("description", "")
        tags = kwargs.get("tags", [])
        thumbnail_path = kwargs.get("thumbnail_path")
        video_type = kwargs.get("video_type", "video")  # video, short, premiere
        schedule_time = kwargs.get("schedule_time")

        return {
            "status": "success",
            "platform": "youtube",
            "title": title,
            "video_type": video_type,
            "description": description,
            "tags": tags,
            "message": f"Uploaded to YouTube ({video_type}): {title}",
            "video_url": "https://youtube.com/watch?v=placeholder",
            "posted_at": datetime.now().isoformat()
        }
