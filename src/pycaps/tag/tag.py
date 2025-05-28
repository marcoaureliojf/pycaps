from dataclasses import dataclass

@dataclass(frozen=True)
class Tag:
    name: str
