# Fault Monitoring

**Automated fault-zone seismicity monitoring and visualization for major active fault systems in Iran**

Monitoring seismic activity along active faults is essential for understanding earthquake patterns, identifying seismic clusters, tracking temporal variations, and supporting geological and geophysical investigations. With earthquake information continuously reported by multiple international and regional seismic networks, a unified monitoring framework provides an efficient way to analyze fault-related seismicity in near real time.

This repository provides an automated workflow for collecting, updating, processing, and visualizing earthquake catalogs from multiple seismic agencies for selected active fault systems across Iran.

---

## Overview

Iran Faults Monitor integrates earthquake data from several authoritative seismic networks and generates fault-specific seismicity maps and analytical products.

The system automatically:

* Downloads and updates earthquake catalogs
* Merges data from multiple seismic agencies
* Filters events based on fault regions
* Generates seismicity distribution maps
* Produces density-stripe visualizations
* Creates publication-quality figures
* Supports continuous fault monitoring workflows

---

## Data Sources

Earthquake information is retrieved from:

* United States Geological Survey (USGS)
* International Seismological Centre (ISC)
* Institute of Geophysics, University of Tehran (IRSC)
* International Institute of Earthquake Engineering and Seismology (IIEES)
* Kandilli Observatory and Earthquake Research Institute (KOERI)

Bathymetric and topographic background data are derived from:

* GEBCO

---

## Monitored Fault Systems

The repository currently supports monitoring of the following major fault zones:

| Fault Zone  |
| ----------- |
| AVAJ        |
| BAM-RAVAR   |
| DAMAVAND    |
| DEHSHIR     |
| IPAK        |
| KAZEROON    |
| KERMAN      |
| KOPEDAGH    |
| KUHBANAN    |
| NE-LUT      |
| NEYSHABUR   |
| QOM         |
| SABZVAR     |
| SEIMARE     |
| SEMNAN      |
| SHAHRUD     |
| TEHRAN      |
| TURKMANCHAY |
| VAN-TABRIZ  |
| WEST-LUT    |
| ZAGROS      |

---

## Repository Structure

```text
.
├── LICENSE
├── README.md
├── iran_faults_monitor_v5.py
│
├── update_iiees_database.sh
├── update_iiees_v2.py
├── update_irsc_database_v6.sh
├── update_isc_database_v1.sh
├── update_koeri_database.sh
└── update_usgs_database_v1.sh
```

### Main Components

| File                         | Description                                |
| ---------------------------- | ------------------------------------------ |
| `iran_faults_monitor_v5.py`  | Main processing and visualization workflow |
| `update_usgs_database_v1.sh` | Update USGS earthquake catalog             |
| `update_isc_database_v1.sh`  | Update ISC earthquake catalog              |
| `update_irsc_database_v6.sh` | Update IRSC earthquake catalog             |
| `update_iiees_database.sh`   | Update IIEES earthquake catalog            |
| `update_iiees_v2.py`         | IIEES catalog processing utilities         |
| `update_koeri_database.sh`   | Update KOERI earthquake catalog            |

---

## Generated Products

For each monitored fault zone, the system can generate:

### Seismicity Maps

Spatial distribution of earthquakes along and around the fault system, including magnitude-dependent visualization and regional tectonic context.

### Density-Stripe Analysis

Visualization of earthquake concentration patterns along fault strike, highlighting seismic clusters and potential segmentation.

### Temporal Monitoring Outputs

Updated seismicity catalogs suitable for ongoing fault activity assessment.

### Publication-Quality Figures

High-resolution maps designed for research reports, conference presentations, and scientific publications.

---

## Example Outputs

### Seismic Density Maps

<img width="1974" height="1410" alt="SABZVAR_DS_7" src="https://github.com/user-attachments/assets/acf7b704-109f-4fdf-958e-1563aa30f393" />

<img width="1974" height="1410" alt="SEIMARE_DS_7" src="https://github.com/user-attachments/assets/eab46af8-6500-479e-b2a2-1a9bda5318aa" />

<img width="1939" height="2059" alt="ZAGROS_seis_7" src="https://github.com/user-attachments/assets/a34ff6dd-be43-4340-a1e6-4b367ff1b7c0" />

<img width="1944" height="2793" alt="NE-LUT_seis_7" src="https://github.com/user-attachments/assets/57b0cc88-4c5b-496b-a788-e1014fb4ffc4" />

### Density Stripe Visualizations

<img width="1939" height="2059" alt="ZAGROS_stripe_7" src="https://github.com/user-attachments/assets/8e5fb015-f587-4585-8c86-3cfae33242d5" />

### Legend and Supporting Graphics

<img width="1935" height="2032" alt="KOPEDAGH_legend" src="https://github.com/user-attachments/assets/cf03255b-6de3-4a93-a396-c24efc6812b1" />

The repository produces high-resolution figures similar to the examples shown above, enabling rapid visual assessment of seismic activity patterns across Iran's major active fault zones.

---

## Applications

This project can be used for:

* Active fault monitoring
* Seismic hazard assessment
* Earthquake clustering analysis
* Tectonic investigations
* Fault segmentation studies
* Academic research
* Earthquake catalog integration
* Educational and outreach activities

---

## Scientific Motivation

Iran is located within the active collision zone between the Arabian and Eurasian plates and hosts numerous seismically active fault systems. Continuous monitoring of earthquake occurrence along these faults provides valuable insights into crustal deformation, seismic hazard, and regional tectonic processes.

By integrating multiple seismic catalogs into a unified framework, this repository facilitates systematic monitoring of fault-related seismicity and supports reproducible geoscientific research.

---

## Citation

If you use this repository in scientific work, please cite the corresponding publication or reference this repository appropriately.

```bibtex
@software{Fault_Monitoring,
  title={Fault_Monitoring},
  author={Fariba Khosravani, Mahdi Farmahinifarahani},
  year={2026},
  url={https://github.com/faribakhosravani/Fault_Monitoring/tree/main}
}
```

---

## License

This project is distributed under the terms specified in the `LICENSE` file.

---

**Fault Monitoring Matters.** Continuous observation of seismicity along active fault systems provides critical information for understanding earthquake behavior, improving hazard assessments, and advancing tectonic research across Iran and the surrounding region.
