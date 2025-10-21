# Special analysis with InsanSeg and Nimbus
Using, InstaSeg, QuPath latest segmentation tool, that can use large number of channels to segment cells and Nimbus, a tool that can use a large number of channels and cell segmentation to provide probability distribution for each cell and channel. we provide a pipeline that segmnet and classify cells in multi-channel images. The pipeline can be used both manualy using GUI or in Wexac for some of it steps.

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

## 3. Assign Nimbus probabilities
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

<pre><code>
# run this to get all the names of possible channels: you can then copy the relevant ones to the include_channels list below
tif_files = [f for f in os.listdir(os.path.join(tiff_dir,"fov0")) if f.endswith(".tiff")]
# Print them in the required format
formatted = ', '.join(f'"{file}"' for file in tif_files)
print(formatted.replace(".tiff",""))
</code></pre>
•	A csv file with all the measurements exported from QuPath together with the probabilities assigned to each cell by Nimbus can be found in {base_dir}/image_data/export/combined_measurments.csv file and can be used for clustering and further analysis external to QuPath.

After making the modifications, you can run the whole notebook, or stop after section 5 the cell that generates a csv file that can be uploaded to QuPath can be found as  {base_dir}/ nimbus_output/nimbus_cell_table.csv. The cell is 
Run the notebook cell by cell 

## 4. Upload probabilities to QuPath
This script runs on the currently open image. To run the script do the following steps:
<ol>
<li>Make sure the image used for the segmentation is selected in the project</li>
<li>Download the <strong>import_Nimbus_Predictions.groovy</strong> file from [here](../../tree/QuPath)</li>
<li>Open the script in your QuPath project.</li>
<li>Modify the script to fit your needs. Specifically:
  <ol>
    <li>Set the path to the table created by nimbus (line 9)
    <img width="858" height="83" alt="image" src="https://github.com/user-attachments/assets/4a0b83d8-89eb-4e46-9254-29e291754255" />
    </li>
    <li>In case you exported specific regions and not the entire image:
      <ol>
        <li>Set parameter <strong>annotationToConsider</strong>strong> to the class used when exported the segmentation. (line ~12)</li>
        <li>Set the variable <strong>fullImageAnnotation</strong> to be false (line ~13)</li>
        <li>Otherwise, Set the variable <strong>annotationToConsider</strong> to be true (line ~13)</li>
      </ol>
    </li>
  </ol>
    <li>Run the script. When completed, each cell will have additional measurements with the probability of that cell to express each marker (see example below)<br/>
    <img width="453" height="559" alt="image" src="https://github.com/user-attachments/assets/4f35adff-706e-4227-a2c2-bf863c34df33" />
    </li>
  </ol>
  
## 5. Assign initial classification
This script set initial classification to each cell (that can later be used for training an Object classification – see Train Object Classifier for details) based on the probabilities given by nimbus for each channel and a user defined cell class definitions based on these probabilities.
This script runs on the currently open image. To run the script do the following steps:
<ol>
  <li>Make sure the image used for the segmentation is selected in the project</li>
  <li>Download the Set_Class_by_Measurments_Threshold.groovy file from  [here](../../tree/QuPath)</li>
  <li>Open the script in your QuPath project.</li>
  <li>Modify the script to fit your needs. Specifically:
    <ol>
      <li></li>Set defaultPositiveThreshold: set this to a value that will be used as the positive threshold for channels that no specific threshold is provided in the Class table (See Define Class table for details) (line ~42)</ol>
      <li>Set defaultNegativeThreshold: set this to a value that will be used as the negative threshold for channels that no specific threshold is provided in the Class table (See Define Class table for details) (line ~42)</li>
<li>Set defaultSuffix: a string that will be concatenated to ALL measurements indicated in the Class table table (See Define Class table for details) (line ~44)
<li>In case you exported specific regions and not the entire image:
<li>Set parameter annotationToConsider to the class used when exported the segmentation. (line ~49)
<li>Set the variable fullImageAnnotation to be false (line ~50)
Otherwise, 
<li>Set the variable fullImageAnnotation to be true (line ~50)
<li>Set classificationFolder, classificationFileName: A folder and a file name where a tsv file containing the center coordinates of every cell that was associated to a single class, together with its associated class. This file can be uploaded to QuPath to facilitate Object Classification (See Train object classifier for details), (lines ~53,54).
g.	Set cell classes: See Define Class table for details.


      

