import os
import subprocess
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


class PreviousDatasetHelperTests(unittest.TestCase):
    def test_run_previous_dataset_workflow_forwards_paths_and_flags(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        helper = repo_root / "scripts" / "run_previous_dataset_workflow.sh"

        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            workspace = root / "workspace"
            log_path = root / "workflow.log"
            stage_args_path = root / "stage-args.txt"
            python_args_path = root / "python-args.txt"

            stage_script = root / "stage_previous_dataset.sh"
            stage_script.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "%s\\n" "$@" > "$STAGE_ARGS_PATH"',
                        'mkdir -p "$1/gcmsCSVs" "$1/extractedPeaks" "$1/folds" "$1/kegg"',
                        ': > "$1/kegg/keggCompoundsWithFiehlibSpectrum.mat"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            python_bin = root / "python-bin"
            python_bin.write_text(
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        'printf "%s\\n" "$@" > "$PYTHON_ARGS_PATH"',
                        "echo workflow-called",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            stage_script.chmod(0o755)
            python_bin.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "STAGE_SCRIPT": str(stage_script),
                    "PYTHON_BIN": str(python_bin),
                    "STAGE_ARGS_PATH": str(stage_args_path),
                    "PYTHON_ARGS_PATH": str(python_args_path),
                }
            )

            subprocess.run(
                [
                    "bash",
                    str(helper),
                    "--workspace",
                    str(workspace),
                    "--log",
                    str(log_path),
                    "--kfold-learn",
                    "2",
                    "--max-components",
                    "5",
                    "--nrandomized",
                    "7",
                    "--shuffle-test",
                    "--no-regenerate-peaks",
                ],
                check=True,
                cwd=repo_root,
                env=env,
                capture_output=True,
                text=True,
            )

            self.assertEqual(stage_args_path.read_text(encoding="utf-8").splitlines(), [str(workspace)])

            expected_python_args = [
                "-m",
                "metabolite_learner.cli",
                "run-workflow",
                "--gcms-csv-dir",
                str(workspace / "gcmsCSVs"),
                "--extracted-peaks-dir",
                str(workspace / "extractedPeaks"),
                "--folds-dir",
                str(workspace / "folds"),
                "--kegg-mat-path",
                str(workspace / "kegg" / "keggCompoundsWithFiehlibSpectrum.mat"),
                "--kfold-learn",
                "2",
                "--max-components",
                "5",
                "--nrandomized",
                "7",
                "--shuffle-test",
            ]
            self.assertEqual(python_args_path.read_text(encoding="utf-8").splitlines(), expected_python_args)
            self.assertEqual(log_path.read_text(encoding="utf-8").strip(), "workflow-called")


if __name__ == "__main__":
    unittest.main()
