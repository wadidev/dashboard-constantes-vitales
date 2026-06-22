"""Dashboard educativo de constantes vitales completamente simuladas."""

from pathlib import Path
import re
import unicodedata

import matplotlib

# Streamlit renderiza las figuras en la web; no necesita una ventana gráfica local.
matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "vital_signs_sample.csv"

VARIABLE_CONFIG = {
    "Frecuencia cardíaca": {
        "column": "frecuencia_cardiaca_bpm",
        "unit": "bpm",
        "emoji": "❤️",
        "decimals": 0,
    },
    "Saturación de oxígeno": {
        "column": "spo2_porcentaje",
        "unit": "%",
        "emoji": "🫁",
        "decimals": 1,
    },
    "Temperatura corporal": {
        "column": "temperatura_c",
        "unit": "°C",
        "emoji": "🌡️",
        "decimals": 1,
    },
    "Presión arterial sistólica": {
        "column": "presion_sistolica_mmhg",
        "unit": "mmHg",
        "emoji": "🩸",
        "decimals": 0,
    },
    "Presión arterial diastólica": {
        "column": "presion_diastolica_mmhg",
        "unit": "mmHg",
        "emoji": "🩸",
        "decimals": 0,
    },
}

STATUS_ICONS = {
    "Normal": "🟢",
    "Atención": "🟠",
    "Crítico": "🔴",
}

STATUS_COLORS = {
    "Normal": "#4caf50",
    "Atención": "#ff9800",
    "Crítico": "#f44336",
}

# Intervalos usados tanto para clasificar como para dibujar las gráficas.
# Cada tupla contiene: límite inferior, límite superior, inclusión de cada
# límite y estado. None representa un intervalo abierto hacia infinito.
STATUS_RANGES = {
    "frecuencia_cardiaca_bpm": [
        (None, 50, False, False, "Crítico"),
        (50, 60, True, False, "Atención"),
        (60, 100, True, True, "Normal"),
        (100, 120, False, True, "Atención"),
        (120, None, False, False, "Crítico"),
    ],
    "spo2_porcentaje": [
        (None, 90, False, False, "Crítico"),
        (90, 95, True, False, "Atención"),
        (95, None, True, False, "Normal"),
    ],
    "temperatura_c": [
        (None, 35.0, False, False, "Crítico"),
        (35.0, 36.0, True, False, "Atención"),
        (36.0, 37.5, True, True, "Normal"),
        (37.5, 38.5, False, True, "Atención"),
        (38.5, None, False, False, "Crítico"),
    ],
    "presion_sistolica_mmhg": [
        (None, 80, False, False, "Crítico"),
        (80, 90, True, False, "Atención"),
        (90, 120, True, True, "Normal"),
        (120, 140, False, False, "Atención"),
        (140, None, True, False, "Crítico"),
    ],
    "presion_diastolica_mmhg": [
        (None, 50, False, False, "Crítico"),
        (50, 60, True, False, "Atención"),
        (60, 80, True, True, "Normal"),
        (80, 90, False, False, "Atención"),
        (90, None, True, False, "Crítico"),
    ],
}


def value_is_in_range(
    value: float,
    lower: float | None,
    upper: float | None,
    include_lower: bool,
    include_upper: bool,
) -> bool:
    """Indica si un valor pertenece a un intervalo abierto o cerrado."""
    lower_ok = lower is None or value > lower or (include_lower and value == lower)
    upper_ok = upper is None or value < upper or (include_upper and value == upper)
    return lower_ok and upper_ok


def create_synthetic_scenarios() -> dict:
    """Genera escenarios fisiológicos sintéticos con fines educativos."""
    scenarios: dict = {}

    stable_data = generate_simulated_data(240, seed=101, include_anomalies=False)
    scenarios["Escenario basal estable"] = stable_data

    elevated_heart_rate = generate_simulated_data(240, seed=202, include_anomalies=False)
    elevated_heart_rate["frecuencia_cardiaca_bpm"] = (
        np.rint(
            np.clip(elevated_heart_rate["frecuencia_cardiaca_bpm"] + 35, 38, 220)
        ).astype(int)
    )
    scenarios["Escenario con frecuencia cardíaca elevada"] = elevated_heart_rate

    reduced_spo2 = generate_simulated_data(240, seed=303, include_anomalies=False)
    reduced_spo2["spo2_porcentaje"] = np.round(
        np.clip(reduced_spo2["spo2_porcentaje"] - 7, 70, 100), 1
    )
    scenarios["Escenario con SpO₂ reducida"] = reduced_spo2

    elevated_temperature_pressure = generate_simulated_data(
        240, seed=404, include_anomalies=False
    )
    elevated_temperature_pressure["temperatura_c"] = np.round(
        np.clip(elevated_temperature_pressure["temperatura_c"] + 1.6, 34, 42), 1
    )
    elevated_temperature_pressure["presion_sistolica_mmhg"] = np.rint(
        np.clip(elevated_temperature_pressure["presion_sistolica_mmhg"] + 25, 70, 220)
    ).astype(int)
    elevated_temperature_pressure["presion_diastolica_mmhg"] = np.rint(
        np.clip(elevated_temperature_pressure["presion_diastolica_mmhg"] + 15, 40, 150)
    ).astype(int)
    scenarios["Escenario con temperatura y presión elevadas"] = (
        elevated_temperature_pressure
    )

    return scenarios


def export_synthetic_scenarios(path: Path | str = None) -> Path:
    """Concatena y exporta todos los escenarios sintéticos a archivos CSV."""
    if path is None:
        path = BASE_DIR / "data" / "synthetic_scenarios.csv"
    path = Path(path)

    scenarios = create_synthetic_scenarios()
    combined = combine_synthetic_scenarios(scenarios)

    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S")

    scenarios_dir = path.parent / "scenarios"
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    for name, data in scenarios.items():
        normalized_name = unicodedata.normalize("NFKD", name).encode(
            "ascii", "ignore"
        ).decode("ascii")
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", normalized_name).strip("_").lower()
        file_path = scenarios_dir / f"{slug}.csv"
        data.to_csv(file_path, index=False, date_format="%Y-%m-%d %H:%M:%S")

    return path


def combine_synthetic_scenarios(scenarios: dict | None = None) -> pd.DataFrame:
    """Combina los escenarios y añade una columna que identifica su origen."""
    if scenarios is None:
        scenarios = create_synthetic_scenarios()

    frames = []
    for name, df in scenarios.items():
        temp = df.copy()
        temp["scenario_name"] = name
        frames.append(temp)

    return pd.concat(frames, ignore_index=True)


def generate_simulated_data(
    num_measurements: int = 240,
    seed: int | None = None,
    include_anomalies: bool = True,
) -> pd.DataFrame:
    """Genera una serie temporal ficticia sin información de pacientes reales."""
    if num_measurements < 1:
        raise ValueError("El número de mediciones debe ser mayor que cero.")

    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(
        end=pd.Timestamp.now().floor("min"),
        periods=num_measurements,
        freq="5min",
    )
    cycle = np.linspace(0, 4 * np.pi, num_measurements)

    heart_rate = 76 + 7 * np.sin(cycle) + rng.normal(0, 4, num_measurements)
    spo2 = 97.1 + 0.5 * np.sin(cycle / 2) + rng.normal(0, 0.5, num_measurements)
    temperature = 36.7 + 0.25 * np.sin(cycle / 3) + rng.normal(0, 0.12, num_measurements)

    pressure_shift = 8 * np.sin(cycle / 2) + rng.normal(0, 4, num_measurements)
    systolic = 116 + pressure_shift + rng.normal(0, 3, num_measurements)
    diastolic = 74 + 0.45 * pressure_shift + rng.normal(0, 2.5, num_measurements)

    if include_anomalies:
        anomaly_count = max(1, num_measurements // 30)
        anomaly_size = min(anomaly_count, num_measurements)
        heart_rate[rng.choice(num_measurements, anomaly_size, replace=False)] += 48
        spo2[rng.choice(num_measurements, anomaly_size, replace=False)] -= 8
        temperature[rng.choice(num_measurements, anomaly_size, replace=False)] += 2.2
        systolic[rng.choice(num_measurements, anomaly_size, replace=False)] += 35
        diastolic[rng.choice(num_measurements, anomaly_size, replace=False)] += 20

    heart_rate = np.clip(heart_rate, 38, 155)
    spo2 = np.clip(spo2, 84, 100)
    temperature = np.clip(temperature, 34, 40.5)
    systolic = np.clip(systolic, 70, 175)
    diastolic = np.clip(diastolic, 40, 110)
    systolic = np.maximum(systolic, diastolic + 20)

    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "frecuencia_cardiaca_bpm": np.rint(heart_rate).astype(int),
            "spo2_porcentaje": np.round(spo2, 1),
            "temperatura_c": np.round(temperature, 1),
            "presion_sistolica_mmhg": np.rint(systolic).astype(int),
            "presion_diastolica_mmhg": np.rint(diastolic).astype(int),
        }
    )


def save_simulated_data(data: pd.DataFrame, path: Path = DATA_PATH) -> None:
    """Guarda los datos simulados en CSV y crea la carpeta si no existe."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S")


def validate_data(data: pd.DataFrame) -> pd.DataFrame:
    """Comprueba que el CSV contiene las columnas y tipos esperados."""
    required_columns = ["timestamp"] + [config["column"] for config in VARIABLE_CONFIG.values()]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Faltan columnas en el CSV: {', '.join(missing_columns)}")

    clean_data = data[required_columns].copy()
    clean_data["timestamp"] = pd.to_datetime(clean_data["timestamp"], errors="coerce")

    for column in required_columns[1:]:
        clean_data[column] = pd.to_numeric(clean_data[column], errors="coerce")

    if clean_data.isna().any().any():
        raise ValueError("El CSV contiene fechas o valores numéricos no válidos.")

    if clean_data.empty:
        raise ValueError("El CSV no contiene ninguna medición.")

    return clean_data.sort_values("timestamp").reset_index(drop=True)


def load_or_create_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Carga el CSV o genera una muestra reproducible cuando todavía no existe."""
    if not path.exists():
        sample_data = generate_simulated_data(num_measurements=240, seed=42)
        save_simulated_data(sample_data, path)

    return validate_data(pd.read_csv(path))


def classify_vital(variable_column: str, value: float) -> str:
    """Clasifica un valor con umbrales educativos y meramente orientativos."""
    if variable_column not in STATUS_RANGES:
        raise ValueError(f"Variable no reconocida: {variable_column}")

    for lower, upper, include_lower, include_upper, status in STATUS_RANGES[
        variable_column
    ]:
        if value_is_in_range(value, lower, upper, include_lower, include_upper):
            return status

    raise ValueError(f"El valor {value} no encaja en los intervalos configurados.")


def draw_reference_bands(
    ax: Axes,
    variable_column: str,
    plot_ymin: float,
    plot_ymax: float,
    alpha: float,
) -> dict:
    """Dibuja solo la parte visible de los intervalos y devuelve su leyenda."""
    legend_patches = {}

    for lower, upper, _, _, status in STATUS_RANGES[variable_column]:
        visible_low = plot_ymin if lower is None else max(lower, plot_ymin)
        visible_high = plot_ymax if upper is None else min(upper, plot_ymax)

        if visible_high > visible_low:
            color = STATUS_COLORS[status]
            ax.axhspan(visible_low, visible_high, color=color, alpha=alpha, zorder=0)
            legend_patches.setdefault(
                status,
                mpatches.Patch(color=color, alpha=0.4, label=status),
            )

    return legend_patches


def get_trend_indicator(series: pd.Series, decimals: int = 1) -> str:
    """Devuelve un indicador de tendencia basado en las últimas mediciones."""
    if len(series) < 5:
        return "—"
    recent = series.tail(10).values
    slope = np.polyfit(range(len(recent)), recent, 1)[0]
    threshold = 10 ** (-decimals)
    if slope > threshold:
        return "↑"
    if slope < -threshold:
        return "↓"
    return "→"


def build_summary(data: pd.DataFrame) -> pd.DataFrame:
    """Resume estadísticos y recuentos de estados para cada constante."""
    summary_rows = []

    for label, config in VARIABLE_CONFIG.items():
        column = config["column"]
        statuses = data[column].apply(lambda value: classify_vital(column, value))
        summary_rows.append(
            {
                "Constante": label,
                "Unidad": config["unit"],
                "Promedio": round(data[column].mean(), 1),
                "Mínimo": round(data[column].min(), 1),
                "Máximo": round(data[column].max(), 1),
                "Normal": int((statuses == "Normal").sum()),
                "Atención": int((statuses == "Atención").sum()),
                "Crítico": int((statuses == "Crítico").sum()),
            }
        )

    return pd.DataFrame(summary_rows)


def create_line_chart(data: pd.DataFrame, label: str, config: dict) -> plt.Figure:
    """Gráfica temporal con bandas de referencia coloreadas por estado."""
    col = config["column"]
    fig, ax = plt.subplots(figsize=(11, 4))

    y_min = data[col].min()
    y_max = data[col].max()
    margin = (y_max - y_min) * 0.15 if y_max != y_min else 1
    plot_ymin = y_min - margin
    plot_ymax = y_max + margin

    legend_patches = draw_reference_bands(ax, col, plot_ymin, plot_ymax, alpha=0.10)

    # Colorear los puntos según su estado
    statuses = data[col].apply(lambda v: classify_vital(col, v))
    colors = statuses.map(STATUS_COLORS)

    ax.plot(data["timestamp"], data[col], linewidth=1.6, color="#1976d2", zorder=2, alpha=0.85)
    ax.scatter(data["timestamp"], data[col], c=colors, s=18, zorder=3, linewidths=0)

    # Marcar la última medición
    ax.scatter(
        data["timestamp"].iloc[-1],
        data[col].iloc[-1],
        s=80,
        color="#1976d2",
        zorder=4,
        edgecolors="white",
        linewidths=1.5,
        label="Última medición",
    )

    ax.set_title(f"Evolución de {label}", loc="left", fontweight="bold", fontsize=12)
    ax.set_xlabel("Tiempo", fontsize=10)
    ax.set_ylabel(f"{label} ({config['unit']})", fontsize=10)
    ax.set_ylim(plot_ymin, plot_ymax)
    ax.grid(alpha=0.2, linestyle="--")

    handles = list(legend_patches.values()) + ax.get_legend_handles_labels()[0]
    ax.legend(handles=handles, frameon=False, fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def create_overview_chart(data: pd.DataFrame) -> plt.Figure:
    """Gráfica con las 5 variables en subplots para una visión global."""
    fig, axes = plt.subplots(5, 1, figsize=(11, 14), sharex=True)
    fig.suptitle("Vista global — todas las constantes vitales", fontweight="bold", fontsize=13, y=1.01)

    for ax, (label, config) in zip(axes, VARIABLE_CONFIG.items()):
        col = config["column"]
        statuses = data[col].apply(lambda v: classify_vital(col, v))
        point_colors = statuses.map(STATUS_COLORS)

        y_min = data[col].min()
        y_max = data[col].max()
        margin = (y_max - y_min) * 0.15 if y_max != y_min else 1
        plot_ymin = y_min - margin
        plot_ymax = y_max + margin
        draw_reference_bands(ax, col, plot_ymin, plot_ymax, alpha=0.08)

        ax.plot(data["timestamp"], data[col], linewidth=1.4, color="#1976d2", alpha=0.8, zorder=2)
        ax.scatter(data["timestamp"], data[col], c=point_colors, s=12, zorder=3, linewidths=0)
        ax.set_ylabel(config["unit"], fontsize=9)
        ax.set_title(label, loc="left", fontsize=9, fontweight="bold", pad=2)
        ax.set_ylim(plot_ymin, plot_ymax)
        ax.grid(alpha=0.15, linestyle="--")
        ax.tick_params(axis="y", labelsize=8)

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))
    fig.autofmt_xdate(rotation=30, ha="right")
    fig.tight_layout()
    return fig


def prepare_display_table(data: pd.DataFrame) -> pd.DataFrame:
    """Añade estados legibles a la tabla sin modificar el CSV original."""
    display_data = data.copy()
    display_data["timestamp"] = display_data["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    for label, config in VARIABLE_CONFIG.items():
        column = config["column"]
        display_data[f"Estado: {label}"] = [
            format_vital_status(column, value) for value in display_data[column]
        ]

    friendly_names = {
        "timestamp": "Fecha y hora",
        "frecuencia_cardiaca_bpm": "Frecuencia cardíaca (bpm)",
        "spo2_porcentaje": "SpO₂ (%)",
        "temperatura_c": "Temperatura (°C)",
        "presion_sistolica_mmhg": "Presión sistólica (mmHg)",
        "presion_diastolica_mmhg": "Presión diastólica (mmHg)",
    }
    return display_data.rename(columns=friendly_names)


def format_vital_status(variable_column: str, value: float) -> str:
    """Combina el nombre del estado con su indicador visual."""
    status = classify_vital(variable_column, value)
    return f"{STATUS_ICONS[status]} {status}"


def render_dashboard() -> None:
    """Construye la interfaz principal de Streamlit."""
    st.set_page_config(
        page_title="Dashboard de constantes vitales simuladas",
        page_icon="🫀",
        layout="wide",
    )

    st.title("🫀 Dashboard de constantes vitales simuladas")
    st.write(
        "Aplicación educativa para explorar la evolución temporal de constantes "
        "vitales generadas artificialmente y practicar análisis de datos biomédicos."
    )
    st.warning(
        "Este proyecto tiene finalidad educativa y no debe utilizarse con fines "
        "diagnósticos ni clínicos.",
        icon="⚠️",
    )
    st.caption("Leyenda: 🟢 Normal · 🟠 Atención · 🔴 Crítico")

    try:
        complete_data = load_or_create_data()
    except (OSError, ValueError) as error:
        st.error(f"No se pudieron cargar los datos simulados: {error}")
        st.stop()

    with st.sidebar:
        st.header("Controles")

        if st.button("🔄 Regenerar datos simulados", width="stretch"):
            try:
                regenerated_data = generate_simulated_data(num_measurements=240)
                save_simulated_data(regenerated_data)
            except OSError as error:
                st.error(f"No se pudieron guardar los datos: {error}")
            else:
                st.success("Datos simulados regenerados.")
                st.rerun()

        minimum_measurements = 10 if len(complete_data) >= 10 else 1
        step = 10 if len(complete_data) >= 20 else 1
        measurements_to_show = st.slider(
            "Número de mediciones a mostrar",
            min_value=minimum_measurements,
            max_value=len(complete_data),
            value=min(100, len(complete_data)),
            step=step,
        )
        selected_variable = st.selectbox(
            "Variable para la gráfica individual",
            options=list(VARIABLE_CONFIG.keys()),
        )
        st.divider()
        scenarios = create_synthetic_scenarios()
        scenario_options = ["Ninguno (usar datos guardados)"] + list(scenarios.keys())
        selected_scenario = st.selectbox(
            "Escenario fisiológico sintético",
            options=scenario_options,
            index=0,
        )
        if selected_scenario != scenario_options[0]:
            st.info(
                "Mostrando un escenario artificial para practicar análisis de datos. "
                "No representa un diagnóstico ni a una persona real.",
            )
        combined_scenarios = combine_synthetic_scenarios(scenarios)
        st.download_button(
            label="📥 Descargar escenarios sintéticos (CSV)",
            data=combined_scenarios.to_csv(index=False).encode("utf-8"),
            file_name="escenarios_fisiologicos_sinteticos.csv",
            mime="text/csv",
        )
        st.divider()
        st.caption("Todos los registros son sintéticos y no representan a ningún paciente.")

    if selected_scenario != scenario_options[0]:
        complete_data = scenarios[selected_scenario]

    data = complete_data.tail(measurements_to_show).reset_index(drop=True)
    latest_measurement = data.iloc[-1]

    # ── Métricas con tendencia ──────────────────────────────────────────────
    st.subheader("Última medición simulada")
    metric_columns = st.columns(len(VARIABLE_CONFIG))
    for metric_column, (label, config) in zip(metric_columns, VARIABLE_CONFIG.items()):
        value = latest_measurement[config["column"]]
        status = classify_vital(config["column"], value)
        trend = get_trend_indicator(data[config["column"]], config["decimals"])
        prev_value = data[config["column"]].iloc[-2] if len(data) >= 2 else value
        delta = round(value - prev_value, config["decimals"])
        with metric_column:
            st.metric(
                label=f"{config['emoji']} {label}",
                value=f"{value:.{config['decimals']}f} {config['unit']}",
                delta=f"{delta:+.{config['decimals']}f} {config['unit']}",
                delta_color="off",
            )
            st.caption(f"{STATUS_ICONS[status]} {status} · tendencia {trend}")

    # ── Gráfica individual con bandas de referencia ─────────────────────────
    st.subheader("Evolución temporal")
    selected_config = VARIABLE_CONFIG[selected_variable]
    chart = create_line_chart(data, selected_variable, selected_config)
    st.pyplot(chart, width="stretch")
    plt.close(chart)
    st.caption(
        "Los colores de los puntos indican el estado en cada medición: 🟢 Normal · 🟠 Atención · 🔴 Crítico. "
        "Las bandas de fondo representan los umbrales orientativos educativos."
    )

    # ── Vista global de todas las variables ────────────────────────────────
    with st.expander("📊 Ver todas las variables a la vez", expanded=False):
        overview = create_overview_chart(data)
        st.pyplot(overview, width="stretch")
        plt.close(overview)

    # ── Resumen ────────────────────────────────────────────────────────────
    st.subheader("Resumen automático")
    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("Mediciones mostradas", len(data))
    with summary_cols[1]:
        st.metric("Intervalo simulado", "5 minutos")
    with summary_cols[2]:
        total_critical = sum(
            int((data[c["column"]].apply(lambda v: classify_vital(c["column"], v)) == "Crítico").sum())
            for c in VARIABLE_CONFIG.values()
        )
        st.metric("Lecturas críticas (total)", total_critical)

    st.dataframe(build_summary(data), width="stretch", hide_index=True)

    # ── Tabla de datos ─────────────────────────────────────────────────────
    st.subheader("Datos simulados")
    csv_bytes = data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar datos mostrados (CSV)",
        data=csv_bytes,
        file_name="constantes_vitales.csv",
        mime="text/csv",
    )
    st.dataframe(
        prepare_display_table(data),
        width="stretch",
        hide_index=True,
        height=420,
    )


if __name__ == "__main__":
    render_dashboard()
