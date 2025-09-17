# Metods
This repository contains all the general methods and pipelines that we develop
## Fiji
1. LSCF Library: For sharing common methods between macro solutions
2. Macro template: A skelaton for writing Fiji macros
3. Headless macro template: A skelaton for writing Fiji macros that run in Wexac

### LSCF Library
Fiji macro does not support packages and the only way to share methods between macros is by adding them to ...\Fiji.app\macros\Library.txt.
The following is the way we do it:
1. The latest and greatest Library.txt is stored here ([Library.txt](../../tree/main/Fiji)).
2. Before wrting a new macro we update the version of our local ...\Fiji.app\macros\Library.txt with it.
3. If we use a shared method in a macro we pass to a user, we copy it from the library to the macro before we pass it to the user
4. Every method that we include in the library ends with "_LSCF"  and is documented following the convention: input/output/short description, as the documentation is visible in Fiji editor as tooltip
5. When we write a new method to the library, we notify the other members and update it here

### Macro template
This template contains standart ways to:
1. Read parameters from the user and save them to disk (JSon format)
2. Open files
3. Recurively run on a whole folder
4. Take cleanup and initialization steps

The template can be found here ([Macro Template.ijm](../../tree/main/Fiji)).

### Headless Macro template
This template contains standart ways to:
1. Read parameters from JSon file
2. Do what the other temple does

The template can be found here ([Macro Template_headless.ijm](../../tree/main/Fiji)).

For details how to run Fiji macro on Wexac machine see ([Running Fiji on Wexac.md](../../tree/main)).
