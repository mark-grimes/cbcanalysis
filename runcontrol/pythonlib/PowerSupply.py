#!/usr/bin/python
#
# Use PyVisa to control a Agilent E3646 power supply
#
# David Cussans, August, 2011
#
# based on PulseGen.py by 
# Robert Frazier, Apr, 2011
#
# Modifications:
# DGC , 5/Sept/12: If can't find visa will look for MyGpib, which is a wrapper
#                  around the python wrapper around linux-gpib .....
# Grimes, 23/Sep/13: Added a verbosity option to limit the amount of output. Also
#                    added some methods to get some states. Changed some error messages
#                    to exceptions. Changed soft voltage limit to less than or equal
#                    instead of just less than.
# 
# on Cygwin, before executing Python type:
# PYTHONPATH=/cygdrive/c/Python25/Lib/site-packages/pyvisa/

try:
    from visa import *
except:
    #print "Warning No working VISA. Looking for linux-gpib wrapper"
    try:
        from MyGpib import *
        #print "found linux-gpib wrapper"
    except:
        print "Can't find VISA or MyGpib (linux-gpib wrapper: Power supply control won't work)"
    
class PowerSupply(object):
    def __init__(self, gpibAddress = "GPIB0::13" , psuPresent=1, verbose=True ):
        self.powerSupply = instrument(gpibAddress)
        self.verbose=verbose
        self.psuPresent = psuPresent

        # Get the pulse-generator's ID
        if psuPresent == 1:
            instrumentId = self.powerSupply.ask("*IDN?")
            if self.verbose: print "PowerSupply: talking to:", instrumentId

            self.voltageLimit = 5
            if self.verbose: print "Soft voltage limit set to " , self.voltageLimit
        else:
            print "Declaring no PSU present. Not setting up"
    
    def selftest(self):
        # Perform a self-test - should be 0 if all ok
        selfTestResult = self.powerSupply.ask("*TST?")
        if selfTestResult == "+0" or selfTestResult == "+0\n":
            print "Power supply's self-test passed ok"
        else:
            errorStr = "WARNING! The power supply's self-test failed with code=" + selfTestResult + "!       <-----  PROBLEM FOUND!"
            print errorStr

    
    def reset(self):
          print "Resetting the power supply..."
          self.powerSupply.write("*RST")
          print "...Done!"


    def setChannel(self,  output = "OUTP1"):
         """selects which output to read/write"""

         self.powerSupply.write("INST " + output)
         if self.verbose:
         	outp = self.powerSupply.ask("INST?")
         	print "Controlling output " + outp

    def getChannel(self):
    	return self.powerSupply.ask("INST?")
         
    def setOutput(self, voltage = 0 , current = 0.005 , output = "OUTP1"):
         """
         Set the output voltage and current.
         output selects which output to vary
         """
         if self.psuPresent == 1:
             if (voltage<=self.voltageLimit):
                 self.setChannel( output = output )
                 self.powerSupply.write("APPLY " + str(voltage) + " , " + str(current) )
                 state = self.powerSupply.ask("APPLY?" )
                 if self.verbose: print "Power supply reports Output Voltage, Current = " + state
             else:
                 raise Exception("Soft-limit set to %s . Refusing to set output voltage to %s" % ( self.voltageLimit , voltage))
         
    def getOutput(self,  output = "OUTP1"):
         """
         Reads the output voltage and current.
         output selects which output to read
         """
         self.setChannel( output = output )

         state = self.powerSupply.ask("APPLY?" )
         if self.verbose: print "Power supply reports Voltage, current = " + state
         # Get the state in number format
         splitState=state.split('"')[1].split(',')
         return {"voltage":float(splitState[0]),"current":float(splitState[1])}

    
         
    def getOnOff(self , output = "OUT1" ):
         """ Reads the on/off status of an output"""
         outp = self.powerSupply.ask("OUTP?")
         print "Output State (0/1 = off/on) =  " + outp

    def isOn(self):
    	""" Returns whether the output is on or off as a boolean """
    	outp = self.powerSupply.ask("OUTP?")
    	if outp=="1" or outp=="1\n": return True
    	elif outp=="0" or outp=="0\n": return False
    	else: raise Exception('The command "OUTP?" returned "'+outp+'"')

    def setOn(self , output = "OUT1" ):
         outp = self.powerSupply.write("OUTP 1")
         if self.verbose: self.getOnOff()


    def setOff(self, output = "OUT1" ):
         outp = self.powerSupply.write("OUTP 0")
         if self.verbose: self.getOnOff()

    def setVoltageLimit(self, voltageLimit = 1.25 ):
        """Sets the max voltage. NB. this is a software limit, not the over voltage protection built into the power supply"""
        self.voltageLimit = voltageLimit
        if self.verbose: print "Set soft voltage limit to " , self.voltageLimit

    def getVoltageLimit(self):
    	if self.verbose: print "Set soft voltage limit to " , self.voltageLimit
    	return self.voltageLimit



