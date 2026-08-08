from __future__ import annotations

import json
from urllib.request import Request, urlopen

from backend.version import VERSION

from .core import SemanticVersion, UpdateRelease


REPOSITORY = "dkkhare/AI-Content-Studio"
RELEASES_URL = f"https://api.github.com/repos/{REPOSITORY}/releases"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def _download_json(url, headers, timeout):
    request = Request(url, headers=headers)
    with urlopen(request, timeout=timeout) as response:
        data = response.read(MAX_RESPONSE_BYTES + 1)
    if len(data) > MAX_RESPONSE_BYTES:
        raise ValueError("GitHub release response exceeded the safety limit.")
    return data


class GitHubReleaseClient:
    def __init__(self, *, url=RELEASES_URL, transport=None, timeout=10):
        if not str(url).startswith("https://"):
            raise ValueError("Release API URL must use HTTPS.")
        self.url = str(url)
        self.transport = transport or _download_json
        self.timeout = max(1, min(int(timeout), 30))

    def fetch(self):
        payload = self.transport(
            self.url,
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "AIContentStudio-Updater",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            self.timeout,
        )
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        releases = json.loads(payload) if isinstance(payload, str) else payload
        if not isinstance(releases, list):
            raise ValueError("GitHub releases response must be a list.")
        return releases


class UpdateService:
    def __init__(self, client=None):
        self.client = client or GitHubReleaseClient()

    @staticmethod
    def _asset_url(release, filename):
        assets = release.get("assets", [])
        if not isinstance(assets, list):
            return ""
        for asset in assets:
            if (
                isinstance(asset, dict)
                and asset.get("name") == filename
                and str(asset.get("browser_download_url", "")).startswith("https://")
            ):
                return str(asset["browser_download_url"])
        return ""

    @classmethod
    def _normalize(cls, release):
        if not isinstance(release, dict) or release.get("draft"):
            return None
        tag = str(release.get("tag_name", "")).strip()
        try:
            version = SemanticVersion.parse(tag)
        except ValueError:
            return None
        prerelease = bool(release.get("prerelease")) or bool(version.prerelease)
        installer_name = f"AIContentStudio-Setup-{version}-windows-x64.exe"
        installer_url = cls._asset_url(release, installer_name)
        checksums_url = cls._asset_url(release, "SHA256SUMS.txt")
        page_url = str(release.get("html_url", ""))
        if not installer_url or not checksums_url or not page_url.startswith("https://"):
            return None
        return UpdateRelease(
            version=version,
            tag=tag,
            name=str(release.get("name") or tag),
            notes=str(release.get("body") or ""),
            page_url=page_url,
            installer_url=installer_url,
            checksums_url=checksums_url,
            prerelease=prerelease,
        )

    def check(self, current_version=VERSION, *, include_prereleases=False):
        current = SemanticVersion.parse(current_version)
        candidates = []
        for raw in self.client.fetch():
            release = self._normalize(raw)
            if release is None or release.version <= current:
                continue
            if release.prerelease and not include_prereleases:
                continue
            candidates.append(release)
        return max(candidates, key=lambda item: item.version, default=None)
