import mido
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
import sys
# C:\Users\vimal\Documents\repos\python\venvPyQt\Lib\site-packages\qt5_applications\Qt\bin\designer.exe


class MyWindow(QMainWindow):

    def __init__(self, deviceAdpt):
        super(MyWindow, self).__init__()
        self.ui = None
        self.deviceAdpt = deviceAdpt
        self.deviceAdpt.setUI(self)
        uic.loadUi('zoom-pyqt-layout.ui', self)
        self.setupSignalsAndSlots()
        self.show()

    def setupSignalsAndSlots(self):
        print(self.patch_grid.count())
        banks = (self.patch_grid.itemAt(i).widget()
                 for i in range(self.patch_grid.count()))
        for i in range(self.patch_grid.count()):
            QVBoxLayout = self.patch_grid.itemAt(i)
            for j in range(QVBoxLayout.count()):
                widget = QVBoxLayout.itemAt(j).widget()
                if isinstance(widget, QPushButton):
                    widget.clicked.connect(self.deviceAdpt.patchButtonPressed)


class ZoomG1UIAdapter():
    def __init__(self, device):
        self.device = device
        self.ui = None

    def setUI(self, ui):
        self.ui = ui

    def patchButtonPressed(self):
        button = self.ui.sender()
        buttonName = button.objectName()
        print(buttonName)
        bankNum = buttonName[-2]
        patchNum = buttonName[-1]
        device.selectPatch(bankNum, patchNum)
        patch = device.makePatch(bankNum, patchNum)
        print(patch.slots)
        self.ui.textEdit_1.setText(patch.name)
        self.ui.textEdit_1.append(str(patch.slots))
        self.ui.textEdit_2.setText('\n'.join(patch.data))
        button.setText(patch.name)
        self.ui.labelPatchName.setText(patch.name)
        self.ui.textEdit_2.setText(patch.desc)


class ZoomG1():
    def __init__(self):
        midiIn = mido.open_input("ZOOM G Series 0")
        midiOut = mido.open_output("ZOOM G Series 1")
        midiIn.close()
        midiOut.close()

    class Patch:
        def __init__(self, patchData):
            nameLocations = [[43, 44], [46, 52], 54]
            #descLocations = [[100, 328]]
            descLocations = [[55, 328]]
            slotLocations = {"name": [[38, 38+7]]}
            self.name = ""
            self.desc = ""
            self.data = []
            self.raw = []
            self.slots = []

            self.name = self.extractStringFromPatchSummary(
                patchData["summary"], nameLocations)

            self.desc = self.extractDescFromPatchSummary(
                patchData["summary"], descLocations)

            self.slots = self.extractSlotsFromPatchSlots(
                patchData["slots"], slotLocations)

            for i, byte in enumerate(patchData["summary"].split()):
                char = chr(int('0x'+byte, 16))
                self.data.append(str(i) + " " + char)
                self.raw.append(byte + " ")

        def extractStringFromPatchSummary(self, patchSummary, locations):
            extractedString = ""
            for locationRange in locations:
                if not isinstance(locationRange, list):
                    byte = patchSummary.split()[locationRange]
                    extractedString += chr(int('0x'+byte, 16))
                else:
                    for location in range(locationRange[0], locationRange[1]+1):
                        byte = patchSummary.split()[location]
                        extractedString += chr(int('0x'+byte, 16))
            return extractedString

        def extractDescFromPatchSummary(self, patchData, locations):
            extractedString = ""
            stringified = ''.join(patchData.split())
            # print(stringified)
            #start = stringified.find("54584531", 55) // 2 + 6
            start = stringified.find("5458", 110) // 2 + 6
            print("found", start)
            start = stringified.find("5458", start) // 2 + 6
            print("found", start)

            prefixString = ""
            bytes_to_skip = 4
            bytes_skipped = 0
            for location in range(start, len(patchData.split())):
                byte = patchData.split()[location]
                idx_txe1 = prefixString.find('TXE1')
                if idx_txe1 == -1:
                    if 32 <= int('0x'+byte, 16) and int('0x'+byte, 16) <= 126:
                        prefixString += chr(int('0x'+byte, 16))
                else:
                    if 32 <= int('0x'+byte, 16) and int('0x'+byte, 16) <= 126:
                        if bytes_skipped < bytes_to_skip:
                            bytes_skipped += 1
                        else:
                            extractedString += chr(int('0x'+byte, 16))
                    else:
                        if bytes_skipped < bytes_to_skip:
                            bytes_skipped += 1
                        else:
                            pass
                            #extractedString += '[' + byte + ']' + ' '
            #extractedString = extractedString[idx + 5:]
            idx_edtb = extractedString.find('EDT')
            extractedString = extractedString[0: idx_edtb]
            return extractedString

            for locationRange in locations:
                if not isinstance(locationRange, list):
                    byte = patchData.split()[locationRange]
                    extractedString += chr(int('0x'+byte, 16))
                else:
                    for location in range(locationRange[0], locationRange[1]+1):
                        byte = patchData.split()[location]
                        extractedString += chr(int('0x'+byte, 16))
            return extractedString

        def extractSlotsFromPatchSlots(self, patchSlots, locations):
            slots = []
            for slot in patchSlots:
                name = ""
                for location in locations["name"]:
                    if isinstance(location, list):
                        for i in range(location[0], location[1]+1):
                            byte = slot.split()[i]
                            if not byte == '00':
                                name += chr(int('0x'+byte, 16))
                slots.append({"name": name})
            return slots

    def makePatch(self, bankNum, patchNum):
        patchData = self._downloadPatchData(bankNum, patchNum)
        return self.Patch(patchData)

    def selectPatch(self, bankNum, patchNum):
        midiIn = mido.open_input("ZOOM G Series 0")
        midiOut = mido.open_output("ZOOM G Series 1")

        midiMessage = mido.Message('control_change', control=0, value=0)
        print("cc", midiMessage.hex())
        midiOut.send(midiMessage)

        midiMessage = mido.Message(
            'control_change', control=32, value=int(bankNum)-1)
        print("cc", midiMessage.hex())
        midiOut.send(midiMessage)

        midiMessage = mido.Message('program_change', program=int(patchNum))
        print("pc", midiMessage.hex())
        midiOut.send(midiMessage)
        import time
        time.sleep(0.003)
        midiIn.close()
        midiOut.close()

    def _downloadPatchData(self, bankNum=1, patchNum=0):
        patchData = {"summary": [],
                     "slots": []}

        midiIn = mido.open_input("ZOOM G Series 0")
        midiOut = mido.open_output("ZOOM G Series 1")

        sysexTemplate = "f0 52 00 6e 46 00 00 0{} 00 0{} 00 f7"
        sysexString = sysexTemplate.format(int(bankNum) - 1, patchNum)
        sysexBytes = [int('0x'+byte, 16) for byte in sysexString.split()]
        sysexMessage = mido.Message(type='sysex', data=sysexBytes[1:-1])

        midiOut.send(sysexMessage)
        sysexResponse = midiIn.receive()
        patchData["summary"] = sysexResponse.hex()

        sysexTemplate = "f0 52 00 6e 64 02 0{} 0{} 00 f7"
        i = 0
        while i <= 5:
            sysexString = sysexTemplate.format(i, i)
            sysexBytes = [int('0x'+byte, 16) for byte in sysexString.split()]
            sysexMessage = mido.Message(type='sysex', data=sysexBytes[1:-1])
            midiOut.send(sysexMessage)
            sysexResponse = midiIn.receive()
            patchData["slots"].append(sysexResponse.hex())
            i += 1

        midiIn.close()
        midiOut.close()
        return patchData


if __name__ == '__main__':
    app = QApplication(sys.argv)
    device = ZoomG1()
    deviceAdapter = ZoomG1UIAdapter(device)
    window = MyWindow(deviceAdapter)
    sys.exit(app.exec_())
