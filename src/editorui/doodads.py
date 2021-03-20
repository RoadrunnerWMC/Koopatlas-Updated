from common import *
from .editorcommon import *
import weakref
from math import floor, ceil
import math


class KPEditorDoodad(KPEditorItem):
    SNAP_TO = (12,12)


    def __init__(self, doodad, layer):
        KPEditorItem.__init__(self)

        doodad.qtItem = self
        self._doodadRef = weakref.ref(doodad)
        self._layerRef = weakref.ref(layer)

        self.resizing = None
        self.rotating = None

        self.source = doodad.source

        self._updatePixmap()
        self._updatePosition()
        self._updateSize()
        self._updateTransform()

        if len(doodad.animations) > 0:
            doodad.setupAnimations()

        if not hasattr(KPEditorDoodad, 'SELECTION_PEN'):
            KPEditorDoodad.SELECTION_PEN = QtGui.QPen(Qt.red, 1, Qt.DotLine)


    def _updatePixmap(self):
        pixmap = self.source[1]

        self.prepareGeometryChange()
        w, h = pixmap.width(), pixmap.height()

        self.pixmap = pixmap


    def _updatePosition(self):
        # NOTE: EditorDoodads originate at the centre, not the top left like the others
        self.ignoreMovement = True

        doodad = self._doodadRef()
        x,y = doodad.position
        w,h = doodad.size
        self.setPos(x+floor(w/2.0), y+floor(h/2.0))

        self.ignoreMovement = False


    def _updateSize(self):
        self.prepareGeometryChange()

        w,h = self._doodadRef().size

        self._boundingRect = QtCore.QRectF(-w/2, -h/2, w, h)
        self._selectionRect = self._boundingRect.adjusted(0, 0, -1, -1)


    def _updateTransform(self):
        doodad = self._doodadRef()

        self.setRotation(doodad.angle)


    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self.SELECTION_PEN)
            painter.drawRect(self._selectionRect)


    def _itemMoved(self, oldX, oldY, newX, newY):
        doodad = self._doodadRef()
        w,h = doodad.size
        doodad.position = [newX-floor(w/2.0), newY-floor(h/2.0)]


    def hoverMoveEvent(self, event):
        if self._layerRef() != KP.mapScene.currentLayer:
            self.setCursor(Qt.ArrowCursor)
            return

        pos = event.pos()
        bit = self.resizerPortionAt(pos.x(), pos.y())


        if (event.modifiers() == Qt.ShiftModifier):

            if bit:
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        else:

            if bit == 1 or bit == 4:
                self.setCursor(Qt.SizeFDiagCursor)
            elif bit == 2 or bit == 3:
                self.setCursor(Qt.SizeBDiagCursor)
            elif bit == 7 or bit == 8:
                self.setCursor(Qt.SizeHorCursor)
            elif bit == 5 or bit == 6:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        KPEditorItem.hoverMoveEvent(self, event)


    def hoverLeaveEvent(self, event):
        self.unsetCursor()

        KPEditorItem.hoverLeaveEvent(self, event)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            bit = self.resizerPortionAt(pos.x(), pos.y())

            if self._layerRef() == KP.mapScene.currentLayer and bit:
            # if bit:
                event.accept()

                if (event.modifiers() & Qt.ShiftModifier):
                    self.rotating = self.mapToScene(pos), self._doodadRef().angle
                    self.setCursor(Qt.ClosedHandCursor)
                    return

                else:
                    x, xSide, y, ySide = False, None, False, None

                    if bit == 1 or bit == 7 or bit == 3: # left
                        x, xSide = True, 1

                    elif bit == 2 or bit == 4 or bit == 8: # right
                        x, xSide = True, 0

                    if bit == 1 or bit == 2 or bit == 5: # top
                        y, ySide = True, 1

                    elif bit == 3 or bit == 4 or bit == 6: # bottom
                        y, ySide = True, 0

                    self._updateSize()
                    self.resizing = (x, xSide, y, ySide)
                    return


        KPEditorItem.mousePressEvent(self, event)


    def _tryAndResize(self, obj, axisIndex, mousePosition, stationarySide):

        newSize = abs(mousePosition) * 2

        if newSize < 10:
            return False

        obj.size[axisIndex] = newSize

        return True


    def _tryAndRotate(self, obj, mouseX, mouseY, originalPos, oldAngle, modifiers):
        center = self.mapToScene(self.boundingRect().center())

        objX = center.x()
        objY = center.y()


        origX = originalPos.x()
        origY = originalPos.y()

        dy = origY - objY
        dx = origX - objX
        rads = math.atan2(dy, dx)

        origAngle = math.degrees(rads)

        dy = mouseY - objY
        dx = mouseX - objX
        rads = math.atan2(dy, dx)

        angle = math.degrees(rads)


        # Move this to ItemChange() or something at some point.
        finalAngle = angle - origAngle + oldAngle

        if (modifiers & Qt.ControlModifier):
            finalAngle = int(finalAngle / 45.0) * 45.0

        return True, finalAngle


    def mouseMoveEvent(self, event):
        if self.resizing:
            obj = self._doodadRef()

            hasChanged = False
            resizeX, xSide, resizeY, ySide = self.resizing

            if resizeX:
                hasChanged |= self._tryAndResize(obj, 0, event.pos().x(), xSide)
            if resizeY:
                hasChanged |= self._tryAndResize(obj, 1, event.pos().y(), ySide)

            if hasChanged:
                # Doodads aren't supposed to snap, they're all free flowing like the wind.
                self._updateSize()


        elif self.rotating:
            obj = self._doodadRef()
            scenePos = event.scenePos()
            self.setTransformOriginPoint(self.boundingRect().center())

            hasChanged = False

            hasChanged, angle = self._tryAndRotate(obj, scenePos.x(), scenePos.y(), self.rotating[0], self.rotating[1], event.modifiers())

            if hasChanged:
                obj.angle = angle
                self._updateTransform()


        else:
            KPEditorItem.mouseMoveEvent(self, event)


    def mouseReleaseEvent(self, event):
        if self.resizing and event.button() == Qt.LeftButton:
            self.resizing = None
            # self._doodadRef().position = [self.x(), self.y()]

        elif self.rotating and event.button() == Qt.LeftButton:
            self.rotating = None

        else:
            KPEditorItem.mouseReleaseEvent(self, event)


    def remove(self, withItem=False):
        doodad = self._doodadRef()
        layer = self._layerRef()

        if isinstance(layer, KPPathTileLayer):
            layer.doodads.remove(doodad)
        else:
            layer.objects.remove(doodad)
        doodad.cleanUpAnimations()

        if withItem:
            self.scene().removeItem(self)



