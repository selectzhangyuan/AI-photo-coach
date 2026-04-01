from functools import lru_cache
from io import BytesIO
from typing import Any

from PIL import Image, ImageStat


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class CVFeatureExtractor:
    version = "1.0"

    def extract(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        width, height = image.size

        gray = image.convert("L")
        stats = ImageStat.Stat(gray)
        mean_brightness = round(float(stats.mean[0]), 2)
        contrast = round(float(stats.stddev[0]), 2)

        subject_w = round(width * 0.52)
        subject_h = round(height * 0.62)
        subject_x = round((width - subject_w) * 0.28)
        subject_y = round((height - subject_h) * 0.22)

        subject_center_x = subject_x + subject_w / 2
        subject_center_y = subject_y + subject_h / 2

        composition_balance = round(subject_center_x / max(width, 1), 3)

        highlight_strength = _clamp((mean_brightness - 175) / 80, 0, 1)
        shadow_strength = _clamp((85 - mean_brightness) / 80, 0, 1)

        highlight_region = None
        if highlight_strength > 0.12:
            highlight_region = {
                "x": round(width * 0.62),
                "y": round(height * 0.14),
                "w": round(width * 0.22),
                "h": round(height * 0.18),
                "coord_space": "image_pixels",
            }

        shadow_region = None
        if shadow_strength > 0.12:
            shadow_region = {
                "x": round(width * 0.12),
                "y": round(height * 0.58),
                "w": round(width * 0.24),
                "h": round(height * 0.22),
                "coord_space": "image_pixels",
            }

        horizon_line = {
            "x1": 0,
            "y1": round(height * 0.52),
            "x2": width,
            "y2": round(height * 0.5),
            "coord_space": "image_pixels",
        }

        return {
            "version": self.version,
            "image": {
                "width": width,
                "height": height,
                "mime_type": mime_type,
            },
            "stats": {
                "mean_brightness": mean_brightness,
                "contrast": contrast,
                "composition_balance": composition_balance,
            },
            "subject": {
                "x": subject_x,
                "y": subject_y,
                "w": subject_w,
                "h": subject_h,
                "coord_space": "image_pixels",
            },
            "regions": {
                "highlight": highlight_region,
                "shadow": shadow_region,
            },
            "guidelines": {
                "horizon": horizon_line,
            },
        }


@lru_cache(maxsize=1)
def get_feature_extractor() -> CVFeatureExtractor:
    return CVFeatureExtractor()

