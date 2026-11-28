import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class LocalLLMError(RuntimeError):
    pass


def extract_json(value):
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise LocalLLMError("El modelo local no devolvió un JSON válido.")
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LocalLLMError("El modelo local no devolvió un JSON válido.") from exc


def request_local_analysis(prompt):
    if not settings.LOCAL_LLM_ENABLED:
        raise LocalLLMError(
            "La IA local está desactivada. Activa LOCAL_LLM_ENABLED y el perfil ai."
        )

    body = json.dumps(
        {
            "model": settings.LOCAL_LLM_MODEL,
            "stream": False,
            "format": "json",
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": 0.2},
        }
    ).encode("utf-8")
    request = Request(
        f"{settings.LOCAL_LLM_BASE_URL}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.LOCAL_LLM_TIMEOUT_SECONDS) as response:
            response_body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise LocalLLMError(
            f"El modelo local respondió con HTTP {exc.code}: {detail}"
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LocalLLMError("No se pudo obtener una respuesta de la IA local.") from exc

    message = response_body.get("message", {})
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LocalLLMError("La IA local devolvió una respuesta vacía.")
    return extract_json(content)

