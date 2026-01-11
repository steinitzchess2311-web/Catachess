"""
chess_basic.pgn.common.tags
Event、Site 等 PGN 标签管理

PGN tag management (Event, Site, etc.).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SevenTagRoster:
    """
    PGN 七标签名册（必需标签）
    Seven Tag Roster (required tags)

    These are the seven mandatory tags in PGN format.
    """
    Event: str = "?"
    Site: str = "?"
    Date: str = "????.??.??"
    Round: str = "?"
    White: str = "?"
    Black: str = "?"
    Result: str = "*"

    def to_dict(self) -> dict[str, str]:
        """转换为字典 Convert to dictionary"""
        return {
            "Event": self.Event,
            "Site": self.Site,
            "Date": self.Date,
            "Round": self.Round,
            "White": self.White,
            "Black": self.Black,
            "Result": self.Result,
        }

    @classmethod
    def from_dict(cls, tags: dict[str, str]) -> "SevenTagRoster":
        """从字典创建 Create from dictionary"""
        return cls(
            Event=tags.get("Event", "?"),
            Site=tags.get("Site", "?"),
            Date=tags.get("Date", "????.??.??"),
            Round=tags.get("Round", "?"),
            White=tags.get("White", "?"),
            Black=tags.get("Black", "?"),
            Result=tags.get("Result", "*"),
        )


class PGNTags:
    """
    PGN 标签管理器
    PGN tag manager

    Manages all PGN tags including the seven tag roster and optional tags.
    """

    def __init__(self):
        self._tags: dict[str, str] = {}
        self._init_default_tags()

    def _init_default_tags(self):
        """初始化默认标签 Initialize default tags"""
        roster = SevenTagRoster()
        self._tags = roster.to_dict()

    def set(self, key: str, value: str) -> None:
        """
        设置标签
        Set tag

        Args:
            key: Tag name
            value: Tag value
        """
        self._tags[key] = value

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取标签
        Get tag

        Args:
            key: Tag name
            default: Default value if tag not found

        Returns:
            Tag value or default
        """
        return self._tags.get(key, default)

    def remove(self, key: str) -> None:
        """
        移除标签
        Remove tag

        Args:
            key: Tag name
        """
        if key in self._tags:
            del self._tags[key]

    def get_all(self) -> dict[str, str]:
        """
        获取所有标签
        Get all tags

        Returns:
            Dictionary of all tags
        """
        return self._tags.copy()

    def get_seven_tag_roster(self) -> SevenTagRoster:
        """
        获取七标签名册
        Get seven tag roster

        Returns:
            SevenTagRoster object
        """
        return SevenTagRoster.from_dict(self._tags)

    def set_players(self, white: str, black: str) -> None:
        """
        设置对弈者
        Set players

        Args:
            white: White player name
            black: Black player name
        """
        self.set("White", white)
        self.set("Black", black)

    def set_event(self, event: str, site: str = "?", round_num: str = "?") -> None:
        """
        设置比赛信息
        Set event information

        Args:
            event: Event name
            site: Event location
            round_num: Round number
        """
        self.set("Event", event)
        self.set("Site", site)
        self.set("Round", round_num)

    def set_date(self, date: Optional[datetime] = None) -> None:
        """
        设置日期
        Set date

        Args:
            date: Date object (uses today if None)
        """
        if date is None:
            date = datetime.now()
        self.set("Date", date.strftime("%Y.%m.%d"))

    def set_result(self, result: str) -> None:
        """
        设置结果
        Set result

        Args:
            result: Result string (1-0, 0-1, 1/2-1/2, or *)
        """
        if result not in ["1-0", "0-1", "1/2-1/2", "*"]:
            result = "*"
        self.set("Result", result)

    def set_elo(self, white_elo: Optional[int] = None, black_elo: Optional[int] = None) -> None:
        """
        设置等级分
        Set Elo ratings

        Args:
            white_elo: White player's Elo
            black_elo: Black player's Elo
        """
        if white_elo is not None:
            self.set("WhiteElo", str(white_elo))
        if black_elo is not None:
            self.set("BlackElo", str(black_elo))

    def set_time_control(self, time_control: str) -> None:
        """
        设置时间控制
        Set time control

        Args:
            time_control: Time control string (e.g., "40/9000+30")
        """
        self.set("TimeControl", time_control)
