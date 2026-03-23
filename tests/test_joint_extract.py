import unittest

import numpy as np

from metabolite_learner.joint_extract import fit_joint_components_from_tensor


class JointComponentExtractionTests(unittest.TestCase):
    def test_fit_joint_components_from_tensor_recovers_cell_type_structure(self) -> None:
        time_grid = np.linspace(0.0, 19.0, 20)
        mz_grid = np.arange(50, 62)
        sample_names = [
            "P_plate1_r1",
            "P_plate2_r1",
            "B_plate1_r1",
            "B_plate3_r1",
            "L_plate2_r1",
            "L_plate3_r1",
            "M_plate1_r1",
            "M_plate2_r1",
        ]

        component_a_rt = np.exp(-0.5 * ((time_grid - 5.0) / 1.0) ** 2)
        component_a_spec = np.array([0.0, 0.2, 0.8, 0.4, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float)
        component_b_rt = np.exp(-0.5 * ((time_grid - 13.0) / 1.3) ** 2)
        component_b_spec = np.array([0.0, 0.0, 0.0, 0.1, 0.2, 0.0, 0.1, 0.7, 0.6, 0.1, 0.0, 0.0], dtype=float)

        abundance_a = np.array([2.0, 2.2, 6.5, 6.1, 1.4, 1.6, 0.5, 0.6], dtype=float)
        abundance_b = np.array([1.5, 1.7, 1.8, 1.9, 5.6, 5.2, 0.4, 0.5], dtype=float)

        tensor = np.zeros((time_grid.size, mz_grid.size, len(sample_names)), dtype=float)
        for sample_index in range(len(sample_names)):
            tensor[:, :, sample_index] += abundance_a[sample_index] * np.outer(component_a_rt, component_a_spec)
            tensor[:, :, sample_index] += abundance_b[sample_index] * np.outer(component_b_rt, component_b_spec)
        tensor += 0.01

        result = fit_joint_components_from_tensor(
            tensor,
            time_grid=time_grid,
            mz_grid=mz_grid,
            sample_names=sample_names,
            n_components=2,
            supervision_strength=0.45,
            max_iter=35,
        )

        self.assertEqual(len(result.peaks_integrated), 2)
        self.assertEqual(len(result.spectra), 2)
        self.assertEqual(len(result.chromatograms), 2)
        self.assertIn("cellB", result.component_effects.columns)
        self.assertIn("cellL", result.component_effects.columns)
        self.assertTrue((result.component_effects["supervisionR2"] > 0.5).all())
        self.assertGreater(result.component_effects["cellB"].max(), 0.3)
        self.assertGreater(result.component_effects["cellL"].max(), 0.3)
        self.assertEqual(
            result.chromatograms.filter(like="rt").shape[1],
            time_grid.size,
        )


if __name__ == "__main__":
    unittest.main()
