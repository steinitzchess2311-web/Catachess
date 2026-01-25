from pydantic import BaseModel
from typing import List, Union

class EngineLine(BaseModel):
    multipv: int
    score: Union[int, str]   # cp or "mate"
    pv: List[str]

class EngineResult(BaseModel):
    lines: List[EngineLine]
    source: str | None = None
