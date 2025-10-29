//@ Boolean(label = "Analyse a whole folder", value=true, description = "Uncheck to process a 'single file'", persist=true) iWholeDir
//@ File (label = "Input folder (for 'whole folder')", required=false, style="directory", persist=true) iInputDir
//@ File (label = "Input file (for 'single file')", required=false, persist=true) iInputFile
// File (label = "Output folder", style="directory", persist=true) iOutputDir
//@ String(label = "File suffix", required=false, value="tif", description="Relevant for 'whole folder' processing", persist=true) iSuffix
//@ Integer (label = "Threshold intensity", value=3000, persist=true) iIntensity
//@ Boolean(label = "Use input parameters", description = "Use input parameters for each file under 'Output folder/file name'", persist=true) iUseInputParameters


// These sparameters should be included input parameters
var iWholeDir="uninitialized";
var iInputDir="uninitialized";
var iInputFile="uninitialized";
var iOutputDir="uninitialized";
var iSuffix="uninitialized";


//----Macro parameters-----------
var pMacroName = "GapVeinHL";
var pMacroVersion = "1.0.0";
//---Global parameters
var gParmsFileName = "Parameters.txt";



var arguments_path = getArgument();
ReadParmsJson(arguments_path);
var gParmsFileName = File.getNameWithoutExtension(arguments_path);
return main();

function main(){
	Initialization();
	if(iWholeDir){
		ProcessFolder(iInputDir, iOutputDir, iSuffix);
	}
	else{
		ProcessFile(iInputFile, iOutputDir);
	}
	CleanUp(true);
	waitForUser("--------------------DONE--------------------");
	return 0;
}
function CheckInput(){
	return true;
}
function Initialization(){
	File.makeDirectory(iOutputDir);
}
function ProcessFolder(inputDir,outputDir,suffix) {
	list = getFileList(inputDir);
	list = Array.sort(list);
	for (i = 0; i < list.length; i++) {
		if(File.isDirectory(inputDir + File.separator + list[i])){
			File.makeDirectory(outputDir+ File.separator + list[i]);
			ProcessFolder(inputDir + File.separator + list[i],outputDir+ File.separator + list[i],suffix);
		}
		if(endsWith(list[i], suffix))
			ProcessFile(inputDir+File.separator+list[i], outputDir);
	}
}

function ProcessFile(file, outputDir) {
	print("Processing "+file);
	imageId = openFile(file);
	if(!CheckInput())
		return false;
	
	fileName = File.getNameWithoutExtension(file);
	outputDir = outputDir + File.separator + fileName;
	
	File.makeDirectory(outputDir);
	SaveParmsJson(outputDir + File.separator + gParmsFileName;);
	getDimensions(width, height, channels, slices, frames);
	getVoxelSize(pixelWidth, pixelHeight, pixelDepth, pixelUnit);
	//add your code here
	
	CleanUp(true);
}
function CheckInput(){
	return true;
}

function CleanUp(finalCleanUp)
{
	run("Close All");
	close("\\Others");
	run("Collect Garbage");
}
function openFile(file)
{
	h5OpenParms = "datasetname=[/data: (1, 1, 1024, 1024, 1) uint8] axisorder=tzyxc";
	//imsOpenParms = "autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_"; //bioImage importer auto-selection
	imsOpenParms = "color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT use_virtual_stack series_1"
	nd2OpenParms = "autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT";
	qptiffOpenParms = "autoscale color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT series_1"
	// ===== Open File ========================
	// later on, replace with a stack and do here Z-Project, change the message above
	if ( endsWith(file, "h5") )
		run("Import HDF5", "select=["+file+"] "+ h5OpenParms);
	if ( endsWith(file, "ims") )
		run("Bio-Formats Importer", "open=["+file+"] "+ imsOpenParms);
	if ( endsWith(file, "nd2") )
		run("Bio-Formats Importer", "open=["+file+"] " + nd2OpenParms);
	if ( endsWith(file, "qptiff") )
		run("Bio-Formats Importer", "open=["+file+"] " + qptiffOpenParms);
	else
		open(file);
	
	imageId = getImageID();

	return imageId;
}

function SaveParmsJson(parmsFile)
{
	//open Json
	File.saveString("{", parmsFile);
	File.append("", parmsFile); 
	//macro version
	File.append("\t\"Macro version\": \""+pMacroVersion+"\",", parmsFile);
	// input parameters
	File.append("\t\"File suffix\": \""+iSuffix+"\",", parmsFile);  //NOTICE - string parameters are between ""
	File.append("\t\"Threshold intensity\":" +iIntensity, parmsFile); //NOTICE - No ',' on last parameter
	//close Json
	File.append("}", parmsFile);
}
function ReadParmsJson(parmsFile)
{
	if(!File.exists(parmsFile)){
		print("Warning: no input parameters file for "+parmsFile);
		return;
	}
	jsonText = File.openAsString(parmsFile);
	iSuffix  = extractValue(jsonText, "File suffix");
	iIntensity = extractValue(jsonText, "Threshold intensity");
	waitForUser("'"+iSuffix+"'");
	waitForUser("'"+iIntensity+"'");
	// Extract values manually
	function extractValue(text, key) {
	    keyPos = indexOf(text, "\"" + key + "\"");
	    if (keyPos == -1) return "";
	    
	    colonPos = indexOf(text, ":", keyPos);
	    commaPos = indexOf(text, ",", colonPos);
	    if(commaPos != -1)
	    	endPos = commaPos;
	    else
			endPos = indexOf(text, "}", colonPos);	    
	    value = trim(substring(text, colonPos + 1, endPos));
	    // Remove quotes if it's a string
	    if (startsWith(value, "\"") && endsWith(value, "\""))
	        value = substring(value, 1, lengthOf(value) - 1);
	    return value;
	}
}
