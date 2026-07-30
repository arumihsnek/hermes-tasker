import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from runtime_echo import (
    RuntimeEchoInvocation,
    RuntimeEchoSpec,
    RuntimeEchoValidationError,
)


class RuntimeEchoSpecTests(unittest.TestCase):
    def valid(self, **overrides):
        value = {
            "capability": "runtime.echo",
            "payload": "hello runtime",
            "command_id": "runtime-echo-command-v1",
            "result_token": "runtime-echo-token-v1",
        }
        value.update(overrides)
        return value

    def test_accepts_valid_spec(self):
        spec = RuntimeEchoSpec.from_mapping(self.valid())
        self.assertEqual(spec.capability, "runtime.echo")
        self.assertEqual(spec.payload, "hello runtime")

    def test_rejects_unknown_capability(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "unsupported capability"):
            RuntimeEchoSpec.from_mapping(self.valid(capability="runtime.other"))

    def test_rejects_missing_payload(self):
        value = self.valid()
        del value["payload"]
        with self.assertRaisesRegex(RuntimeEchoValidationError, "missing required field: payload"):
            RuntimeEchoSpec.from_mapping(value)

    def test_rejects_wrong_payload_type(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "payload must be a string"):
            RuntimeEchoSpec.from_mapping(self.valid(payload=42))

    def test_rejects_empty_command_id(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "command_id must not be empty"):
            RuntimeEchoSpec.from_mapping(self.valid(command_id=""))

    def test_rejects_empty_result_token(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "result_token must not be empty"):
            RuntimeEchoSpec.from_mapping(self.valid(result_token=""))

    def test_rejects_unknown_field(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "unknown field: extra"):
            RuntimeEchoSpec.from_mapping(self.valid(extra="no"))

    def test_serialization_is_deterministic(self):
        spec = RuntimeEchoSpec.from_mapping(self.valid())
        self.assertEqual(spec.to_json(), spec.to_json())
        self.assertEqual(
            spec.to_json(),
            '{"capability":"runtime.echo","command_id":"runtime-echo-command-v1","payload":"hello runtime","result_token":"runtime-echo-token-v1"}',
        )


class RuntimeEchoInvocationTests(unittest.TestCase):
    def spec(self, **overrides):
        value = {
            "capability": "runtime.echo",
            "payload": "hello runtime",
            "command_id": "runtime-echo-command-v1",
            "result_token": "runtime-echo-token-v1",
        }
        value.update(overrides)
        return RuntimeEchoSpec.from_mapping(value)

    def test_converts_spec_to_semantic_ir(self):
        invocation = RuntimeEchoInvocation.from_spec(self.spec())
        self.assertEqual(invocation.capability_id, "runtime.echo")
        self.assertEqual(invocation.invocation_id, "runtime-echo-command-v1")
        self.assertEqual(invocation.payload, "hello runtime")

    def test_is_deterministic_and_has_value_equality(self):
        self.assertEqual(
            RuntimeEchoInvocation.from_spec(self.spec()),
            RuntimeEchoInvocation.from_spec(self.spec()),
        )
        self.assertEqual(
            RuntimeEchoInvocation.from_spec(self.spec()).to_json(),
            RuntimeEchoInvocation.from_spec(self.spec()).to_json(),
        )

    def test_has_no_xml_or_transport_representation(self):
        invocation = RuntimeEchoInvocation.from_spec(self.spec())
        self.assertEqual(
            set(invocation.to_mapping()),
            {"capability_id", "invocation_id", "payload", "result_token"},
        )
        self.assertNotIn("<", invocation.to_json())
        self.assertNotIn("transport", invocation.to_json())

    def test_rejects_impossible_capability(self):
        with self.assertRaisesRegex(RuntimeEchoValidationError, "unsupported capability"):
            RuntimeEchoInvocation(
                capability_id="runtime.other",
                invocation_id="id",
                result_token="token",
                payload="payload",
            )

    def test_adapts_only_valid_ir_to_legacy_renderer_request(self):
        invocation = RuntimeEchoInvocation.from_spec(self.spec())
        request = invocation.to_legacy_tasker_request()
        self.assertEqual(request["artifact_spec"]["artifact_type"], "task")
        self.assertEqual(request["artifact_spec"]["actions"][0]["code"], 126)
        self.assertIn("runtime-echo-command-v1", request["artifact_spec"]["actions"][0]["arguments"][0]["value"])

    def test_adapter_output_is_deterministic(self):
        invocation = RuntimeEchoInvocation.from_spec(self.spec())
        self.assertEqual(invocation.to_legacy_tasker_request(), invocation.to_legacy_tasker_request())


if __name__ == "__main__":
    unittest.main()
