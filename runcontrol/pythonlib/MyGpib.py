#!/usr/bin/env python
#
"""
Thin layer on top of linux-gpib Python interface to make it look like pyvisa

To pick up Gpib.py need:
PYTHONPATH=/usr/local/lib64/python2.6/site-packages
"""

import Gpib

def instrument(resource_name, **keyw):
    """
    Instantiates a Gpib object
    return value: the generated Gpib instance
    """
    return MyGpib(resource_name=resource_name, **keyw)

class MyGpib(object):

    def __init__(self, boardId=0 , resource_name="" ):
        """
        Decodes the a resource name like GPIB0::13
        into the primary address (=13 in this example) then
        instantiates, and returns, a linux-gpib object
        """
        self.boardId = boardId
        #print "resource name = " , resource_name
        # GPIBAddress is something like "GPIB0::13"
        primaryAddress = int(resource_name[ (resource_name.find("::")+2): ])
        #print "Gpib address = " , primaryAddress
        self.instrument = Gpib.Gpib(boardId,primaryAddress)

    def write(self,command):
        return self.instrument.write(command)

    def read(self,maxSize=1024):
        return self.instrument.read(maxSize)

    def ask(self,command,maxSize=1024):
        self.instrument.write(command)
        return self.instrument.read(maxSize)


