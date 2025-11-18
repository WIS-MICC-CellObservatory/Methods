# Vein analysis
In this document we describe steps to analyse endethelium within a vein using Arivis. It includes the following steps
1. Converting the image to Arivis
2. Creating an object that capture the inner vein
3. Measuring the endethilium inside the vein in growing rings starting with the inner vein object
4. Tracking and analysing the endethilum network

**Notice: Arivis 4.4 and above must be used**

## 1. Converting the image to Arivis
to convert an image to Arivis one should use the "Arivis SIS Convertor"

<img width="273" height="57" alt="image" src="https://github.com/user-attachments/assets/2ae039b2-3356-4d7f-9668-f20b39a5063c" />

<img width="1093" height="1088" alt="image" src="https://github.com/user-attachments/assets/77ca7e3e-7ffa-43bb-90e1-ad827857e7e1" />

Once opened, select the "+" button to add files. Make sure you also set the right folder where the generated Arivis file (".sis" suffix) is stored.

We recommend that the folder where the image is stored is a designated folder (consider using the image name - without prefix - as the folder name)

**Known issue:** If the path to the folder is too long (number of characters), converter may fail to start

**Notice:** Open the image in arivis and make sure the voxel size is correct (select the "i" view and comapre image properties to the original image). In case the voxel size was not set correctly, fix it manualey by selecting the "Edit" Button

## 2. Inner vein object
Open the image in Arivis and load the pipeline that can be found here
