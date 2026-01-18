"""
Node-level tag predictor.

Provides node_id-aware tagging that integrates with the tagger pipeline.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..models import FinalResult
from ..runner import TaggingPipeline

logger = logging.getLogger(__name__)


@dataclass
class NodeTagResult:
    """Result of tagging a single node."""
    node_id: str
    fen: str
    move_uci: Optional[str]
    tags: List[str] = field(default_factory=list)
    features: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class NodePredictor:
    """
    Predicts tags for individual nodes in a move tree.

    Wraps TaggingPipeline to provide node-aware results.
    """

    def __init__(
        self,
        pipeline: Optional[TaggingPipeline] = None,
        engine: Optional[Any] = None,
        depth: int = 14,
        multipv: int = 6,
    ):
        """
        Initialize node predictor.

        Args:
            pipeline: Existing TaggingPipeline (or creates new one)
            engine: Chess engine for analysis
            depth: Engine analysis depth
            multipv: Number of principal variations
        """
        if pipeline:
            self._pipeline = pipeline
        elif engine:
            self._pipeline = TaggingPipeline(
                engine=engine,
                depth=depth,
                multipv=multipv,
            )
        else:
            self._pipeline = None

    def predict_node_tags(
        self,
        node_id: str,
        fen: str,
        move_uci: Optional[str] = None,
    ) -> NodeTagResult:
        """
        Predict tags for a single node.

        Args:
            node_id: Node ID for result tracking
            fen: FEN position before the move
            move_uci: UCI notation of the move (optional)

        Returns:
            NodeTagResult with tags and features
        """
        if not self._pipeline:
            return NodeTagResult(
                node_id=node_id,
                fen=fen,
                move_uci=move_uci,
                error="No pipeline configured",
            )

        if not move_uci:
            return NodeTagResult(
                node_id=node_id,
                fen=fen,
                move_uci=None,
                tags=[],
                features={},
            )

        try:
            result = self._pipeline.evaluate(fen, move_uci)
            return NodeTagResult(
                node_id=node_id,
                fen=fen,
                move_uci=move_uci,
                tags=list(result.tags) if result.tags else [],
                features=dict(result.features) if result.features else {},
            )
        except Exception as e:
            logger.error(f"Error predicting tags for node {node_id}: {e}")
            return NodeTagResult(
                node_id=node_id,
                fen=fen,
                move_uci=move_uci,
                error=str(e),
            )

    def predict_batch(
        self,
        nodes: List[Dict[str, Any]],
    ) -> List[NodeTagResult]:
        """
        Predict tags for a batch of nodes.

        Args:
            nodes: List of dicts with node_id, fen, and optional uci

        Returns:
            List of NodeTagResult objects
        """
        results = []
        for node in nodes:
            result = self.predict_node_tags(
                node_id=node["node_id"],
                fen=node["fen"],
                move_uci=node.get("uci"),
            )
            results.append(result)

        logger.info(f"Predicted tags for {len(results)} nodes")
        return results


def tag_position(fen: str, move_uci: str, pipeline: TaggingPipeline) -> FinalResult:
    """
    Convenience function to tag a single position.

    Args:
        fen: FEN string
        move_uci: UCI move notation
        pipeline: Configured tagging pipeline

    Returns:
        FinalResult from pipeline
    """
    return pipeline.evaluate(fen, move_uci)
