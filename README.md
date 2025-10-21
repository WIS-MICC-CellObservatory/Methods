# Methods
This repository contains all the general methods and pipelines that we develop.

**Table of contents**
1. Fiji

   1.1 LSCF Library
   
   1.2 Macro/Headless macro templates
2. QuPath

   2.1 LSCF Scripts
   
   2.2 Running QuPath on Wexac
3. Python
 
   3.1 LSCF Apps
   
   3.2 LSCF Jupyter notebooks

   3.3 Sharing python solution with users

   3.4 User interface template
4. Arivis
   
   4.1 LSCF Python components
5. PipeLines
   
   5.1 Nimbus Pipeline
## Fiji
1. LSCF Library: For sharing common methods between macro solutions
2. Macro template: A skeleton for writing Fiji macros
3. Headless macro template: A skeleton for writing Fiji macros that run in Wexac

### LSCF Library
Fiji macro does not support packages and the only way to share methods between macros is by adding them to ...\Fiji.app\macros\Library.txt.
The following is the way we do it:
1. The latest and greatest Library.txt is stored here ([Library.txt](../../tree/main/Fiji)).
2. Before writing a new macro we update the version of our local ...\Fiji.app\macros\Library.txt with it.
3. If we use a shared method in a macro we pass to a user, we copy it from the library to the macro before we pass it to the user
4. Every method that we include in the library ends with "_LSCF" and is documented following the convention: input/output/short description, as the documentation is visible in Fiji editor as tooltip
5. When we write a new method to the library, we notify the other members and update it here

### Macro template
This template contains standard ways to:
1. Read parameters from the user and save them to disk (Json format)
2. Open files
3. Recursively run on a whole folder
4. Take cleanup and initialization steps

The template can be found here ([Macro Template.ijm](../../tree/main/Fiji)).

### Headless Macro template
This template contains standard ways to:
1. Read parameters from Json file
2. Do what the other temple does

The template can be found here ([Macro Template_headless.ijm](../../tree/main/Fiji)).

For details how to run Fiji macro on Wexac machine see ([Running Fiji on Wexac.md](../../tree/main)).

## QuPath
1. Running QuPath on Wexac

## Python
1. Sharing python solution with users
2. User interface template

### Sharing python solution with users
Python solutions depend heavily on existing packages and when we develop a solution it would probably include some external packages.

To make sure the packages are installed on the computer the user runs our solution, in anaconda we create a designate environment for each solution we provide:
**Steps**
1. Create a new environment: The environment name should be **xxx_env** where *xxx* is the name of the solution file
2. Install python packages
3. Develop Solution file: Either a Jupyter notebook or a python file
4. Export environment: name the export file **xxx_env.yml** where *xxx* is the solution file name. Use the following command:
<p align="center">
  conda env export -n "xxx_env" > "xxx_env.yml"
</p>
Once the solution is ready we provide the users with 3 files:

1. The solution file (ends with **.py** or **.pyinb**, e.g. imzml.pyinb)
2. environment file that we created in with the export command above (e.g., xxx_env.yml)
3. README.md file with details how to run the solution

General instructions regarding how users can run the solution file can be found in ([Running LSCF Python solution.md](../../tree/main)).

