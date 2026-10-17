import httpx
from fastapi import APIRouter, HTTPException, status

from schemas.translation import TranslationRequest, TranslationResponse

router = APIRouter(prefix="/translate", tags=["translation"])
TRANSLATION_URL = "https://api.mymemory.translated.net/get"


@router.post("", response_model=TranslationResponse)
async def translate_text(payload: TranslationRequest):
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(
                TRANSLATION_URL,
                params={
                    "q": payload.text,
                    "langpair": f"{payload.source_language}|{payload.target_language}",
                },
            )
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Translation service is temporarily unavailable.",
        ) from exc

    translated_text = result.get("responseData", {}).get("translatedText")
    if result.get("responseStatus") != 200 or not translated_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Translation service could not translate this text.",
        )

    return TranslationResponse(
        translated_text=translated_text,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )
