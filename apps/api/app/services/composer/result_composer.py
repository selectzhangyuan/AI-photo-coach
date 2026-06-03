import logging
import time
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class ResultComposer:
    version = "1.1"

    def compose(
        self,
        feature_id: str,
        features: dict[str, Any],
        llm_result: dict[str, Any],
        edit_actions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        result = {
            "version": self.version,
            "summary": llm_result["summary"],
            "suggestions": llm_result["suggestions"],
            "scores": llm_result.get("scores"),
            "features_ref": {"feature_id": feature_id},
            "annotations": self._build_annotations(features),
            "edit_actions": edit_actions,
        }

        logger.debug(
            "Result composed",
            extra={
                "suggestion_count": len(llm_result.get("suggestions", [])),
                "annotation_count": len(result["annotations"]),
                "edit_action_count": len(edit_actions),
                "duration_ms": round((time.monotonic() - t0) * 1000),
            },
        )

        return result

    @staticmethod
    def _build_annotations(features: dict[str, Any]) -> list[dict[str, Any]]:
        annotations: list[dict[str, Any]] = []
        subject = features.get("subject")
        if subject:
            annotations.append(
                {
                    "id": "a1",
                    "source": "cv",
                    "category": "composition",
                    "geometry_type": "bbox",
                    "coords": subject,
                    "label": "subject",
                    "message": "主体检测区域，可用于构图分析与自动裁剪。",
                    "confidence": 0.86,
                    "related_suggestion_ids": ["s1"],
                }
            )

        highlight = features.get("regions", {}).get("highlight")
        if highlight:
            annotations.append(
                {
                    "id": "a2",
                    "source": "cv",
                    "category": "exposure",
                    "geometry_type": "bbox",
                    "coords": highlight,
                    "label": "highlight",
                    "message": "高光区域较亮，后续可联动曝光调整。",
                    "confidence": 0.73,
                    "related_suggestion_ids": ["s2"],
                }
            )

        shadow = features.get("regions", {}).get("shadow")
        if shadow:
            annotations.append(
                {
                    "id": "a3",
                    "source": "cv",
                    "category": "exposure",
                    "geometry_type": "bbox",
                    "coords": shadow,
                    "label": "shadow",
                    "message": "暗部区域较重，后续可联动阴影或曝光调整。",
                    "confidence": 0.72,
                    "related_suggestion_ids": ["s2"],
                }
            )

        horizon = features.get("guidelines", {}).get("horizon")
        if horizon:
            annotations.append(
                {
                    "id": "a4",
                    "source": "cv",
                    "category": "guideline",
                    "geometry_type": "line",
                    "coords": horizon,
                    "label": "horizon",
                    "message": "参考地平线，用于后续构图和校正能力。",
                    "confidence": 0.64,
                    "related_suggestion_ids": [],
                }
            )

        return annotations


@lru_cache(maxsize=1)
def get_result_composer() -> ResultComposer:
    return ResultComposer()

