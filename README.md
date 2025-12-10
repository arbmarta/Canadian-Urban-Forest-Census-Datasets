# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).  

The project integrates municipal boundary data, ecozone classifications, and national road network datasets to create a harmonized geospatial framework for assessing urban forest conditions across Canada.  
It includes both final analytical outputs and intermediate processing layers that support reproducibility, spatial validation, and transparent methodological documentation. Together, these datasets allow for consistent comparison of urban areas, detailed spatial attribution of ecological context, and robust quantification of road infrastructure patterns that influence urban forest structure and management needs. The repository is designed so that each stage of the workflow—from raw inputs to processed analytical products—can be traced, audited, and re-run entirely from source files.

# Output Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `analysis.py` | `census_subdivisions_2021.shp` | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `analysis.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `analysis.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area (km²), assigned ecozone, dominance status, and percentage coverage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | `roads.shp` | Polylines | Road network features clipped to the 343 urban census subdivision boundaries. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Final dissolved road-buffer polygons representing 20 m buffered road segments within each urban census subdivision. |
| **road_lengths_by_csd** | .csv | `roads.py` | `clipped_roads.gpkg` | Tabular | Summarized road lengths (km) for each urban census subdivision, including CSDUID and CSDNAME. |

# Determining Urban Areas
To determine urban municipalities, we use census subdivisions, which is Statistics Canada's dataset of municipal boundaries. We selected census subdivisions that meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

We then excluded Indigenous Communities because they operate under different governance structures.

Additional edits were performed after excluding non-urban and Indigenous census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city.  
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation.  
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.

# Input Datasets

| File Name | File Type | Relevant Code | Source Format | Description |
|-----------|-----------|----------------|----------------|-------------|
| **census_subdivisions_2021** | .shp | `analysis.py` | Polygons (CBF – 2021 Census Boundary File) | Full national Census Subdivision boundary dataset used for selecting and processing urban CSDs. Must contain `CSDUID` and `CSDNAME`. |
| **eligible_csduid** | .csv | `analysis.py` | CSV | Table listing eligible CSDUIDs that meet Statistics Canada’s definition of urban census subdivisions. |
| **ecozones** | .shp | `analysis.py` | Polygons | National ecozone boundary file used for intersecting and assigning each CSD to an ecozone. Must contain `ZONE_NAME`. |
| **roads** | .shp; .gpkg | `roads.py` | Polylines | Intercensal 2024 road network used for clipping road segments to urban census subdivision boundaries. Loaded as `Datasets/Inputs/roads/roads.shp`. |

# Temporary Outputs  
*(Intermediate datasets created for efficiency or reuse, but not final products)*

| File Name (path) | File Type | Relevant Code | Source Format | Description |
|------------------|-----------|---------------|----------------|-------------|
| `Datasets/Outputs/roads/intersecting_roads.gpkg` | .gpkg | `roads.py` | Polylines | Road features that intersect any urban CSD, produced via spatial filtering. |
| `Datasets/Outputs/roads/clipped_roads.gpkg` | .gpkg | `roads.py` | Polylines | Road segments clipped to individual urban CSD boundaries (used to compute lengths). |
| `Datasets/Outputs/roads/buffered_roads.gpkg` | .gpkg | `roads.py` | Polygons | 20 m buffered road segments per CSD prior to dissolving overlaps. |
