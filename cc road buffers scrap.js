// CSDUIDs to exclude
var excludeList = [4802013, 4802014, 4802018, 4802019, 4802022, 4802029, 4802034, 4802036, 4803002,
    4803004, 5923008, 5926005, 5926010, 5927008, 5929005, 5933054, 5935010, 5937014,
    5937028, 5937033, 5955014, 5955034, 1001485, 1001517, 1001542, 1005017, 1102075,
    1102080, 1103014, 1103025, 1202006, 1203006, 1206004, 1206006, 1207024, 1211011,
    1212009, 1212014, 1214002, 1303012, 2452035, 2452080, 2453050, 2453052, 2454025,
    2456083, 2457005, 2457020, 2457025, 2457030, 2466062, 2466072, 2466087, 2466097,
    2466102, 2466107, 2466112, 2466117, 2466142, 2467015, 2467020, 2467025, 2467030,
    2467035, 2467050, 2468030, 2469055, 2471033, 2471055, 2471060, 4806029, 4806034,
    4807002, 4807026, 4807054, 4808008, 4808011, 4808012, 4808024, 4808026, 2471065,
    2471070, 2471075, 2471083, 2471090, 2472005, 2472010, 2472015, 2472020, 2473005,
    2473010, 2473015, 2473020, 2473025, 2473030, 2475017, 2476055, 2480050, 2481017,
    2483065, 2484060, 2485025, 2489804, 3501012, 3502008, 3502044, 3507008, 3507015,
    3507024, 3509004, 3509021, 3509028, 3543052, 3543064, 3543074, 3547002, 3547048,
    3547064, 3548021, 3549032, 3554052, 4601060, 4602037, 4602044, 4602046, 4602061,
    4603040, 4603050, 4603053, 4603074, 4701008, 4701024, 4702047, 4703036, 4704048,
    4705016, 4705052, 4706027, 4706030, 4706031, 4706039, 4707037, 4707039, 4708004,
    4709012, 4710068, 4711066, 4711068, 4711070, 4711073, 4711075, 4713051, 4714044,
    4714051, 4714076, 4715008, 4715028, 4715066, 4715068, 4716029, 4717029, 4717052,
    4801006, 4802008, 4802009, 4802012, 3512002, 3514021, 3515014, 3518001, 4808029,
    4808031, 4808039, 4809015, 4810011, 4810028, 4810052, 4811002, 4811013, 4811016,
    3526065, 3529006, 3530010, 3530013, 3530016, 3531011, 3531016, 3532004, 3532018,
    3532042, 3534011, 3534021, 3537034, 3537039, 3538019, 3538030, 3538031, 3539036,
    3540028, 3542029, 3542059, 3543031, 3543042, 4813019, 4815035, 4817029, 4819009,
    4819012, 5901012, 5901022, 5903004, 5903011, 5903015, 5903045, 5905005, 5905009,
    5905018, 5907005, 5907009, 5907014, 5907041, 5909052, 5915001, 5915043, 5915046,
    5915051, 5915055, 5915065, 5917010, 5917015, 5917021, 5917030, 5917034, 5917040,
    5917041, 5917044, 5917047, 5919012, 5919016, 5919021, 5921007, 5921018, 5921023,
    4803026, 4805018, 4805048, 4806006, 4806009, 4811018, 4811019, 4811048, 4811049,
    4811056, 5915022, 5915025, 5915029, 5915034, 5915039, 1305022, 1306020, 1307022,
    1310032, 1314022, 2432040, 2437067, 2439062, 2441060, 2442098, 2457035, 2457040,
    2458007, 2458012, 2458033, 2458037, 2458227, 2459010, 2460005, 2460013, 2461025,
    2461030, 2461035, 2464008, 2464015, 2443027, 2446035, 2447017, 2447025, 2449075,
    4614039, 4617050, 4618074, 4620048, 4622026, 4806017, 4806019, 2466032, 2466047,
    2466058, 4607062, 4612056, 4613047, 3522021, 3523008, 4811062, 4811068, 4812009,
    4812018, 5915007, 5915011, 5915015, 2409065, 2411040, 2421045, 3526043, 3526053,
    4806012, 4609029, 3518005, 3518009, 4806021, 5915002, 2423057, 2465005, 2466023];

// Set the projection to Statistics Canada Lambert
var statsCanLambert = ee.Projection('EPSG:3347');

// Access census subdivision shapefiles
var censusSub = ee.FeatureCollection('projects/heroic-glyph-383701/assets/road_buffers')
  .filter(ee.Filter.inList('CSDUID', excludeList).not());

// Access Meta 1m Canopy Height Model
var canopyHeight = ee.ImageCollection('projects/meta-forest-monitoring-okw37/assets/CanopyHeight').mosaic();

// Reproject canopy height to Stats Can Lambert
var canopyHeightReprojected = canopyHeight.reproject({
  crs: statsCanLambert,
  scale: 1
});

// Create binary canopy layer (>= 2m = 1, < 2m = 0)
var canopyBinary = canopyHeightReprojected.gte(2);

// Display the binary canopy layer
Map.addLayer(canopyBinary.selfMask(), {palette: ['green']}, 'Canopy (>=2m)', false);

// Define batch parameters
var totalFeatures = censusSub.size();
var batchSize = 50; // Process x CSDs at a time
var batchNumber = 0; // Change this for each run (0, 1, 2, 3, etc.)

// Calculate start and end indices
var startIndex = batchNumber * batchSize;

// Get subset of features
var censusSubBatch = ee.FeatureCollection(censusSub.toList(batchSize, startIndex));

print('Total CSDs:', totalFeatures);
print('Processing batch:', batchNumber);
print('CSDs in this batch:', censusSubBatch.size());

// Function to calculate canopy metrics for each CSD
var calculateCanopyMetrics = function(feature) {
  // Get the geometry
  var geometry = feature.geometry();

  // Calculate pixel area in square meters (1m x 1m = 1 sq m per pixel)
  var pixelArea = ee.Image.pixelArea().reproject({
    crs: statsCanLambert,
    scale: 1
  });

  // Calculate total area of the CSD in square meters
  var totalArea = pixelArea.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    crs: statsCanLambert,
    scale: 1,
    maxPixels: 1e13
  }).get('area');

  // Calculate canopy area (where binary = 1)
  var canopyAreaImage = canopyBinary.multiply(pixelArea);
  var canopyAreaResult = canopyAreaImage.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geometry,
    crs: statsCanLambert,
    scale: 1,
    maxPixels: 1e13
  });

  // Get the first (and only) value from the result
  var canopyArea = ee.Number(canopyAreaResult.values().get(0));

  // Convert to square kilometers
  var totalAreaKm2 = ee.Number(totalArea).divide(1e6);
  var canopyAreaKm2 = canopyArea.divide(1e6);

  // Calculate proportion as percentage
  var canopyProportion = canopyAreaKm2.divide(totalAreaKm2).multiply(100);

  // Add properties to feature
  return feature.set({
    'total_area_km2': totalAreaKm2,
    'canopy_area_km2': canopyAreaKm2,
    'canopy_proportion': canopyProportion
  });
};

// Calculate metrics for batch of CSDs
var censusWithCanopy = censusSubBatch.map(calculateCanopyMetrics);

// Set map center to Canada and zoom level
Map.setCenter(-96, 62, 4); // Centered on Canada

// Display the census subdivisions (showing full collection for reference)
Map.addLayer(censusSub, {color: 'blue'}, 'All Census Subdivisions', false);
Map.addLayer(censusSubBatch, {color: 'red'}, 'Current Batch', true);

// Print results
print('Census Subdivisions with Canopy Metrics:', censusWithCanopy);
print('Number of CSDs in batch:', censusWithCanopy.size());

// Export results to CSV with batch number in filename
Export.table.toDrive({
  collection: censusWithCanopy,
  description: 'canopy_cover_road_buffer_batch_' + batchNumber,
  fileFormat: 'CSV',
  selectors: ['CSDUID', 'total_area_km2', 'canopy_area_km2', 'canopy_proportion']
});

print('Export task created. Check the Tasks tab to run it.');