from functools import lru_cache
from typing import Any


class LLMAnalyzer:
    version = "1.0"

    def analyze(self, features: dict[str, Any]) -> dict[str, Any]:
        image = features["image"]
        subject = features["subject"]
        stats = features["stats"]

        width = image["width"]
        subject_center_x = subject["x"] + subject["w"] / 2
        balance = subject_center_x / max(width, 1)

        summary_parts = ["主体可读性还可以"]
        if balance < 0.42:
            summary_parts.append("但画面重心偏左")
        elif balance > 0.58:
            summary_parts.append("但画面重心偏右")
        else:
            summary_parts.append("画面重心基本稳定")

        if stats["mean_brightness"] < 96:
            summary_parts.append("整体曝光偏暗")
        elif stats["mean_brightness"] > 182:
            summary_parts.append("高光略抢眼")
        else:
            summary_parts.append("曝光处于可优化区间")

        suggestions: list[dict[str, Any]] = []

        if balance < 0.42:
            suggestions.append(
                {
                    "id": "s1",
                    "type": "composition",
                    "priority": "high",
                    "problem": "主体重心偏左，右侧留白较多。",
                    "action": "裁掉右侧约 10% 到 18% 的空间，让主体更靠近右侧三分线。",
                    "text": "主体重心偏左，建议裁掉右侧约 10% 到 18% 的空间，让主体更靠近右侧三分线。",
                }
            )
        elif balance > 0.58:
            suggestions.append(
                {
                    "id": "s1",
                    "type": "composition",
                    "priority": "high",
                    "problem": "主体重心偏右，左侧留白承担了过多视觉重量。",
                    "action": "裁掉左侧约 10% 的空白，并保留主体前方空间。",
                    "text": "主体重心偏右，建议裁掉左侧约 10% 的空白，并保留主体前方空间。",
                }
            )
        else:
            suggestions.append(
                {
                    "id": "s1",
                    "type": "composition",
                    "priority": "medium",
                    "problem": "主体位置基本合理，但视觉焦点还不够集中。",
                    "action": "可轻微收紧画面边缘，减少无效背景，让主体占比再提高一点。",
                    "text": "主体位置基本合理，可轻微收紧画面边缘，减少无效背景，让主体占比再提高一点。",
                }
            )

        if stats["mean_brightness"] < 96:
            suggestions.append(
                {
                    "id": "s2",
                    "type": "exposure",
                    "priority": "high",
                    "problem": "整体亮度偏低，暗部信息容易丢失。",
                    "action": "先提高曝光约 0.3 到 0.5 档，再少量提升阴影细节。",
                    "text": "整体亮度偏低，建议先提高曝光约 0.3 到 0.5 档，再少量提升阴影细节。",
                }
            )
        elif stats["mean_brightness"] > 182:
            suggestions.append(
                {
                    "id": "s2",
                    "type": "exposure",
                    "priority": "high",
                    "problem": "高光较亮，容易抢走主体注意力。",
                    "action": "略降曝光并压住高光，避免明亮区域先于主体吸引视线。",
                    "text": "高光较亮，建议略降曝光并压住高光，避免明亮区域先于主体吸引视线。",
                }
            )
        else:
            suggestions.append(
                {
                    "id": "s2",
                    "type": "exposure",
                    "priority": "medium",
                    "problem": "曝光没有明显错误，但层次感还可以加强。",
                    "action": "保持整体曝光不变，微调局部对比提升主体层次。",
                    "text": "曝光没有明显错误，建议保持整体曝光不变，微调局部对比提升主体层次。",
                }
            )

        suggestions.append(
            {
                "id": "s3",
                "type": "story",
                "priority": "low",
                "problem": "当前叙事焦点主要依赖主体位置，背景参与度不强。",
                "action": "在保留主体周围留白的前提下，适当清理分散注意力的边缘区域。",
                "text": "当前叙事焦点主要依赖主体位置，建议清理分散注意力的边缘区域。",
            }
        )

        return {
            "version": self.version,
            "summary": "，".join(summary_parts) + "。",
            "suggestions": suggestions,
            "scores": self._build_scores(stats, balance),
        }

    @staticmethod
    def _build_scores(stats: dict[str, Any], balance: float) -> dict[str, int]:
        composition = max(55, min(90, round(88 - abs(0.5 - balance) * 85)))
        exposure = max(50, min(90, round(90 - abs(135 - stats["mean_brightness"]) * 0.32)))
        color = max(58, min(84, round(68 + min(stats["contrast"], 40) * 0.25)))
        story = max(55, min(82, round((composition + exposure) / 2 - 8)))

        return {
            "composition": composition,
            "exposure": exposure,
            "color": color,
            "story": story,
        }


@lru_cache(maxsize=1)
def get_llm_analyzer() -> LLMAnalyzer:
    return LLMAnalyzer()

