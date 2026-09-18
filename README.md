# Procesamiento de Datos Radiométricos en Aguas Continentales
### Escuela de Primavera 2026 · Teleobservación de Aguas Marinas, Costeras e Interiores
**Instituto de Altos Estudios Espaciales "Mario Gulich" (CONAE / Universidad Nacional de Córdoba)**


## Descripción General

Este repositorio contiene el material teórico-práctico, el código fuente y el conjunto de datos de campo para la **Escuela de Primavera 2026**. 

El objetivo principal es brindar una formación integral en el flujo metodológico riguroso para la adquisición, calibración, corrección espectral y análisis cuantitativo de **mediciones espectrorradiométricas de campo (*in situ*) sobre cuerpos de agua continentales**. Se aborda la estimación de la **reflectancia de teledetección ($R_{rs}$)**, la **convolución espectral con sensores satelitales** (Sentinel-3 OLCI y Sentinel-2 MSI) y la formulación y calibración de **algoritmos bio-ópticos en el Rojo e Infrarrojo Cercano (Red-NIR)** para el monitoreo de calidad del agua en reservorios eutróficos (aguas ópticamente complejas o Caso 2).

---

## Contexto de la Campaña y Sitio de Estudio

* **Cuerpo de agua**: **Embalse San Roque** (Valle de Punilla, Provincia de Córdoba, Argentina).
* **Fecha de campaña**: 27 de octubre de 2022.
* **Marco institucional**: Proyecto **PROSAT II-ARG** (*Programa de Desarrollo de Tecnologías Satelitales* - Préstamo BID N° 4840/OC) / Instituto Gulich (CONAE/UNC).
* **Características limnológicas y bio-ópticas**:
  * Lago templado-cálido, monomíctico, con régimen trófico predominantemente eutrófico a hipereutrófico.
  * Presencia recurrente de floraciones masivas de cianobacterias (*Microcystis aeruginosa*).
  * Constituye un escenario típico de **aguas Caso 2**: la señal óptica no está gobernada únicamente por el fitoplancton, sino también por elevadas concentraciones de materia orgánica disuelta coloreada (CDOM) y sólidos suspendidos totales (TSS).

---

## Fundamentos 
1. **Calibración Radiométrica y Corrección de Empalmes (*Splice Correction*)**:
   Las cuentas digitales crudas ($DN$) se transforman a radiancia física calibrada mediante coeficientes absolutos trazables a NIST. Las discontinuidades instrumentales debidas a los saltos térmicos y ópticos entre detectores (VNIR a 1000 nm y SWIR1/SWIR2 a 1800 nm) se corrigen con un ajuste parabólico continuo.
2. **Reflectancia de Teledetección ($R_{rs}$)**:
   $$R_{rs}(\lambda) = \frac{L_w(\lambda)}{E_d(\lambda)} = \frac{L_{wat}(\lambda) - \rho_F(W) \cdot L_{sky}(\lambda)}{\pi \cdot L_{spc}(\lambda) / \rho_{spc}(\lambda)}$$
   donde $\rho_F(W)$ es el factor de reflexión superficial de Fresnel en función de la velocidad del viento $W$ ([Mobley, 1999](https://doi.org/10.1364/AO.38.007442)).
3. **Convolución Espectral Satelital**:
   Integración numérica de los espectros hiperespectrales con las Funciones de Respuesta Espectral Relativa ($RSR$) de **Sentinel-3A OLCI** y **Sentinel-2 MSI**:
   $$R_{rs}^{\text{sat}}(k) = \frac{\int_{\lambda_{\min}}^{\lambda_{\max}} R_{rs}(\lambda) \, RSR_k(\lambda) \, d\lambda}{\int_{\lambda_{\min}}^{\lambda_{\max}} RSR_k(\lambda) \, d\lambda}$$
4. **Modelos Bio-Ópticos Red-NIR**:
   Superación de las limitaciones de los algoritmos de relación azul/verde en aguas continentales productivas mediante bandas donde domina la absorción por pigmentos y la retrodispersión particulada:
   * **Clorofila-a**: Cociente $R_{rs}(709) / R_{rs}(665)$ (máximo pico de retrodispersión vs. absorción diagnóstica de Chl-a).
   * **Turbidez**: Reflectancia monocanal en $R_{rs}(709)$ (proporcional a retrodispersión inorgánica y celular).
   * **Cianobacterias**: Cociente $R_{rs}(709) / R_{rs}(620)$ (sensible a la absorción específica de la ficocianina a 620 nm).

---

## Estructura del Repositorio

```text
├── EDP_radiometria_campo.ipynb          # Cuaderno principal interactivo (teoría, código y ejercicios)
├── README.md                            # Documentación general del curso y guía de uso
├── src/
│   ├── asdreader.py                     # Módulo Python para lectura de binarios ASD FieldSpec (.asd v8)
└── data/
    ├── radiometricos/                   # Espectros crudos organizados por estación de muestreo
    │   ├── punto-1/ … punto-6/          # Medición en 6 estaciones a lo largo del gradiente trófico
    │   │   ├── *-wat.asd                # Radiancia total emergente del agua (L_wat)
    │   │   ├── *-sky.asd                # Radiancia difusa del cielo (L_sky)
    │   │   └── *-spc.asd                # Radiancia de panel de referencia Spectralon (L_spc)
    └── complemetarios/                  # Datos auxiliares de calibración, validación y satélite
        ├── calibracion/                 # Coeficientes instrumentales de fábrica (.raw, .ref, .ill, .ini)
        ├── instrumentos/                # Datos limnológicos in situ:
        │   └── 185-20221027-ESR-AlgaeTorch.csv  # Clorofila-a, Ficocianina y Turbidez (bbe Moldaenke)
        ├── planilla campo/              # Planilla de campaña original escaneada (.pdf) con metadatos
        ├── fotos/                       # Registro fotográfico organizado por estación (punto-01 a punto-06: cielo, agua y planilla)
        ├── rsr/                         # Curvas de Respuesta Espectral Relativa de sensores espaciales
        │   ├── s3a_olci_RSR.nc          # Curvas RSR Sentinel-3A OLCI
        │   ├── sentinel-2a_msi_RSR.nc   # Curvas RSR Sentinel-2A MSI
        │   ├── sentinel-2b_msi_RSR.nc   # Curvas RSR Sentinel-2B MSI
        │   └── … (Landsat-8, MODIS, PACE OCI, etc.)
        ├── sentinel2/                   # Escena satelital Sentinel-2B L2A (26/10/2022) en formato GeoTIFF
        └── sentinel3/                   # Escena satelital Sentinel-3A OLCI WFR (27/10/2022) en GeoTIFF
```

---

## Instalación y Requisitos

### Requisitos de Software
* **Python**: Versión 3.9 o superior.
* **Librerías principales**:
  * Cálculo numérico y estadística: `numpy`, `scipy`, `pandas`, `xarray`, `netCDF4`
  * Visualización y cartografía: `matplotlib`, `seaborn`, `contextily`
  * Teledetección y satélite (opcional): `earthengine-api`

### Opción 1: Ejecución Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/fnemina/edp2026-radiometria-aguas.git
   cd edp2026-radiometria-aguas
   ```

2. **Crear y activar un entorno virtual**:
   * Con `venv`:
     ```bash
     python3 -m venv venv-edp
     source venv-edp/bin/activate  # En Windows: venv-edp\Scripts\activate
     ```
   * O con `conda` / `mamba`:
     ```bash
     conda create -n edp2026 python=3.10 -y
     conda activate edp2026
     ```

3. **Instalar las dependencias**:
   ```bash
   pip install numpy scipy pandas xarray netCDF4 matplotlib seaborn contextily jupyterlab
   ```

4. **Iniciar Jupyter Lab**:
   ```bash
   jupyter lab EDP_radiometria_campo.ipynb
   ```

### Opción 2: Ejecución en Google Colab

El cuaderno incluye al inicio celdas preparadas para descargar automáticamente el repositorio en entornos efímeros:
```python
!git clone https://github.com/fnemina/edp2026-radiometria-aguas.git
%cd edp2026-radiometria-aguas
!pip install contextily netCDF4 -qq
```

---

## Actividades Prácticas para los Alumnos

El cuaderno finaliza con una sección de **6 actividades de aplicación, análisis crítico y modelado bio-óptico**:

1. **Actividad 1: Sensibilidad de $R_{rs}$ al viento y al destello (*glint*)**:
   Evaluación del impacto del factor de Fresnel $\rho_F(W)$ y discusión sobre sobreestimaciones e incertidumbres en el azul vs. NIR.
2. **Actividad 2: Análisis de incertidumbre y propagación de errores en réplicas de campo**:
   Cálculo del coeficiente de variación espectral ($CV(\lambda)$) y análisis de anomalías en las réplicas instrumentales.
3. **Actividad 3: Convolución cruzada y comparación de sensores (Sentinel-3 OLCI vs. Sentinel-2 MSI)**:
   Análisis del efecto del ancho de banda y la ausencia del canal de 620 nm en Sentinel-2 para la detección de ficocianina.
4. **Actividad 4: Implementación de modelos bio-ópticos avanzados (Modelo de 3 bandas de Gitelson)**:
   Ajuste y validación del modelo $[R_{rs}^{-1}(\lambda_1) - R_{rs}^{-1}(\lambda_2)] \times R_{rs}(\lambda_3)$ para Clorofila-a.
5. **Actividad 5: Discriminación de cianobacterias vs. algas verdes (Chl-a vs. Ficocianina)**:
   Evaluación del desacople trófico entre estaciones dominadas por biomasa algal general vs. dominadas por cianobacterias.
6. **Actividad 6: Análisis limnológico y mapeo espacial en el Embalse San Roque**:
   Mapeo con Sentinel-2 L2A / Google Earth Engine, propagación de incertidumbre analítica e interpretación del gradiente ambiental.


---

## Referencias Bibliográficas Clave

* **Dall'Olmo, G., & Gitelson, A. A. (2005)**. Effect of bio-optical parameter variability on the remote estimation of chlorophyll-a concentration in turbid productive waters. *Applied Optics*, 44(3), 412–422. [DOI](https://doi.org/10.1364/AO.44.000412).
* **Dogliotti, A. I. et al. (2015)**. A single algorithm to retrieve turbidity from remotely-sensed data in all coastal and estuarine waters. *Remote Sensing of Environment*, 156, 157–168. [DOI](https://doi.org/10.1016/j.rse.2014.09.020).
* **Gitelson, A. A., Schalles, J. F., & Hladik, C. M. (2007)**. Remote chlorophyll-a retrieval in turbid, productive estuaries: Chesapeake Bay case study. *Remote Sensing of Environment*, 109(4), 464–472. [DOI](https://doi.org/10.1016/j.rse.2007.01.016).
* **Mobley, C. D. (1999)**. Estimation of the remote-sensing reflectance from above-surface measurements. *Applied Optics*, 38(36), 7442–7455. [DOI](https://doi.org/10.1364/AO.38.007442).
* **Mobley, C. D., Boss, E., & Roesler, C. (2011)**. *Ocean Optics Web Book*. [oceanopticsbook.info](https://www.oceanopticsbook.info/).
* **Nechad, B., Ruddick, K. G., & Park, Y. (2010)**. Calibration and validation of a generic multisensor algorithm for mapping of total suspended matter in turbid waters. *Remote Sensing of Environment*, 114(4), 854–866. [DOI](https://doi.org/10.1016/j.rse.2009.11.022).
* **Pahlevan, N. et al. (2021)**. ACIX-Aqua: A global assessment of atmospheric correction methods for Landsat-8 and Sentinel-2 over lakes, rivers, and coastal waters. *Remote Sensing of Environment*, 258, 112366. [DOI](https://doi.org/10.1016/j.rse.2021.112366).
* **Simis, S. G. H., Peters, S. W. M., & Gons, H. J. (2005)**. Remote sensing of the cyanobacterial pigment phycocyanin in turbid inland water. *Limnology and Oceanography*, 50(1), 237–245. [DOI](https://doi.org/10.4319/lo.2005.50.1.0237).

---

## Créditos e Institución

* **Autores**: Francisco Nemiña y Raul Rubio
* **Curso**: Teleobservación de Aguas Marinas, Costeras e Interiores.
* **Programa**: Escuela de Primavera 2026 (EDP 2026).
* **Institución**: Instituto de Altos Estudios Espaciales "Mario Gulich" (Comisión Nacional de Actividades Espaciales - CONAE / Universidad Nacional de Córdoba - UNC), Falda del Cañete, Córdoba, Argentina.
