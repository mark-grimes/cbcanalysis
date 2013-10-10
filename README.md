cbcanalysis
===========

CMSSW code to analyse data for the CBC, and python scripts for the xdaq readout.
The directory structure is setup so that it can be included as a git submodule in CMSSW under "XtalDAQ". To include in CMSSW:

    cd $CMSSW_BASE/src
    git submodule add git@github.com:kknb1056/cbcanalysis.git XtalDAQ/OnlineCBCAnalyser

Some directories are hard coded however, I can't figure out how to get XDAQ to use environment variables for paths in the configuration file. You'll need to change runcontrol/analysisTest.xml to reflect wherever your CMSSW_BASE is. Look for the line where the variable "parameterSet" is set for the FUEventProcessor.
