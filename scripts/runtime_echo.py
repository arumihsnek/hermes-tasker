"""Typed Runtime Echo v1 contracts, independent of XML and transport."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


RUNTIME_ECHO_CAPABILITY = "runtime.echo"
_REQUIRED_FIELDS = ("capability", "payload", "command_id", "result_token")
_MAX_PAYLOAD_LENGTH = 1024
_MAX_IDENTIFIER_LENGTH = 256


class RuntimeEchoValidationError(ValueError):
    """Stable validation failure at the public Typed Spec boundary."""


def _required_string(value: Mapping[str, Any], field: str, limit: int) -> str:
    if field not in value:
        raise RuntimeEchoValidationError(f"missing required field: {field}")
    result = value[field]
    if not isinstance(result, str):
        raise RuntimeEchoValidationError(f"{field} must be a string")
    if not result:
        raise RuntimeEchoValidationError(f"{field} must not be empty")
    if len(result) > limit:
        raise RuntimeEchoValidationError(f"{field} exceeds maximum length")
    return result


@dataclass(frozen=True)
class RuntimeEchoSpec:
    """The minimal validated external request for the Runtime Echo capability."""

    capability: str
    payload: str
    command_id: str
    result_token: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RuntimeEchoSpec":
        if not isinstance(value, Mapping):
            raise RuntimeEchoValidationError("spec must be an object")
        unknown = sorted(set(value) - set(_REQUIRED_FIELDS))
        if unknown:
            raise RuntimeEchoValidationError(f"unknown field: {unknown[0]}")
        capability = _required_string(value, "capability", _MAX_IDENTIFIER_LENGTH)
        if capability != RUNTIME_ECHO_CAPABILITY:
            raise RuntimeEchoValidationError("unsupported capability")
        return cls(
            capability=capability,
            payload=_required_string(value, "payload", _MAX_PAYLOAD_LENGTH),
            command_id=_required_string(value, "command_id", _MAX_IDENTIFIER_LENGTH),
            result_token=_required_string(value, "result_token", _MAX_IDENTIFIER_LENGTH),
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "capability": self.capability,
            "command_id": self.command_id,
            "payload": self.payload,
            "result_token": self.result_token,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
