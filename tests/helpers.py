"""Shared test helpers."""

from random import Random


class ScriptedRandom(Random):
    """Yield predetermined roll faces for active dice in order."""

    def __init__(self, faces: list[int]):
        super().__init__(0)
        self._faces = list(faces)

    def randint(self, a: int, b: int) -> int:  # noqa: ARG002
        if not self._faces:
            raise AssertionError("ran out of scripted faces")
        return self._faces.pop(0)
