"""Pruebas básicas del dashboard educativo."""

import tempfile
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from app import (
    VARIABLE_CONFIG,
    build_summary,
    classify_vital,
    create_synthetic_scenarios,
    create_overview_chart,
    export_synthetic_scenarios,
    generate_simulated_data,
    get_trend_indicator,
    load_or_create_data,
    validate_data,
)


class VitalSignsDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = generate_simulated_data(num_measurements=60, seed=123)

    def test_generated_data_has_expected_structure(self) -> None:
        expected_columns = ["timestamp"] + [
            config["column"] for config in VARIABLE_CONFIG.values()
        ]
        self.assertEqual(self.data.columns.tolist(), expected_columns)
        self.assertEqual(len(self.data), 60)
        self.assertFalse(self.data.isna().any().any())
        self.assertTrue(
            (self.data["presion_sistolica_mmhg"] > self.data["presion_diastolica_mmhg"]).all()
        )

    def test_classification_boundaries(self) -> None:
        cases = [
            ("frecuencia_cardiaca_bpm", 60, "Normal"),
            ("frecuencia_cardiaca_bpm", 50, "Atención"),
            ("frecuencia_cardiaca_bpm", 49, "Crítico"),
            ("spo2_porcentaje", 95, "Normal"),
            ("spo2_porcentaje", 90, "Atención"),
            ("spo2_porcentaje", 89, "Crítico"),
            ("temperatura_c", 36.0, "Normal"),
            ("temperatura_c", 35.9, "Atención"),
            ("temperatura_c", 34.9, "Crítico"),
            ("presion_sistolica_mmhg", 120, "Normal"),
            ("presion_sistolica_mmhg", 121, "Atención"),
            ("presion_sistolica_mmhg", 140, "Crítico"),
            ("presion_diastolica_mmhg", 80, "Normal"),
            ("presion_diastolica_mmhg", 81, "Atención"),
            ("presion_diastolica_mmhg", 90, "Crítico"),
        ]

        for column, value, expected_status in cases:
            with self.subTest(column=column, value=value):
                self.assertEqual(classify_vital(column, value), expected_status)

    def test_summary_counts_match_measurements(self) -> None:
        summary = build_summary(self.data)
        totals = summary[["Normal", "Atención", "Crítico"]].sum(axis=1)
        self.assertTrue((totals == len(self.data)).all())

    def test_empty_csv_is_rejected(self) -> None:
        empty_data = pd.DataFrame(columns=self.data.columns)
        with self.assertRaisesRegex(ValueError, "ninguna medición"):
            validate_data(empty_data)

    def test_missing_csv_is_created_automatically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            sample_path = Path(temporary_directory) / "data" / "sample.csv"
            loaded_data = load_or_create_data(sample_path)
            self.assertTrue(sample_path.exists())
            self.assertEqual(len(loaded_data), 240)

    def test_synthetic_scenarios_are_coherent(self) -> None:
        scenarios = create_synthetic_scenarios()
        self.assertTrue(all("Paciente" not in name for name in scenarios))

        baseline_summary = build_summary(scenarios["Escenario basal estable"])
        self.assertEqual(int(baseline_summary["Crítico"].sum()), 0)

        elevated_hr = scenarios["Escenario con frecuencia cardíaca elevada"]
        elevated_hr_states = elevated_hr["frecuencia_cardiaca_bpm"].apply(
            lambda value: classify_vital("frecuencia_cardiaca_bpm", value)
        )
        self.assertGreater(int((elevated_hr_states != "Normal").sum()), 200)

        reduced_spo2 = scenarios["Escenario con SpO₂ reducida"]
        reduced_spo2_states = reduced_spo2["spo2_porcentaje"].apply(
            lambda value: classify_vital("spo2_porcentaje", value)
        )
        self.assertGreater(int((reduced_spo2_states != "Normal").sum()), 200)

    def test_overview_axes_follow_the_data_range(self) -> None:
        chart = create_overview_chart(self.data)
        try:
            for axis, config in zip(chart.axes, VARIABLE_CONFIG.values()):
                values = self.data[config["column"]]
                data_span = float(values.max() - values.min())
                axis_span = float(axis.get_ylim()[1] - axis.get_ylim()[0])
                self.assertLessEqual(axis_span, data_span * 1.31 + 0.1)
        finally:
            plt.close(chart)

    def test_trend_indicators(self) -> None:
        self.assertEqual(get_trend_indicator(pd.Series(range(10))), "↑")
        self.assertEqual(get_trend_indicator(pd.Series(range(10, 0, -1))), "↓")
        self.assertEqual(get_trend_indicator(pd.Series([5] * 10)), "→")

    def test_scenarios_can_be_exported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "scenarios.csv"
            exported_path = export_synthetic_scenarios(output_path)
            combined = pd.read_csv(exported_path)

            self.assertEqual(len(combined), 960)
            self.assertIn("scenario_name", combined.columns)
            self.assertEqual(len(list((output_path.parent / "scenarios").glob("*.csv"))), 4)


if __name__ == "__main__":
    unittest.main()
