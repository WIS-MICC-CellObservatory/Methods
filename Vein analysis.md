# Vein analysis
In this document we describe steps to analyse endothelium within a vein using Arivis. It includes the following steps
1. Converting the image to Arivis
2. Creating an object that capture the inner vein
3. Measuring the endothelium inside the vein in growing rings starting with the inner vein object
4. Tracking and analysing the endothelium network

**Notice: Arivis 4.4 and above must be used**

## 1. Converting the image to Arivis
to convert an image to Arivis one should use the "Arivis SIS Convertor"

<img width="273" height="57" alt="image" src="https://github.com/user-attachments/assets/2ae039b2-3356-4d7f-9668-f20b39a5063c" />

<img width="1093" height="1088" alt="image" src="https://github.com/user-attachments/assets/77ca7e3e-7ffa-43bb-90e1-ad827857e7e1" />

Once opened, select the "+" button to add files. Make sure you also set the right folder where the generated Arivis file (".sis" suffix) is stored.

We recommend that the folder where the image is stored is a designated folder (consider using the image name - without prefix - as the folder name)

**Known issue:** If the path to the folder is too long (number of characters), converter may fail to start

**Notice:** Once convertion is completed, open the image in Arivis and make sure the voxel size is correct (select the "i" view and compare image properties to the original image). In case the voxel size was not set correctly, fix it manually by selecting the "Edit" Button

## 2. Inner vein object
1. Open the image in Arivis
2. We recommend focusing on a region of the vein for the analysis to save time. To do so:
- Switch to 2D view: Select the <img width="61" height="66" alt="image" src="https://github.com/user-attachments/assets/947aa7b1-2da9-432b-bfea-e8158bbb14af" /> button on the lower left 
- Focus on the area of the vein you are interested in using the mouse scroller and the <img width="160" height="52" alt="image" src="https://github.com/user-attachments/assets/9b02bf46-c524-4248-b83d-45dc16e94d2f" /> buttons
 (make sure the entire width of the vein is captured and some more)

<img width="2708" height="1264" alt="image" src="https://github.com/user-attachments/assets/0346ca0f-0c92-4c7a-a5ba-47c3a2d53c2b" />
3. load the "Vein complement" pipeline that can be found [here](../../tree/Arivis):
- Enter the pipeline panel: Analysis>Analysis panel.
- Load the pipeline using the import option that can be found in the drop-down menu on the upper right corner of the panel. navigate to where you have downloaded the pipeline
- A prompt indicating the pipeline is zipped is given - select the import button to proceed
The following pipeline is loaded to the panel:

<img width="1109" height="1455" alt="image" src="https://github.com/user-attachments/assets/0e15743f-252f-44b6-94ff-f7f080c17efc" />


4. In case you are running on the entire image set the "ROI" of the first operation, "Input ROI" to be "Current image Set". However, if you focused on a specific region (as suggested above) then:
- Set the "ROI" to be "Current View (2D)": As a result the current image coordinates are set in the "Bounds" parameter
- Now switch the ROI to be "Custom"
- Change the "Planes" parameter to be "All:1-nnn", where nnn is the number of planes in the image

5. In the "Intensity Threshold Segmenter" operation change the "Threshold" value if needed: Use the "Value picker" tool to guestimate the right value
6. Run the pipeline to that point only: in the drop-down menu of that operation ("Intensity Threshold Segmenter", that is) located at its upper right corner select the "Run pipeline to here" option
7. Nevigate to the "Object table" by selecting the <img width="57" height="53" alt="image" src="https://github.com/user-attachments/assets/b9a638d4-f91b-489c-ac67-be117ba400ab" /> button
8. Select the "red signal" object on the left. A list of all the identified object is listed on the right. Sort them by volume (largest to smallest). If the "Volume" column does not appear add it by selecting the volume feature from the "Feature column" menu
<img width="1853" height="863" alt="image" src="https://github.com/user-attachments/assets/7afdad36-a514-40e9-9349-a3a390f62a8f" />
9. Only the largest object represents the vein, so use the volume of the second largest object to set the threshold volume in the next operation "Object Feature Filter"

10. Now you can run the pipeline all the way to the end by selecting the run button located at the top of the pipeline 
<img width="200" height="231" alt="image" src="https://github.com/user-attachments/assets/e8599756-d7a6-4b74-98e5-a437257dea7c" />

11. Nevigate again to the "Object table" and select the "vein complement" object. In the list of objects on the right, only one represent the inner vein (usually it would be the 2nd when sorted by volume). Delete all the other objects in the list (ctrl select and right click "delete")
**Notice:** if more than one object represent the inner vein contact us

12. Save the image so the single "vein complement" object can be used in the next pipeline

## 3. Ring analysis
1. load the "Endothelium rings" pipeline that can be found [here](../../tree/Arivis)
2. **Important**: Copy the bounds values used in the "Vein complement" to the bounds parameter in the "Input ROI" operation
3. Set the value in the "Intensity threshold" operation to fit the signal in the green channel
4. Set the output file in the "Export object feature" operation (at the end of the pipeline): It is an excel file that contains the results
5. By default the pipeline generates the following rings
- 10 pixels into the "vein complement"
- 50 pixels from the inner side of the vein
- the following 50 pixels (50-100)
- the following 100 pixels (100-200)
- the following 100 pixels (200-300)
For each ring it provides 2 objects: one that represent the whole ring (I-10, I50, S100, S200 and S300)
<img width="1132" height="1180" alt="image" src="https://github.com/user-attachments/assets/d36ad635-bb99-4c3e-b3e7-ee5953b9516d" />

and one that represent the endothelium within the ring (E-10, E50, E100, E200 and E300)

One can change the size of the rings but it needs to be done with care: It is recommended that the naming convention is kept such that the name of the object represent its distance from the inner side of the vein

## 4. Neurite analysis
1. load the "Neurite analysis" pipeline that can be found [here](../../tree/Arivis)
2. **Important**: Copy the bounds values used in the "Vein complement" to the bounds parameter in the "Input ROI" operation
3. Run the pipeline and check the traces generated in the "Object table"
4. Add columns from the "Feature column" as suggested in this tutorial: https://www.youtube.com/watch?v=fcFmbzwIdyk&t=2020s 
