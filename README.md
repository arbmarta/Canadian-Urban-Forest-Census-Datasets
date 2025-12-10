# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).  

The project integrates municipal boundary data, ecozone classifications, and national road network datasets to create a harmonized geospatial framework for assessing urban forest conditions across Canada. It includes both final analytical outputs and intermediate processing layers that support reproducibility, spatial validation, and transparent methodological documentation. Together, these datasets allow for consistent comparison of urban areas, detailed spatial attribution of ecological context, and robust quantification of road infrastructure patterns that influence urban forest structure and management needs. The repository is designed so that each stage of the workflow—from raw inputs to processed analytical products—can be traced, audited, and re-run entirely from source files.

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
| **census_subdivisions_2021** | .shp | `analysis.py` | Polygons (CBF – 2021 Census Boundary File) | Full national Census Subdivision boundary dataset used for selecting and processing urban CSDs. Must contain `CSDUID` and `CSDNAME`. |
| **eligible_csduid** | .csv | `analysis.py` | CSV | Table listing eligible CSDUIDs that meet Statistics Canada’s definition of urban census subdivisions. |
| **ecozones** | .shp | `analysis.py` | Polygons | National ecozone boundary file used for intersecting and assigning each CSD to an ecozone. Must contain `ZONE_NAME`. |
| **roads** | .shp; .gpkg | `roads.py` | Polylines | Intercensal 2024 road network used for clipping road segments to urban census subdivision boundaries. Loaded as `Datasets/Inputs/roads/roads.shp`. |

## Temporary Outputs  
*(Intermediate datasets created for efficiency or reuse, but not final products)*

| File Name (path) | File Type | Relevant Code | Source Format | Description |
|------------------|-----------|---------------|----------------|-------------|
| **intersecting_roads** | .gpkg | `roads.py` | Polylines | Road features that intersect any urban CSD, produced via spatial filtering. |
| **clipped_roads** | .gpkg | `roads.py` | Polylines | Road segments clipped to individual urban CSD boundaries (used to compute lengths). |
| **buffered_roads** | .gpkg | `roads.py` | Polygons | 20 m buffered road segments per CSD prior to dissolving overlaps. |

## Output Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `analysis.py` | `census_subdivisions_2021.shp` | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `analysis.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `analysis.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area (km²), assigned ecozone, dominance status, and percentage coverage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | `roads.shp` | Polylines | Road network features clipped to the 343 urban census subdivision boundaries. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Final dissolved road-buffer polygons representing 20 m buffered road segments within each urban census subdivision. |
| **road_lengths_by_csd** | .csv | `roads.py` | `clipped_roads.gpkg` | Tabular | Summarized road lengths (km) for each urban census subdivision, including CSDUID and CSDNAME. |

# Scripts
## `analysis.py`

`analysis.py` prepares the complete set of urban Census Subdivisions (CSDs) used in the Canadian Urban Forest Census. It filters the national CSD boundary file using Statistics Canada’s urban criteria, applies project-specific adjustments, computes land area, assigns each CSD to an ecozone, and generates the final spatial and tabular datasets used in subsequent analyses.

**High-level responsibilities:**
- Load the 2021 Census Subdivision boundary file, the list of eligible CSDUIDs, and the national ecozone boundaries.  
- Select urban CSDs using both the eligibility list and additional name-based rules.  
- Apply manual adjustments:  
  - Merge Lloydminster (AB + SK) into a single CSD.  
  - Merge Turner Valley and Black Diamond into “Diamond Valley.”  
  - Remove Petit-Rocher due to updated density falling below the urban threshold.  
- Compute geometric attributes, including land area in square kilometers.  
- Intersect each CSD with ecozones, calculate coverage percentages, and assign a dominant ecozone where coverage ≥ 50.01%.  
- Produce final outputs:  
  - `urban_csds.gpkg` / `.shp` (urban CSD polygons),  
  - `urban_csd_centroids.gpkg` / `.shp` (centroid points),  
  - `urban_csds_attributes.csv` (areas, ecozone assignment, dominance).  
- Generate QA summaries and optional maps for merged CSDs and multi-ecozone CSDs.

**Primary inputs:**  
`census_subdivisions_2021.shp`, `eligible_csduid.csv`, `ecozones.shp` (must include `ZONE_NAME`).  

**Primary outputs:**  
Urban polygons, centroids, and urban attribute tables used across the project.


## `roads.py`
`roads.py` processes the national road network to produce urban-specific road datasets. It identifies all road segments intersecting urban CSDs, clips them to municipal boundaries, computes road lengths per CSD, generates 20-metre road buffers, and outputs both intermediate and final spatial datasets.

**High-level responsibilities:**
- Load the national intercensal road network and the final processed urban CSD polygons.  
- Reproject roads to match the CSD CRS when necessary.  
- Spatially filter the road network to features that intersect any urban CSD (saved as `intersecting_roads.gpkg`).  
- Clip road features to individual CSD boundaries and save the results in `clipped_roads.gpkg`.  
- Calculate road lengths (m → km) for each CSD and export `road_lengths_by_csd.csv`.  
- Buffer clipped road segments by 20 metres, clip buffers to their respective CSDs, and save `buffered_roads.gpkg`.  
- Dissolve overlapping buffers within each CSD to create final contiguous buffer polygons, exported as `road_buffers.gpkg` and `.shp`.  
- Output QA metrics such as total CSDs with road coverage and summary statistics for road lengths.

**Primary inputs:**  
`roads.shp` (or `.gpkg` road network), `urban_csds.gpkg`.

**Primary outputs:**  
Clipped roads, buffered roads, dissolved road buffers, and per-CSD road-length summaries.
