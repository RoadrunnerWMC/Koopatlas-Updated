from common import *


class KPTilesetChooserDialog(QtWidgets.QDialog):
    def __init__(self, label='Choose a tileset', specials=None):
        QtWidgets.QDialog.__init__(self)

        self.setWindowTitle('Select Tileset')
        self.setWindowIcon(QtGui.QIcon('Resources/Koopatlas.png'))

        self.label = QtWidgets.QLabel(label)
        self.label.setWordWrap(True)

        # can't be assed to create a model
        self.chooser = QtWidgets.QListWidget()

        self.nameList = list(KP.knownTilesets.keys())
        self.nameList.sort()

        # this piece of the API is kinda shitty but whatever
        self.specials = specials
        if specials:
            self.chooser.addItems(self.specials)
        self.chooser.addItems(self.nameList)

        self.chooser.currentRowChanged.connect(self.handleCurrentRowChanged)
        self.chooser.itemActivated.connect(self.handleItemActivated)

        self.buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok |
                QtWidgets.QDialogButtonBox.Cancel)

        self.okButton = self.buttons.button(QtWidgets.QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.chooser)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def handleCurrentRowChanged(self, row):
        self.okButton.setEnabled(row != -1)

    def handleItemActivated(self, item):
        self.accept()

    def getChoice(self):
        item = self.chooser.currentItem()
        number = self.chooser.currentRow()

        if item is None:
            return None
        else:
            if self.specials is not None and number < len(self.specials):
                return number
            else:
                return str(item.text())


    @classmethod
    def run(cls, *args):
        dialog = cls(*args)
        result = dialog.exec_()

        if result == QtWidgets.QDialog.Accepted:
            return dialog.getChoice()
        else:
            return None




class KPAnimationPresetChooser(QtWidgets.QDialog):
    def __init__(self, label='Choose a preset to add:', specials=None):
        QtWidgets.QDialog.__init__(self)

        self.setWindowTitle('Add Preset')
        self.setWindowIcon(QtGui.QIcon('Resources/Koopatlas.png'))

        self.label = QtWidgets.QLabel(label)
        self.label.setWordWrap(True)

        # can't be assed to create a model
        self.chooser = QtWidgets.QListWidget()

        settings = KP.app.settings
        import mapfile

        if settings.contains('AnimationPresets'):
            self.presetList = mapfile.load(settings.value('AnimationPresets'))
            self.presets = mapfile.load(settings.value('AnimationPresetData'))

        else:
            self.presetList =  ["Circle", "Wiggle", "Drifting Cloud"]
            self.presets = [   [["Loop", "Sinusoidial", 200.0, "X Position", -200.0, 200.0, 0, 0],
                                ["Loop", "Cosinoidial", 200.0, "Y Position", -200.0, 200.0, 0, 0]],

                               [["Reversible Loop", "Sinusoidial", 50.0, "Y Scale", 100.0, 120.0, 0, 0],
                                ["Loop", "Cosinoidial", 50.0, "X Scale", 100.0, 90.0, 0, 0],
                                ["Reversible Loop", "Sinusoidial", 20.0, "Angle", 10.0, -10.0, 0, 0]],

                               [["Loop", "Sinusoidial", 5000.0, "X Position", -400.0, 400.0, 0, 0],
                                ["Loop", "Sinusoidial", 200.0, "Y Position", 10.0, -10.0, 0, 0],
                                ["Reversible Loop", "Linear", 500.0, "Opacity", 80.0, 40.0, 0, 0]]  ]

            settings.setValue('AnimationPresets', mapfile.dump(self.presetList))
            settings.setValue('AnimationPresetData', mapfile.dump(self.presets))


        self.chooser.addItems(self.presetList)

        self.chooser.currentRowChanged.connect(self.handleCurrentRowChanged)
        self.chooser.itemActivated.connect(self.handleItemActivated)

        self.buttons = QtWidgets.QDialogButtonBox(
                QtWidgets.QDialogButtonBox.Ok |
                QtWidgets.QDialogButtonBox.Cancel)

        self.okButton = self.buttons.button(QtWidgets.QDialogButtonBox.Ok)
        self.okButton.setEnabled(False)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.chooser)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

    def handleCurrentRowChanged(self, row):
        self.okButton.setEnabled(row != -1)

    def handleItemActivated(self, item):
        self.accept()

    def getChoice(self):
        item = self.chooser.currentItem()
        number = self.chooser.currentRow()

        if item is None:
            return None
        else:
            return self.presets[number]


    @classmethod
    def run(cls, *args):
        dialog = cls(*args)
        result = dialog.exec_()

        if result == QtWidgets.QDialog.Accepted:
            return dialog.getChoice()
        else:
            return None





def getTextDialog(title, label, existingText=''):

    text, ok = QtWidgets.QInputDialog.getText(KP.mainWindow, title, label, QtWidgets.QLineEdit.Normal, existingText)

    print(text)
    if ok and text != '':
        return text
    else:
        return None



