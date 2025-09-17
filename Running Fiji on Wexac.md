# Running Fiji on Wexac
## Introduction
Wexac provides powerful machines to run Fiji in both batch and interactive modes. In both modes Fiji can be embedded in a docker that isolates it from the specific machine on which it runs. Having an isolated environment is the preferred way as it ensures stability and reproducibility.
This document goes over the technicalities, suggests best practices and list some of the known bugs/issues.
## Interactive mode
This mode enables the user to run on Wexac as if it was a workstation
Once you enter one of Wexac login machines (see Appendix: Accessing Wexac for details), you run the following command as to acquire an interactive machine:
bsub -XF -Is -R "rusage[mem=200000]" -gpu num=1 -q gpu-interactive /bin/bash
You can set the amount of memory you want (change mem=200000) or weather you want a machine with (-q gpu-interactive) or without (-q interactive) gpu.
Once a machine is found, you enter your password, and you can run Fiji (or any other app that is installed on Wexac). For Fiji you run the following command:
~/data/Fiji.app/ImageJ-linux64 --heap 100GB &
Where ~/data/Fiji.app/ImageJ-linux64 is the path to Fiji executable, and  --heap 100GB sets the amount of memory it needs
### Known issues
1.	CLIJ does not work as it is based on OpenCL that is not installed on Wexac machines
2.	Currently the session may be terminated unexpectedly by Wexac
3.	File path (including name) should not include ‘,’ or ‘;’

## Batch mode
Once you enter one of Wexac login machines (see Appendix: Accessing Wexac for details),
The best way to run a fiji job (or ant job) is by preparing a batch file (e.g., runFiji.bsub) that you submit. 
For Fiji the batch file should contain:

    #BSUB -q gpu-interactive
    #BSUB -R rusage[mem=10GB]
    #BSUB -gpu num=1 
    #BSUB -J Ab35alphSMA
    #BSUB -o "<Path to Result folder> /%J.out"
    #BSUB -e "<Path to Result folder> /%J.err"
    "<Path to Fiji shell script>/RunHeadlessFiji.sh" "<Path to Fiji app>/Fiji.app/ImageJ-linux64" "<Path to Fiji macro>/MyFijiMacro.ijm" "Path to JSon parameters file"
Where RunHeadlessFiji.sh can be dowloaded from here ([Fiji folder](../../tree/main/Fiji)).

**Notice:**
•	Each of the above is surrounded by double quates, this is to enable spaces in them.
•	Wexac job can accept many parameters that may be relevant for the job and you need to consult documentation for additional options.

### Known issues
1.	CLIJ does not work as it is based on OpenCL that is not installed on Wexac machines
2.	File path (including name) should not include ‘,’ or ‘;’
3.	Unexplained crashes may occur…
4.	Erode 3D creates an additional window with the exact same title as the window that it works on. We recommend not using this command.
5.	Imaris files pop up a window that requires user resposes
### Best Practices
1.	We suggest that every Fiji macro that you run in batch will have two versions, an interactive version and a batch version. The latter will have the same macro name as the former, with _headless added to it.
2.	The batch and non-batch versions will be based on our macro templates (see Appendix: Fiji macro templates, for details). They are based on the following principles:
-	The only difference between the two macros is in the way the macro parameters are read: The interactive macro generates an input window, while the batch macro reads them from a “Paramteres.txt” input file that its path is passed as an argument to it.
-	The macros write the input parameters to a “Paramteres.txt” file in Json format. This format is the expected format of the input file to the batch macro
