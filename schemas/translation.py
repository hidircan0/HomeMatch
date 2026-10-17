from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=450)
    source_language: Literal["tr", "en"]
    target_language: Literal["tr", "en"]

    @model_validator(mode="after")
    def languages_must_differ(self):
        if self.source_language == self.target_language:
            raise ValueError("Source and target languages must differ.")
        return self


class TranslationResponse(BaseModel):
    translated_text: str
    source_language: Literal["tr", "en"]
    target_language: Literal["tr", "en"]
