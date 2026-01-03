## Description

This repository houses all datasets, scripts, and workflows used in the **Canadian Urban Forest Census (2025)**. The project integrates municipal boundaries, national roadway infrastructure, ecozone classifications, high-resolution canopy data, and census demographics to build a comprehensive geospatial framework for assessing urban forest conditions across Canada.

The workflow begins by identifying all qualifying urban Census Subdivisions (CSDs), using Statistics Canada’s urban criteria and applying targeted administrative adjustments (e.g., amalgamations and exclusions). These finalized urban polygons form the foundation for all subsequent spatial products, including centroid point layers, ecozone assignments, clipped road networks, and dissolved road buffer geometries (10 m and 20 m).

Using Meta’s 1-m Canopy Height Model, the project computes detailed canopy metrics at multiple spatial scales:
- Across full urban CSDs
- Within 10 m and 20 m transportation buffer zones

Outputs include road-length summaries, ecozone coverage statistics, and merged demographic attributes, enabling integrated analyses of tree cover, equity, infrastructure, and ecological region.

The repository captures every stage of this workflow—from raw input data to final analytical tables—to ensure transparency, reproducibility, and scalability for future urban forest research and policy development.

# Determining Urban Areas
To determine urban municipalities, we use census subdivisions, which is Statistics Canada's dataset of municipal boundaries. We selected census subdivisions that meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

We then excluded Indigenous Communities because they operate under different governance structures.

Additional edits were performed after excluding non-urban and Indigenous census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city.  
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation.  
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.

# Datasets

## Input Datasets

| File Name | File Type | Relevant Code | Source Format | Description |
|-----------|-----------|----------------|----------------|-------------|
| **census_subdivisions_2021** | .shp | `census_subdivisions.py` | Polygons (CBF – 2021 Census Boundary File) | Full national Census Subdivision boundary dataset used for identifying and processing urban CSDs. |
| **eligible_csduid.csv** | .csv | `census_subdivisions.py` | CSV | Table listing CSDUIDs that meet Statistics Canada’s criteria for inclusion as urban census subdivisions. |
| **ecozones** | .shp | `census_subdivisions.py` | Polygons | National ecozone boundary file used for intersecting and assigning each CSD to an ecozone. Must contain `ZONE_NAME`. |
| **roads** | .shp; .gpkg | `roads.py` | Polylines | Intercensal 2024 road network used for clipping and buffering road segments. |
| **meta_canopy_height_model** | EE Asset | `canopy_metrics.js` | Raster (1 m resolution) | Meta 1-m Canopy Height Model used to generate canopy ≥ 2 m binary layers and calculate canopy coverage metrics. |
| **provinces_simplified_1km.gpkg** | .gpkg | `mapping.py` | Polygons | Generalized provincial boundaries for optional cartographic or reference purposes. Not directly used in core processing scripts. |
| **amalgamated_cities.csv** | .csv | `census_of_population.py` | Tabular | Lookup table of municipal amalgamations used in Census 2021. May support QA or historical alignment. |
| **indigenous_identity.csv** | .csv | `census_of_population.py` | Tabular | Census 2021 counts of Indigenous identity by CSD. Potential future use for exclusion, analysis, or mapping. |
| **labour.csv** | .csv | `census_of_population.py` | Tabular | Labour force statistics from Census 2021 by CSD. May support socioeconomic analyses of urban forests. |
| **population.csv** | .csv | `census_of_population.py` | Tabular | Population counts and densities from Census 2021. May duplicate or supplement existing metrics. |
| **visible_minorities.csv** | .csv | `census_of_population.py` | Tabular | Demographic distribution of visible minority groups by CSD. May support future equity-focused analyses. |

## Temporary Outputs  
*(Intermediate datasets created for efficiency or reuse, but not final products)*

| File Name (path) | File Type | Relevant Code | Source Format | Description |
|------------------|-----------|---------------|----------------|-------------|
| **intersecting_roads** | .gpkg | `roads.py` | Polylines | Road features that intersect any urban CSD, produced via spatial filtering. |
| **clipped_roads** | .gpkg | `roads.py` | Polylines | Road segments clipped to individual urban CSD boundaries (used to compute lengths). |
| **buffered_roads** | .gpkg | `roads.py` | Polygons | 20 m buffered road segments per CSD prior to dissolving overlaps. |
| **10m_buffers/export \*** | .csv | `canopy_metrics.js` | Tabular | Intermediate GEE CSV exports representing canopy coverage in 10-m road buffer zones, organized in batches for parallel processing. |
| **20m_buffers/export \*** | .csv | `canopy_metrics.js` | Tabular | Intermediate GEE CSV exports representing canopy coverage in 20-m road buffer zones, organized in batches for parallel processing. |

## Output Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `census_subdivisions.py` | Census Subdivision Boundary File (2021) | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `census_subdivisions.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes.csv** | .csv | `census_subdivisions.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area, assigned ecozone, dominance status, and percent ecozone coverage. |
| **clipped_roads.gpkg** | .gpkg | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network features clipped to urban census subdivision boundaries. |
| **road_buffers_20m.gpkg** | .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Final dissolved 20 m buffer polygons representing buffered road segments within each urban census subdivision. |
| **road_buffers_10m.gpkg** | .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Optional dissolved 10 m buffer polygons for comparative or sensitivity analyses. |
| **road_lengths_by_csd.csv** | .csv | `roads.py` | `clipped_roads.gpkg` | Tabular | Summarized road lengths (km) for each urban census subdivision. |
| **canopy_cover_csd.csv** | .csv | `canopy_metrics.js` | `urban_csds` | Tabular | Canopy area (km²) and canopy percentage for each urban census subdivision based on Meta 1-m canopy height data. |
| **canopy_cover_road_buffers_20m.csv** | .csv | `canopy_metrics.js` | `road_buffers_20m.gpkg` | Tabular | Canopy area (km²) and canopy percentage within 20-m dissolved road-buffer zones for each CSD. |
| **canopy_cover_road_buffers_10m.csv** | .csv | `canopy_metrics.js` | `road_buffers_10m.gpkg` | Tabular | Canopy area (km²) and canopy percentage within 10-m dissolved road-buffer zones for each CSD. |
| **Canadian_urban_forest_census_independent_variables.csv** | .csv | `merged_datasets.py` | Aggregated outputs | Tabular | Merged dataset containing key urban forest and infrastructure variables for statistical or regression analysis. |

# Scripts Documentation

This directory contains the core processing scripts for analyzing urban canopy coverage across Canadian municipalities.

---

## 📊 Overview

The pipeline consists of three main components:

1. **Spatial Processing** (`urban_csds.py`, `roads.py`) — Prepare municipal boundaries and road networks
2. **Canopy Analysis** (`canopy_metrics.js`) — Calculate vegetation metrics using Google Earth Engine
3. **Data Integration** (`dataset_merge.py`) — Consolidate outputs into a unified dataset

---

## 🗂️ Script Details

### `urban_csds.py`

**Purpose:** Identify and process eligible urban Census Subdivisions (CSDs) across Canada

Consolidates demographic data from the 2021 Census of Population with spatial boundaries and ecological classifications to create a comprehensive dataset of urban municipalities.

#### Key Responsibilities

- Load and merge demographic datasets from the 2021 Census (population, labour, Indigenous identity, visible minorities)
- Filter CSDs using urban criteria: **≥1,000 population** and **≥400 people/km²**
- Exclude Indigenous reserves and non-standard CSDs based on naming patterns
- Handle amalgamated cities by merging geometries (e.g., Lloydminster, Diamond Valley)
- Assign each urban CSD to a dominant ecozone based on spatial intersection
- Calculate ecozone coverage percentages and flag CSDs without dominant zones
- Generate national and regional maps with ecozone boundaries
- Export outputs in multiple formats (Shapefile, GeoPackage)

#### Inputs

```
Datasets/Inputs/2021_census_of_population/
├── population.csv
├── labour.csv
├── indigenous_identity.csv
├── visible_minorities.csv
└── amalgamated_cities.csv

Datasets/Inputs/census_subdivisions_2021/
└── census_subdivisions_2021.shp

Datasets/Inputs/ecozone_shp/
└── ecozones.shp

Datasets/Inputs/provinces/
└── provinces_simplified_1km.gpkg
```

#### Outputs

```
Datasets/Outputs/2021_census_of_population/
└── 2021_census_of_population_municipalities.csv

Datasets/Outputs/urban_csds/
├── urban_csds.shp
├── urban_csds.gpkg
└── urban_csds_attributes.csv

Datasets/Outputs/urban_csd_centroids/
├── urban_csd_centroids.shp
└── urban_csd_centroids.gpkg

figures/eligible_csds/
├── eligible_csds_nationally.pdf
├── eligible_csds_british_columbia.pdf
├── eligible_csds_prairies.pdf
├── eligible_csds_ontario.pdf
├── eligible_csds_quebec.pdf
└── eligible_csds_atlantic_canada.pdf
```

#### Features

- **Urban Criteria:** Population ≥1,000 and density ≥400 people/km²
- **Indigenous Exclusion:** Removes CSDs with numeric characters in names plus specific exclusions (PETIT-ROCHER, WENDAKE)
- **Amalgamation Handling:** Merges geometries for border cities and consolidated municipalities
- **Ecozone Assignment Logic:**
  - Single ecozone intersection → direct assignment (100% coverage)
  - Multiple ecozones → assigns dominant zone if ≥50.01% coverage
  - Flags CSDs with no dominant ecozone as assignment errors
- **QA Checks:** Reports filtering results, amalgamation changes, and multi-ecozone CSDs

#### Ecozone Color Scheme

Ecozones are grouped into six categories:

| Group | Ecozones |
|-------|----------|
| **Arctic** | Arctic Cordillera, Northern Arctic, Southern Arctic |
| **Subarctic** | Taiga Shield, Hudson Plain |
| **Forested** | MixedWood Plain, Boreal Shield, Boreal Plain, Taiga Cordillera, Taiga Plain, Boreal Cordillera |
| **Mountain** | Montane Cordillera |
| **Prairie** | Prairie |
| **Maritime** | Pacific Maritime, Atlantic Maritime |

#### Regional Definitions

Maps are generated for five regions:

- **British Columbia:** PRUID 59
- **Prairies:** Alberta (48), Saskatchewan (47), Manitoba (46)
- **Ontario:** PRUID 35
- **Québec:** PRUID 24
- **Atlantic Canada:** NL (10), PE (11), NS (12), NB (13)

---

### `roads.py`

**Purpose:** Process the national road network to generate municipality-specific metrics and buffer zones

Creates buffered geometries around road segments for canopy analysis, with configurable buffer distances.

#### Key Responsibilities

- Load and reproject the national road network to match urban CSD coordinate reference system
- Filter roads to include only segments that intersect urban municipalities
- Clip road segments to their respective CSD boundaries
- Compute per-CSD road lengths (in kilometers) and export summary
- Create road buffers at user-defined distance (default: 20 m)
- Clip buffered segments to municipal boundaries
- Dissolve overlapping buffers within each CSD to create contiguous zones
- Export outputs in GeoPackage and Shapefile formats

#### Inputs

```
Datasets/Inputs/roads/
└── roads.shp

Datasets/Outputs/urban_csds/
└── urban_csds.gpkg
```

#### Outputs

```
Datasets/Outputs/roads/
├── intersecting_roads.gpkg         # Filtered road segments intersecting urban areas
├── clipped_roads.gpkg              # Roads clipped to CSD boundaries
├── road_lengths_by_csd.csv         # Total road length (km) per CSD
└── road_buffers_XXm/               # Buffer outputs (XX = buffer distance)
    ├── buffered_roads_XXm.gpkg     # Unmerged buffers per segment
    ├── road_buffers_XXm.gpkg       # Final dissolved buffer polygons (GeoPackage)
    └── road_buffers_XXm.shp        # Final dissolved buffer polygons (Shapefile)
```

> **Note:** `XXm` refers to the buffer distance in meters (e.g., `10m` or `20m`)

#### Features

- **Caching:** Skips reprocessing if intermediate files already exist
- **Progress Tracking:** Uses `tqdm` for visual progress during clipping and buffering
- **Geometry QA:** Warns about CSDs with less than 100 km of road length
- **Safe Handling:** Type checks and fallback matching for `CSDUID` to avoid errors
- **Export Compatibility:** Shortens field names for shapefile compliance

#### Switching Buffer Sizes

Change the `BUFFER_DISTANCE_M` variable at the top of the script:

```python
BUFFER_DISTANCE_M = 10  # or 20
```

Then re-run the script to regenerate datasets for the new buffer distance.

---

### `canopy_metrics.js`

**Purpose:** Calculate canopy coverage metrics using Google Earth Engine

A GEE script that processes input geometries in batches to compute total area, canopy area (≥2 m), and canopy proportion for each spatial unit.

#### Key Responsibilities

- Load selected spatial input layer from GEE assets:
  - `urban_csds` — full municipal areas
  - `road_buffers_10m` — 10-metre road buffer zones
  - `road_buffers_20m` — 20-metre road buffer zones
- Exclude user-defined CSDUIDs (if applicable)
- Load and mosaic the Meta 1-m Canopy Height Model
- Reproject all data to Statistics Canada Lambert projection (EPSG:3347)
- Create binary canopy mask (1 if canopy height ≥2 m, else 0)
- Divide input dataset into batches for scalable processing
- For each feature in current batch:
  - Compute total area and canopy area in square kilometers
  - Calculate canopy proportion as percentage
  - Append metrics as new attributes
- Display QA layers and export results to CSV

#### Batching Logic

The script processes features in batches to avoid computation limits:

- **Batch Size:** Number of features per run (e.g., 50)
- **Batch Number:** Current batch index (starting at 0)
- **Manual Increment:** You must update `batchNumber` for each export

#### Inputs

**Spatial layers** (choose one):
```
projects/heroic-glyph-383701/assets/urban_csds
projects/heroic-glyph-383701/assets/road_buffers_10m
projects/heroic-glyph-383701/assets/road_buffers_20m
```

**Canopy height model:**
```
projects/meta-forest-monitoring-okw37/assets/CanopyHeight
```

#### Outputs

CSV files with columns: `CSDUID`, `total_area_km2`, `canopy_area_km2`, `canopy_proportion`

Filename format: `canopy_cover_road_buffer_batch_<batchNumber>.csv`

#### Key Variables

```javascript
excludeList  // Optional array of CSDUIDs to exclude
batchSize    // Number of features per batch (e.g., 50)
batchNumber  // Current batch index (starting at 0)
```

#### Optional QA Displays

- Binary canopy raster (green)
- Input geometry layers: full vs. current batch (blue and red)

---

### `dataset_merge.py`

**Purpose:** Consolidate all project outputs into a unified dataset

Merges spatial attributes, road metrics, canopy metrics, and demographic indicators into a single table for analysis.

#### Key Responsibilities

- Load datasets:
  - Urban CSD attributes
  - Road length summaries
  - Canopy metrics for CSDs and buffer zones (10 m and 20 m)
  - 2021 Census of Population for urban municipalities
- Add suffixes to column names to prevent conflicts:
  - `_csd`, `_10m_buffer`, `_20m_buffer`
- Perform inner joins across all datasets on `CSDUID`
- Check for:
  - Mismatches in `CSDNAME` fields
  - Rows with `dominant_ecozone` ≠ `"Yes"`
- Drop or preserve `dominant_ecozone` based on QA results
- Rename columns for clarity
- Export final merged dataset

#### Inputs

```
Datasets/Outputs/urban_csds/
└── urban_csds_attributes.csv

Datasets/Outputs/roads/
└── road_lengths_by_csd.csv

Datasets/Outputs/gee_export/
├── canopy_cover_csd.csv
├── canopy_cover_road_buffers_10m.csv
└── canopy_cover_road_buffers_20m.csv

Datasets/Outputs/2021_census_of_population/
└── 2021_census_of_population_municipalities.csv
```

#### Output

```
Datasets/Outputs/
└── Canadian_urban_forest_census_independent_variables.csv
```

A comprehensive table combining spatial, ecological, and demographic metrics for all urban municipalities.

#### QA Checks

- Detects CSDs without dominant ecozone (< 50.01% coverage)
- Confirms column renaming for fields present in data
- Handles discrepancies in duplicate name fields
- Warns about remaining raw columns

#### Use Cases

- Regression modeling of urban canopy cover
- Equity assessments of green infrastructure
- Geospatial correlation analyses
- Dashboard or report-ready data publishing

---

## 🔄 Processing Workflow

```
1. urban_csds.py
   ↓ Identifies eligible municipalities
   ↓ Assigns ecozones
   
2. roads.py
   ↓ Processes road network
   ↓ Creates buffer zones
   
3. canopy_metrics.js (Google Earth Engine)
   ↓ Calculates canopy metrics
   ↓ Processes in batches
   
4. dataset_merge.py
   ↓ Consolidates all outputs
   ↓ Final dataset ready for analysis
```

---

## 📦 Dependencies

### Python Libraries
- `geopandas`, `pandas`, `numpy`
- `shapely`, `pyproj`
- `matplotlib`, `contextily`
- `tqdm`

### External Tools
- Google Earth Engine (for `canopy_metrics.js`)

---

## 📝 Notes

- All spatial data uses EPSG:3347 (Statistics Canada Lambert Conformal Conic)
- Road buffer distances can be switched by modifying `BUFFER_DISTANCE_M` in `roads.py`
- GEE batch processing requires manual increment of `batchNumber` for each export
- Final merged dataset includes suffixes to distinguish canopy metrics by spatial unit
