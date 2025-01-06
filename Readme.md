##########################################################################################
MinOCA : Learning DROCA using polynomially many queries using a SAT solver
Author: Prince Mathew
##########################################################################################
#Badges: Functional, Reusable, and Available 
Link: 

##########################################################################################
Running the code:
##########################################################################################
Copy the contents of this directory to your machine.

1. Open your terminal/command prompt and navigate to the directory containing this file. 
	Alternatively, right click inside the folder containing this file and click "open in Terminal".
2. Execute the following command: pip3 install --no-index --find-links ./Packages/ -r requirements.txt
	-- This will install the required packages to run the code (for Ubuntu 22.04.1 LTS running  Python 3.10.4). 
3. Navigate to the directory ./MinOCA_Implementation/ by running the command: cd MinOCA_Implementation/
4. Execute the following command: python3 LearningDROCA.py
5. Follow the on-screen instructions based on your requirements.


Note: Create folders 'inputs' and 'Trash' inside the directory MinOCA_Implementation if not already present



##########################################################################################
File Organisation:
##########################################################################################

The folder ./Datasets/ contains the two datasets (Dataset1 and Dataset1) used for experiments.
	The file ./Datasets/DatasetFormat_ReadMe explains the format of the input specified.
	./Datasets/Dataset1/: contains the inputs used to compare MinOCA and BPS. Here, the final states can be reached only by a zero test.
	./Dataset2/Dataset2/: contains the inputs used to evaluate the performance of MinOCA. The notion of acceptance is by final state.
The folder ./ResultsCSV/ contains the results of experiments on both datasets.
	./ResultsCSV/Dataset1/BPS/ : contains the results of experiments on BPS using Dataset1.
	./ResultsCSV/Dataset1/MinOCA/ : contains the results of experiments on MinOCA using Dataset1.
	./ResultsCSV/Dataset2/MinOCA/ : contains the results of experiments on MinOCA using Dataset2.

The folder ./MinOCA_Implementation/ contains the Python implementation of MinOCA.
The folder ./MinOCA_Implementation/inputs/ is initially empty and will have the random DROCAs generated using the code.
The outputs of experiments will be stored in the folder ./MinOCA_Implementation/outputs/ as a .csv file.
A representative sample of the inputs used to compare MinOCA and BPS is provided in the folder ./MinOCA_Implementation/TestCases/Representative_Sample/.
A set of inputs containing 10 known DROCAs are given in the folder ./MinOCA_Implementation/TestCases/Known/.
The folder ./MinOCA_Implementation/TestCases/Trash/ will contain the intermediate files generated such as the .dot image of the final DROCA, if drawn. 

The files acyclic.py, minimiser.py, hopcroft.py, sdfa.py, strunion.py and dfaminer.py in the folder ./MinOCA_Implementation/ are part of the DFAMiner tool that finds the minimal separating DFA (https://github.com/liyong31/DFAMiner) Copyright (c) 2024 Yong Li.

The folder ./Extras contains the code used to run the inputs on BPS.
The folder ./Packages/ contains the packages required to run the code on Ubuntu 22.04.1 LTS running Python 3.10.4
The file ./requirements.txt contains the list of packages required.

The implementation of MinOCA is contained in the file ./MinOCA_Implementation/minOCA.py


######################################### Additional Information ###############################

##########################################################################################
					  				Packages Needed
##########################################################################################

#The following Python packages are required to run the code
. python-sat - SAT solver in Python
. dfa - Used for converting dfa object to dictionary format and vice-versa
. pydot - Used for generating and viewing the final OCA
. graphviz - Graph visualisation software 

Installation Instructions.
Mac/Windows:
pip install python-sat
pip install dfa
pip install pydot
pip install graphviz


Note: Make sure that the directory in which you have installed the package is added to your systems environment variable PATH.

##########################################################################################
								  Optional Softwares 
##########################################################################################

Graphviz
The code to view the graph while running the code is commented out for now. One can use this feature after installing Graphviz in your operating system. 

Linux: 
sudo apt-get install graphviz

Mac:
Installation command: brew install graphviz

Windows:
Download the Graphviz installer from https://graphviz.org/download/ and install it.
32-bit: https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/2.49.0/stable_windows_10_cmake_Release_Win32_graphviz-install-2.49.0-win32.exe
64-bit: https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/2.49.0/stable_windows_10_cmake_Release_x64_graphviz-install-2.49.0-win64.exe


Pandas					
#The package is needed only if you want to write the Hankel matrix in a file (i.e. if you are using the function PrintTableToFile).
#Not currently needed
. Pandas - open-source data analysis and manipulation tool
Installation Instructions.

Mac/Windows:
pip install pandas

#Note
We performed our experiments on an Apple M1 chip with 8GB of RAM, running macOS Sonoma Version 14.3. 