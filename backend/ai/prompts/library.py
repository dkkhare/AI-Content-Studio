from __future__ import annotations

from .template import PromptTemplate


class PromptNotFoundError(KeyError):
    pass


class PromptLibrary:
    """Version-aware prompt registry."""

    def __init__(self):
        self._templates: dict[str, dict[str, PromptTemplate]] = {}

    def register(self, template: PromptTemplate, *, replace: bool = False) -> None:
        name = template.name.strip().lower()
        version = template.version.strip()
        if not name or not version:
            raise ValueError("Prompt name and version are required.")
        versions = self._templates.setdefault(name, {})
        if version in versions and not replace:
            raise ValueError(f"Prompt already registered: {name}@{version}")
        versions[version] = template

    def get(self, name: str, version: str | None = None) -> PromptTemplate:
        key = str(name).strip().lower()
        versions = self._templates.get(key)
        if not versions:
            raise PromptNotFoundError(f"Prompt is not registered: {key}")
        if version is not None:
            try:
                return versions[str(version)]
            except KeyError as exc:
                raise PromptNotFoundError(f"Prompt version is not registered: {key}@{version}") from exc
        latest = sorted(versions, key=self._version_key)[-1]
        return versions[latest]

    def names(self) -> list[str]:
        return sorted(self._templates)

    def versions(self, name: str) -> list[str]:
        key = str(name).strip().lower()
        return sorted(self._templates.get(key, {}), key=self._version_key)

    @staticmethod
    def _version_key(value: str):
        parts = []
        for item in str(value).replace("v", "", 1).split("."):
            try:
                parts.append((0, int(item)))
            except ValueError:
                parts.append((1, item))
        return tuple(parts)
