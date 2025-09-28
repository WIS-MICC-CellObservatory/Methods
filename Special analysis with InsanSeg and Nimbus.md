# Special analysis with InsanSeg and Nimbus
Using, InstaSeg, QuPath latest segmentation tool, that can use large number of channels to segment cells and Nimbus, a tool that can use a large number of channels and cell segmentation to provide probability distribution for each cell and channel, we train a cell classifier in QuPath for special analysis

This document describes how to run the pipeline online or in Wexac.

## The pipeline
The analysis includes the following steps:
1.  Create a project in QuPath that includes the image/s to be analysed
2.	**Export InstaSeg segmentation**: Using QuPath Groovy script, run InstanSeg on any subset of images/specific image/specific annotations and export The Segmentation, and tiff for each channel in a folder structure Nimbus python script expects. See Export InstaSeg segmentation.
3.	**Assign a probabilities**: Using Jupyter Lab, run Payton script to assign a probability value for each cell-channel pair. See **Assign a probabilities** for details
4.	**Upload probabilities to QuPath**: Using QuPath Groovy script, upload the probabilities given by Nimbus back to QuPath. See **Upload probabilities to QuPath** for details
5.	**Assign initial classification**: Using QuPath groovy script, we assign initial classifications to each cell based on cell class table provided by the user. See **Assign initial classification** for details
6.	**Train object classifier**: In QuPath, Create cell classification based on these probabilities. See **Train object classifier** for details. Notice, this step cannot be performed in Wexac as it requires *Human-in-the-loop*

We start by describing how to run the each step online, and then describe how to run them all in Wexac 

## 2. Export InstaSeg segmentation
<ol>
  <li>Download Export_Regions_for_Nimbus.groovy script template from here [here](../../tree/QuPath).</li>
  <li>Open the script in your QuPath project.</li>
  <li>Modify the script to fit your needs. Specifically:
    <ol>
      <li>In case you want to run on specific annotations and not on the entire image/s:
      <ol>
          <li>Create annotations of interests and set their class to be the same (e.g., “Region”). (line ~111)</li>
          <li>Set the parameter <strong>annotationToConsider</strong> accordingly. (line ~111)</li>
          <li>Set the variable <strong>fullImageAnnotation</strong> to be false (line ~112)</li>
        <img width="403" height="85" alt="image" src="https://github.com/user-attachments/assets/eafbecec-1258-4632-badb-cb37da007c80" />
      </ol>
      <li>Otherwise, Set the variable <strong>fullImageAnnotation</strong> to be true (line ~112)</li>
    </li>
    <li>Set the output folders (lines ~113,114)
      <ol>
          <li><strong>outFolder</strong>: The folder where the folders and files required by Nimbus will reside</li>
          <li><strong>InstanSegPath</strong>: Path to the model InstanSeg will use for segmentation (Usually the path includes the QuPath project folder and in it the folder that includes the InstanSeg related model. E.g. "A:/tzlily/Qpath6_MC38/fluorescence_nuclei_and_cells"</li>
          <img width="882" height="93" alt="image" src="https://github.com/user-attachments/assets/8f3d1a57-f05d-46d8-be43-669577862338" />
      </ol>
    </li>
    <li>Define the channels that will be used for the segmentation (line ~117-120):
<img width="884" height="147" alt="image" src="https://github.com/user-attachments/assets/a823d7bd-9bb8-4a22-83fc-f774ddad57d3" />
Notice:
      
•	One may want to ignore the 3 auto-florescence channels (by omitting channels 1-3 created by the Lunaphore system), in case compresence between the segmentation with and without them favoured omitting them.<br/>
•	In case one has more than 7 channels, more can be added.<br/>
•	One can use either the channel name or number
    </li>
  </ol></li>
  <li>If you want to run on several images rather than the current one, use the run->run for project option</li>
</ol>

