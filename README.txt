You should now have ICAT installed with your selected authenticators 
and any other components you chose to install.

The installation log will be found in the installation directory you chose.

You can run the installation again to change most of the parameters.

There is an uninstall program in the installation directory which 
should uninstall everything except for property files for each 
component.

The installation directory has a directory for each component. 
To reconfigure a single component go to the directory for that 
component (other than glassfish), edit the appropriate properties file
and run, in the case of unix, "python setup install -v"

To permit complete reconfiguration of a component simply delete the
directory for that component.

To update a component unzip the distribution into the installation 
directory, allowing it to overwrite existing files, change directory
to the directory of that component and run "python setup install -v". 
After doing this attempting to re-run the installer may not work as 
expected.