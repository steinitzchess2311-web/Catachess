import csv
from pathlib import Path
from typing import Dict, List

from .models import PlayerProfile


def load_profile_csv(path: str | Path, name: str | None = None) -> PlayerProfile:
    csv_path = Path(path)
    weights: Dict[str, float] = {}

    with csv_path.open("r", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tag = (row.get("tag") or "").strip()
            ratio = (row.get("ratio") or "").strip()
            if not tag or not ratio:
                continue
            try:
                weights[tag] = float(ratio)
            except ValueError:
                continue

    total_weight = sum(weights.values())
    profile_name = name or csv_path.stem
    return PlayerProfile(
        name=profile_name,
        weights=weights,
        total_weight=total_weight,
        source_path=str(csv_path),
    )


def list_profiles(root: str | Path) -> List[str]:
    root_path = Path(root)
    if not root_path.exists():
        return []
    return sorted([p.stem for p in root_path.glob("*.csv")])
