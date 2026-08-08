from __future__ import annotations

import json
import unittest

from backend.updating import GitHubReleaseClient, SemanticVersion, UpdateService


def release(version, *, prerelease=False, draft=False, assets=True):
    tag = f"v{version}"
    items = []
    if assets:
        items = [
            {
                "name": f"AIContentStudio-Setup-{version}-windows-x64.exe",
                "browser_download_url": f"https://github.com/download/{version}/installer.exe",
            },
            {
                "name": "SHA256SUMS.txt",
                "browser_download_url": f"https://github.com/download/{version}/SHA256SUMS.txt",
            },
        ]
    return {
        "tag_name": tag,
        "name": f"Release {version}",
        "body": "Changes",
        "html_url": f"https://github.com/releases/{tag}",
        "draft": draft,
        "prerelease": prerelease,
        "assets": items,
    }


class SemanticVersionTests(unittest.TestCase):
    def test_semantic_precedence(self):
        ordered = [
            "1.0.0-alpha",
            "1.0.0-alpha.1",
            "1.0.0-alpha.beta",
            "1.0.0-beta",
            "1.0.0-beta.2",
            "1.0.0-beta.11",
            "1.0.0-rc.1",
            "1.0.0",
            "1.0.1",
        ]
        parsed = [SemanticVersion.parse(value) for value in ordered]
        self.assertEqual(sorted(reversed(parsed)), parsed)

    def test_invalid_versions_are_rejected(self):
        for value in ("", "1", "1.2", "01.2.3", "1.2.3-01", "latest"):
            with self.assertRaises(ValueError, msg=value):
                SemanticVersion.parse(value)


class UpdateServiceTests(unittest.TestCase):
    @staticmethod
    def service(releases):
        client = GitHubReleaseClient(
            transport=lambda url, headers, timeout: json.dumps(releases)
        )
        return UpdateService(client)

    def test_selects_highest_newer_stable_release_with_required_assets(self):
        service = self.service(
            [
                release("0.18.0"),
                release("0.20.0"),
                release("0.21.0-beta.1", prerelease=True),
                release("0.22.0", draft=True),
                release("0.23.0", assets=False),
                {"tag_name": "latest"},
            ]
        )
        update = service.check("0.19.0")
        self.assertEqual(str(update.version), "0.20.0")
        self.assertTrue(update.installer_url.startswith("https://"))
        self.assertTrue(update.checksums_url.endswith("SHA256SUMS.txt"))

    def test_prerelease_channel_is_explicit(self):
        service = self.service(
            [release("0.20.0"), release("0.21.0-beta.2", prerelease=True)]
        )
        self.assertEqual(str(service.check("0.19.0").version), "0.20.0")
        self.assertEqual(
            str(service.check("0.19.0", include_prereleases=True).version),
            "0.21.0-beta.2",
        )

    def test_current_or_older_release_returns_none(self):
        service = self.service([release("0.18.0"), release("0.19.0")])
        self.assertIsNone(service.check("0.19.0"))

    def test_transport_contract_and_https_api_are_enforced(self):
        calls = []

        def transport(url, headers, timeout):
            calls.append((url, headers, timeout))
            return "[]"

        client = GitHubReleaseClient(transport=transport, timeout=99)
        self.assertEqual(client.fetch(), [])
        self.assertEqual(calls[0][2], 30)
        self.assertIn("User-Agent", calls[0][1])
        with self.assertRaises(ValueError):
            GitHubReleaseClient(url="http://example.com/releases")


if __name__ == "__main__":
    unittest.main()
