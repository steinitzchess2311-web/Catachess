from __future__ import annotations

from dataclasses import dataclass

from modules.opening_trainer.service import (
    STANDARD_START_FEN,
    build_eligibility_summary,
    build_unit_catalog,
)


@dataclass
class FakeChapter:
    id: str
    title: str
    starting_fen: str | None = None


@dataclass
class FakeVariation:
    id: str
    chapter_id: str
    parent_id: str | None
    move_number: int
    color: str
    san: str
    fen: str
    rank: int = 0


def _simple_standard_tree(chapter_id: str) -> list[FakeVariation]:
    return [
        FakeVariation(
            id=f"{chapter_id}-w1",
            chapter_id=chapter_id,
            parent_id=None,
            move_number=1,
            color="white",
            san="e4",
            fen="fen_after_e4",
            rank=0,
        ),
        FakeVariation(
            id=f"{chapter_id}-b1",
            chapter_id=chapter_id,
            parent_id=f"{chapter_id}-w1",
            move_number=1,
            color="black",
            san="e5",
            fen="fen_after_e5",
            rank=0,
        ),
        FakeVariation(
            id=f"{chapter_id}-b2",
            chapter_id=chapter_id,
            parent_id=f"{chapter_id}-w1",
            move_number=1,
            color="black",
            san="c5",
            fen="fen_after_c5",
            rank=1,
        ),
        FakeVariation(
            id=f"{chapter_id}-w2",
            chapter_id=chapter_id,
            parent_id=f"{chapter_id}-b1",
            move_number=2,
            color="white",
            san="Nf3",
            fen="fen_after_nf3_vs_e5",
            rank=0,
        ),
        FakeVariation(
            id=f"{chapter_id}-w3",
            chapter_id=chapter_id,
            parent_id=f"{chapter_id}-b2",
            move_number=2,
            color="white",
            san="Nc3",
            fen="fen_after_nc3_vs_c5",
            rank=0,
        ),
    ]


def test_eligibility_requires_standard_start_and_5_ply() -> None:
    chapters = [
        FakeChapter(id="c1", title="Custom", starting_fen="custom fen"),
        FakeChapter(id="c2", title="Short", starting_fen=STANDARD_START_FEN),
    ]
    variations_by_chapter = {
        "c1": _simple_standard_tree("c1"),
        "c2": [
            FakeVariation(
                id="c2-w1",
                chapter_id="c2",
                parent_id=None,
                move_number=1,
                color="white",
                san="d4",
                fen="fen_after_d4",
            ),
        ],
    }

    summary = build_eligibility_summary(chapters, variations_by_chapter)
    assert summary["eligible"] is False
    assert "No standard-start variation line reaches 5+ plies" in summary["reasons"]


def test_chapter_mode_splits_on_opponent_multiple_responses() -> None:
    chapter = FakeChapter(id="c1", title="Italian/French")
    variations_by_chapter = {"c1": _simple_standard_tree("c1")}

    catalog = build_unit_catalog(
        study_id="s1",
        mode="chapter",
        trainee_color="white",
        chapters=[chapter],
        variations_by_chapter=variations_by_chapter,
    )
    assert catalog["eligibility"]["eligible"] is False

    # Extend one line so eligibility passes (>=5 ply)
    variations_by_chapter["c1"].extend(
        [
            FakeVariation(
                id="c1-b3",
                chapter_id="c1",
                parent_id="c1-w2",
                move_number=2,
                color="black",
                san="Nc6",
                fen="fen_after_nc6",
            ),
            FakeVariation(
                id="c1-w4",
                chapter_id="c1",
                parent_id="c1-b3",
                move_number=3,
                color="white",
                san="Bb5",
                fen="fen_after_bb5",
            ),
            FakeVariation(
                id="c1-b4",
                chapter_id="c1",
                parent_id="c1-w4",
                move_number=3,
                color="black",
                san="a6",
                fen="fen_after_a6",
            ),
        ]
    )

    catalog = build_unit_catalog(
        study_id="s1",
        mode="chapter",
        trainee_color="white",
        chapters=[chapter],
        variations_by_chapter=variations_by_chapter,
    )
    assert catalog["eligibility"]["eligible"] is True
    assert catalog["total_units"] == 2
    labels = sorted(leaf["path"][-1] for leaf in catalog["leaf_units"])
    assert labels == ["1...c5", "1...e5"]


def test_merged_mode_deduplicates_identical_lines() -> None:
    chapters = [
        FakeChapter(id="c1", title="A"),
        FakeChapter(id="c2", title="B"),
    ]
    variations_by_chapter = {
        "c1": _simple_standard_tree("c1"),
        "c2": _simple_standard_tree("c2"),
    }

    # Make c1 eligible by extending one branch to 5 ply.
    variations_by_chapter["c1"].extend(
        [
            FakeVariation(
                id="c1-b3",
                chapter_id="c1",
                parent_id="c1-w2",
                move_number=2,
                color="black",
                san="Nc6",
                fen="fen_after_nc6",
            ),
            FakeVariation(
                id="c1-w4",
                chapter_id="c1",
                parent_id="c1-b3",
                move_number=3,
                color="white",
                san="Bb5",
                fen="fen_after_bb5",
            ),
            FakeVariation(
                id="c1-b4",
                chapter_id="c1",
                parent_id="c1-w4",
                move_number=3,
                color="black",
                san="a6",
                fen="fen_after_a6",
            ),
        ]
    )
    variations_by_chapter["c2"].extend(
        [
            FakeVariation(
                id="c2-b3",
                chapter_id="c2",
                parent_id="c2-w2",
                move_number=2,
                color="black",
                san="Nc6",
                fen="fen_after_nc6",
            ),
            FakeVariation(
                id="c2-w4",
                chapter_id="c2",
                parent_id="c2-b3",
                move_number=3,
                color="white",
                san="Bb5",
                fen="fen_after_bb5",
            ),
            FakeVariation(
                id="c2-b4",
                chapter_id="c2",
                parent_id="c2-w4",
                move_number=3,
                color="black",
                san="a6",
                fen="fen_after_a6",
            ),
        ]
    )

    catalog = build_unit_catalog(
        study_id="s1",
        mode="merged",
        trainee_color="white",
        chapters=chapters,
        variations_by_chapter=variations_by_chapter,
    )
    assert catalog["eligibility"]["eligible"] is True
    assert catalog["total_units"] == 2
    merged_root = catalog["roots"][0]
    assert merged_root["kind"] == "merged"
    assert merged_root["line_count"] == 2


def test_split_depth_limit_does_not_split_after_ply_8() -> None:
    chapter = FakeChapter(id="deep", title="Deep Split")
    variations = [
        FakeVariation("w1", "deep", None, 1, "white", "e4", "f1"),
        FakeVariation("b1", "deep", "w1", 1, "black", "e5", "f2"),
        FakeVariation("w2", "deep", "b1", 2, "white", "Nf3", "f3"),
        FakeVariation("b2", "deep", "w2", 2, "black", "Nc6", "f4"),
        FakeVariation("w3", "deep", "b2", 3, "white", "Bb5", "f5"),
        FakeVariation("b3", "deep", "w3", 3, "black", "a6", "f6"),
        FakeVariation("w4", "deep", "b3", 4, "white", "Ba4", "f7"),
        FakeVariation("b4", "deep", "w4", 4, "black", "Nf6", "f8"),
        FakeVariation("w5", "deep", "b4", 5, "white", "O-O", "f9"),
        FakeVariation("b5a", "deep", "w5", 5, "black", "Be7", "f10a", rank=0),
        FakeVariation("b5b", "deep", "w5", 5, "black", "b5", "f10b", rank=1),
    ]

    catalog = build_unit_catalog(
        study_id="s1",
        mode="chapter",
        trainee_color="white",
        chapters=[chapter],
        variations_by_chapter={"deep": variations},
    )
    assert catalog["eligibility"]["eligible"] is True
    assert catalog["total_units"] == 1

