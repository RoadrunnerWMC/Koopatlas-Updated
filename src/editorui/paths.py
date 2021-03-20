from common import *
from .editorcommon import *
import weakref

PathAnimationList = [
    'Walk', 'WalkSand', 'WalkSnow', 'WalkWater',
    'Jump', 'JumpSand', 'JumpSnow', 'LaunchStarRight',
    'Ladder', 'LadderLeft', 'LadderRight', 'Fall',
    'Swim', 'Run', 'Pipe', 'Door',
    'Land', 'EnterCaveUp', 'LaunchStarLeft', 'Invisible']
PathAnimationNamesList = [
    'Walk', 'Walk (Sand)', 'Walk (Snow)', 'Walk (Water)',
    'Jump', 'Jump (Sand)', 'Jump (Snow)', 'Launch Star (Right)',
    'Ladder', 'Ladder (Left)', 'Ladder (Right)', 'Fall',
    'Swim', 'Run', 'Pipe', 'Door',
    'Land', 'Enter Cave (Up)', 'Launch Star (Left)', 'Invisible']

PATH_NODE_STATE_MOVEMENT = 0
PATH_NODE_STATE_LEVEL = 1
PATH_NODE_STATE_EXIT = 2
PATH_NODE_STATE_TRANSITION = 3

FIRST_PATH_NODE_STATE = PATH_NODE_STATE_MOVEMENT
LAST_PATH_NODE_STATE = PATH_NODE_STATE_TRANSITION

class KPEditorNode(KPEditorItem):
    SNAP_TO = (12,12)


    class ToggleButton(QtWidgets.QPushButton):
        stateToggled = QtCore.pyqtSignal(int)


        def __init__(self, initialState):
            QtWidgets.QPushButton.__init__(self)

            self.setIconSize(QtCore.QSize(24, 24))
            self.setFixedSize(24, 24)

            self.iconList = [KP.icon('Through'), KP.icon('Level'), KP.icon('Exit'), KP.icon('WorldChange')]

            self.state = initialState

            if not hasattr(KPEditorNode.ToggleButton, 'PALETTE'):
                KPEditorNode.ToggleButton.PALETTE = QtGui.QPalette(Qt.transparent)

            self.setPalette(self.PALETTE)

            self.released.connect(self.toggle)


        def toggle(self):
            self.state += 1
            if self.state > LAST_PATH_NODE_STATE:
                self.state = FIRST_PATH_NODE_STATE

            self.stateToggled.emit(self.state)


        def paintEvent(self, event):
            painter = QtGui.QPainter(self)

            if self.isDown():
                self.iconList[self.state].paint(painter, self.contentsRect(), Qt.AlignCenter, QtGui.QIcon.Disabled)
            else:
                self.iconList[self.state].paint(painter, self.contentsRect())

            painter.end()


    class HiddenProxy(QtWidgets.QGraphicsProxyWidget):
        def __init__(self, widget):
            QtWidgets.QGraphicsProxyWidget.__init__(self, None)
            self.setWidget(widget)
            self.setZValue(999999)
            self.hide()


    class LevelSlotSpinner(QtWidgets.QSpinBox):
        def __init__(self):
            QtWidgets.QSpinBox.__init__(self)

            self.setRange(1, 99)

            palette = self.palette()
            palette.setColor(QtGui.QPalette.ButtonText, Qt.black)
            palette.setColor(QtGui.QPalette.Window, Qt.transparent)

            self.setPalette(palette)


    class TransitionBox(QtWidgets.QComboBox):
        def __init__(self):
            QtWidgets.QComboBox.__init__(self)

            self.addItems(['Fade Out', 'Circle Wipe', 'Bowser Wipe', 'Goo Wipe Down',
                           'Mario Wipe', 'Circle Wipe Slow', 'Glitchgasm'])

            palette = self.palette()
            palette.setColor(QtGui.QPalette.ButtonText, Qt.black)
            palette.setColor(QtGui.QPalette.Window, Qt.transparent)

            self.setPalette(palette)


    class SecretBox(QtWidgets.QCheckBox):
        def __init__(self):
            QtWidgets.QCheckBox.__init__(self)

            palette = self.palette()
            palette.setColor(QtGui.QPalette.ButtonText, Qt.black)
            palette.setColor(QtGui.QPalette.Window, Qt.transparent)

            self.setPalette(palette)


    class mapArcEdit(QtWidgets.QLineEdit):
        def __init__(self):
            QtWidgets.QLineEdit.__init__(self)

            self.setText('None.arc')

            palette = self.palette()
            palette.setColor(QtGui.QPalette.ButtonText, Qt.black)
            palette.setColor(QtGui.QPalette.Window, Qt.transparent)

            self.setPalette(palette)


    def __init__(self, node):
        KPEditorItem.__init__(self)

        node.qtItem = self
        self._nodeRef = weakref.ref(node)

        self.setZValue(101)

        self._boundingRect = QtCore.QRectF(-24, -24, 48, 48)
        self._levelRect = self._boundingRect
        self._stopRect = QtCore.QRectF(-12, -12, 24, 24)
        self._worldChangeRect = QtCore.QRectF(-14, -15, 32, 32)  # slightly offset to account for the arrow in the corner of the image
        self._tinyRect = QtCore.QRectF(-6, -6, 12, 12)
        self.isLayerSelected = False

        if not hasattr(KPEditorNode, 'SELECTION_PEN'):
            KPEditorNode.SELECTION_PEN = QtGui.QPen(Qt.blue, 1, Qt.DotLine)

        if node.level:
            initialState = PATH_NODE_STATE_LEVEL
        elif node.mapChange is not None:
            initialState = PATH_NODE_STATE_EXIT
        elif node.worldDefID is not None:
            initialState = PATH_NODE_STATE_TRANSITION
        else:
            initialState = PATH_NODE_STATE_MOVEMENT

        self.button = self.ToggleButton(initialState)
        self.buttonProxy = self.HiddenProxy(self.button)
        self.button.stateToggled.connect(self.stateChange)


        self.world = self.LevelSlotSpinner()
        self.worldProxy = self.HiddenProxy(self.world)
        self.world.valueChanged.connect(self.worldChange)

        self.stage = self.LevelSlotSpinner()
        self.stageProxy = self.HiddenProxy(self.stage)
        self.stage.valueChanged.connect(self.stageChange)

        self.secret = self.SecretBox()
        self.secretProxy = self.HiddenProxy(self.secret)
        self.secret.stateChanged.connect(self.secretChange)

        if node.level is not None:
            self.world.setValue(node.level[0])
            self.stage.setValue(node.level[1])

        if node.hasSecret is not None:
            self.secret.setChecked(node.hasSecret)


        self.foreignID = self.LevelSlotSpinner()
        self.foreignID.setRange(0,255)
        self.foreignIDProxy = self.HiddenProxy(self.foreignID)
        self.foreignID.valueChanged.connect(self.foreignIDChange)

        self.mapChange = self.mapArcEdit()
        self.mapChangeProxy = self.HiddenProxy(self.mapChange)
        self.mapChange.textEdited.connect(self.mapChangeChange)

        self.transition = self.TransitionBox()
        self.transitionProxy = self.HiddenProxy(self.transition)
        self.transition.currentIndexChanged.connect(self.transitionChange)

        self.worldDefID = self.LevelSlotSpinner()
        self.worldDefID.setRange(0,255)
        self.worldDefIDProxy = self.HiddenProxy(self.worldDefID)
        self.worldDefID.valueChanged.connect(self.worldDefIDChange)

        if node.foreignID is not None:
            self.foreignID.setValue(node.foreignID)

        if node.mapChange is not None:
            self.mapChange.setText(node.mapChange)

        if node.worldDefID is not None:
            self.worldDefID.setValue(node.worldDefID)

        self.transition.setCurrentIndex(node.transition)


        self._updatePosition()
        self._updateBoundingRect(initialState)


    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemSceneHasChanged:
            self.scene().addItem(self.buttonProxy)
            self.scene().addItem(self.worldProxy)
            self.scene().addItem(self.stageProxy)
            self.scene().addItem(self.secretProxy)
            self.scene().addItem(self.foreignIDProxy)
            self.scene().addItem(self.transitionProxy)
            self.scene().addItem(self.mapChangeProxy)
            self.scene().addItem(self.worldDefIDProxy)

        return QtWidgets.QGraphicsLineItem.itemChange(self, change, value)


    def showProxyAt(self, proxy, x, y):
        proxy.setPos(self.scenePos().x() + x, self.scenePos().y() + y)
        proxy.show()


    def stateChange(self, state):

        node = self._nodeRef()

        node.transition = 0
        node.mapChange = None
        node.mapID = None
        node.foreignID = None
        node.level = None
        node.worldDefID = None

        if state == PATH_NODE_STATE_LEVEL:
            node.level = [1, 1]
            self.world.setValue(node.level[0])
            self.stage.setValue(node.level[1])

        elif state == PATH_NODE_STATE_EXIT:
            node.transition = 0
            node.mapChange = 'None.arc'
            node.foreignID = 0

            usedIDs = []
            for nodesPicker in KP.map.pathLayer.nodes:
                usedIDs.append(nodesPicker.mapID)

            i = 1
            while i in usedIDs:
                i += 1

            node.mapID = i

            self.foreignID.setValue(1)
            self.mapChange.setText('None.arc')
            self.transition.setCurrentIndex(0)

        elif state == PATH_NODE_STATE_TRANSITION:
            node.worldDefID = 0


        self._updateBoundingRect(state)
        self.update()
        KP.mainWindow.pathNodeList.update()


    def worldChange(self, world):

        node = self._nodeRef()
        node.level[0] = world

        KP.mainWindow.pathNodeList.update()


    def stageChange(self, stage):

        node = self._nodeRef()
        node.level[1] = stage

        KP.mainWindow.pathNodeList.update()


    def secretChange(self, secret):

        node = self._nodeRef()
        node.hasSecret = secret

        KP.mainWindow.pathNodeList.update()


    def foreignIDChange(self, ID):

        node = self._nodeRef()
        node.foreignID = ID

        KP.mainWindow.pathNodeList.update()


    def worldDefIDChange(self, ID):
        node = self._nodeRef()
        node.worldDefID = ID


    def transitionChange(self, index):

        node = self._nodeRef()
        node.transition = index

        KP.mainWindow.pathNodeList.update()


    def mapChangeChange(self, mapname):

        node = self._nodeRef()
        node.mapChange = mapname

        KP.mainWindow.pathNodeList.update()


    def _updatePosition(self):
        self.ignoreMovement = True

        node = self._nodeRef()
        x, y = node.position
        self.setPos(x+12, y+12)

        self.ignoreMovement = False


    def _updateBoundingRect(self, state):
        if state == PATH_NODE_STATE_MOVEMENT:
            self._boundingRect = QtCore.QRectF(-12, -12, 24, 24)
        elif state == PATH_NODE_STATE_LEVEL:
            self._boundingRect = QtCore.QRectF(-20, -16, 40, 32)
        elif state == PATH_NODE_STATE_EXIT:
            self._boundingRect = QtCore.QRectF(-20, -16, 40, 32)
        elif state == PATH_NODE_STATE_TRANSITION:
            self._boundingRect = QtCore.QRectF(-16, -13, 32, 26)


    def _itemMoved(self, oldX, oldY, newX, newY):
        node = self._nodeRef()
        node.position = (newX-12, newY-12)

        for exit in node.exits:
            exit.qtItem.updatePosition()


    def setLayerSelected(self, selected):
        self.isLayerSelected = selected
        self.update()


    def paint(self, painter, option, widget):

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        node = self._nodeRef()

        selectionRect = None

        if node.level:
            painter.setBrush(QtGui.QColor(0, 0, 0, 0))
            painter.setPen(QtGui.QColor(0, 0, 0, 0))
            pix = QtGui.QPixmap("Resources/BlackLevel.png")
            painter.drawPixmap(-pix.width()//2, -pix.height()//2, pix)
            selectionRect = self._boundingRect.adjusted(1,5,-1,-5)

        elif node.mapChange is not None:
            painter.setBrush(QtGui.QColor(0, 0, 0, 0))
            painter.setPen(QtGui.QColor(0, 0, 0, 0))
            pix = QtGui.QPixmap("Resources/ExitWorld.png")
            painter.drawPixmap(-pix.width()//2, -pix.height()//2, pix)

            textPath = QtGui.QPainterPath()
            font = QtGui.QFont("Times", 22)
            font.setStyleStrategy(QtGui.QFont.ForceOutline)
            textPath.addText(-6, 3, font, str(node.mapID))

            painter.setBrush(QtGui.QColor(140, 140, 255))
            pen = QtGui.QPen(QtGui.QColor(80, 80, 255))
            pen.setWidth(1)
            pen.setStyle(Qt.SolidLine)
            painter.setPen(pen)
            painter.drawPath(textPath)

            selectionRect = self._boundingRect.adjusted(1,5,-1,-5)

        elif node.worldDefID is not None:
            painter.setBrush(QtGui.QColor(0, 0, 0, 0))
            painter.setPen(QtGui.QColor(0, 0, 0, 0))
            painter.drawPixmap(self._worldChangeRect.topLeft(), QtGui.QPixmap("Resources/WorldChange.png"))
            selectionRect = self._worldChangeRect

        elif len(node.exits) != 2:
            if self.isLayerSelected:
                brush = QtGui.QBrush(QtGui.QColor(255, 40, 40))
            else:
                brush = QtGui.QBrush(QtGui.QColor(255, 220, 220))
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setBrush(brush)
            painter.drawEllipse(self._stopRect)
            selectionRect = self._stopRect.adjusted(-1,-1,1,1)

        else:
            if self.isLayerSelected:
                brush = QtGui.QBrush(QtGui.QColor(255, 40, 40))
            else:
                brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
            painter.setPen(QtGui.QColor(255, 255, 255))
            painter.setBrush(brush)
            painter.drawEllipse(self._tinyRect)
            selectionRect = self._tinyRect.adjusted(-1,-1,1,1)


        if self.isSelected():
            painter.setPen(self.SELECTION_PEN)
            painter.setBrush(QtGui.QColor(0,0,0,0))
            painter.drawEllipse(selectionRect)

            # WHAT THE FUCK SINCE WHEN DO YOU SHOW/HIDE WIDGETS IN A PAINT EVENT
            # oh well, I don't feel like refactoring this
            self.showProxyAt(self.buttonProxy, 12, -24)

            if node.level:
                self.showProxyAt(self.worldProxy, -42, 24)
                self.showProxyAt(self.stageProxy, 6, 24)
                self.showProxyAt(self.secretProxy, -60, 26)

            else:
                self.worldProxy.hide()
                self.stageProxy.hide()
                self.secretProxy.hide()

            if node.mapChange is not None:
                self.showProxyAt(self.foreignIDProxy, 60, 24)
                self.showProxyAt(self.transitionProxy, -102, 24)
                self.showProxyAt(self.mapChangeProxy, -100, 60)

            else:
                self.foreignIDProxy.hide()
                self.transitionProxy.hide()
                self.mapChangeProxy.hide()

            if node.worldDefID is not None:
                self.showProxyAt(self.worldDefIDProxy, 60, 24)
            else:
                self.worldDefIDProxy.hide()

        else:
            self.buttonProxy.hide()
            self.worldProxy.hide()
            self.stageProxy.hide()
            self.secretProxy.hide()
            self.foreignIDProxy.hide()
            self.transitionProxy.hide()
            self.mapChangeProxy.hide()
            self.worldDefIDProxy.hide()


    def remove(self, withItem=False):
        node = self._nodeRef()
        layer = KP.map.pathLayer

        try:
            layer.nodes.remove(node)
        except ValueError:
            pass

        KP.mainWindow.pathNodeList.removeLayer(node)

        if len(node.exits) == 2:
            # let's try to join the two!
            pathOne, pathTwo = node.exits
            pathOneL = KP.mainWindow.pathNodeList.findLayerFor(pathOne)
            pathTwoL = KP.mainWindow.pathNodeList.findLayerFor(pathTwo)

            start1, end1 = pathOne._startNodeRef(), pathOne._endNodeRef()
            start2, end2 = pathTwo._startNodeRef(), pathTwo._endNodeRef()

            if start1 == node:
                start = end1
            else:
                start = start1

            if start2 == node:
                end = end2
            else:
                end = start2

            # make sure no path already exists between these nodes
            nope = False

            for pathToCheck in start.exits:
                if pathToCheck._startNodeRef() == end:
                    nope = True
                elif pathToCheck._endNodeRef() == end:
                    nope = True

            if not nope:
                joinedPath = KPPath(start, end, pathOne)

                # if both paths have the same tileset, just use that one
                if pathOneL.tileset == pathTwoL.tileset:
                    tileset = pathOneL.tileset
                else:
                    tileset = None

                if KP.mainWindow.pathNodeList.addLayer(joinedPath, False, tileset=tileset):
                    layer.paths.append(joinedPath)
                    item = KPEditorPath(joinedPath)
                    self.scene().addItem(item)

            for path in (pathOne, pathTwo):
                path.qtItem.remove(True)
        else:
            # we can't join them so just nuke them
            for exit in node.exits[:]:
                exit.qtItem.remove(True)

        if withItem:
            self.scene().removeItem(self)
            self.scene().removeItem(self.buttonProxy)
            self.scene().removeItem(self.worldProxy)
            self.scene().removeItem(self.stageProxy)
            self.scene().removeItem(self.secretProxy)
            self.scene().removeItem(self.foreignID)
            self.scene().removeItem(self.transition)
            self.scene().removeItem(self.mapChange)
            self.scene().removeItem(self.worldDefID)


class KPEditorPath(QtWidgets.QGraphicsLineItem):


    class PathOptionsMenuButton(QtWidgets.QPushButton):


        class PathOptionsWidget(QtWidgets.QWidget):
            def __init__(self, pathRef):
                QtWidgets.QWidget.__init__(self)

                self._pathRef = pathRef

                TopLayout = QtWidgets.QHBoxLayout()
                Layout = QtWidgets.QGridLayout()

                # Make an exclusive button group for our animations.
                self.ExclusiveButtons = QtWidgets.QButtonGroup()

                i = 0
                j = 1
                id = 0
                for anim, name in zip(PathAnimationList, PathAnimationNamesList):
                    newButton = QtWidgets.QPushButton(QtGui.QIcon("Resources/Anm/" + anim), "")
                    newButton.setCheckable(True)
                    newButton.setIconSize(QtCore.QSize(38, 38))
                    newButton.setToolTip(name)
                    self.ExclusiveButtons.addButton(newButton, id)

                    Layout.addWidget(newButton, j, i)

                    if id == 0:
                        newButton.setChecked(True)

                    id += 1
                    i += 1
                    if i == 4:
                        i = 0
                        j += 1



                # Movement Speed Spin Box
                self.moveSpeedSpinner = QtWidgets.QDoubleSpinBox()
                self.moveSpeedSpinner.setMinimum(0.0)
                self.moveSpeedSpinner.setMaximum(256.0)
                self.moveSpeedSpinner.setDecimals(2)
                self.moveSpeedSpinner.setSingleStep(0.05)
                self.moveSpeedSpinner.setValue(1.0)

                TopLayout.addWidget(QtWidgets.QLabel("Speed:"))
                TopLayout.addWidget(self.moveSpeedSpinner)


                # Connections

                if QtCompatVersion > 0x50000:
                    self.ExclusiveButtons.idReleased.connect(self.updatePathAnim)
                else:
                    self.ExclusiveButtons.buttonReleased[int].connect(self.updatePathAnim)

                self.moveSpeedSpinner.valueChanged.connect(self.updateMoveSpeed)

                # Layout
                Layout.addLayout(TopLayout, 0, 0, 1, 4)
                self.setLayout(Layout)


            def updateMoveSpeed(self, speed):
                path = self._pathRef()

                path.movementSpeed = speed
                path.qtItem.update()


            def updatePathAnim(self, buttonID):
                path = self._pathRef()

                path.animation = buttonID
                path.qtItem.update()


        def __init__(self, pathRef):
            QtWidgets.QPushButton.__init__(self)

            self.setText("Options")

            self.menu = QtWidgets.QMenu(self)
            layout = QtWidgets.QVBoxLayout()
            self.bgroupWidget = self.PathOptionsWidget(pathRef)
            layout.addWidget(self.bgroupWidget)

            self.menu.setLayout(layout)

            # dropShadow = QtWidgets.QGraphicsDropShadowEffect()
            # self.menu.setGraphicsEffect(dropShadow)
            self.setMenu(self.menu)


    class HiddenProxy(QtWidgets.QGraphicsProxyWidget):
        def __init__(self, widget):
            QtWidgets.QGraphicsProxyWidget.__init__(self, None)
            self.setWidget(widget)
            self.setZValue(999999)
            self.hide()


    def __init__(self, path):
        QtWidgets.QGraphicsLineItem.__init__(self)

        self.setFlag(self.ItemIsSelectable, True)

        self.setZValue(100)

        startNode = path._startNodeRef().qtItem
        endNode = path._endNodeRef().qtItem

        startNode.update()
        endNode.update()

        self._startNodeRef = weakref.ref(startNode)
        self._endNodeRef = weakref.ref(endNode)
        self._pathRef = weakref.ref(path)
        self.isLayerSelected = False

        path.qtItem = self

        if not hasattr(KPEditorPath, 'PEN'):
            KPEditorPath.BRUSH = QtGui.QBrush(QtGui.QColor(255, 255, 255, 140))
            KPEditorPath.PEN = QtGui.QPen(KPEditorPath.BRUSH, 8, Qt.SolidLine, Qt.RoundCap)
        self.setPen(KPEditorPath.PEN)

        if not hasattr(KPEditorPath, 'SELECTION_PEN'):
            KPEditorPath.SELECTION_PEN = QtGui.QPen(Qt.blue, 1, Qt.DotLine)

        self.options = self.PathOptionsMenuButton(self._pathRef)
        self.optionsProxy = self.HiddenProxy(self.options)

        self.options.bgroupWidget.ExclusiveButtons.button(path.animation).setChecked(True)
        self.options.bgroupWidget.moveSpeedSpinner.setValue(path.movementSpeed)

        self.updatePosition()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ControlModifier:
            return

        # modify the unlock settings
        from unlock import KPUnlockSpecDialog

        dlg = KPUnlockSpecDialog('path', 'unlocked')

        if hasattr(self._pathRef(), 'unlockSpec'):
            dlg.setSpec(self._pathRef().unlockSpec)

        result = dlg.exec_()
        if result == QtWidgets.QDialog.Accepted:
            print("New spec:", dlg.spec)
            self._pathRef().unlockSpec = dlg.spec


    def updatePosition(self):
        path = self._pathRef()

        sn = path._startNodeRef()
        en = path._endNodeRef()
        if sn is None or en is None:
            return

        x1, y1 = path._startNodeRef().position
        x2, y2 = path._endNodeRef().position

        originLine = QtCore.QLineF(x1+12, y1+12, x2+12, y2+12)
        self.setPos(originLine.pointAt(0.5))
        dy = originLine.dy()/2
        dx = originLine.dx()/2

        self.setLine(QtCore.QLineF(-dx, -dy, dx, dy))


    def setLayerSelected(self, selected):
        self.isLayerSelected = selected
        self.update()


    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemSceneHasChanged:
            self.scene().addItem(self.optionsProxy)

        return QtWidgets.QGraphicsLineItem.itemChange(self, change, value)


    def paint(self, painter, option, widget):

        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        if self.isLayerSelected:
            brush = QtGui.QBrush(QtGui.QColor(255, 40, 40, 200))
            pen = QtGui.QPen(brush, 12, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(brush)
        else:
            painter.setPen(KPEditorPath.PEN)

        painter.drawLine(self.line())

        if self.isSelected():
            painter.setPen(self.SELECTION_PEN)
            painter.setBrush(QtGui.QColor(0,0,0,0))
            painter.drawPath(self.shape())

            self.optionsProxy.setPos(self.scenePos().x() - 54, self.scenePos().y() + 24)
            self.optionsProxy.show()

        else:
            self.optionsProxy.hide()


    def remove(self, withItem=False):
        if hasattr(self, 'hasBeenRemovedAlready'):
            return

        self.hasBeenRemovedAlready = True

        path = self._pathRef()
        layer = KP.map.pathLayer
        KP.mainWindow.pathNodeList.removeLayer(path)

        layer.paths.remove(path)

        for ref in (self._startNodeRef, self._endNodeRef):
            node = ref()._nodeRef()
            try:
                node.exits.remove(path)
                node.qtItem.update()
            except ValueError:
                pass

        if withItem:
            self.scene().removeItem(self)
            self.scene().removeItem(self.optionsProxy)



