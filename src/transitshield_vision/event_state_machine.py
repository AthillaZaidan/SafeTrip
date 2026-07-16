from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _EntityState:
    state: str = "clear"
    candidate_started_at: float | None = None
    cooldown_until: float = 0.0


@dataclass(frozen=True)
class StateUpdate:
    state: str
    confirmed_now: bool = False
    closed_now: bool = False
    candidate_started_at: float | None = None
    persistence_seconds: float = 0.0


class EventStateMachine:
    def __init__(self, minimum_duration_seconds: float, cooldown_seconds: float):
        if minimum_duration_seconds < 0 or cooldown_seconds < 0:
            raise ValueError("durations cannot be negative")
        self.minimum_duration_seconds = minimum_duration_seconds
        self.cooldown_seconds = cooldown_seconds
        self._entities: dict[str, _EntityState] = {}

    def update(self, entity_key: str, condition: bool, timestamp_seconds: float) -> StateUpdate:
        entity = self._entities.setdefault(entity_key, _EntityState())
        if entity.state == "cooldown":
            if timestamp_seconds < entity.cooldown_until:
                return StateUpdate("cooldown")
            entity.state = "clear"

        if not condition:
            if entity.state == "alerted":
                started = entity.candidate_started_at
                entity.state = "cooldown"
                entity.cooldown_until = timestamp_seconds + self.cooldown_seconds
                entity.candidate_started_at = None
                return StateUpdate("cooldown", closed_now=True, candidate_started_at=started)
            entity.state = "clear"
            entity.candidate_started_at = None
            return StateUpdate("clear")

        if entity.state == "clear":
            entity.state = "candidate"
            entity.candidate_started_at = timestamp_seconds

        started = entity.candidate_started_at if entity.candidate_started_at is not None else timestamp_seconds
        persistence = max(0.0, timestamp_seconds - started)
        if entity.state == "candidate" and persistence + 1e-9 >= self.minimum_duration_seconds:
            entity.state = "alerted"
            return StateUpdate("alerted", confirmed_now=True, candidate_started_at=started, persistence_seconds=persistence)
        return StateUpdate(entity.state, candidate_started_at=started, persistence_seconds=persistence)

    def reset(self) -> None:
        self._entities.clear()
