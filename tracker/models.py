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

    @property
    def board_key(self) -> tuple[int, int]:
        return (
            self.level,
            self.board_position,
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


@dataclass(frozen=True)
class FailedSession:
    folder: Path
    reason: str


@dataclass
class Career:
    folder: Path
    sessions: list[Session]
    failed_sessions: list[FailedSession]
    excluded_sessions: list[Path]


@dataclass(frozen=True)
class CareerBoardStats:
    level: int
    board_position: int
    screen_name: str
    attempts: int
    clears: int
    deaths: int
    average_points_gained: float
    best_points_gained: int

    @property
    def board_label(self) -> str:
        return (
            f"{self.level}-{self.board_position} "
            f"({self.screen_name})"
        )

    @property
    def clear_rate(self) -> float:
        if self.attempts == 0:
            return 0.0

        return (
            self.clears
            / self.attempts
            * 100
        )


@dataclass(frozen=True)
class CareerSummary:
    tracked_sessions: int
    skipped_sessions: int
    high_score: int
    average_score: float
    median_score: float
    lifetime_points: int
    total_play_time_seconds: float
    total_boards_cleared: int
    total_lives_lost: int
    completed_games: int
    quit_or_incomplete_games: int
    average_first_death_score: float | None
    board_stats: list[CareerBoardStats]