# Dashboard de constantes vitales simuladas

Aplicación interactiva desarrollada con Python y Streamlit para visualizar y analizar constantes vitales completamente simuladas.

> **Aviso:** Este proyecto tiene finalidad educativa y no debe utilizarse con fines diagnósticos ni clínicos. Los datos son sintéticos y no pertenecen a pacientes reales.

## Objetivo

Practicar conceptos básicos de ingeniería biomédica y análisis de series temporales: generación de señales fisiológicas ficticias, visualización, estadística descriptiva y clasificación mediante umbrales orientativos simplificados.

La aplicación trabaja con:

- Frecuencia cardíaca en bpm.
- Saturación de oxígeno SpO₂ en porcentaje.
- Temperatura corporal en °C.
- Presión arterial sistólica y diastólica en mmHg.

## Características principales

- Generación y carga automática de datos simulados.
- Métricas con última medición, variación y tendencia.
- Clasificación visual: normal, atención o crítico.
- Gráfica temporal con puntos clasificados y bandas de referencia.
- Vista global de las cinco constantes con escalas ajustadas.
- Escenarios fisiológicos sintéticos reproducibles.
- Descarga de los datos mostrados y de los escenarios en CSV.
- Promedios, mínimos, máximos y recuentos por estado.
- Tabla completa de mediciones sintéticas.
- Controles para filtrar y regenerar la muestra.

## Tecnologías utilizadas

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib

Se recomienda **Python 3.10 o superior**.

## Demo

Demo: Próximamente

## Capturas

![Vista previa del proyecto](assets/preview.png)

Pendiente: añadir captura real del proyecto.

## Instalación y ejecución

```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

Para ejecutar las pruebas:

```bash
python -m pytest
```

## Estructura del proyecto

```text
dashboard-constantes-vitales/
├── .gitignore
├── app.py
├── requirements.txt
├── README.md
├── tests/
│   └── test_app.py
└── data/
    └── vital_signs_sample.csv
```

## Umbrales educativos utilizados

| Constante | Normal | Atención | Crítico |
|---|---|---|---|
| Frecuencia cardíaca | 60–100 bpm | 50–59 o 101–120 bpm | <50 o >120 bpm |
| SpO₂ | ≥95 % | 90–94 % | <90 % |
| Temperatura | 36,0–37,5 °C | 35,0–35,9 o 37,6–38,5 °C | <35,0 o >38,5 °C |
| Presión sistólica | 90–120 mmHg | 80–89 o 121–139 mmHg | <80 o ≥140 mmHg |
| Presión diastólica | 60–80 mmHg | 50–59 o 81–89 mmHg | <50 o ≥90 mmHg |

Estos intervalos son simplificaciones para practicar programación condicional. No representan una guía clínica completa.

## Instalación detallada

Se recomienda utilizar un entorno virtual:

```bash
python -m venv .venv
```

Activación en Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Activación en macOS o Linux:

```bash
source .venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

Streamlit abrirá el dashboard en `http://localhost:8501`.

Si `data/vital_signs_sample.csv` no existe, la aplicación lo generará automáticamente. El botón de la barra lateral permite crear una muestra nueva.

## Escenarios fisiológicos sintéticos

La aplicación incluye cuatro escenarios artificiales: basal estable, frecuencia cardíaca elevada, SpO₂ reducida y temperatura/presión elevadas. Se seleccionan desde la barra lateral y sirven para practicar la interpretación visual de series temporales.

El botón de descarga genera un CSV combinado con una columna `scenario_name` que identifica el escenario de cada medición. La función `export_synthetic_scenarios()` también permite exportar desde Python un archivo combinado y cuatro CSV individuales.

**Importante:** son escenarios ficticios, no casos clínicos ni diagnósticos. No introduzcas datos identificables o reales de pacientes.

## Pruebas

El proyecto incluye pruebas unitarias para generación, clasificación, validación, resumen, escenarios, tendencias, exportación y escalas de las gráficas:

```bash
python -m unittest discover -s tests -v
```

## Organización del código

`app.py` está dividido en funciones pequeñas para generar, guardar, validar, clasificar, resumir y visualizar los datos. Esta separación facilita estudiar el código y ampliar el proyecto sin mezclar la lógica de datos con la interfaz.

## Competencias demostradas

- Simulación reproducible de series temporales con NumPy.
- Limpieza y análisis tabular con Pandas.
- Visualización científica con Matplotlib.
- Desarrollo de interfaces interactivas con Streamlit.
- Validación de datos y pruebas automáticas básicas.

## Capturas sugeridas adicionales

Para GitHub o LinkedIn, se recomienda incluir:

1. Una captura horizontal con el título, el aviso educativo y las cinco métricas.
2. La gráfica temporal con bandas de referencia y puntos clasificados.
3. La vista global o el resumen estadístico con los recuentos de estados.

## Mejoras futuras

- Añadir filtros por intervalo temporal.
- Exportar el resumen a CSV o PDF.
- Incorporar nuevas señales simuladas, como frecuencia respiratoria.
- Añadir integración continua para ejecutar las pruebas en GitHub Actions.
- Añadir detección educativa de anomalías mediante métodos estadísticos.
- Desplegar la aplicación en Streamlit Community Cloud.

## Limitaciones

Los umbrales implementados son simplificaciones orientativas para demostrar lógica de programación. No constituyen criterios médicos completos y no deben utilizarse para evaluar personas, emitir diagnósticos ni tomar decisiones clínicas.

## Publicación sugerida para LinkedIn

He mejorado mi dashboard educativo de constantes vitales simuladas con Python y Streamlit. Esta versión incorpora escenarios fisiológicos sintéticos, tendencias, bandas de referencia, una vista global, exportación CSV y pruebas automatizadas. El proyecto es exclusivamente educativo y no debe utilizarse con fines diagnósticos ni clínicos.
