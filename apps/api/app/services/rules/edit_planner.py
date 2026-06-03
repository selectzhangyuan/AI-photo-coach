import logging
import time
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class EditPlanner:
    def plan(self, features: dict[str, Any], suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        t0 = time.monotonic()
        image = features["image"]
        subject = features["subject"]
        stats = features["stats"]

        actions: list[dict[str, Any]] = []

        crop = self._plan_crop(image=image, subject=subject)
        if crop is not None:
            actions.append(crop)

        exposure_action = self._plan_exposure(stats["mean_brightness"])
        if exposure_action is not None:
            actions.append(exposure_action)

        if suggestions:
            actions.append(
                {
                    "id": "e3",
                    "action_type": "white_balance",
                    "source": "rule",
                    "params": {"mode": "gray_world", "strength": 0.18},
                    "reason": "为后续调色预留一个稳定、轻量的自动白平衡选项。",
                    "previewable": True,
                    "apply_mode": "non_destructive",
                }
            )

        logger.debug(
            "Edit plan generated",
            extra={
                "actions_count": len(actions),
                "duration_ms": round((time.monotonic() - t0) * 1000),
            },
        )

        return actions

    @staticmethod
    def _plan_crop(image: dict[str, Any], subject: dict[str, Any]) -> dict[str, Any] | None:
        width = image["width"]
        height = image["height"]
        subject_center_x = subject["x"] + subject["w"] / 2
        ratio = subject_center_x / max(width, 1)

        if 0.42 <= ratio <= 0.58:
            return None

        crop_width = round(width * 0.86)
        crop_height = round(height * 0.86)
        target_center_x = crop_width * (2 / 3 if ratio < 0.5 else 1 / 3)
        crop_x = round(max(0, min(width - crop_width, subject_center_x - target_center_x)))
        crop_y = round((height - crop_height) / 2)

        return {
            "id": "e1",
            "action_type": "crop",
            "source": "rule",
            "params": {
                "x": crop_x,
                "y": crop_y,
                "w": crop_width,
                "h": crop_height,
                "ratio": "free",
            },
            "reason": "根据主体重心偏移自动收紧边缘空间，让主体更靠近三分线。",
            "previewable": True,
            "apply_mode": "destructive",
        }

    @staticmethod
    def _plan_exposure(mean_brightness: float) -> dict[str, Any] | None:
        if mean_brightness < 96:
            return {
                "id": "e2",
                "action_type": "exposure",
                "source": "rule",
                "params": {"alpha": 1.08, "beta": 18},
                "reason": "整体亮度偏低，自动提升曝光与中低频亮度。",
                "previewable": True,
                "apply_mode": "non_destructive",
            }
        if mean_brightness > 182:
            return {
                "id": "e2",
                "action_type": "exposure",
                "source": "rule",
                "params": {"alpha": 0.94, "beta": -14},
                "reason": "高光较强，自动回收亮度峰值并压低整体曝光。",
                "previewable": True,
                "apply_mode": "non_destructive",
            }
        return None


@lru_cache(maxsize=1)
def get_edit_planner() -> EditPlanner:
    return EditPlanner()

