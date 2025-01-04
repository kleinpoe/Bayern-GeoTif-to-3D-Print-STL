# Bayern GeoTIF to 3D printable model

This workflow is designed to create 3D printable models from GeoTIF Files provided by the Bayernatlas (https://atlas.bayern.de/), which is bavaria, a region of Germany.
It might work with other data as well but no promises made.

## Requirements

- Python
- FIJI ImageJ [optional but recommended]
- Blender [optional]

## Workflow

1. Download the Data from https://geodaten.bayern.de/opengeodata/index.html. Chose "Digitales Oberflächenmodell 20cm".
These are 16 bit float tif images. Each pixel value (z-Value) represents a height of the geo surface in meters. The surface includes mountains, buildings and vegtation. The raster has a resolution of 20cm, i.e. neighboring pixels are 20cm apart.
Use the website to download the tif files you would like to print.

![Download TIF files from Bayern Atlas](./ReadmeAssets/BayernAtlasDownload.png)

2. Optional: Open and inspect the tif files in FIJI (Drag and Drop, confirm with enter). Ensure that you have downloaded tifs that make up a rectangle
3. Stitch the downloaded tifs so that you have only one. Use the `Stichter.py` to stitch the tifs. It will automatically detect matching edges. Customize input and output filenames inside the script (at the bottom).
4. Optional: Crop the tif using FIJI so you only print your region of interest. Use 
`Image -> Crop`

![Stitch and crop the images](./ReadmeAssets/StitchCrop.png)

5. Convert the tif to an stl using the `Converter.py`. Customize the input and output files as well as subsampling and scale using the parameters at the bottom of the script.
6. Optional: Inspect the generated STL in Blender.
7. Import the STL in your Slicer. Bambu Studio has a simplify command which worked nicely for me. Use a high quality profile to print.

![Stitch and crop the images](./ReadmeAssets/BambuStudio.png)

## Issues

- The model might be quite large and blender or your slicer might not be able to handle it. You can try:
    - Use the subsampling in the conversion step.
    - Divide the model in smaller pieces
    - Use the Remesh Modifier of blender (Did not work for me, always crashed)
- The STL model might be mirrored: Use the subsampling parameter of the conversion-step with negative sign. 
- The images from BayernAtlas are slightly rotated (see screenshot above). You may compensate this in FIJI if you need north facing perfectly up.
- I flavored this guide very bavaria specific but you might learn something from this example which might help you apply the method to non-bavarian use-cases.