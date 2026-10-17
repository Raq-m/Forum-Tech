import re
import unicodedata
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError


URL_PATTERN = re.compile(
    r"(?:https?://|www\.)[^\s<>\"']+",
    flags=re.IGNORECASE,
)


def normalize_text(value):
    return unicodedata.normalize("NFKC", value).casefold()


def validate_forum_content(value):
    normalized = normalize_text(value)

    for word in getattr(settings, "FORUM_BLOCKED_WORDS", []):
        word = normalize_text(word.strip())

        if word and re.search(
            rf"(?<!\w){re.escape(word)}(?!\w)",
            normalized,
        ):
            raise ValidationError(
                "El contenido contiene una expresion no permitida.",
                code="blocked_word",
            )

    blocked_domains = {
        domain.strip().lower().rstrip(".")
        for domain in getattr(
            settings,
            "FORUM_BLOCKED_DOMAINS",
            [],
        )
        if domain.strip()
    }

    for match in URL_PATTERN.finditer(value):
        url = match.group().rstrip(".,;!?)")
        if url.lower().startswith("www."):
            url = "https://" + url

        try:
            hostname = urlsplit(url).hostname
        except ValueError:
            raise ValidationError(
                "El contenido contiene un enlace no valido.",
                code="invalid_link",
            )

        if not hostname:
            raise ValidationError(
                "El contenido contiene un enlace no valido.",
                code="invalid_link",
            )

        hostname = hostname.lower().rstrip(".")

        if any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in blocked_domains
        ):
            raise ValidationError(
                "El contenido contiene un dominio bloqueado.",
                code="blocked_domain",
            )