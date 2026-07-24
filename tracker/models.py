from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScoreSample:
    elapsed_seconds: float
    score: int


@dataclass(frozen=True)
class GameEvent:
    elapsed_seconds: float
    event: str
    score: int
    level: int
    board_position: int
    screen_type: int
    screen_name: str
    lives: int
    details: str

    @property
    def board_label(self) -> str:
        return (
            f"{self.level}-{self.board_position} "
            f"({self.screen_name})"
        )

    @property
    def board_key(self) -> tuple[int, int]:
        return (
            self.level,
            self.board_position,
        )


@dataclass
class Session:
    folder: Path
    score_log: Path
    events_log: Path
    score_samples: list[ScoreSample]
    events: list[GameEvent]


@dataclass(frozen=True)
class BoardPerformance:
    level: int
    board_position: int
    screen_name: str
    start_score: int
    end_score: int
    points_gained: int
    deaths: int
    cleared: bool

    @property
    def board_label(self) -> str:
        return (
            f"{self.level}-{self.board_position} "
            f"({self.screen_name})"
        )


@dataclass(frozen=True)
class SessionSummary:
    final_score: int
    duration_seconds: float
    lives_lost: int
    boards_cleared: int
    game_over: bool
    first_death_score: int | None
    starting_board: str | None
    ending_board: str | None
    furthest_board: str | None
    board_performances: list[BoardPerformance]