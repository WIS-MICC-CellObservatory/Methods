# 3D Cellpose training
Here we describe a recomended worflow of training 3D cellpose modeling. It consist of the following steps:
## Table of content
1. Crop the images to include ~ 10 cells with all the slices that captures them (or at least some of them)
2. Intial segmentation of a 3D cropped images done by a pre-defined model provided by Cellpose creates initial 3D label image
3. A Python script generates 3 directories "XY", "ZX" and "ZY" that contain tif image for each slice in the related plane. The script is created for both 3D images (the Cropped 3D image and the 3D label image created by Cellpose)
4. The user then, selects a subset of slices (on XY, ZX and ZY planes) to fix.
5. Using the fixed slices a new model is trained and tested against the original 3D cropped images

## 1. Cropping 3D images
In Fiji:
1. Open the 3D image and find a region of the image containing relevant information (~10 cells to be segmented). 
2. Create a "Rectangle selection" of that region and Duplicate it (right click). When duplicating, select consecutive slices and up to 2 consecuitive channels relevant for the segmentation.
<img width="428" height="329" alt="image" src="https://github.com/user-attachments/assets/ed407590-62fe-4153-ad25-a9942e2f3181" />

(In case the 2 channels are not consecutive, you need to create a subset of the image first, where the channels in between the 2 channels are ommited. For that use **Image>Hyperstacks>Make Subset**)

3. Save the cropped image with a meaningfull name (e.g., adding "_crop1" suffix to the original name)
4. Repeat these steps for other reagions of interest in the image and in other images

## 2. Cellpose initial 3D segmentation
1. Open anaconda prompt and activate the relevant cellpose enviorenment (e.g., "conda activate cellpose3")
2. run **cellpose --Zstack** to open the GUI for 3D segmentation 
3. Load each of the cropped images and segment it using the pre-define model provided by Cellpose (e.g., **cyto3** or **cpsam**)
4. Save the label image created by the image

## 3. Generate XY, ZX, ZY matching slices
1. Close the cellpose GUI and reopen the anaconda window where the cellpose enviorment is activated
2. There, run **python isotropic_3D_slicer.py --gui** that can be found here. (you need to provide a full path or nevigate to where you stored it on disk). A window opens (see image below)
<img width="1200" height="942" alt="image" src="https://github.com/user-attachments/assets/48011e4a-7831-48b7-80b2-26d402be098d" />

3. First run it on the cropped image. Set the parameters as follows

**- Input TIFF**: full path to cropped image

**- Z Axis**: select **first**. If for some reason the slices dimentions dont look right, contact us
**- Channel Axis**: if there is only one channel, select **None**, otherwise select **1**. If for some reason the slices dont look right, contact us
- Select the cropped image as the input file

- Select the image type to be **image**
- If there is only one channel se
When training a cellpose model, Cellpose provide an initial segmentation for each slice in the 3D image one must segment all the cells seen in the image
