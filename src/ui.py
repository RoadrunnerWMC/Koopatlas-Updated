# -*- coding: UTF-8 -*-

from common import *
from editorui.editorcommon import *
from editorui.editormain import *
import os, copy
import os.path
import sys

if sys.version_info[0] >= 3:
    unicode = str

def QFileDialog_getOpenFileName(*args, **kwargs):
    retVal = QtWidgets.QFileDialog.getOpenFileName(*args, **kwargs)
    if QtCompatVersion < 0x50000:
        return retVal
    return retVal[0]

def QFileDialog_getOpenFileNames(*args, **kwargs):
    retVal = QtWidgets.QFileDialog.getOpenFileNames(*args, **kwargs)
    if QtCompatVersion < 0x50000:
        return retVal
    return retVal[0]

def QFileDialog_getSaveFileName(*args, **kwargs):
    retVal = QtWidgets.QFileDialog.getSaveFileName(*args, **kwargs)
    if QtCompatVersion < 0x50000:
        return retVal
    return retVal[0]


class KPPathNodeList(QtWidgets.QWidget):

    class KPPathNodeItem(QtWidgets.QTreeWidgetItem):
        def __init__(self, parent, layer, associate):
            QtWidgets.QTreeWidgetItem.__init__(self, parent)

            self.layer = layer
            self.associate = associate

            self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)

        def data(self, index, role=Qt.DisplayRole):

            if role == Qt.DecorationRole:
                if isinstance(self.associate, KPNode):
                    node = self.associate

                    if node.level:
                        return KP.icon('BlackLevel')
                    elif node.mapChange is not None:
                        return KP.icon('Exit')
                    elif len(node.exits) != 2:
                        return KP.icon('Stop')
                    else:
                        return KP.icon('Through')

                else:
                    return KP.icon('LayerPath')

            elif role == Qt.DisplayRole:
                if isinstance(self.associate, KPNode):
                    node = self.associate

                    if node.level:
                        return "Level: {0}".format(node.level)
                    elif node.mapChange is not None:
                        return "Exit: World {0}, entrance {1}".format(node.mapID, node.foreignID)
                    elif len(node.exits) == 3:
                        return "Node: 3-way Junction"
                    elif len(node.exits) == 4:
                        return "Node: 4-way Junction"
                    elif (len(node.exits) == 1) or (len(node.exits) == 0):
                        return "Node: End Point"
                    elif len(node.exits) > 4:
                        return "Illegal Node"
                    else:
                        return "Node: Pass-Through"

                else:
                    animation = PathAnimationNamesList[self.associate.animation]

                    return 'Path: {1}'.format(None, animation)

            elif role == Qt.CheckStateRole:
                return (Qt.Checked if self.layer.visible else Qt.Unchecked)

            else:
                return QtWidgets.QTreeWidgetItem.data(self, index, role)

        def setData(self, column, role = Qt.EditRole, value = None):
            if role == Qt.CheckStateRole:
                self.layer.visible = value

        def layer(self):
            return self.layer

        def associate(self):
            return self.associate

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setDragEnabled(True)
        self.tree.setDragDropMode(self.tree.InternalMove)
        self.tree.setHeaderHidden(True)
        self.tree.currentItemChanged.connect(self.handleRowChanged)
        self.tree.itemClicked.connect(self.handleRowClicked)
        self.tree.itemDoubleClicked.connect(self.jumpToPathNode)
        self.layout.addWidget(self.tree)

        self.toolbar = QtWidgets.QToolBar()
        self.layout.addWidget(self.toolbar)

        self.setupToolbar(self.toolbar)
        self.setLayout(self.layout)

        self.lastTileset = ''

    def reset(self):
        self.tree.clear()

        for layer in KP.map.associateLayers:
            self.loadLayer(layer)

    def setupToolbar(self, tb):
        self.actAddFolder = tb.addAction(KP.icon('NewFolder'), 'Add Folder', self.addFolder)
        self.actRemoveFolder = tb.addAction(KP.icon('DelFolder'), 'Remove Folder', self.removeFolder)
        self.selectTileset = tb.addAction(KP.icon('LayerNewTile'), 'Select Tileset', self.setTileset)

    def handleRowChanged(self, currentItem, previousItem):
        currentIsNodeItem = isinstance(currentItem, self.KPPathNodeItem)
        prevIsNodeItem = isinstance(previousItem, self.KPPathNodeItem)

        if currentIsNodeItem:
            self.selectedLayerChanged.emit(currentItem.layer)
        if prevIsNodeItem:
            previousItem.associate.qtItem.setLayerSelected(False)
        if currentIsNodeItem:
            currentItem.associate.qtItem.setLayerSelected(True)

        if KP.app.keyboardModifiers() & Qt.ControlModifier and currentIsNodeItem:
            layer = currentItem.layer

            KP.mainWindow.scene.clearSelection()
            listToUse = layer.objects + layer.doodads

            for obj in listToUse:
                item = obj.qtItem
                if item:
                    item.setSelected(True)

    def handleRowClicked(self, item):
        if isinstance(item, self.KPPathNodeItem):
            self.layerClicked.emit(item.layer)


    def jumpToPathNode(self, item):
        try:
            pos = item.associate.qtItem.pos()
            KP.mainWindow.editor.centerOn(pos)
        except:
            pass

    def addFolder(self):
        item = QtWidgets.QTreeWidgetItem(self.tree)
        item.setIcon(0, KP.icon('Folder'))
        item.setText(0, 'Untitled Folder')
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEditable | Qt.ItemIsEnabled)

    def removeFolder(self):
        item = self.tree.currentItem()
        if not isinstance(item, self.KPPathNodeItem):
            kids = item.takeChildren()
            parent = item.parent()
            if parent:
                parent.takeChild(item)
            else:
                self.tree.takeTopLevelItem(self.tree.currentIndex().row())

            self.tree.addTopLevelItems(kids)

    def setTileset(self):
        item = self.tree.currentItem()
        if not isinstance(item, self.KPPathNodeItem):
            return

        layer = item.layer
        assoc = item.associate
        name = 'path' if isinstance(item.associate, KPPath) else 'node'

        from dialogs import KPTilesetChooserDialog

        tilesetName = KPTilesetChooserDialog.run('Choose a tileset for the %s layer:' % name)
        if tilesetName is None:
            return

        layer.setTileset(tilesetName)
        KP.mainWindow.objectSelector.setTileset(KP.tileset(layer.tileset))
        KP.mainWindow.scene.update()

    def addLayer(self, associate, dialog, tileset=None):
        name = 'path' if isinstance(associate, KPPath) else 'node'

        from dialogs import KPTilesetChooserDialog

        if tileset:
            self.lastTileset = tileset
        elif dialog or not self.lastTileset:
            tilesetName = KPTilesetChooserDialog.run('Choose a tileset for the %s layer:' % name)
            if tilesetName is None:
                return False

            self.lastTileset = tilesetName

        layer = KPPathTileLayer(associate)
        layer.tileset = self.lastTileset

        item = self.KPPathNodeItem(self.tree, layer, associate)

        return True

    def loadLayer(self, layer):

        # If there is a folder path available...
        if layer.folder != '':
            folder = layer.folder.split('/')

            # Remove the last empty
            folder.pop()

            myFolder = None

            # Go Through each subfolder
            for subfolder in folder:
                itemList = self.findFolder(subfolder)

                if itemList:
                    myFolder = itemList

                else:
                    if myFolder:
                        item = QtWidgets.QTreeWidgetItem(myFolder)
                    else:
                        item = QtWidgets.QTreeWidgetItem(self.tree)

                    item.setIcon(0, KP.icon('Folder'))
                    item.setText(0, subfolder)
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                    myFolder = item

            # Now that we've got all the folders, put it in!
            self.KPPathNodeItem(myFolder, layer, layer.associate)

        else:
            self.KPPathNodeItem(self.tree, layer, layer.associate)

    def findFolder(self, matchString):

        itemList = QtWidgets.QTreeWidgetItemIterator(self.tree, QtWidgets.QTreeWidgetItemIterator.Editable)

        while itemList.value():
            item = itemList.value()

            if str(item.text(0)) == matchString:
                return item

            itemList += 1

        return None

    def findItemFor(self, associate):
        itemList = QtWidgets.QTreeWidgetItemIterator(self.tree, QtWidgets.QTreeWidgetItemIterator.NotEditable)

        while itemList.value():
            item = itemList.value()

            if not isinstance(item, self.KPPathNodeItem):
                continue

            if item.associate == associate:
                return item

            itemList += 1

    def findLayerFor(self, associate):
        item = self.findItemFor(associate)
        if item:
            return item.layer

    def removeLayer(self, associate):
        item = self.findItemFor(associate)
        if item:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree.indexFromItem(item).row()
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))

    def getLayers(self):
        layerList = []
        for itemI in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(itemI)

            if not isinstance(item, self.KPPathNodeItem):
                self.recursiveLayerRetriever(item, layerList)
            else:
                layerList.append(item.layer)

        return layerList

    def recursiveLayerRetriever(self, parent, layerList):

        for itemI in range(parent.childCount()):
            item = parent.child(itemI)

            if not isinstance(item, self.KPPathNodeItem):
                self.recursiveLayerRetriever(item, layerList)
            else:
                layerList.append(item.layer)

    def setLayerFolders(self):

        itemList = QtWidgets.QTreeWidgetItemIterator(self.tree, QtWidgets.QTreeWidgetItemIterator.NotEditable)

        while itemList.value():
            item = itemList.value()

            if not isinstance(item, self.KPPathNodeItem):
                continue

            item.layer.folder = ''
            daddy = item.parent()

            while daddy:
                item.layer.folder = str(daddy.text(0)) + '/' + item.layer.folder

                daddy = daddy.parent()

            itemList += 1


    selectedLayerChanged = QtCore.pyqtSignal(KPLayer)
    layerClicked = QtCore.pyqtSignal(KPLayer)


class KPLayerList(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)

        self.listView = QtWidgets.QListView()
        self.layout.addWidget(self.listView)

        self.toolbar = QtWidgets.QToolBar()
        self.layout.addWidget(self.toolbar)

        self.setupToolbar(self.toolbar)

        self.updateModel()
        self.setLayout(self.layout)

    def updateModel(self):
        self.model = KP.map.layerModel
        self.listView.setModel(self.model)
        self.listView.clicked.connect(self.handleRowChanged)
        self.setButtonStates()

    def setupToolbar(self, tb):
        self.actAddTile = tb.addAction(KP.icon('LayerNewTile'), 'Add Tile Layer', self.addTileLayer)
        self.actAddDoodad = tb.addAction(KP.icon('LayerNewObjects'), 'Add Doodad Layer', self.addDoodadLayer)
        self.actRemove = tb.addAction(KP.icon('LayerRemove'), 'Remove', self.removeLayer)
        self.actMoveUp = tb.addAction(QtGui.QIcon(), 'Move Up', self.moveUp)
        self.actMoveDown = tb.addAction(QtGui.QIcon(), 'Move Down', self.moveDown)
        self.actPlayPause = tb.addAction(KP.icon('APlay'), 'Play', self.toggleAnimatingScene)

    def toggleAnimatingScene(self):
        self.playPaused.emit()

    def setButtonStates(self):
        index = self.selectedLayerIndex()
        layer = KP.map.layers[index]

        self.actRemove.setEnabled(
                (index != -1) and
                (len(KP.map.layers) > 1) and
                (not isinstance(layer, KPPathLayer)))

        self.actMoveUp.setEnabled(index > 0)
        self.actMoveDown.setEnabled((index != -1) and (index < (len(KP.map.layers) - 1)))

    def selectedLayerIndex(self):
        return self.listView.selectionModel().currentIndex().row()

    def selectedLayer(self):
        return KP.map.layers[self.selectedLayerIndex()]

    def selectLayer(self, row):
        index = self.listView.currentIndex()
        newIndex = index.sibling(row, 0)
        self.listView.setCurrentIndex(newIndex)

    def handleRowChanged(self, current):
        self.selectedLayerChanged.emit(KP.map.layers[current.row()])
        self.setButtonStates()

        if KP.app.keyboardModifiers() & Qt.ControlModifier:
            index = self.selectedLayerIndex()
            layer = KP.map.layers[index]

            if (index != -1) and (len(KP.map.layers) > 1) and (not isinstance(layer, KPPathLayer)):

                KP.mainWindow.scene.clearSelection()
                listToUse = layer.objects

                for obj in listToUse:
                    item = obj.qtItem
                    if item:
                        item.setSelected(True)

    def addTileLayer(self):
        from dialogs import KPTilesetChooserDialog

        tilesetName = KPTilesetChooserDialog.run('Choose a tileset for the new layer:')
        if tilesetName is None:
            return

        layer = KP.map.createNewTileLayer(tilesetName)

        KP.map.appendLayer(layer)
        self.setButtonStates()

    def addDoodadLayer(self):
        layer = KP.map.createNewDoodadLayer()

        KP.map.appendLayer(layer)
        self.setButtonStates()

    def removeLayer(self):
        layer = self.selectedLayer()
        scene = KP.mainWindow.scene

        if isinstance(layer, KPPathLayer):
            return

        for obj in layer.objects:
            item = obj.qtItem
            if item:
                scene.removeItem(item)

        KP.map.removeLayer(self.selectedLayer())
        self.setButtonStates()

    def moveUp(self):
        index = self.selectedLayerIndex()
        KP.map.moveLayer(index, index - 1)
        self.setButtonStates()
        KP.mainWindow.editor.viewport().update()

    def moveDown(self):
        index = self.selectedLayerIndex()
        KP.map.moveLayer(index, index + 2)
        self.setButtonStates()
        KP.mainWindow.editor.viewport().update()

    def moveTop(self):
        index = self.selectedLayerIndex()
        KP.map.moveLayer(index, 0)
        self.setButtonStates()
        KP.mainWindow.editor.viewport().update()

    def moveBottom(self):
        index = self.selectedLayerIndex()
        KP.map.moveLayer(index, len(KP.map.layers))
        self.setButtonStates()
        KP.mainWindow.editor.viewport().update()

    playPaused = QtCore.pyqtSignal()
    selectedLayerChanged = QtCore.pyqtSignal(KPLayer)


class KPDoodadSelector(QtWidgets.QWidget):

    def __init__(self):
        """Initialises the widget."""

        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)

        self.listView = QtWidgets.QListView()
        self.listView.setViewMode(self.listView.IconMode)
        self.listView.setWrapping(True)
        self.listView.setDragDropMode(self.listView.DragOnly)
        self.listView.setSelectionMode(self.listView.SingleSelection)
        self.listView.setResizeMode(self.listView.Adjust)
        self.listView.setGridSize(QtCore.QSize(128, 128))
        self.listView.setIconSize(QtCore.QSize(100, 100))
        self.listView.setSpacing(4)


        self.toolbar = QtWidgets.QToolBar()

        self.addDoodadButton = self.toolbar.addAction(QtGui.QIcon(), 'Add', self.addDoodadFromFile)
        self.removeDoodadButton = self.toolbar.addAction(QtGui.QIcon(), 'Remove', self.removeDoodad)

        self.updateModel()

        self.layout.addWidget(self.toolbar)
        self.layout.addWidget(self.listView)

        self.setLayout(self.layout)

    def updateModel(self):
        self.model = KP.map.doodadModel
        self.listView.setModel(self.model)
        self.listView.selectionModel().currentRowChanged.connect(self.handleRowChanged)
        self.setButtonStates()

    def keyPressEvent(self, event):
        self.listView.keyPressEvent(event)

        if event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
            doodad = self.selectedDoodad()
            if doodad is None:
                return

            # TODO: Check if selected
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                    "Delete Doodad?", "Are you sure you want to delete this doodad? This action cannot be undone.",
                    QtWidgets.QMessageBox.NoButton, self)
            msgBox.addButton("Delete", QtWidgets.QMessageBox.AcceptRole)
            msgBox.addButton("Cancel", QtWidgets.QMessageBox.RejectRole)
            if msgBox.exec_() == QtWidgets.QMessageBox.AcceptRole:
                KP.map.removeDoodad(doodad)

    # def addDoodad(self, image, name):
        # TODO: REMOVE
        # """Takes a name and a QPixmap and turns it into an icon, then goes ahead and makes a doodad.
        # Doodads are QListWidget items with an index number as Qt.UserRole #32."""


        # doodie = QtWidgets.QListWidgetItem(QtGui.QIcon(image), name)
        # # !!
        # doodie.setSizeHint(QtCore.QSize(128,128))
        # doodie.setData(32, self.nextIndex)
        # doodie.setToolTip(name)
        # doodie.setTextAlignment(Qt.AlignBottom | Qt.AlignHCenter)

        # self.doodadList.addItem(doodie)
        # self.nextIndex += 1

    def addDoodadFromFile(self):
        """Asks the user for files to load in as doodads."""

        files = QFileDialog_getOpenFileNames(self,
                "Choose an image or several image files.", "",
                "Images (*.png *.jpeg *.jpg *.bmp)")

        if files:
            for image in files:
                name = os.path.basename(unicode(image)).split('.')[0]

                pix = QtGui.QPixmap()
                pix.load(image)

                KP.map.addDoodad(name, pix)

    def removeDoodad(self):
        """Removes selected doodad"""

        item = self.selectedDoodad()
        if item:
            KP.map.removeDoodad(item)

    def setButtonStates(self):
        index = self.selectedDoodadIndex()

        self.removeDoodadButton.setEnabled(index != -1)

    def selectedDoodadIndex(self):
        return self.listView.selectionModel().currentIndex().row()

    def selectedDoodad(self):
        return KP.map.doodadDefinitions[self.listView.selectionModel().currentIndex().row()]

    def handleRowChanged(self, current, previous):
        self.selectedDoodadChanged.emit(KP.map.doodadDefinitions[current.row()])
        self.setButtonStates()

    selectedDoodadChanged = QtCore.pyqtSignal(object)


class KPObjectSelector(QtWidgets.QWidget):
    def __init__(self):
        """Initialises the widget. Remember to call setTileset() on it
        whenever the layer changes."""

        QtWidgets.QWidget.__init__(self)

        self.menuSetup = False

        self.sorterButton = QtWidgets.QToolButton()

        self.sorterButton.setText('Pick a Layer')
        self.sorterButton.setEnabled(False)
        self.sorterButton.setPopupMode(self.sorterButton.InstantPopup)
        self.sorterButton.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.sorterButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.sorterMenu = QtWidgets.QMenu()
        self.sorterButton.setMenu(self.sorterMenu)


        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(0)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setFixedHeight(28)
        self.toolbar.addWidget(self.sorterButton)
        self.layout.addWidget(self.toolbar)

        self.listView = QtWidgets.QListView()
        self.listView.setFlow(QtWidgets.QListView.LeftToRight)
        self.listView.setLayoutMode(QtWidgets.QListView.SinglePass)
        self.listView.setMovement(QtWidgets.QListView.Static)
        self.listView.setResizeMode(QtWidgets.QListView.Adjust)
        self.listView.setWrapping(True)
        self.listView.setEnabled(False)
        self.layout.addWidget(self.listView)

        self.setLayout(self.layout)

        self.model = None


        # Borrowed the signals and junk from Reggie, figure we'll need em'
        # Some more signals are set in setTileset
        self.listView.clicked.connect(self.handleObjReplace)
        self.sorterMenu.aboutToShow.connect(self.fixUpMenuSize)
        self.sorterMenu.triggered.connect(self.toggleTopLevel)

    def beginUsingMenu(self):
        if self.menuSetup: return

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        self.sorterButton.setFont(font)
        self.sorterButton.setEnabled(True)
        self.menuSetup = True

    def fixUpMenuSize(self):
        self.sorterMenu.setFixedWidth(self.sorterButton.width())

    def currentSelectedObject(self):
        """Returns the currently selected object reference, for painting purposes."""

        index = self.listView.currentIndex().row()
        object = self.model.groupItem().getItem(index)

        return object

    def setTileset(self, tileset):
        """Sets the model and the menu sorting list"""
        model = tileset.getModel()

        if model == self.model:
            return

        self.tileset = tileset

        self.model = model
        self.listView.setModel(model)
        self.listView.setEnabled(True)

        model.view = self.listView

        menuList = model.groupItem().getGroupList()

        self.beginUsingMenu()
        if QtCompatVersion < 0x50000:
            string = QtCore.QString(QtCore.QChar(0x25BE))
            string.append(' All Groups')
        else:
            string = '\u25BE All Groups'

        self.sorterButton.setText(string)
        self.sorterMenu.clear()

        for item in menuList:
            actionMan = self.sorterMenu.addAction(item[0])

            actionMan.setData((item[1], item[2]))

        # a Quick Fix
        self.listView.setRowHidden(0, True)

        # set up signals
        self.listView.selectionModel().currentRowChanged.connect(self.handleRowChanged)

    def toggleTopLevel(self, action):
        """Changes the top level group in the list view."""

        name = str(action.text()).strip()
        startRow = action.data()[0] + 1
        endRow = action.data()[1]

        for row in range(self.model.rowCount()):
            if (row < startRow) or (row > endRow):
                self.listView.setRowHidden(row, True)
            else:
                self.listView.setRowHidden(row, False)

        if QtCompatVersion < 0x50000:
            string = QtCore.QString(QtCore.QChar(0x25BE))
            string.append(' ' + name)
        else:
            string = '\u25BE ' + name

        self.sorterButton.setText(string)

    def handleRowChanged(self, current, previous):
        """Throws a signal emitting the current object when changed"""
        i = current.row()
        object, depth = self.model.groupItem().getItem(i)

        self.objChanged.emit(self.tileset.objects.index(object), object)

    def handleObjReplace(self, index):
        """Throws a signal when the selected object is used as a replacement"""
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            i = current.row()
            object, depth = self.model.groupItem().getItem(i)

            self.objReplaced.emit(self.tileset.objects.index(object), object)

    objChanged = QtCore.pyqtSignal(int, KPTileObject)
    objReplaced = QtCore.pyqtSignal(int, KPTileObject)


class KPAnmOptions(QtWidgets.QWidget):

    class AnmDelegate(QtWidgets.QStyledItemDelegate):

        def createEditor(self, parent, option, index):

            loop = ["Contiguous", "Loop", "Reversible Loop"]
            interp = ["Linear", "Sinusoidial", "Cosinoidial"]
            anmType = ["X Position", "Y Position", "Angle", "X Scale", "Y Scale", "Opacity"]

            thing = index.data(Qt.DisplayRole)
            thong = index.data(Qt.EditRole)

            if thing in loop:
                editWidget = QtWidgets.QComboBox(parent)
                editWidget.addItems(loop)

                return editWidget

            elif thing in interp:
                editWidget = QtWidgets.QComboBox(parent)
                editWidget.addItems(interp)

                return editWidget

            elif thing in anmType:
                editWidget = QtWidgets.QComboBox(parent)
                editWidget.addItems(anmType)

                return editWidget

            elif isinstance(thong, float) or isinstance(thong, int):
                editWidget = QtWidgets.QDoubleSpinBox(parent)
                editWidget.setSingleStep(0.05)
                editWidget.setRange(-10000.0, 10000.0)
                return editWidget

            else:
                print("Thing was something else!")
                print(thong)
                print(type(thong))

        def setEditorData(self, editor, index):

            if isinstance(editor, QtWidgets.QDoubleSpinBox):
                thing = index.data(Qt.EditRole)

                editor.setValue(thing)

            elif isinstance(editor, QtWidgets.QComboBox):
                thing = index.data(Qt.DisplayRole)

                editor.setCurrentIndex(editor.findText(thing))

            else:
                print("editor is something else!")
                print(editor)

        def setModelData(self, editor, model, index):

            if isinstance(editor, QtWidgets.QDoubleSpinBox):
                editor.interpretText()
                value = editor.value()

                model.setData(index, value, QtCore.Qt.EditRole)

            elif isinstance(editor, QtWidgets.QComboBox):
                value = editor.currentText()

                model.setData(index, value, QtCore.Qt.EditRole)

            else:
                print("editor is something else!")
                print(editor)

        def updateEditorGeometry(self, editor, option, index):
            editor.setGeometry(option.rect)

    # def __init__(self, doodadRef):
        #   QtWidgets.QPushButton.__init__(self)

        #   self._doodadRef = doodadRef
        #   self.setText("Animate")

        #   self.menu = QtWidgets.QMenu(self)
        #   self.menuWidget = self.AnmOptionsWidget(doodadRef, self)
        #   self.menuWidgetAction = QtWidgets.QWidgetAction(self)
        #   self.menuWidgetAction.setDefaultWidget(self.menuWidget)
        #   self.menu.addAction(self.menuWidgetAction)


        #   menuPalette = self.menu.palette()
        #   menuPalette.setColor(QtGui.QPalette.Window, Qt.black)
        #   self.menu.setPalette(menuPalette)

        #   self.setMenu(self.menu)

        #   palette = self.palette()
        #   palette.setColor(QtGui.QPalette.ButtonText, Qt.black)
        #   palette.setColor(QtGui.QPalette.Window, Qt.transparent)

        #   self.setPalette(palette)

        #   self.menu.aboutToHide.connect(self.resolveAnmList)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self._doodadRef = None
        self.doodadList = None

        # Setup Layout
        BottomLayout = QtWidgets.QGridLayout()


        # Time for the Table View, model and Delegate
        self.model = QtGui.QStandardItemModel(0, 8)
        self.anmTable = QtWidgets.QTableView()
        self.anmTable.setModel(self.model)

        delegate = self.AnmDelegate()
        self.anmTable.setItemDelegate(delegate)

        self.model.setHorizontalHeaderLabels(["Looping", "Interpolation", "Frame Len", "Type", "Start Value", "End Value", "Delay", "Delay Offset"])
        self.anmTable.setColumnWidth(0, 150)
        self.anmTable.setColumnWidth(1, 100)
        self.anmTable.setColumnWidth(2, 65)
        self.anmTable.setColumnWidth(3, 120)
        self.anmTable.setColumnWidth(4, 65)
        self.anmTable.setColumnWidth(5, 65)
        self.anmTable.setColumnWidth(6, 65)
        self.anmTable.setColumnWidth(7, 80)

        self.anmTable.horizontalHeader().setVisible(True)
        self.anmTable.verticalHeader().setVisible(False)

        BottomLayout.addWidget(self.anmTable, 0, 0, 1, 8)


        # Add/Remove Animation Buttons
        addbutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/Plus.png"), "")
        rembutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/Minus.png"), "")
        presetbutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/AddPreset.png"), "Add Preset")
        newpbutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/NewPreset.png"), "New Preset")
        # savebutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/SavePreset.png"), "Save")
        # loadbutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/LoadPreset.png"), "Load")
        # clearbutton = QtWidgets.QPushButton(QtGui.QIcon("Resources/ClearPreset.png"), "Clear")
        BottomLayout.addWidget(addbutton, 1, 0, 1, 1)
        BottomLayout.addWidget(rembutton, 1, 1, 1, 1)
        BottomLayout.addWidget(QtWidgets.QLabel(""), 1, 2, 1, 2)
        BottomLayout.addWidget(presetbutton, 1, 6, 1, 1)
        BottomLayout.addWidget(newpbutton, 1, 7, 1, 1)
        # BottomLayout.addWidget(savebutton, 1, 6, 1, 1)
        # BottomLayout.addWidget(loadbutton, 1, 7, 1, 1)
        # BottomLayout.addWidget(clearbutton, 1, 8, 1, 1)


        # Annnnndddd we're spent.
        self.setLayout(BottomLayout)

        addbutton.released.connect(self.addAnmItem)
        rembutton.released.connect(self.remAnmItem)

        presetbutton.released.connect(self.selectPreset)
        newpbutton.released.connect(self.addToPreset)
        # savebutton.released.connect(KP.mainWindow.saveAnimPresets)
        # loadbutton.released.connect(KP.mainWindow.loadAnimPresets)
        # clearbutton.released.connect(KP.mainWindow.clearAnimPresets)

    def setupAnms(self, doodadList):
        self.doodadList = doodadList
        self._doodadRef = doodadList[0]
        doodad = self._doodadRef()

        for row in doodad.animations:

            # Fix for backwards compatibility
            if len(row) == 6:
                row.append(0)

            if len(row) == 7:
                row.append(0)

            itemA = QtGui.QStandardItem()
            itemB = QtGui.QStandardItem()
            itemC = QtGui.QStandardItem()
            itemD = QtGui.QStandardItem()
            itemE = QtGui.QStandardItem()

            itemA.setData(row[2], QtCore.Qt.EditRole)
            itemB.setData(row[4], QtCore.Qt.EditRole)
            itemC.setData(row[5], QtCore.Qt.EditRole)
            itemD.setData(row[6], QtCore.Qt.EditRole)
            itemE.setData(row[7], QtCore.Qt.EditRole)

            self.model.appendRow([QtGui.QStandardItem(row[0]), QtGui.QStandardItem(row[1]),
                                  itemA, QtGui.QStandardItem(row[3]), itemB, itemC, itemD, itemE])

        self.update()

    def sizeHint(self):
        return QtCore.QSize(591,300)

    def addAnmItem(self):

        itemA = QtGui.QStandardItem()
        itemB = QtGui.QStandardItem()
        itemC = QtGui.QStandardItem()
        itemD = QtGui.QStandardItem()
        itemE = QtGui.QStandardItem()

        itemA.setData(1, QtCore.Qt.EditRole)
        itemB.setData(0.0, QtCore.Qt.EditRole)
        itemC.setData(0.0, QtCore.Qt.EditRole)
        itemD.setData(0, QtCore.Qt.EditRole)
        itemE.setData(0, QtCore.Qt.EditRole)

        self.model.appendRow([QtGui.QStandardItem("Contiguous"), QtGui.QStandardItem("Linear"),
                              itemA, QtGui.QStandardItem("X Position"),
                              itemB, itemC, itemD, itemE])

    def remAnmItem(self):

        if self.model.rowCount() == 0:
            return

        rowNum, ok = QtWidgets.QInputDialog.getInt(self,
                "Select A Row", "Delete This Row:", 0, 0, self.model.rowCount(), 1)
        if ok:
            self.model.removeRows(rowNum, 1)

    def selectPreset(self):
        from dialogs import KPAnimationPresetChooser
        presetList = KPAnimationPresetChooser.run()

        if presetList is None: return
        if presetList is []: return
        if presetList is [[]]: return

        q = QtGui.QStandardItem

        for row in presetList:
            a = q(row[0])
            b = q(row[1])
            c = q()
            c.setData(row[2], Qt.EditRole)
            d = q(row[3])
            e = q()
            e.setData(row[4], Qt.EditRole)
            f = q()
            f.setData(row[5], Qt.EditRole)
            g = q()
            g.setData(row[6], Qt.EditRole)
            h = q()
            h.setData(row[6], Qt.EditRole)

            self.model.appendRow([a,b,c,d,e,f,g,h])

        self.resolveAnmList()

    def addToPreset(self):
        from dialogs import getTextDialog

        name = getTextDialog('Add to Presets', 'Enter a name for the preset:')
        if name is None:
            print('Returning')
            return

        print('Adding.')
        preset = []
        for row in range(self.model.rowCount()):
            listrow = []
            for column in range(8):
                item = self.model.item(row, column)
                data = item.data(Qt.EditRole)

                if hasattr(QtCore, 'QString') and isinstance(data, QtCore.QString):
                    data = str(data)

                listrow.append(data)

            preset.append(listrow)

        settings = KP.app.settings
        import mapfile

        if settings.contains('AnimationPresets'):

            presetList = mapfile.load(settings.value('AnimationPresets'))
            presets = mapfile.load(settings.value('AnimationPresetData'))

        else:

            presetList = []
            presets = []

        presetList.append(name)
        presets.append(preset)

        settings.setValue('AnimationPresets', mapfile.dump(presetList))
        settings.setValue('AnimationPresetData', mapfile.dump(presets))

    def resolveAnmList(self):
        if self.doodadList is None:
            return

        anmList = []
        model = self.model
        rows = model.rowCount()

        for x in range(rows):
            rowList = []

            for item in range(8):
                index = model.index(x, item)
                data = model.data(index, Qt.EditRole)
                rowList.append(data)

            anmList.append(rowList)

        shouldRestartAnims = False
        for doodad in self.doodadList:
            if doodad() is not None:
                d = doodad()

                d.animations = anmList
                d.setupAnimations()
                shouldRestartAnims = True

        model.clear()
        self.model.setHorizontalHeaderLabels(["Looping", "Interpolation", "Frame Len", "Type", "Start Value", "End Value", "Delay", "Delay Offset"])
        self._doodadRef = None
        self.doodadList = None

        self.update()
        if KP.mainWindow.scene.playing and shouldRestartAnims:
            KP.mainWindow.resetAnim()


class KPMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setWindowTitle('Koopatlas')
        self.setWindowIcon(QtGui.QIcon('Resources/Koopatlas.png'))
        self.setIconSize(QtCore.QSize(16, 16))

        self.scene = KPMapScene()
        self.clipboard = None

        self.editor = KPEditorWidget(self.scene)
        self.setCentralWidget(self.editor)

        self.ZoomLevel = 5

        self.setupDocks()
        self.setupMenuBar()

        self.refreshMapState()

    def _createAction(self, internalName, callback, title):
        act = QtWidgets.QAction(title, self)
        act.triggered.connect(callback)
        self.actions[internalName] = act
        return act

    def setupActions(self):
        self.actions = {}

        self._createAction('new', self.newMap, '&New')
        self._createAction('open', self.openMap, '&Open...')
        self._createAction('save', self.saveMap, '&Save')
        self._createAction('saveAs', self.saveMapAs, 'Save &As...')

    def setupMenuBar(self):
        mb = self.menuBar()

        QKeySequence = QtGui.QKeySequence

        f = mb.addMenu('&File')
        self.fa = f.addAction('New',                        self.newMap, QKeySequence("Ctrl+N"))
        self.fb = f.addAction('Open...',                    self.openMap, QKeySequence("Ctrl+O"))
        self.fc = f.addAction('Open Recent')                #
        f.addSeparator()
        self.fd = f.addAction('Save',                       self.saveMap, QKeySequence("Ctrl+S"))
        self.fe = f.addAction('Save As...',                 self.saveMapAs, QKeySequence("Ctrl+Shift+S"))
        self.ff = f.addAction('Export...',                  self.exportMap, QKeySequence("Ctrl+E"))
        self.fj = f.addAction('Batch...',                   self.batchSave, QKeySequence("Ctrl+Shift+E"))
        f.addSeparator()
        self.fg = f.addAction('Take Screenshot...',         self.screenshot, QKeySequence("Ctrl+Alt+S"))
        self.fh = f.addAction('Export Doodads...',          self.exportDoodads, QKeySequence("Ctrl+Alt+Shift+D"))
        f.addSeparator()
        # self.fi = f.addAction('Quit')

        e = mb.addMenu('Edit')
        self.ea = e.addAction('Copy',                       self.copy, QKeySequence.Copy)
        self.eb = e.addAction('Cut')                        # X
        self.ec = e.addAction('Paste',                      self.paste, QKeySequence.Paste)
        e.addSeparator()
        self.ed = e.addAction('Select All',                 self.selectAll, QKeySequence.SelectAll)
        self.ee = e.addAction('Deselect',                   self.deSelect, QKeySequence("Ctrl+D"))

        l = mb.addMenu('Layers')
        self.la = l.addAction('Add Tileset Layer',          self.layerList.addTileLayer, QKeySequence("Ctrl+T"))
        self.lb = l.addAction('Add Doodad Layer',           self.layerList.addDoodadLayer, QKeySequence("Ctrl+R"))
        self.lc = l.addAction('Remove Layer',               self.layerList.removeLayer, QKeySequence("Ctrl+Del"))
        l.addSeparator()
        self.ld = l.addAction('Move Layer Up',              self.layerList.moveUp, QKeySequence("Ctrl+Up"))
        self.le = l.addAction('Move Layer Down',            self.layerList.moveDown, QKeySequence("Ctrl+Down"))
        self.lf = l.addAction('Move Layer to Top',          self.layerList.moveTop, QKeySequence("Ctrl+Shift+Up"))
        self.lg = l.addAction('Move Layer to Bottom',       self.layerList.moveBottom, QKeySequence("Ctrl+Shift+Down"))
        l.addSeparator()
        self.li = l.addAction('Add Doodad...',              self.doodadSelector.addDoodadFromFile, QKeySequence("Ctrl+Shift+R"))
        self.lh = l.addAction('Add Tileset...',             self.moveTilesetToFolder, QKeySequence("Ctrl+Shift+T"))
        self.lj = l.addAction('Change Tileset...',          self.changeTileset, QKeySequence("Ctrl+Shift+Alt+T"))

        a = mb.addMenu('Animate')
        self.aa = a.addAction('Play Animations',            self.playAnim, QKeySequence("Ctrl+P"))
        self.ac = a.addAction('Reset Animations',           self.resetAnim, QKeySequence("Ctrl+Shift+P"))
        a.addSeparator()
        self.ad = a.addAction('Load Animation Presets...',  self.loadAnimPresets)
        self.ae = a.addAction('Save Animation Presets...',  self.saveAnimPresets)
        self.af = a.addAction('Clear Animation Presets',    self.clearAnimPresets)

        m = mb.addMenu('Map')
        self.ma = m.addAction('Set Background...',          self.setMapBackground)
        self.ma = m.addAction('World Editor...',            self.showWorldEditor)

        w = mb.addMenu('Window')
        self.wa = w.addAction('Show Grid',                  self.showGrid, QKeySequence("Ctrl+G"))
        self.wa.setCheckable(True)
        w.addSeparator()
        self.wb = w.addAction('Zoom In',                    self.ZoomIn, QKeySequence.ZoomIn)
        self.wc = w.addAction('Zoom Out',                   self.ZoomOut, QKeySequence.ZoomOut)
        self.wd = w.addAction('Actual Size',                self.ZoomActual, QKeySequence("Ctrl+="))
        self.wh = w.addAction('Show Wii Zoom',              self.showWiiZoom, QKeySequence("Ctrl+F"))
        self.wh.setCheckable(True)
        w.addSeparator()

        layerAction = self.layerListDock.toggleViewAction()
        layerAction.setShortcut(QKeySequence("Ctrl+1"))
        w.addAction(layerAction)

        objectAction = self.objectSelectorDock.toggleViewAction()
        objectAction.setShortcut(QKeySequence("Ctrl+2"))
        w.addAction(objectAction)

        doodadAction = self.doodadSelectorDock.toggleViewAction()
        doodadAction.setShortcut(QKeySequence("Ctrl+3"))
        w.addAction(doodadAction)

        h = mb.addMenu('Help')
        self.ha = h.addAction('About Koopatlas',            self.aboutDialog)
        self.hb = h.addAction('Koopatlas Documentation',    self.goToHelp)
        # self.hc = h.addAction('Keyboard Shortcuts')

    def setupDocks(self):
        self.layerList = KPLayerList()
        self.layerListDock = QtWidgets.QDockWidget('Layers')
        self.layerListDock.setWidget(self.layerList)

        self.layerList.selectedLayerChanged.connect(self.handleSelectedLayerChanged)
        self.layerList.playPaused.connect(self.playAnim)

        self.pathNodeList = KPPathNodeList()
        self.pathNodeDock = QtWidgets.QDockWidget('Path/Node Layers')
        self.pathNodeDock.setWidget(self.pathNodeList)
        self.pathNodeList.selectedLayerChanged.connect(self.handleSelectedPathNodeLayerChanged)
        self.pathNodeList.layerClicked.connect(self.handleSelectedPathNodeLayerChanged)

        self.objectSelector = KPObjectSelector()
        self.objectSelector.objChanged.connect(self.handleSelectedObjectChanged)

        self.objectSelectorDock = QtWidgets.QDockWidget('Objects')
        self.objectSelectorDock.setWidget(self.objectSelector)
        self.objectSelectorDock.hide()

        self.doodadSelector = KPDoodadSelector()
        self.doodadSelector.selectedDoodadChanged.connect(self.handleSelectedDoodadChanged)

        self.doodadSelectorDock = QtWidgets.QDockWidget('Doodads')
        self.doodadSelectorDock.setWidget(self.doodadSelector)
        self.doodadSelectorDock.hide()

        self.anmOpts = KPAnmOptions()
        self.editor.userClick.connect(self.anmPopulate)

        self.anmOptsDock = QtWidgets.QDockWidget('Doodad Animations')
        self.anmOptsDock.setWidget(self.anmOpts)
        self.anmOptsDock.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        self.anmOptsDock.setFeatures(self.anmOptsDock.DockWidgetVerticalTitleBar | self.anmOptsDock.DockWidgetMovable | self.anmOptsDock.DockWidgetFloatable)
        self.anmOptsDock.hide()

        self.addDockWidget(Qt.RightDockWidgetArea, self.layerListDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.pathNodeDock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.objectSelectorDock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.doodadSelectorDock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.anmOptsDock)

    def refreshMapState(self):
        self.layerList.updateModel()
        self.doodadSelector.updateModel()
        self.pathNodeList.reset()

        self.scene = KPMapScene()
        self.editor.assignNewScene(self.scene)
        self.anmPopulate()
        self.updateTitlebar()

        # scroll to the first path or node
        scrollTo = (0, 0)
        for layer in self.pathNodeList.getLayers():
            assoc = layer.associate
            if isinstance(assoc, KPPath):
                start, end = assoc._startNodeRef(), assoc._endNodeRef()
                if start is not None:
                    scrollTo = start.position
                    break
                elif end is not None:
                    scrollTo = end.position
                    break
            elif isinstance(assoc, KPNode):
                scrollTo = assoc.position
                break
        self.editor.centerOn(scrollTo[0], scrollTo[1])

    def updateTitlebar(self):
        path = KP.map.filePath
        if path is None:
            effectiveName = 'Untitled Map'
        else:
            effectiveName = os.path.basename(path)

        self.setWindowTitle('%s - Koopatlas' % effectiveName)

    def checkDirty(self):
        return False


#####################
# Slots for Widgets #
#####################

    def handleSelectedLayerChanged(self, layer):
        sel = self.pathNodeList.tree.selectionModel()
        if sel:
            sel.clearSelection()

        self.scene.setCurrentLayer(layer)

        showObjects, showDoodads = False, False

        if isinstance(layer, KPDoodadLayer):
            showDoodads = True

        elif isinstance(layer, KPTileLayer):
            KP.loadTileset(layer.tileset)
            showObjects = True

            self.objectSelector.setTileset(KP.tileset(layer.tileset))

        self.objectSelectorDock.setVisible(showObjects)
        self.doodadSelectorDock.setVisible(showDoodads)
        self.anmOptsDock.setVisible(showDoodads)

    def handleSelectedPathNodeLayerChanged(self, layer):

        sel = self.layerList.listView.selectionModel()
        if sel:
            sel.clearSelection()

        self.scene.setCurrentLayer(layer)

        KP.loadTileset(layer.tileset)

        self.objectSelector.setTileset(KP.tileset(layer.tileset))

        self.objectSelectorDock.setVisible(True)
        self.doodadSelectorDock.setVisible(True)

    def handleSelectedObjectChanged(self, index, obj):
        sel = self.doodadSelector.listView.selectionModel()
        if sel:
            sel.clearSelection()

        self.editor.objectToPaint = obj
        self.editor.objectIDToPaint = index
        self.editor.typeToPaint = 'object'

    def handleSelectedDoodadChanged(self, doodad):
        sel = self.objectSelector.listView.selectionModel()
        if sel:
            sel.clearSelection()

        self.editor.doodadToPaint = doodad
        self.editor.typeToPaint = 'doodad'

    def anmPopulate(self):

        selection = self.scene.selectedItems()
        if len(selection) == 0:
            self.anmOpts.resolveAnmList()
            self.anmOptsDock.setWindowTitle("No Doodads Selected")
            return

        doodadList = []

        for selItem in selection:
            if isinstance(selItem, KPEditorDoodad):
                doodadList.append(selItem._doodadRef)

        self.anmOpts.resolveAnmList()

        if len(doodadList) == 0:
            self.anmOptsDock.setWindowTitle("No Doodads Selected")
            return

        suffix = ''
        if len(doodadList) > 1:
            suffix = 's'
        self.anmOptsDock.setWindowTitle("Editing {0} Doodad{1}".format(len(doodadList), suffix))
        self.anmOpts.setupAnms(doodadList)


########################
# Slots for Menu Items #
########################

# File
########################
    def newMap(self):
        if self.checkDirty(): return

        KP.map = KPMap()
        self.refreshMapState()

    def openMap(self):
        if self.checkDirty(): return

        target = unicode(QFileDialog_getOpenFileName(
            self, 'Open Map', '', 'Koopatlas map (*.kpmap)'))

        if len(target) == 0:
            return

        import mapfile
        with open(target, 'rb') as file:
            obj = mapfile.load(file.read())
        obj.filePath = target
        KP.map = obj
        KP.map.filePath = target
        self.refreshMapState()

    def saveMap(self, forceNewName=False):
        target = KP.map.filePath

        if target is None or forceNewName:
            dialogDir = '' if target is None else os.path.dirname(target)
            target = unicode(QFileDialog_getSaveFileName(
                    self, 'Save Map', dialogDir, 'Koopatlas map (*.kpmap)'))

            if len(target) == 0:
                return

            KP.map.filePath = target
            self.updateTitlebar()

        KP.map.save()

    def saveMapAs(self):
        self.saveMap(True)

    def exportMap(self):
        target = KP.map.filePath

        dialogDir = '' if target is None else os.path.dirname(target)
        target = unicode(QFileDialog_getSaveFileName(
                self, 'Export Map', dialogDir, 'Koopatlas binary map (*.kpbin)'))

        if len(target) == 0:
            return

        KP.map.export(target)

    def screenshot(self):
        items = ("Current Window", "Entire Map")

        item, ok = QtWidgets.QInputDialog.getItem(self, "Screenshot",
                "Choose a Screenshot Source:", items, 0, False)
        if ok and item:
            fn = QFileDialog_getSaveFileName(self, 'Choose a new filename', 'untitled.png', 'Portable Network Graphics (*.png)')
            if fn == '': return
            fn = unicode(fn)

            if item == "Current Window":
                ScreenshotImage = QtGui.QImage(self.editor.width(), self.editor.height(), QtGui.QImage.Format_ARGB32)
                ScreenshotImage.fill(QtCore.Qt.transparent)

                RenderPainter = QtGui.QPainter(ScreenshotImage)
                self.editor.render(RenderPainter, QtCore.QRectF(0,0,self.editor.width(),  self.editor.height()), QtCore.QRect(QtCore.QPoint(0,0), QtCore.QSize(self.editor.width(),  self.editor.height())))
                RenderPainter.end()

            else:

                ScreenshotImage = QtGui.QImage(self.scene.itemsBoundingRect().width()+100, self.scene.itemsBoundingRect().height()+100, QtGui.QImage.Format_ARGB32)
                ScreenshotImage.fill(QtCore.Qt.transparent)

                RenderPainter = QtGui.QPainter(ScreenshotImage)
                self.scene.render(RenderPainter, QtCore.QRectF(ScreenshotImage.rect()), self.scene.itemsBoundingRect().adjusted(-50.0, -50.0, 50.0, 50.0))
                RenderPainter.end()

            ScreenshotImage.save(fn, 'PNG', 50)


    def exportDoodads(self):
        fn = QtWidgets.QFileDialog.getExistingDirectory(self, 'Export Doodads')
        if fn == '': return
        fn = unicode(fn)

        for d in KP.map.doodadDefinitions:
            d[1].save(fn + '/' + d[0] + '.png', 'PNG')


    def batchSave(self):
        target = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose a folder. All KPMAP files will be exported to KPBIN.')
        if target == '': return
        target = unicode(target)

        for fileName in os.listdir(target):
            print(fileName)

            if fileName[-6:] == ".kpmap":
                import mapfile

                print('Found a map')
                with open(target + "/" + fileName, 'rb') as file:
                    obj = mapfile.load(file.read())
                # obj.save()
                obj.export(target + "/" + fileName[:-6] + '.kpbin')

                print('Saved and Exported {0}'.format(fileName[:-6]))


# Edit
########################
    def selectAll(self):

        path = QtGui.QPainterPath()
        path.addRect(self.scene.sceneRect())
        self.scene.setSelectionArea(path)

    def deSelect(self):
        self.scene.clearSelection()


    def copy(self):
        self.clipboard = self.scene.selectedItems()


    def paste(self):
        self.scene.clearSelection()
        if self.clipboard is None:
            return

        for paper in self.clipboard:

            if isinstance(paper, KPEditorObject):
                layer = paper._layerRef()
                co = copy.deepcopy(paper._objRef())

                co.updateCache()
                layer.objects.append(co)
                layer.updateCache()

                q = KPEditorObject(co, layer)
                self.scene.addItem(q)
                q.setSelected(True)

            if isinstance(paper, KPEditorDoodad):
                layer = paper._layerRef()
                cd = copy.copy(paper._doodadRef())

                layer.objects.append(cd)

                cd.setupAnimations()
                q = KPEditorDoodad(cd, layer)
                self.scene.addItem(q)
                q.setSelected(True)
                if self.scene.playing:
                    self.resetAnim()


# Layers
########################
    def moveTilesetToFolder(self):

        path = QFileDialog_getOpenFileName(self,
                "Choose a tileset file. It will be copied to the Koopatlas Tilesets folder.", "",
                "Koopuzzle Tilesets (*.arc)")
        if path:
            import shutil
            import os

            # Todo: refactor this to use a KP method
            name = os.path.basename(path[:-4])
            shutil.copy(path, 'Tilesets')

            with open(path) as file:
                data = file.read()

            KP.knownTilesets[name] = {'path': path}

    def changeTileset(self):

        layer = self.layerList.selectedLayer()

        if not isinstance(layer, KPTileLayer):
            return


        from dialogs import KPTilesetChooserDialog

        tilesetName = KPTilesetChooserDialog.run('Choose a tileset to change to:')
        if tilesetName is None:
            return

        layer.tileset = tilesetName

        self.objectSelector.setTileset(KP.tileset(layer.tileset))


# Animate
########################
    def playAnim(self):
        self.scene.playPause()
        self.playButtonChanged()

    def playButtonChanged(self):
        if self.scene.playing:
            self.aa.setText('Stop Animations')
            self.layerList.actPlayPause.setIcon(KP.icon('AStop'))
            self.layerList.actPlayPause.setText('Stop')
        else:
            self.aa.setText('Play Animations')
            self.layerList.actPlayPause.setIcon(KP.icon('APlay'))
            self.layerList.actPlayPause.setText('Play')

    def resetAnim(self):
        if self.scene.playing == True:
            self.scene.playPause()
        self.scene.playPause()

    def loadAnimPresets(self):
        path = QFileDialog_getOpenFileName(self,
                "Choose a Koopatlas Animation Preset File.", "",
                "Koopatlas Animation Preset (*.kpa)")
        if path:
            import mapfile

            with open(path, 'rb') as file:
                data = file.read()
            loaded = mapfile.load(data)

            settings = KP.app.settings

            presetList = []
            presets = []

            if settings.contains('AnimationPresets'):
                presetList = mapfile.load(settings.value('AnimationPresets'))
                presets = mapfile.load(settings.value('AnimationPresetData'))

            if presetList is None:
                presetList = []
                presets = []

            presetList.extend(loaded[0])
            presets.extend(loaded[1])

            settings.setValue('AnimationPresets', mapfile.dump(presetList))
            settings.setValue('AnimationPresetData', mapfile.dump(presets))

    def saveAnimPresets(self):

        settings = KP.app.settings
        import mapfile

        msg = QtWidgets.QMessageBox()
        msg.setText("No Animation Presets Found.")

        if settings.contains('AnimationPresets'):
            presetList = mapfile.load(settings.value('AnimationPresets'))
            presets = mapfile.load(settings.value('AnimationPresetData'))
        else:
            msg.exec_()
            return

        if len(presetList) == 0:
            msg.exec_()
            return

        path = QFileDialog_getSaveFileName(self,
                "Save Koopatlas Animation Preset externally.", "KP Preset.kpa",
                "Koopatlas Animation Preset (*.kpa)")

        if path:
            import mapfile
            output = [presetList, presets]

            with open(path, 'wb') as file:
                file.write(mapfile.dump(output))

    def clearAnimPresets(self):
        settings = KP.app.settings
        import mapfile

        settings.setValue('AnimationPresets', mapfile.dump([]))
        settings.setValue('AnimationPresetData', mapfile.dump([]))


# Map
########################
    def setMapBackground(self):
        from dialogs import getTextDialog
        newBG = getTextDialog('Map Background', 'Enter a path (ex. /Maps/Water.brres):', KP.map.bgName)
        if newBG is not None:
            KP.map.bgName = newBG

    def showWorldEditor(self):
        from worldeditor import KPWorldEditor
        dlg = KPWorldEditor(KP.map, self)
        dlg.show()

# Window
########################
    def ZoomActual(self):
        """Handle zooming to the editor size"""
        self.ZoomLevel = 5
        self.ZoomTo()

    def ZoomIn(self):
        """Handle zooming in"""
        self.ZoomLevel += 1
        self.ZoomTo()

    def ZoomOut(self):
        """Handle zooming out"""
        self.ZoomLevel -= 1
        self.ZoomTo()

    def ZoomTo(self):
        """Zoom to a specific level"""
        tr = QtGui.QTransform()

        zooms = [5.0, 10.0, 25.0, 50.0, 75.0, 100.0, 150.0, 200.0, 400.0]
        scale = zooms[self.ZoomLevel] / 100.0

        tr.scale(scale, scale)


        self.editor.setTransform(tr)

        self.wb.setEnabled(self.ZoomLevel != 8)
        self.wc.setEnabled(self.ZoomLevel != 0)
        self.wd.setEnabled(self.ZoomLevel != 5)

        self.scene.update()

    def showGrid(self):
        """Handle toggling of the grid being showed"""
        # settings.setValue('GridEnabled', checked)

        if self.scene.grid == True:
            self.scene.grid = False
            self.wa.setChecked(False)
        else:
            self.scene.grid = True
            self.wa.setChecked(True)

        self.scene.update()

    def showWiiZoom(self):
        if self.editor.grid == True:
            self.editor.grid = False

        else:
            self.editor.grid = True

        self.editor.update()


# Help
########################
    def aboutDialog(self):
        caption = "About Koopatlas"

        text = "<big><b>Koopatlas</b></big><br><br>    The Koopatlas Editor is an editor for custom two dimensional world maps, for use with the Newer SMBWii world map engine. It should be included with its companion program, Koopuzzle, which will create tilesets compatible with Koopatlas.<br><br>    Koopatlas was programmed by Treeki and Tempus of the Newer Team.<br><br>    Find the website at html://www.newerteam.com for more information."


        msg = QtWidgets.QMessageBox.about(KP.mainWindow, caption, text)

    def goToHelp(self):
        QtGui.QDesktopServices().openUrl(QtCore.QUrl('http://www.newerteam.com/koopatlas-help'))



