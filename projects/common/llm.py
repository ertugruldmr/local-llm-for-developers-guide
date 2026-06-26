import os
from typing import TYPE_CHECKING, TypeVar

from openai import OpenAI

if TYPE_CHECKING:
    from pydantic import BaseModel


def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", "http://localhost:1234/v1"),
        api_key=os.environ.get("LLM_API_KEY", "lmstudio"),
    )


LLM_MODEL = os.environ.get("LLM_MODEL", "local-model")


T = TypeVar("T", bound="BaseModel")


class QuarantineError(Exception):
    """Raised when a model response fails schema validation twice in a row.

    The caller is expected to set the offending row aside (quarantine) rather
    than crash the batch.
    """

    def __init__(self, raw: str, error: Exception) -> None:
        self.raw = raw
        self.error = error
        super().__init__(f"validation failed after retry: {error}")


def structured_call(
    messages: list[dict[str, str]],
    schema: type[T],
    *,
    model: str = LLM_MODEL,
    temperature: float = 0.0,
) -> T:
    """Call the model and validate the JSON response against `schema`.

    On validation failure: retry once with the validator error appended to the
    prompt, then raise `QuarantineError`. This is the documented
    structured-output / retry-once-then-quarantine pattern.
    """
    client = get_client()
    convo: list[dict[str, str]] = list(messages)
    last_error: Exception | None = None
    last_raw: str = ""

    for _ in range(2):
        resp = client.chat.completions.create(
            model=model,
            messages=convo,  # type: ignore[arg-type]
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        last_raw = resp.choices[0].message.content or ""
        try:
            return schema.model_validate_json(last_raw)
        except Exception as error:  # pydantic ValidationError or JSON decode error
            last_error = error
            convo = [
                *messages,
                {"role": "assistant", "content": last_raw},
                {
                    "role": "user",
                    "content": (
                        "Your previous response failed schema validation with this "
                        f"error:\n{error}\nReturn corrected JSON only."
                    ),
                },
            ]

    raise QuarantineError(last_raw, last_error)  # type: ignore[arg-type]
