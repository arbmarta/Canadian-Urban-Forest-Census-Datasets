import rasterio
from pyproj import Transformer
import numpy as np

# Open the raster
precip_path = 'Datasets/Inputs/climate/average_annual_precip_mm_1991_2020.tif'

with rasterio.open(precip_path) as src:
    print("=" * 70)
    print("RASTER PIXEL SIZE CALCULATION")
    print("=" * 70)

    # Get raster properties
    crs = src.crs
    res = src.res  # Resolution in the raster's native units
    bounds = src.bounds  # Extent of raster

    print(f"\nRaster CRS: {crs}")
    print(f"Resolution in native units: {res[0]:.8f} × {res[1]:.8f}")
    print(f"Native units: {'degrees' if crs.is_geographic else 'meters'}")

    if crs.is_geographic:
        print("\n--- Geographic CRS Detected (lat/lon in degrees) ---")

        # Get center of raster to calculate at representative latitude
        center_lon = (bounds.left + bounds.right) / 2
        center_lat = (bounds.bottom + bounds.top) / 2
        print(f"\nRaster center: {center_lat:.2f}°N, {center_lon:.2f}°W")

        # Calculate pixel size at the center latitude
        # Create transformer to convert degrees to meters (using EPSG:3857 Web Mercator as proxy)
        transformer = Transformer.from_crs(crs, "EPSG:3857", always_xy=True)

        # Get corners of a single pixel at the center of the raster
        pixel_corners = [
            (center_lon, center_lat),  # Bottom-left
            (center_lon + res[0], center_lat),  # Bottom-right
            (center_lon, center_lat + abs(res[1])),  # Top-left
            (center_lon + res[0], center_lat + abs(res[1]))  # Top-right
        ]

        # Transform to meters
        corners_meters = [transformer.transform(lon, lat) for lon, lat in pixel_corners]

        # Calculate pixel dimensions in meters
        width_m = corners_meters[1][0] - corners_meters[0][0]
        height_m = corners_meters[2][1] - corners_meters[0][1]

        # Convert to km
        width_km = width_m / 1000
        height_km = height_m / 1000
        pixel_area_km2 = (width_km * height_km)

        print(f"\n📏 ACTUAL PIXEL SIZE (at raster center, ~{center_lat:.0f}°N):")
        print(f"   Width:  {width_km:.2f} km")
        print(f"   Height: {height_km:.2f} km")
        print(f"   Area:   {pixel_area_km2:.2f} km²")

        # Also calculate at typical Canadian latitudes
        print(f"\n📏 PIXEL SIZE AT DIFFERENT CANADIAN LATITUDES:")

        for lat in [45, 50, 55, 60]:
            transformer = Transformer.from_crs(crs, "EPSG:3857", always_xy=True)

            pixel_corners = [
                (center_lon, lat),
                (center_lon + res[0], lat),
                (center_lon, lat + abs(res[1])),
                (center_lon + res[0], lat + abs(res[1]))
            ]

            corners_meters = [transformer.transform(lon, lat) for lon, lat in pixel_corners]
            width_m = corners_meters[1][0] - corners_meters[0][0]
            height_m = corners_meters[2][1] - corners_meters[0][1]
            width_km = width_m / 1000
            height_km = height_m / 1000
            area_km2 = width_km * height_km

            print(f"   {lat}°N: {width_km:.2f} km × {height_km:.2f} km = {area_km2:.2f} km²")

        # Compare with simple degree approximation
        print(f"\n⚠️  COMPARISON:")
        print(f"   Simple approximation (1° = 111 km at equator):")
        simple_km = res[0] * 111
        simple_area = simple_km ** 2
        print(f"      {simple_km:.2f} km × {simple_km:.2f} km = {simple_area:.2f} km²")
        print(f"   Accurate calculation at {center_lat:.0f}°N:")
        print(f"      {width_km:.2f} km × {height_km:.2f} km = {pixel_area_km2:.2f} km²")

        print(f"\n✅ RECOMMENDED VALUE FOR YOUR CODE:")
        print(f"   Use: ~{width_km:.1f} km × {height_km:.1f} km (~{pixel_area_km2:.0f} km² per pixel)")

    else:
        print("\n--- Projected CRS Detected ---")
        width_km = abs(res[0]) / 1000
        height_km = abs(res[1]) / 1000
        pixel_area_km2 = width_km * height_km

        print(f"\n📏 PIXEL SIZE:")
        print(f"   Width:  {width_km:.2f} km")
        print(f"   Height: {height_km:.2f} km")
        print(f"   Area:   {pixel_area_km2:.2f} km²")

    print("\n" + "=" * 70)