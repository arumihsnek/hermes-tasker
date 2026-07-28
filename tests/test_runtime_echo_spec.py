import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from runtime_echo import RuntimeEchoSpec, RuntimeEchoValidationError


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


if __name__ == "__main__":
    unittest.main()
