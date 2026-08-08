from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PublishResult:
    external_id: str = ""
    external_url: str = ""
    destination: str = ""
    raw: dict[str, Any] | None = None


class PublishingProvider:
    provider_id = "base"
    display_name = "Publishing Provider"

    def configured(self) -> bool:
        return True

    def configuration_error(self) -> str:
        return ""

    def publish(self, manifest: dict[str, Any], *, root: Path) -> PublishResult:
        raise NotImplementedError


class ManualPublishingProvider(PublishingProvider):
    provider_id = "manual"
    display_name = "Manual / External"

    def publish(self, manifest: dict[str, Any], *, root: Path) -> PublishResult:
        raise RuntimeError("Manual publishing does not upload files. Use Mark Published after publishing externally.")


class YouTubePublishingProvider(PublishingProvider):
    provider_id = "youtube"
    display_name = "YouTube"

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    def __init__(self, *, client_secrets_path: str = "", token_path: str = ""):
        self.client_secrets_path = str(client_secrets_path or "").strip()
        self.token_path = str(token_path or "").strip()

    def configured(self) -> bool:
        return bool(self.client_secrets_path) and Path(self.client_secrets_path).is_file()

    def configuration_error(self) -> str:
        if not self.client_secrets_path:
            return "YouTube OAuth client-secrets file is not configured."
        if not Path(self.client_secrets_path).is_file():
            return f"YouTube OAuth client-secrets file does not exist: {self.client_secrets_path}"
        return ""

    def _credentials(self):
        if not self.configured():
            raise RuntimeError(self.configuration_error())
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise RuntimeError(
                "YouTube publishing requires google-api-python-client, google-auth-oauthlib, and google-auth."
            ) from exc

        credentials = None
        token = Path(self.token_path) if self.token_path else None
        if token and token.is_file():
            credentials = Credentials.from_authorized_user_file(str(token), self.SCOPES)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        if not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, self.SCOPES)
            credentials = flow.run_local_server(port=0)
        if token:
            token.parent.mkdir(parents=True, exist_ok=True)
            token.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    @staticmethod
    def _body(manifest: dict[str, Any]) -> dict[str, Any]:
        youtube = manifest.get("youtube", {}) if isinstance(manifest.get("youtube"), dict) else {}
        snippet = {
            "title": str(youtube.get("title", ""))[:100],
            "description": str(youtube.get("description", ""))[:5000],
            "tags": [str(value) for value in youtube.get("tags", []) if str(value).strip()],
            "categoryId": str(youtube.get("category_id", "27") or "27"),
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi",
        }
        status = {
            "privacyStatus": str(youtube.get("privacy", "private") or "private"),
            "selfDeclaredMadeForKids": bool(youtube.get("made_for_kids", False)),
        }
        return {"snippet": snippet, "status": status}

    def publish(self, manifest: dict[str, Any], *, root: Path) -> PublishResult:
        files = manifest.get("files", {}) if isinstance(manifest.get("files"), dict) else {}
        video_value = str(files.get("video", ""))
        if not video_value:
            raise ValueError("Publish manifest has no final video path.")
        video_path = (root / video_value).resolve()
        if not video_path.is_file():
            raise ValueError(f"Final video does not exist: {video_path}")

        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise RuntimeError(
                "YouTube publishing requires google-api-python-client, google-auth-oauthlib, and google-auth."
            ) from exc

        youtube = build("youtube", "v3", credentials=self._credentials())
        request = youtube.videos().insert(
            part="snippet,status",
            body=self._body(manifest),
            media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
        )
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = str((response or {}).get("id", ""))
        if not video_id:
            raise RuntimeError("YouTube upload completed without returning a video ID.")

        thumbnail_value = str(files.get("thumbnail", ""))
        thumbnail_path = (root / thumbnail_value).resolve() if thumbnail_value else None
        if thumbnail_path and thumbnail_path.is_file():
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), resumable=False),
            ).execute()

        return PublishResult(
            external_id=video_id,
            external_url=f"https://www.youtube.com/watch?v={video_id}",
            destination="youtube",
            raw=response if isinstance(response, dict) else {},
        )
