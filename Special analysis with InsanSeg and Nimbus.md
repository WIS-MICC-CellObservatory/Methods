# Special analysis with InsanSeg and Nimbus
Using, InstaSeg, QuPath latest segmentation tool, that can use large number of channels to segment cells and Nimbus, a tool that can use a large number of channels and cell segmentation to provide probability distribution for each cell and channel, we train a cell classifier in QuPath for special analysis

This document describes how to run the pipeline online or in Wexac.

## The pipeline
The analysis includes the following steps:
1.  Create a project in QuPath that includes the image/s to be analysed
2.	**Export InstaSeg segmentation**: Using QuPath Groovy script, run InstanSeg on any subset of images/specific image/specific annotations and export The Segmentation, and tiff for each channel in a folder structure Nimbus python script expects. See Export InstaSeg segmentation.
3.	**Assign Numbus probabilities**: Using Jupyter Lab, run Payton script to assign a probability value for each cell-channel pair. See **Assign Nimbus probabilities** for details
4.	**Upload probabilities to QuPath**: Using QuPath Groovy script, upload the probabilities given by Nimbus back to QuPath. See **Upload probabilities to QuPath** for details
5.	**Assign initial classification**: Using QuPath groovy script, we assign initial classifications to each cell based on cell class table provided by the user. See **Assign initial classification** for details
6.	**Train object classifier**: In QuPath, Create cell classification based on these probabilities. See **Train object classifier** for details. Notice, this step cannot be performed in Wexac as it requires *Human-in-the-loop*

We start by describing how to run the each step online, and then describe how to run them all in Wexac 

## 2. Export InstaSeg segmentation
<ol>
  <li>Download Export_Regions_for_Nimbus.groovy script template from [here](../../tree/QuPath).</li>
  <li>Open the script in your QuPath project.</li>
  <li>Modify the script to fit your needs. Specifically:
    <ol>
      <li>In case you want to run on specific annotations and not on the entire image/s:
      <ol>
          <li>Create annotations of interests and set their class to be the same (e.g., “Region”). (line ~111)</li>
          <li>Set the parameter <strong>annotationToConsider</strong> accordingly. (line 98)</li>
          <li>Set the variable <strong>fullImageAnnotation</strong> to be false (line 99)</li>
        <img width="403" height="85" alt="image" src="https://github.com/user-attachments/assets/eafbecec-1258-4632-badb-cb37da007c80" />
      </ol>
      <li>Otherwise, Set the variable <strong>fullImageAnnotation</strong> to be true (line 99)</li>
    </li>
    <li>Set the output folders (lines 100,103)
      <ol>
          <li><strong>outFolder</strong>: The folder where the folders and files required by Nimbus will reside</li>
          <li><strong>InstanSegPath</strong>: Path to the model InstanSeg will use for segmentation (Usually the path includes the QuPath project folder and in it the folder that includes the InstanSeg related model. E.g. "A:/tzlily/Qpath6_MC38/fluorescence_nuclei_and_cells"</li>
          <img width="882" height="93" alt="image" src="https://github.com/user-attachments/assets/8f3d1a57-f05d-46d8-be43-669577862338" />
      </ol>
    </li>
    <li>Define the channels that will be used for the segmentation (line ~106-109):
<img width="884" height="147" alt="image" src="https://github.com/user-attachments/assets/a823d7bd-9bb8-4a22-83fc-f774ddad57d3" />
Notice:
      
•	One may want to ignore the 3 auto-florescence channels (by omitting channels 1-3 created by the Lunaphore system), in case compresence between the segmentation with and without them favoured omitting them.<br/>
•	In case one has more than 7 channels, more can be added.<br/>
•	One can use either the channel name or number
    </li>
  </ol></li>
  <li>If you want to run on several images rather than the current one, use the run->run for project option</li>
</ol>

## 2. Assign Nimbus probabilities
Check the instructions in [Running LSCF Python solution.md](../../tree) for general instruction regarding running Jupyter notebooks. Specificaly:
<ol>
<li>Download the **nimbus_env.yml** file from [here](../../tree/Python/Nimbus) and generate **nimbus_env** with it</li>
<li>Download the **nimbus.pyinb** file from [here](../../tree/Python/Nimbus)</li>
<li>Activate the **nimbus_env** and open nimbus.pyinb in Jupyter nootebook</li>
<li>Modify the script to fit your needs. Specifically:
  <ol>
    <li>Set the base directory: Set it to the path used as output path when exporting the QuPath segmentation (See **Export InstaSeg segmentation** section) together with the current image name. E.g.: "A:/tzlily/EhudTest4/Image1", where “A:/tzlily/EhudTest4” was the output folder and “Image1” was the image that its segmentations were exported.
    <img width="675" height="87" alt="image" src="https://github.com/user-attachments/assets/8cfd8640-e0ff-4d82-b3e5-b19cd1f9e2c6" />
    </li>
    <li>Define the channels you want Nimbus to generate probabilities for: Provide a list of case sensitive channel names. For example, the Dapi and the 3 auto-florescence channels may not be included).
Notice: the list may not include channels that were not specified when exporting the segmentation from QuPath segmentation (See **Export InstaSeg segmentation**). 
<img width="955" height="169" alt="image" src="https://github.com/user-attachments/assets/57132825-683c-4e7a-8366-2addaefd73d3" />
    </li>
  </ol>
</li>
</ol>

**Notice:** 

•	One may check the {base_dir}/image_data/fov0 directory for the list of channels that may be included, or run the following code:
