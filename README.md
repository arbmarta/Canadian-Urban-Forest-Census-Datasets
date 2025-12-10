# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).

# Datasets

| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **urban_csds** | .shp; .gpkg | `analysis.py` | Census Subdivision Boundary File (2021) | Polygons | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `analysis.py` | `urban_csds.gpkg` | Points | Centroids generated from the final urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `analysis.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area, assigned ecozone, dominance status, and percentage coverage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network features clipped to the 343 urban census subdivision boundaries. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polygons | Final dissolved buffer polygons representing buffered road segments within each urban census subdivision. |
| **road_lengths_by_csd** | .csv | `roads.py` | `clipped_roads.gpkg` | Tabular | Summarized road lengths (km) for each urban census subdivision, including CSDUID and CSDNAME. |

# Determining Urban Areas
To determine urban municipalities, we use census subdivisions, which is Statistics Canada's dataset of municipal boundaries. We selected census subdivisions that meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

We then excluded Indigenous Communities because they operate under different governance structures.

Additional edits were performed after excluding non-urban and Indigenous census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.

# Input Datasets

| File Name | File Type | Relevant Code | Source Format | Description |
|-----------|-----------|----------------|----------------|-------------|
| **census_subdivisions_2021** | .shp | `analysis.py` | Polygons (CBF – 2021 Census Boundary File) | Full national Census Subdivision boundary dataset used as the base layer for selecting and processing urban CSDs. |
| **eligible_csduid** | .csv | `analysis.py` | CSV | Table listing eligible CSDUIDs that meet the criteria for inclusion as urban census subdivisions. |
| **ecozones** | .shp | `analysis.py` | Polygons | National ecozone boundary file used for intersecting and assigning each CSD to an ecozone. |
| **road_network_2024** | .shp; .gpkg | `roads.py` | Polylines | Intercensal 2024 road network used for clipping road segments to urban census subdivision boundaries. |

# Temporary Outputs  
*(Intermediate datasets created for efficiency or reuse, but not final products)*

| File Name (path) | File Type | Relevant Code | Source Format | Description |
|------------------|-----------|---------------|----------------|-------------|
| `Datasets/Outputs/roads/intersecting_roads.gpkg` | .gpkg | `roads.py` | Polylines | Roads that intersect any urban CSD, produced via spatial filtering. |
| `Datasets/Outputs/roads/buffered_roads.gpkg` | .gpkg | `roads.py` | Polygons | 20 m buffered road segments per CSD before dissolving overlaps. |
