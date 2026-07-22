# API Integration Notes

## Instagram (Meta Graph API)

### Setup Steps
1. Create Meta Developer Account
2. Create App → Add Instagram Graph API product
3. Link Instagram Business Account
4. Generate Access Token (requires app review for production)

### Required Permissions
- `instagram_basic` - Read profile info
- `instagram_content_publish` - Publish posts/reels
- `pages_read_engagement` - Read comments/likes
- `pages_manage_posts` - Manage posts

### Endpoints
```
POST /{ig-user-id}/media          # Create media container
POST /{ig-user-id}/media_publish  # Publish container
GET  /{ig-user-id}/insights       # Get analytics
```

### Limitations
- Max 25 posts per day (testing)
- Images must be publicly accessible URL
- Videos: max 60 seconds (feed), 90 seconds (reels)
- Requires Business/Creator account

---

## Twitter/X API v2

### Setup Steps
1. Apply for Twitter Developer Account
2. Create Project & App
3. Generate API Keys + Bearer Token
4. Set up OAuth 2.0 for user posting

### Endpoints
```
POST /2/tweets                    # Create tweet
POST /2/media/upload              # Upload media
GET  /2/users/:id/tweets          # Get user tweets
```

### Limitations
- Free tier: 1,500 tweets/month
- Media upload: 5MB (images), 15MB (video)
- Rate limit: 300 requests/15min

---

## TikTok API

### Setup Steps
1. TikTok Developer Account
2. Create App → Content Posting API
3. OAuth flow for user authorization
4. Business account required

### Endpoints
```
POST /post/publish/video/initiate     # Initiate upload
POST /post/publish/video/upload       # Upload video
POST /post/publish/video/complete     # Finalize upload
```

### Limitations
- Videos must be pre-approved
- Max video length: 10 minutes
- Requires manual review for some accounts

---

## YouTube Data API v3

### Setup Steps
1. Google Cloud Console
2. Enable YouTube Data API v3
3. Create OAuth 2.0 credentials
4. Set up consent screen

### Endpoints
```
POST   /upload/videos           # Upload video
POST   /thumbnails/set          # Set thumbnail
GET    /videos                  # Get video details
```

### Limitations
- Daily quota: 10,000 units
- Video upload: ~1,600 units per upload
- Max video length: 12 hours (verified accounts)

---

## Cost Estimates

| API | Free Tier | Paid Tier | Monthly Estimate |
|-----|-----------|-----------|------------------|
| Instagram | 25 posts/day | Unlimited (business) | $0 |
| Twitter | 1,500 tweets/mo | $100/mo basic | $0-100 |
| TikTok | Limited | Business account | $0 |
| YouTube | 10k units/day | $0.50/1k units | $0-50 |
| ElevenLabs | 10k chars/mo | $5-330/mo | $29 |
| Stable Diffusion | Varies | $0.002-0.02/image | $50-200 |

**Total Monthly Estimate:** $79-379 (depending on usage)

---

## Authentication Flow

```python
# Example OAuth flow for Instagram
class InstagramAuth:
    def __init__(self, app_id, app_secret, redirect_uri):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
    
    def get_auth_url(self):
        scope = [
            'instagram_basic',
            'instagram_content_publish',
            'pages_read_engagement'
        ]
        return (
            f"https://www.instagram.com/oauth/authorize?"
            f"client_id={self.app_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={','.join(scope)}&"
            f"response_type=code"
        )
    
    def exchange_code_for_token(self, code):
        # Exchange authorization code for access token
        pass
```

---

## Error Handling

| Error Code | Meaning | Action |
|------------|---------|--------|
| 429 | Rate limited | Implement exponential backoff |
| 401 | Invalid token | Refresh token |
| 403 | Permission denied | Request additional scopes |
| 413 | File too large | Compress/reduce quality |
| 422 | Invalid format | Convert to supported format |

---

## Testing Checklist

- [ ] Instagram: Post image with caption
- [ ] Instagram: Post reel with audio
- [ ] Instagram: Read comments/likes
- [ ] Twitter: Post tweet with image
- [ ] Twitter: Post thread
- [ ] TikTok: Upload video
- [ ] YouTube: Upload video with thumbnail
- [ ] All platforms: Handle rate limits
- [ ] All platforms: Token refresh flow
- [ ] All platforms: Error handling
