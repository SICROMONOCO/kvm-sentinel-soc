"""Flag fragments loaded from the environment.

Each of the three stages has its own independent fragment. An empty fragment
means that stage is unconfigured and can never validate. The expected values
are intentionally never stringified or logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_ENV_KEYS: dict[int, str] = {
    1: "FLAG_PART1",
    2: "FLAG_PART2",
    3: "FLAG_PART3",
}


@dataclass(frozen=True, slots=True)
class FlagConfig:
    """The three independently configured flag fragments."""

    part1: str
    part2: str
    part3: str

    @classmethod
    def from_env(cls) -> "FlagConfig":
        """Read all three fragments once from the current environment."""

        return cls(
            part1=os.environ.get(_ENV_KEYS[1], ""),
            part2=os.environ.get(_ENV_KEYS[2], ""),
            part3=os.environ.get(_ENV_KEYS[3], ""),
        )

    def expected(self, flag_no: int) -> str:
        """Return the expected fragment for ``flag_no`` (empty if unset)."""

        if flag_no == 1:
            return self.part1
        if flag_no == 2:
            return self.part2
        if flag_no == 3:
            return self.part3
        return ""


def flag_config_from_env() -> FlagConfig:
    """Convenience wrapper around :meth:`FlagConfig.from_env`."""

    return FlagConfig.from_env()
