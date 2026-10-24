from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from warpproof.cli import main
from warpproof.model import baseline_candidate, decode_candidate, load_candidate, make_candidate


class ExactInputTests(unittest.TestCase):
    def setUp(self):
        self.data = dict(baseline_candidate().source)

    def test_exact_equivalent_coefficients_have_same_parameter_identity(self):
        first = make_candidate({(1, 0): Fraction(1, 1000)})
        second = dict(first.source)
        second["id"] = "different-description"
        second["coefficients"] = [{"x_power": 1, "transverse_power": 0, "coefficient": "2/2000"}]
        self.assertEqual(first.parameter_hash, decode_candidate(second).parameter_hash)
        self.assertNotEqual(first.candidate_hash, decode_candidate(second).candidate_hash)

    def test_frozen_parameters_cannot_be_overridden(self):
        for field in ("speed_c", "energy", "formal_certification", "python_code", "metric"):
            with self.subTest(field=field):
                data = dict(self.data, **{field: 0})
                with self.assertRaises(ValueError):
                    decode_candidate(data)

    def test_exact_coefficient_and_degree_gates(self):
        for coefficient in (0.001, "0.001", "1/0", "NaN", "1e-3", "101/1000"):
            with self.subTest(coefficient=coefficient):
                data = dict(self.data, coefficients=[{"x_power": 1, "transverse_power": 0, "coefficient": coefficient}])
                with self.assertRaises(ValueError):
                    decode_candidate(data)
        for i, j in ((5, 0), (1, 2), (-1, 0), (True, 0)):
            with self.subTest(powers=(i, j)):
                data = dict(self.data, coefficients=[{"x_power": i, "transverse_power": j, "coefficient": "1/1000"}])
                with self.assertRaises(ValueError):
                    decode_candidate(data)

    def test_ambiguous_json_and_duplicate_terms_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"candidate.json"
            path.write_text('{"id":"first","id":"second"}')
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                load_candidate(path)
        term = {"x_power": 1, "transverse_power": 0, "coefficient": "1/1000"}
        with self.assertRaisesRegex(ValueError, "Duplicate polynomial"):
            decode_candidate(dict(self.data, coefficients=[term, term]))

    def test_raw_input_hash_retains_byte_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"candidate.json"
            path.write_text(json.dumps(self.data))
            one = load_candidate(path)
            path.write_text(json.dumps(self.data, indent=2)+"\n")
            two = load_candidate(path)
            self.assertEqual(one.parameter_hash, two.parameter_hash)
            self.assertEqual(one.candidate_hash, two.candidate_hash)
            self.assertNotEqual(one.raw_input_sha256, two.raw_input_sha256)


class FormalGateTests(unittest.TestCase):
    def test_formal_gate_refuses_certification(self):
        output = StringIO()
        with redirect_stdout(output):
            code = main(["verify", "--require-formal"])
        self.assertEqual(code, 2)
        result = json.loads(output.getvalue())
        self.assertIs(result["accepted"], False)
        self.assertIs(result["formal_certification"], False)

    def test_a_candidate_cannot_self_assert_certification(self):
        data = dict(baseline_candidate().source, formal_certification=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fake.json"
            path.write_text(json.dumps(data))
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                code = main(["verify", "--require-formal", "--candidate", str(path)])
        self.assertNotEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
