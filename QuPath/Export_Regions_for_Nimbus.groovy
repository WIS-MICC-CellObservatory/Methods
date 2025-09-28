/*
// ABOUT 
-----------
    Exports Regions for Nimbus analysis 

    For further info about Nimbus, see: 
    - https://www.biorxiv.org/content/10.1101/2024.06.02.597062v1 
      doi: https://doi.org/10.1101/2024.06.02.597062 
    - https://github.com/angelolab/Nimbus-Inference
    
// Workflow
------------

1.optionally create overlapping Tiles for a region defined by annotations of call WholeTissueClass, 
  if createFullImageAnnotation is set to 1, create one full image annotation (you can use this in most cases) 
  set the class of the new annotations to TilesClass, 
  set their names to fovN (where N is a running number)
  
2.Run InstanSeg for all regions of class WholeTissueClass

- for each Tile of class TilesClass: 
  3. Export single channel images
  4. Export labeled nuclei image and labeled cells image, add the cell label to the detection table as additional column
     Save Detection Measurements, to be able to correspond the object id, with the cell label for further analysis
    
- folder structure follows the Nimbus input structure: 
|-- base_dir
|   |-- image_name
|       |-- image_data
|       |   |-- fov0
|       |   |   |-- CD31.tiff
|       |   |   |-- CD45.tiff
|       |   |   |-- ...
|       |   |-- fov1
|       |   |   |-- CD31.tiff
|       |   |   |-- CD45.tiff
|       |   |   |-- ...
|       |-- segmentation
|       |   |   |-- fov0_nuclei.tiff
|       |   |   |-- fov0_whole_cell.tiff
|       |   |   |-- fov1_nuclei.tiff
|       |   |   |-- fov1_whole_cell.tiff

// NOTES 
---------
1. We save the files in Nimbus compatible folder structure,
   to enable processing a whole set of Images, we place the files under distinct folder for each image 
   
2. for cell number larger than 16bit, QuPath opt for saving the label image may be saved as RGB and 
   the label values will be packed as 24bit integer.
   label = RED * 256 * 256 + GREEN * 256 + BLUE
   
   You can use the Fiji script to convert it to 32bit float
   Nimbus support both 32bit float label images and RGB label images
   
   see: https://forum.image.sc/t/exporting-cell-segmentation-as-label-mask/66999/2

Authors: Ofra Golani, Rouven Hoefflin, Ehud Sivan (MICC Cel Observatory, Weizmann Institute of Science)

Tested on QuPath 0.6.0-rc3, March 2025

Due to the simple nature of this code, no copyright is applicable
*/
// Manage Imports
import groovy.time.*
import java.io.BufferedReader;
import java.io.FileReader;
import qupath.lib.objects.PathAnnotationObject;
import qupath.lib.objects.PathDetectionObject;
import qupath.lib.objects.PathTileObject;

import ij.IJ
import ij.gui.Roi
import ij.plugin.ChannelSplitter
import ij.plugin.frame.RoiManager

import qupath.imagej.gui.IJExtension
import qupath.imagej.tools.IJTools
import qupath.lib.objects.PathObjectTools
import qupath.lib.regions.RegionRequest
import qupath.lib.regions.ImagePlane
import qupath.lib.geom.Point2
import qupath.lib.roi.ROIs
import qupath.lib.roi.RectangleROI
import qupath.lib.roi.LineROI
import qupath.lib.roi.interfaces.ROI
import qupath.lib.roi.RoiTools.CombineOp
import qupath.lib.gui.QuPathGUI
import java.awt.geom.Path2D;

import static qupath.lib.gui.scripting.QPEx.*
import org.slf4j.Logger;
//import qupath.ext.biop.cellpose.Cellpose2D

// ========= User Defined Parameters ===========================================
//The detections it will classify are either the detections of the entire image (fullImageAnnotation = true) 
//or only those belonging to specific type of annotations, as defined in annotationToConsider variable 
annotationToConsider = "ZoomClass"
fullImageAnnotation = false
outFolder = "A:/tzlily/ZoomClass1"

//InstanSeg parameters 
instanSegPath = "A:/tzlily/Qpath6_MC38/fluorescence_nuclei_and_cells"

// channels to consider in InstanSeg segmentation
channelsForSegmentation = [ColorTransforms.createChannelExtractor("DAPI"), 
                        ColorTransforms.createChannelExtractor(4), 
                        ColorTransforms.createChannelExtractor(5), 
                        ColorTransforms.createChannelExtractor(6)]

// ========= General Parameters =================================================
downsample = 1
selectAnnotations = true 
segmentationMethod = "InstanSeg" // "InstanSeg"
// ========= Constant Parameters =================================================
segmentationFolderName = 'segmentation'
imageDataFolderName = 'image_data'
measurementsFolderName = 'export'
nimbusRegionPrefix = "fov"

// ========== Main Code ===================================================
ProcessImage(outFolder)

// ========== Methods ===================================================
boolean ProcessImage(outFolder){
    println("Image: "+getProjectEntry().getImageName())

    // Get the image name

    imageName = GeneralTools.stripExtension(GeneralTools.stripExtension(getProjectEntry().getImageName()))
    imageData = getCurrentImageData()


    labels_folder = buildFilePath( outFolder, imageName, segmentationFolderName ) 
    channels_folder = buildFilePath( outFolder, imageName, imageDataFolderName ) 
    measurements_folder = buildFilePath( outFolder, imageName, measurementsFolderName ) 

    mkdirs( channels_folder )
    mkdirs( labels_folder )
    mkdirs( measurements_folder )

    annotations = GetAnnotations(fullImageAnnotation, annotationToConsider, selectAnnotations)
    if (annotations.isEmpty() )
        return

    switch(segmentationMethod){
        case "InstanSeg":
            RunInstanSeg(annotations)
            break
        case "Cellpose":
            RunCellpose(annotations)
            break
        default:
            println "ERROR: Segmentation '$segmentationMethod' not supported"
            return false
    }
    
    ExportIndividualChannels(annotations)
    ExportLabelImages(annotations)
    ExportMeasurments()
    RemoveFullImageAnnotation(annotations, fullImageAnnotation)
    return true;
}

def RunCellpose(annotations){
    print("Running Cellpose segmentation")
    if (annotations.isEmpty() )
        return


def pathModel_nuc = 'cyto3'
def cellpose = Cellpose2D.builder( pathModel_nuc )
        .channels("DAPI" )
        .pixelSize( 0.3 )              // Resolution for detection
        .diameter(10)                  // Median object diameter. Set to 0.0 for the `bact_omni` model or for automatic computation
        .build()
/*
    def pixelSize = imageData.getServer().getPixelCalibration().getPixelWidth()

    def cellpose = Cellpose2D.builder( cellposePathModel )
            .pixelSize( pixelSize )              // Resolution for detection
    //        .channels( 'Nuclei' )            // Select detection channel(s)
    //        .preprocess( ImageOps.Filters.median(1) )                // List of preprocessing ImageOps to run on the images before exporting them
    //        .tileSize(2048)                // If your GPU can take it, make larger tiles to process fewer of them. Useful for Omnipose
            .cellposeChannels(cellposeMainChannel,cellposeNucleusChannel)         // Overwrites the logic of this plugin with these two values. These will be sent directly to --chan and --chan2
    //        .maskThreshold(-0.2)           // Threshold for the mask detection, defaults to 0.0
    //        .flowThreshold(0.5)            // Threshold for the flows, defaults to 0.4 
            .diameter(0)                   // Median object diameter. Set to 0.0 for the `bact_omni` model or for automatic computation
    //        .setOverlap(60)                // Overlap between tiles (in pixels) that the QuPath Cellpose Extension will extract. Defaults to 2x the diameter or 60 px if the diameter is set to 0 
    //        .invert()                      // Have cellpose invert the image
    //        .useOmnipose()                 // Add the --omni flag to use the omnipose segmentation model
    //        .excludeEdges()                // Clears objects toutching the edge of the image (Not of the QuPath ROI)
    //        .clusterDBSCAN()               // Use DBSCAN clustering to avoir over-segmenting long object
    //        .cellExpansion(5.0)            // Approximate cells based upon nucleus expansion
    //        .cellConstrainScale(1.5)       // Constrain cell expansion using nucleus size
    //        .classify("My Detections")     // PathClass to give newly created objects
            .measureShape()                // Add shape measurements
            .measureIntensity()            // Add cell measurements (in all compartments)  
    //        .createAnnotations()           // Make annotations instead of detections. This ignores cellExpansion
    //        .useGPU()                      // Optional: Use the GPU if configured, defaults to CPU only
            .build()
    
    // Run detection for the selected objects */
    cellpose.detectObjects(imageData, annotations)
        
    fireHierarchyUpdate()
    println 'Cellpose detection done'
}
  
def RunInstanSeg(annotations){
    print("Running InstanSeg segmentation")
    if (annotations.isEmpty() )
        return

    qupath.ext.instanseg.core.InstanSeg.builder()
        .modelPath(instanSegPath)
        .device("gpu")
        .inputChannels(channelsForSegmentation)
        .outputChannels()
        .tileDims(512)
        .interTilePadding(48)
        .nThreads(4)
        .makeMeasurements(true)
        .randomColors(false)
        .build()
        .detectObjects()
        
    fireHierarchyUpdate()
    println 'InstanSeg detection done'
}

def ExportIndividualChannels(annotations){
    for (annotation_idx = 0; annotation_idx<annotations.size(); annotation_idx++)
    {
        a = annotations[annotation_idx]
        fov_name = nimbusRegionPrefix+annotation_idx
        server = imageData.getServer();
        viewer = getCurrentViewer();
        hierarchy = getCurrentHierarchy();
    
        pathImage = null;
        request = RegionRequest.createInstance(imageData.getServerPath(), downsample, a.getROI())
        pathImage = IJExtension.extractROIWithOverlay(server, a, hierarchy, request, false, viewer.getOverlayOptions());
        image = pathImage.getImage()
       
        // save individual channel images for each region N under dedicated folder called fovN
        def fov_folder = new File ( buildFilePath( channels_folder , fov_name ) )
        mkdirs( fov_folder.getAbsolutePath() )
            
        // Split channels
        def channelNames = getCurrentServer().getMetadata().getChannels().collect { c -> c.name }
        imp_chs =  ChannelSplitter.split( image )
        channelNames.eachWithIndex {cName, cName_idx ->
            output = imp_chs[  cName_idx ]
            IJ.save( output , new File ( fov_folder, cName ).getAbsolutePath()+'.tiff' )
        }
        println( fov_name + ": Channel Images Saved." )
    }
    fireHierarchyUpdate()
}

def ExportLabelImages(annotations){
    // Create an ImageServer where the pixels are derived from annotations
    def labelServerNuc = new LabeledImageServer.Builder(imageData)
        .backgroundLabel(0, ColorTools.WHITE) // Specify background label (usually 0 or 255)
        .downsample(downsample)    // Choose server resolution; this should match the resolution at which tiles are exported
        .useCellNuclei()
        .useInstanceLabels() // Use this for instance segmentation
        .shuffleInstanceLabels(false)
        .multichannelOutput(false) // If true, each label refers to the channel of a multichannel binary image (required for multiclass probability)
        .build()
    
    def labelServerCell = new LabeledImageServer.Builder(imageData)
        .backgroundLabel(0, ColorTools.WHITE) // Specify background label (usually 0 or 255)
        .downsample(downsample)    // Choose server resolution; this should match the resolution at which tiles are exported
        .useCells()
        .useInstanceLabels() // Use this for instance segmentation
        .shuffleInstanceLabels(false)
        .multichannelOutput(false) // If true, each label refers to the channel of a multichannel binary image (required for multiclass probability)
        .build()
    
    for (annotation_idx = 0; annotation_idx<annotations.size(); annotation_idx++)
    {
        a = annotations[annotation_idx]
        fov_name = nimbusRegionPrefix+annotation_idx
        def regionNuc = RegionRequest.createInstance(
            labelServerNuc.getPath(), downsample, a.getROI())
        def outputPath = buildFilePath(labels_folder, fov_name +"_nuclei.tiff")
        writeImageRegion(labelServerNuc, regionNuc, outputPath)
    }

    for (annotation_idx = 0; annotation_idx<annotations.size(); annotation_idx++)
    {
        a = annotations[annotation_idx]
        fov_name = nimbusRegionPrefix+annotation_idx
        def regionCell = RegionRequest.createInstance(
            labelServerCell.getPath(), downsample, a.getROI())
        def outputPath = buildFilePath(labels_folder, fov_name +"_whole_cell.tiff")
        writeImageRegion(labelServerCell, regionCell, outputPath)
        println(labels_folder + " - " + fov_name + ": Label Images Saved." )
    }

    // Add instances
    def labels = labelServerCell.getInstanceLabels()
    for (def entry in labels.entrySet()) {
        try (def ml = entry.getKey().getMeasurementList()) {
            ml.put('Instance', entry.getValue())
        }
    }
    fireHierarchyUpdate()
}

def ExportMeasurments(){
    def measurementsPath = buildFilePath(measurements_folder, "measurments.tsv")
    saveDetectionMeasurements(measurementsPath)
}
def RemoveFullImageAnnotation(annotations, fullImageAnnotation){
    if(fullImageAnnotation){
        //remove the created whole image annotation 
        annotations.each{
            removeObject(it,true)
        }
    }
}

def GetAnnotations(fullImageAnnotation, annotationToConsider, selectAnotations){
    if(fullImageAnnotation){
        createFullImageAnnotation(true)
        //pathClass = getPathClass(WholeTissueClass)
        pathClass = WholeTissueClass
        annotations = getSelectedObjects()
        annotations.each{
            it.setPathClass(pathClass)
        }
    }
    else{
        annotations = getAnnotationObjects().findAll { it.getPathClass() == getPathClass(annotationToConsider) }
        if(annotations.size() == 0){
            println "ERROR: No annotations of class '$annotationToConsider' were found"
        }
        pathClass = getPathClass(annotationToConsider)
        pathClass = annotationToConsider
    }
    if(selectAnotations){
        selectObjectsByClassification(pathClass)
    }
    return annotations
}


println "============= Workflow Done ===================="







