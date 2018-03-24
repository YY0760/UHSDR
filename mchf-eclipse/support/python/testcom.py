from __future__ import print_function


#comPort="COM15"
#comPort="/dev/ttyACM0"
comPort = ""

import serial
import sys
import json

# we list all used cat command codes here
# this list includes the officially known FT817 codes (including the "undocumented" ones)
class CatCmdFt817:
    READ_EEPROM = 0xBB
    WRITE_EEPROM = 0xBC

# this list includes the special UHSDR codes implemented only in the UHSDR dialect of FT817 CAT (which must be different from the Ft817 ones)
class CatCmdUhsdr(CatCmdFt817):
    UHSDR_ID = 0x42  # this will return the bytes ['U', 'H' , 'S', 'D', 'R' ] and is used to identify an UHSDR with high enough firmware level
    

class CatCmd(CatCmdUhsdr):
    True

class UhsdrConfigIndex:
    VER_MAJOR = 176
    VER_MINOR = 310
    VER_BUILD = 171
    NUMBER_OF_ENTRIES = 407

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
class catSerial:
    def __init__(self, comObj):
        self.comObj = comObj
    def sendCommand(self, command):
        bytesWritten = self.comObj.write(command)
        return bytesWritten == 5

    def readResponse(self,count):
        response = self.comObj.read(count)
        return (len(response) == count,response)
    


class catCommands:
    def __init__(self, catObj):
        self.catObj = catObj

    def execute(self, cmd, count):
        if self.catObj.sendCommand(cmd):
            ok,res = self.catObj.readResponse(count)
            return ok,bytearray(res)
        else:
            return (False,bytearray([]))

    def readEEPROM(self, addr):
        cmd = bytearray([ (addr & 0xff00)>>8,addr & 0xff, 0x00, 0x00, CatCmd.READ_EEPROM])
        ok,res = self.execute(cmd,2)
        if ok:
            return res[1] * 256 + res[0]
        else:
            return ok

    def readUHSDR(self):
        cmd = bytearray([ 0x00, 0x00 , 0x00, 0x00, CatCmd.UHSDR_ID])
        ok,res = self.execute(cmd,5)

        return res == bytearray("UHSDR")
   

    def writeEEPROM(self, addr, value16bit):
        cmd = bytearray([ (addr & 0xff00)>>8,addr & 0xff, (value16bit & 0xff) >> 0, (value16bit & 0xff00) >> 8, CatCmd.WRITE_EEPROM])
        ok,res = self.execute(cmd,1)
        return ok
    
    def readUHSDRConfig(self, index):
        return self.readEEPROM(index + 0x8000);

    def writeUHSDRConfig(self, index, value):
        return self.writeEEPROM(index + 0x8000, value);

class UhsdrConfig():
    def __init__(self, catObj):
        self.catObj = catObj

    def getVersion(self):
        return (self.catObj.readUHSDRConfig(UhsdrConfigIndex.VER_MAJOR),
                    self.catObj.readUHSDRConfig(UhsdrConfigIndex.VER_MINOR),
                    self.catObj.readUHSDRConfig(UhsdrConfigIndex.VER_BUILD))
    
    def isUhsdrConnected(self):
        return self.catObj.readUHSDR()
    
    def getConfigValueCount(self):
        return self.catObj.readUHSDRConfig(UhsdrConfigIndex.NUMBER_OF_ENTRIES)
        
    def getValue(self, index):
        # TODO: do some range checking here
        return self.catObj.readUHSDRConfig(index)


if __name__ == "__main__":   
    if (len(comPort) > 0):
        mySer = serial.Serial(comPort, 38400, timeout=0.500, parity=serial.PARITY_NONE)
        myCom = catSerial(mySer)
        myCAT = catCommands(myCom)
        myUHSDR = UhsdrConfig(myCAT)

        if myUHSDR.isUhsdrConnected():
            print("UHSDR Firmware Version", myUHSDR.getVersion())
            valList = []
            data = {}
            data['eeprom'] = []
            numberOfValues = myUHSDR.getConfigValueCount()
            for index in range(numberOfValues):
                val = myUHSDR.getValue(index)
                valList.append(val)
                data['eeprom'].append({ 'addr' : index , 'value' : val })
            #print(valList)
                
            if all(val is not False for val in valList) or len(valList) != 0:
                with open('uhsdr_config.json', 'w') as outfile:  
                    json.dump(data, outfile, indent=4)
                    outfile.close()
                    print("saved data to uhsdr_config.json file")
            else:
                eprint("Could not read list sucessfully")
        else:   
            eprint("Could not find a connected UHSDR with extended CAT commands (required)")
            
        #print myCAT.readEEPROM(512);
        #print myCAT.readUHSDRConfig(512);
        #print myCAT.writeEEPROM(512,0xabcd);
        #print myCAT.writeUHSDRConfig(512,0xfedc);
    else:
        eprint("please specify UHSDR TRX com port at begin of file")


