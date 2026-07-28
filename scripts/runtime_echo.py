"""Typed Runtime Echo v1 contracts, independent of XML and transport."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


RUNTIME_ECHO_CAPABILITY = "runtime.echo"
RUNTIME_ECHO_TASK_ID = 910001
RUNTIME_ECHO_TASK_NAME = "Hermes Runtime Echo v1"
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


@dataclass(frozen=True)
class RuntimeEchoInvocation:
    """Validated semantic IR for one Runtime Echo invocation."""

    capability_id: str
    invocation_id: str
    result_token: str
    payload: str

    def __post_init__(self) -> None:
        RuntimeEchoSpec.from_mapping({
            "capability": self.capability_id,
            "command_id": self.invocation_id,
            "result_token": self.result_token,
            "payload": self.payload,
        })

    @classmethod
    def from_spec(cls, spec: RuntimeEchoSpec) -> "RuntimeEchoInvocation":
        if not isinstance(spec, RuntimeEchoSpec):
            raise RuntimeEchoValidationError("spec must be a RuntimeEchoSpec")
        return cls(
            capability_id=spec.capability,
            invocation_id=spec.command_id,
            result_token=spec.result_token,
            payload=spec.payload,
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "capability_id": self.capability_id,
            "invocation_id": self.invocation_id,
            "payload": self.payload,
            "result_token": self.result_token,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def expected_result(self) -> dict[str, str]:
        return {
            "capability": self.capability_id,
            "command_id": self.invocation_id,
            "payload": self.payload,
            "result_token": self.result_token,
            "status": "success",
        }

    def to_legacy_tasker_request(self) -> dict[str, Any]:
        """Narrow, deterministic bridge to the established renderer request shape."""
        return_value = json.dumps(
            self.expected_result(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        return {
            "tasker_version": "6.7.6-beta",
            "artifact_spec": {
                "artifact_type": "task",
                "id": RUNTIME_ECHO_TASK_ID,
                "name": RUNTIME_ECHO_TASK_NAME,
                "effects": ["runtime.echo"],
                "requirements": {"tasker": True},
                "actions": [{
                    "code": 126,
                    "arguments": [
                        {"position": 0, "value": return_value},
                        {"position": 1, "value": 1},
                        {"position": 2, "value": 0},
                        {"position": 3, "value": 0},
                        {"position": 4, "value": ""},
                    ],
                }],
            },
        }
