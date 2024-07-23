"""Custom FastAPI response classes."""

from typing import Any

import yaml
from fastapi import Response


class YAMLResponse(Response):
    media_type = "application/x-yaml"

    def render(self, content: Any) -> bytes:
        return yaml.dump(content, encoding="utf-8")
