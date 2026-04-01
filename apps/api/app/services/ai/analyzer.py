from functools import lru_cache
from typing import Any

from app.services.composer.result_composer import get_result_composer
from app.services.cv.feature_extractor import get_feature_extractor
from app.services.llm.analyzer import get_llm_analyzer
from app.services.rules.edit_planner import get_edit_planner


class AnalyzerFacade:
    def analyze(self, image_bytes: bytes, mime_type: str) -> dict[str, Any]:
        features = get_feature_extractor().extract(image_bytes=image_bytes, mime_type=mime_type)
        llm_result = get_llm_analyzer().analyze(features=features)
        edit_actions = get_edit_planner().plan(features=features, suggestions=llm_result["suggestions"])
        return get_result_composer().compose(
            feature_id="inline",
            features=features,
            llm_result=llm_result,
            edit_actions=edit_actions,
        )


@lru_cache(maxsize=1)
def get_analyzer() -> AnalyzerFacade:
    return AnalyzerFacade()

