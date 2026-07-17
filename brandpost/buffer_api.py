"""Buffer API client for scheduling generated posts to Instagram.

Buffer's public API is GraphQL, a single endpoint (https://api.buffer.com)
authenticated with a Bearer access token from Settings -> API in Buffer.
Reference: https://developers.buffer.com

Important constraint (from Buffer's own docs): the API has no image upload
endpoint. Every image must be a stable, public, unauthenticated HTTPS URL
that stays reachable until the scheduled post actually publishes. This
module only ever receives URLs it's given - see storage.public_url_for()
for how BrandPost Studio produces them from its own static file serving.

Multi-image (carousel) support for the "assets" list is not explicitly
documented by Buffer at the time this was written; it is modeled here as an
ordered list matching Instagram's own carousel semantics, but treat it as
best-effort and verify the first scheduled carousel in Buffer's dashboard.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime

API_URL = "https://api.buffer.com"


class BufferError(RuntimeError):
    pass


def _api_key(explicit_key: str | None = None) -> str | None:
    return explicit_key or os.environ.get("BUFFER_API_KEY")


def is_configured(explicit_key: str | None = None) -> bool:
    return bool(_api_key(explicit_key))


def _graphql(query: str, variables: dict, api_key: str) -> dict:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise BufferError("the requests library is not installed") from exc

    try:
        resp = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as exc:
        raise BufferError(f"Buffer API request failed: {exc}") from exc

    payload = resp.json()
    if payload.get("errors"):
        raise BufferError("Buffer API error: " + "; ".join(e.get("message", "") for e in payload["errors"]))
    return payload.get("data", {})


@dataclass
class Channel:
    id: str
    display_name: str
    service: str


def get_first_organization_id(api_key: str) -> str:
    data = _graphql(
        "query GetOrganizations { account { organizations { id name } } }", {}, api_key
    )
    orgs = data.get("account", {}).get("organizations", [])
    if not orgs:
        raise BufferError("No Buffer organizations found for this API key.")
    return orgs[0]["id"]


def get_instagram_channels(api_key: str, organization_id: str | None = None) -> list[Channel]:
    org_id = organization_id or get_first_organization_id(api_key)
    query = """
    query GetChannels($input: ChannelsInput!) {
      channels(input: $input) { id name displayName service }
    }
    """
    data = _graphql(query, {"input": {"organizationId": org_id}}, api_key)
    channels = data.get("channels", [])
    return [
        Channel(id=c["id"], display_name=c.get("displayName") or c.get("name", ""), service=c.get("service", ""))
        for c in channels
        if "instagram" in (c.get("service") or "").lower()
    ]


def schedule_post(
    api_key: str,
    channel_id: str,
    caption: str,
    image_urls: list[str],
    scheduled_at: datetime | None,
    alt_texts: list[str] | None = None,
) -> str:
    """Create an Instagram post via Buffer. scheduled_at=None adds it to the
    channel's next open queue slot instead of a specific time. Returns the
    Buffer post id."""
    if not image_urls:
        raise BufferError("At least one public image URL is required.")

    alt_texts = alt_texts or [""] * len(image_urls)
    assets = [
        {"image": {"url": url, "metadata": {"altText": alt or "Instagram post image"}}}
        for url, alt in zip(image_urls, alt_texts)
    ]

    post_input = {
        "text": caption,
        "channelId": channel_id,
        "schedulingType": "automatic",
        "assets": assets,
        "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}},
    }
    if scheduled_at is not None:
        post_input["mode"] = "customScheduled"
        post_input["dueAt"] = scheduled_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    else:
        post_input["mode"] = "addToQueue"

    query = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess { post { id } }
        ... on MutationError { message }
      }
    }
    """
    data = _graphql(query, {"input": post_input}, api_key)
    result = data.get("createPost", {})
    if "message" in result:
        raise BufferError(f"Buffer rejected the post: {result['message']}")
    post = result.get("post")
    if not post:
        raise BufferError("Buffer returned no post id and no error - unexpected response shape.")
    return post["id"]
