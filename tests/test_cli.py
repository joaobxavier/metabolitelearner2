import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from metabolite_learner.agilent import EXPECTED_SHAPE, TIME_GRID, convert_agilent_to_csv
from metabolite_learner.cli import build_parser
from metabolite_learner.pls import MetaboLiteLearner


class CliParserTests(unittest.TestCase):
    def test_run_workflow_command_parses(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run-workflow"])
        self.assertEqual(args.command, "run-workflow")

    def test_run_workflow_shuffle_test_flag_parses(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["run-workflow", "--shuffle-test"])
        self.assertTrue(args.shuffle_test)


class PlsRegressionCompatibilityTests(unittest.TestCase):
    def test_learn_builds_beta_with_feature_rows_and_target_columns(self) -> None:
        rng = np.random.default_rng(0)
        x = rng.normal(size=(12, 6))
        y = rng.normal(size=(12, 2))

        learner = MetaboLiteLearner(x, y, kfold=3, max_components=2, nrandomized=2)

        self.assertEqual(learner.beta.shape, (x.shape[1] + 1, y.shape[1]))


class AgilentConversionTests(unittest.TestCase):
    def test_convert_agilent_to_csv_reads_tic_front_from_d_directory(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sample_dir = root / "ExampleSample.D"
            sample_dir.mkdir()

            tic_front = sample_dir / "tic_front.csv"
            tic_front.write_text(
                "\n".join(
                    [
                        "ExampleSample.D",
                        "Start of data points",
                        "6.00,10",
                        "18.00,20",
                        "30.00,30",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            output_dir = root / "out"
            written = convert_agilent_to_csv(root, output_dir)

            self.assertEqual(written, [output_dir / "ExampleSample.csv"])
            converted = pd.read_csv(written[0], header=None).to_numpy(dtype=float)

            self.assertEqual(converted.shape, EXPECTED_SHAPE)
            np.testing.assert_allclose(converted[:, 0], np.interp(TIME_GRID, [6.0, 18.0, 30.0], [10.0, 20.0, 30.0]))
            np.testing.assert_allclose(converted[:, 1:], 0.0)

    def test_convert_agilent_to_csv_reads_matrix_csv_from_d_directory(self) -> None:
        sample_dir = Path(
            "ExampleSample.D"
        )
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sample_path = root / sample_dir
            sample_path.mkdir()
            reference = np.zeros(EXPECTED_SHAPE, dtype=float)
            reference[0, 0] = 1.0
            reference[-1, -1] = 2.0
            pd.DataFrame(reference).to_csv(sample_path / "matrix.csv", header=False, index=False)

            output_dir = root / "out"
            written = convert_agilent_to_csv(root, output_dir, sample_dirs=[sample_path])
            converted = pd.read_csv(written[0], header=None).to_numpy(dtype=float)

        self.assertEqual(converted.shape, EXPECTED_SHAPE)
        np.testing.assert_allclose(converted, reference)


if __name__ == "__main__":
    unittest.main()
