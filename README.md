# Description
This repository houses all datasets and processing scripts used in the Canadian Urban Forest Census (2025). The project integrates municipal boundaries, national roadway infrastructure, ecozone classifications, and high-resolution canopy data to build a comprehensive geospatial framework for analyzing urban forest conditions across Canada. 

The workflow begins by identifying and preparing all qualifying urban Census Subdivisions (CSDs), applying Statistics Canada’s urban criteria along with essential administrative edits. These standardized urban polygons serve as the foundation for additional spatial products, including centroid point layers, ecozone assignments, clipped road networks, and dissolved 20-metre road-buffer geometries.

Using high-resolution Meta 1-m Canopy Height data, the project then derives canopy metrics for each urban CSD as well as for road-adjacent buffer zones, enabling assessment of canopy distribution both across municipalities and within transportation corridors. The repository captures every stage of this workflow—from raw inputs to final analytical outputs—to ensure complete transparency, reproducibility, and scalability for future urban forest assessments.

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

## Output Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `census_subdivisions.py` | Census Subdivision Boundary File (2021) | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `census_subdivisions.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `census_subdivisions.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area, assigned ecozone, dominance status, and percent ecozone coverage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network features clipped to urban census subdivision boundaries. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Final dissolved 20 m buffer polygons representing buffered road segments within each urban census subdivision. |
| **road_lengths_by_csd** | .csv | `roads.py` | `clipped_roads.gpkg` | Tabular | Summarized road lengths (km) for each urban census subdivision. |
| **canopy_metrics_urban_csds** | .csv | `canopy_metrics.js` | `urban_csds` | Tabular | Canopy area (km²) and canopy percentage for each urban census subdivision based on Meta 1-m canopy height data. |
| **canopy_metrics_road_buffers** | .csv | `canopy_metrics.js` | `road_buffers` | Tabular | Canopy area (km²) and canopy percentage within dissolved 20 m road-buffer zones for each CSD. |

# Scripts
## `census_subdivisions.py`

`census_subdivisions.py` prepares the complete set of urban Census Subdivisions (CSDs) used in the Canadian Urban Forest Census. It filters the national CSD boundary file using Statistics Canada’s urban criteria, applies project-specific adjustments, computes land area, assigns each CSD to an ecozone, and generates the final spatial and tabular datasets used in subsequent analyses.

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

## `canopy_metrics.js`
`canopy_metrics.js` (Google Earth Engine script) calculates canopy coverage metrics for spatial units derived from this project. The script is flexible and can use **either the final `urban_csds` polygons** or the **`road_buffers` polygons** as its input layer. When run on `urban_csds`, the script computes canopy statistics for entire municipal areas. When run on `road_buffers`, it instead analyzes canopy coverage within road-adjacent buffer zones. The choice of input directly influences the resulting area values and canopy percentages.

**High-level responsibilities:**
- Load the selected input layer (`urban_csds` or `road_buffers`) from Google Earth Engine assets.  
- Load and mosaic the Meta 1-m Canopy Height Model (`CanopyHeight`) dataset.  
- Create a binary canopy mask where vegetation ≥ 2 m is classified as canopy.  
- For each spatial unit (CSD polygon or buffer polygon), compute:  
  - Total area (km²),  
  - Total canopy area (km²),  
  - Canopy proportion (%) based on 1-m pixel area.  
- Append canopy metrics as new attributes to each feature.  
- Display optional QA layers (canopy mask, polygons).  
- Export a table of canopy metrics (`ID`, `total_area_km2`, `canopy_area_km2`, `canopy_proportion`) as a CSV to Google Drive.

**Primary inputs:**  
- **Option 1:** `projects/heroic-glyph-383701/assets/urban_csds`  
  *(computes canopy metrics for entire urban municipalities)*  
- **Option 2:** `projects/heroic-glyph-383701/assets/road_buffers`  
  *(computes canopy metrics within 20-m dissolved road buffer zones)*  
- Canopy height model: `projects/meta-forest-monitoring-okw37/assets/CanopyHeight`

**Primary outputs:**  
A FeatureCollection enriched with canopy attributes, and an exported CSV summarizing canopy area and canopy percentage for each polygon (CSD or buffer, depending on input).
