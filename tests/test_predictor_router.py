"""
Created at: 2026-07-08 23:35 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:35 EDT
Last Modified by: Codex

Tests for Maia/Catie predictor provider adapters.
"""

import os
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("ALLOW_CONFIG_WARNINGS", "1")
os.environ["DEBUG"] = "false"
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

predictor_path = Path(__file__).parent.parent / "backend" / "routers" / "predictor.py"
spec = importlib.util.spec_from_file_location("predictor_router_under_test", predictor_path)
predictor_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = predictor_module
spec.loader.exec_module(predictor_module)

PredictorRequest = predictor_module.PredictorRequest
_predict_catie = predictor_module._predict_catie
_predict_maia = predictor_module._predict_maia


def test_predict_maia_parses_subprocess_json(tmp_path: Path) -> None:
    python = tmp_path / "python"
    script = tmp_path / "maia.py"
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    script.write_text("# noop\n", encoding="utf-8")

    completed = Mock()
    completed.returncode = 0
    completed.stdout = """
    {
      "model_type": "rapid",
      "device": "cpu",
      "win_prob": 0.42,
      "top_moves": [
        {"move": "g1f3", "prob": 0.32},
        {"move": "d2d4", "prob": 0.21}
      ]
    }
    """
    completed.stderr = ""

    with patch.object(predictor_module.settings, "MAIA_PYTHON", str(python)), patch.object(
        predictor_module.settings, "MAIA_SCRIPT_PATH", str(script)
    ), patch.object(predictor_module.settings, "MAIA_TIMEOUT", 2), patch.object(
        predictor_module.subprocess, "run", return_value=completed
    ):
        response = _predict_maia(
            PredictorRequest(
                provider="maia",
                fen="start-fen",
                top_k=2,
                elo=1500,
            )
        )

    assert response.provider == "maia"
    assert response.model == "maia2-rapid"
    assert response.moves[0].uci == "g1f3"
    assert response.moves[0].probability == 0.32
    assert response.meta["win_prob"] == 0.42


def test_predict_catie_converts_policy_top_k() -> None:
    create_response = Mock()
    create_response.status_code = 202
    create_response.json.return_value = {"task_id": "task-1"}
    create_response.raise_for_status.return_value = None

    poll_response = Mock()
    poll_response.json.return_value = {
        "status": "succeeded",
        "result": {
            "model_id": "carlsen.best",
            "runtime_backend": "gpu",
            "policy": {
                "effective_elo": 1500,
                "top_k": [
                    {"rank": 1, "uci": "e2e4", "san": "e4", "probability": 0.6},
                    {"rank": 2, "uci": "d2d4", "san": "d4", "probability": 0.2},
                ],
            },
        },
    }
    poll_response.raise_for_status.return_value = None

    with patch.object(predictor_module.requests, "post", return_value=create_response), patch.object(
        predictor_module.requests, "get", return_value=poll_response
    ):
        response = _predict_catie(
            PredictorRequest(
                provider="catie",
                fen="start-fen",
                top_k=2,
                elo=1500,
            )
        )

    assert response.provider == "catie"
    assert response.model == "carlsen.best"
    assert response.moves[0].san == "e4"
    assert response.moves[0].probability == 0.6
    assert response.meta["task_id"] == "task-1"
