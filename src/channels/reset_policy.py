from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ResetResponsePolicy(ABC):
    """Decides whether a reset-time response should be absorbed."""

    def __init__(self, max_absorb: int = 1):
        self.max_absorb = max_absorb
        self._absorbed_count = 0

    def reset(self) -> None:
        self._absorbed_count = 0

    def can_absorb(self, message: str) -> bool:
        if self.max_absorb >= 0 and self._absorbed_count >= self.max_absorb:
            return False
        if not self.should_absorb(message):
            return False
        self._absorbed_count += 1
        return True

    @abstractmethod
    def should_absorb(self, message: str) -> bool:
        ...

    def describe(self) -> str:
        return self.__class__.__name__


@dataclass
class ExactMatchResetPolicy(ResetResponsePolicy):
    target: str
    strip: bool = True
    max_absorb: int = 1

    def __post_init__(self) -> None:
        super().__init__(max_absorb=self.max_absorb)

    def should_absorb(self, message: str) -> bool:
        if self.strip:
            return message.strip() == self.target
        return message == self.target

    def describe(self) -> str:
        return f"ExactMatch({self.target!r})"


@dataclass
class RegexResetPolicy(ResetResponsePolicy):
    pattern: str
    flags: int = 0
    max_absorb: int = 1

    def __post_init__(self) -> None:
        super().__init__(max_absorb=self.max_absorb)
        self._compiled = re.compile(self.pattern, self.flags)

    def should_absorb(self, message: str) -> bool:
        return self._compiled.search(message) is not None

    def describe(self) -> str:
        return f"Regex({self.pattern!r})"
