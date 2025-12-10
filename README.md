# Description
This repository houses files used in the analysis of the Canadian Urban Forest Census (2025).

# Datasets


| File Name | File Type | Relevant Code | Source File | Source Format | Description |
|-----------|-----------|----------------|-------------|----------------|-------------|
| **census_subdivisions_2021** | .shp | `analysis.py` | 2021 Census Subdivision Boundary File | Cartographic Boundary File (CBF) | Input layer containing all 2021 census subdivision polygons. |
| **eligible_csduid** | .csv | `analysis.py` | Eligible CSDUID list | CSV | Input table identifying CSDs meeting preliminary eligibility for urban classification. |
| **ecozones** | .shp | `analysis.py` | National ecozone boundary file | Polygons | Input ecozone polygons used for spatial intersection and ecozone assignment. |
| **urban_csds** | .shp; .gpkg | `analysis.py` | Census Subdivision Boundary File | Cartographic Boundary File (CBF) | Final processed polygons representing 343 non-Indigenous urban census subdivisions. |
| **urban_csd_centroids** | .shp; .gpkg | `analysis.py` | `urban_csds.gpkg` | Polygons | Centroids generated from the urban census subdivision polygons. |
| **urban_csds_attributes** | .csv | `analysis.py` | `urban_csds.gpkg` | Tabular | Attribute table containing CSDUID, CSDNAME, land area, assigned ecozone, dominance status, and coverage percentage. |
| **clipped_roads** | .shp; .gpkg | `roads.py` | 2024 Intercensal Road Network File | Polylines | Road network clipped to the boundaries of the 343 urban census subdivisions. |
| **road_buffers** | .shp; .gpkg | `roads.py` | `clipped_roads.gpkg` | Polylines | Buffered versions of clipped road features. |


## Determining Urban Areas
To determine urban municipalities, we use census subdivisions, which is Statistics Canada's dataset of municipal boundaries. We selected census subdivisions that meet the definition of urban used by Statistics Canada:

> Urban areas are those continuously built-up areas having a minimum population concentration of 1,000 persons and a population density of at least 400 persons per square kilometer based on the previous census. (Statistical Classifications: Urban and rural areas - 'Urban' versus 'rural' variant)

We then excluded Indigenous Communities because they operate under different governance structures.

Additional edits were performed after excluding non-urban and Indigenous census subdivisions:
1. The two Lloydminster parts (Alberta and Saskatchewan) were merged as it represents one inter-provincial city
2. Turner Valley and Black Diamond, Alberta were merged in keeping with their amalgamation
3. Petit-Rocher, New Brunswick was removed as its new land area results in a population density below the definition of urban used by Statistics Canada.
