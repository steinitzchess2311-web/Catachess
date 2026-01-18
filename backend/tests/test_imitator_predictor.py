from types import SimpleNamespace

from core.chess_engine.schemas import EngineLine, EngineResult
from core.tagger.pipeline.predictor import predictor
from core.tagger.pipeline.predictor.profile_loader import list_profiles


class DummyEngine:
    def analyze(self, fen: str, depth: int, multipv: int) -> EngineResult:
        lines = [
            EngineLine(multipv=1, score=20, pv=["e2e4"]),
            EngineLine(multipv=2, score=10, pv=["d2d4"]),
        ]
        return EngineResult(lines=lines)


def test_predict_moves_ranks_by_similarity(tmp_path, monkeypatch):
    csv_path = tmp_path / "PlayerA.csv"
    csv_path.write_text("tag,count,ratio\ncontrol_over_dynamics,1,0.6\nneutral_maneuver,1,0.4\n")

    monkeypatch.setattr(predictor, "PROFILES_DIR", tmp_path)
    monkeypatch.setattr(predictor, "get_engine", lambda: DummyEngine())

    def fake_tag_position(*_, **kwargs):
        if kwargs.get("played_move_uci") == "e2e4":
            return SimpleNamespace(control_over_dynamics=True, neutral_maneuver=False)
        return SimpleNamespace(control_over_dynamics=False, neutral_maneuver=True)

    monkeypatch.setattr(predictor, "tag_position", fake_tag_position)

    result = predictor.predict_moves("startpos", "PlayerA", top_n=2)
    assert result["moves"][0]["move"] == "e2e4"
    assert result["moves"][0]["probability"] > result["moves"][1]["probability"]


def test_list_profiles(tmp_path):
    (tmp_path / "DingLiren.csv").write_text("tag,count,ratio\ncontrol_over_dynamics,1,1.0\n")
    (tmp_path / "Alpha.csv").write_text("tag,count,ratio\nneutral_maneuver,1,1.0\n")
    assert list_profiles(tmp_path) == ["Alpha", "DingLiren"]
