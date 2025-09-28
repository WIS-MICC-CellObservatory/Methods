# Running LSCF Python solution
For users to be able to run a python solution LSCF provides they should do the following steps
1. Setting up the computer
2. Run the solution

This document detailes these steps
## Setting up the computer
These steps are done once for each computer
1. Setting the proxy (for isolated computers such as LSCF work-statoins)
2. Install Anaconda (if not installed)
3. Create the solution enviorenment

### Setting the proxy
In the first run the user may need to set the proxy of the workstation (This is the case when working on LSCF workstaions):

**Steps**
1. Open Proxy settings
2. Enable the "Use a proxy Server" checkbox
3. Set the Address to be: http://bcproxy.weizm
4. Set the port 8080
5. Save
<img width="1271" height="996" alt="image" src="https://github.com/user-attachments/assets/bf8307f4-d14a-4c2e-bd33-44946986d54a" />

### Install Anaconda
If Anaconda is installed on the computer it will appear in the Control pannel > Programs > Programs and Feature list:
<img width="1445" height="465" alt="image" src="https://github.com/user-attachments/assets/bab01de0-46bd-447f-b662-bd3d2d7d70cc" />

If not, go to https://www.anaconda.com/download to install it

### Create the solution enviorenment
**Steps**
1. Open an Anaconda prompt
<img width="1027" height="426" alt="image" src="https://github.com/user-attachments/assets/cf167709-6ba0-463e-896c-7903276a3a2a" />

2. Create the Conda relevant environment using the **.yml** file provided (e.g., imzml_env.yml) by running the following command:
<p align="center">
conda env create -f {Path to where .yml file is located on disk}/imzml_env.yml
</p>
This will create **imzml_env** enviorenment
  
## Run the solution
**Steps**
1. Open an Anaconda prompt (See above for details)
2. Navigate to where the solution is stored on disk 

  use cd {path} command to get to the folder where your Jupyter notebook resides. Notice, in case it is on a different drive (e.g., D: and not C:, first switch to that drive by writing the Drive name (e.g., D:) and only then use the cd command

3. Activate the enviorenment (e.g., imzml_env) by running the following command:
<p align="center">
conda activate imzml_env
</p>

4. If the solution is a Jupyter notebook (solution file ends with **.ipynb**), open Jupyter notebook by running:
<p align="center">
Jupyter notebook
</p>
  4.1 Open the relevant Jupyter notebook in the list of notebooks displayed

  4.2 Follow the instructions in the notebook. To run each python code block use CTRL Enter

5. If the solution is a python file (solution file ends with **.py**), run it by running file name (e.g. imzml.py)
<p align="center">
python imzml
</p>
