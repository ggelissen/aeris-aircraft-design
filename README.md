# AERIS — Multidisciplinary Aircraft Design

Team repository for Group 17 of the 2025 Design Synthesis Exercise at the Faculty of Aerospace Engineering, Delft University of Technology.

The codebase supports the conceptual design and analysis of the AERIS aircraft through an integrated Python workflow covering aircraft sizing, aerodynamics, structures, propulsion, flight performance, optimisation, and design trade-offs.

> This is a collaborative student project and an archived engineering snapshot, not a certified aircraft-design tool. Outputs depend on modelling assumptions, empirical methods, and third-party analysis software and must not be used for safety-critical decisions.

## What the project demonstrates

- Iterative Class I and Class II aircraft sizing
- Thrust-to-weight versus wing-loading constraint analysis
- Wing-planform optimisation and fuel-burn trade-offs
- Aerodynamic, structural, propulsion, and flight-performance subsystem models
- Wing loading, stress, buckling, fatigue, and idealised cross-section analysis
- Stability and control calculations
- Multicriteria trade-off and sensitivity analysis
- XDSM-based representation of coupled design workflows
- Unit and system tests across several subsystems

## Integrated design flow

```text
Mission and design requirements
          ↓
Class I sizing and performance constraints
          ↓
Wing-planform optimisation
          ↓
Class II sizing and subsystem analyses
          ↓
Convergence and consistency checks
          ↓
Trade-off, sensitivity, and final design outputs
```

## Repository map

```text
analysis_loops/   design evaluation, iteration and optimisation
class1/           preliminary sizing and performance constraints
class2/           detailed sizing, weights, drag and design iteration
subsystems/       aerodynamics, structures, propulsion and flight performance
tradeoff/         multicriteria trade-off and sensitivity analysis
utils/            units and shared utilities
xdsm/             design-workflow diagrams
Figures/          selected engineering outputs
design_config.yaml
design_variables.py
```

## Gabriël Gelissen's contribution

This was a large team project and all project credit remains shared. The Git history contains approximately 90 commits under Gabriël's `ggelissen` author identities. Those commits are concentrated in:

- preliminary sizing and T/W–W/S performance constraints;
- aircraft design-variable integration and iterative workflow development;
- trade-off and sensitivity analysis;
- wing structural idealisation, stress analysis, and material selection;
- XDSM integration and engineering result visualisation; and
- cross-subsystem cleanup and integration work.

This section describes contribution areas visible in the public history; it does not imply sole authorship of the affected modules.

## Installation status

The repository includes local editable packages and several external engineering tools. The current `requirements.txt` is an environment note, not a clean or fully pinned installation recipe. Reproducing the complete pipeline may require platform-specific executables and licences.

A lightweight Python environment begins with:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

However, the current checkout must first be repaired: the SUAVE gitlink lacks a matching `.gitmodules` entry, and some bundled dependencies are expected at repository-local paths.

## Known repository limitations

- Generated aerodynamic results and solver binaries are committed and make the repository unusually large.
- Some third-party tools are platform-specific and may have separate licence restrictions.
- `data/GEO.DAT` and `data/geo.dat` collide on case-insensitive filesystems.
- The current dependency file does not pin versions.
- Some directories contain exploratory or outdated scripts retained from the design process.

## Licence and attribution

No top-level licence is currently declared. Copyright remains with the respective contributors, and bundled third-party components retain their own licences. Do not apply a blanket open-source licence without agreement from the team and an inventory of third-party material.
