from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering


SEMVER = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


@total_ordering
@dataclass(frozen=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()

    @classmethod
    def parse(cls, value):
        match = SEMVER.fullmatch(str(value).strip())
        if not match:
            raise ValueError(f"Invalid semantic version: {value}")
        prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
        for identifier in prerelease:
            if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                raise ValueError("Numeric prerelease identifiers cannot contain leading zeros.")
        return cls(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            prerelease,
        )

    def __str__(self):
        value = f"{self.major}.{self.minor}.{self.patch}"
        return value + (f"-{'.'.join(self.prerelease)}" if self.prerelease else "")

    @staticmethod
    def _identifier_compare(left, right):
        left_numeric = left.isdigit()
        right_numeric = right.isdigit()
        if left_numeric and right_numeric:
            return (int(left) > int(right)) - (int(left) < int(right))
        if left_numeric != right_numeric:
            return -1 if left_numeric else 1
        return (left > right) - (left < right)

    def _compare(self, other):
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        stable = (self.major, self.minor, self.patch)
        other_stable = (other.major, other.minor, other.patch)
        if stable != other_stable:
            return (stable > other_stable) - (stable < other_stable)
        if not self.prerelease and not other.prerelease:
            return 0
        if not self.prerelease:
            return 1
        if not other.prerelease:
            return -1
        for left, right in zip(self.prerelease, other.prerelease):
            result = self._identifier_compare(left, right)
            if result:
                return result
        return (len(self.prerelease) > len(other.prerelease)) - (
            len(self.prerelease) < len(other.prerelease)
        )

    def __eq__(self, other):
        result = self._compare(other)
        return result is not NotImplemented and result == 0

    def __lt__(self, other):
        result = self._compare(other)
        if result is NotImplemented:
            return NotImplemented
        return result < 0


@dataclass(frozen=True)
class UpdateRelease:
    version: SemanticVersion
    tag: str
    name: str
    notes: str
    page_url: str
    installer_url: str
    checksums_url: str
    prerelease: bool = False

    def __post_init__(self):
        for field_name in ("page_url", "installer_url", "checksums_url"):
            value = getattr(self, field_name)
            if not value.startswith("https://"):
                raise ValueError(f"{field_name} must use HTTPS.")
