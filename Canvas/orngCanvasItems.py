# -*- coding: utf8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os, sys, math
import random
ERROR = 0
WARNING = 1

def getDropShadow(item):
    if hasattr(item, "graphicsEffect"):
        return item.graphicsEffect()
    else:
        return None
    
def setDropShadow(self, offset=QPointF(0.3, 0.5), blur_radius=5):
    if qVersion() >= "4.6" and self.canvasDlg.settings["enableCanvasDropShadows"]:
        effect = QGraphicsDropShadowEffect(self.scene())
        effect.setOffset(offset)
        effect.setBlurRadius(blur_radius)
        self.setGraphicsEffect(effect)
    
class TempCanvasLine(QGraphicsPathItem):
    def __init__(self, canvasDlg, canvas):
        QGraphicsLineItem.__init__(self, None, canvas)
        self.setZValue(-10)
        self.canvasDlg = canvasDlg
        self.startWidget = None
        self.endWidget = None
        self.widget = None

        self.setPen(QPen(QColor(180, 180, 180), 3, Qt.SolidLine))
        
        self.setDropShadow(offset=QPointF(0.0, 0.0))
    
    setDropShadow = setDropShadow
    getDropShadow = getDropShadow
    
    def setStartWidget(self, widget):
        self.startWidget = widget
        pos = widget.getRightEdgePoint()
        endX, endY = startX, startY = pos.x(), pos.y()

        
    def setEndWidget(self, widget):
        self.endWidget = widget
        pos = widget.getLeftEdgePoint()
        endX, endY = startX, startY = pos.x(), pos.y()

        
    def updateLinePos(self, newPos):
        if self.startWidget == None and self.endWidget == None:
            return
        
        if self.startWidget != None:
            func = "getDistToLeftEdgePoint"
        else:
            func = "getDistToRightEdgePoint"
        
        schema = self.canvasDlg.schema
        view = schema.canvasView
        
        self.widget = None
        widgets = view.getItemsAtPos(newPos, CanvasWidget)
        if widgets:
            self.widget = widgets[0]
        else:
            dists = [(getattr(w, func)(newPos), w) for w in schema.widgets]
            dists.sort()
            if dists and dists[0][0] < 20:
                self.widget = dists[0][1]
        
        if self.startWidget:
            pos = self.startWidget.getRightEdgePoint()
        else:
            pos = self.endWidget.getLeftEdgePoint()

        if self.widget not in [self.startWidget, self.endWidget]: 
            if self.startWidget == None and self.widget.widgetInfo.outputs:
                newPos = self.widget.getRightEdgePoint()
            elif self.endWidget == None and self.widget.widgetInfo.inputs:
                newPos = self.widget.getLeftEdgePoint()
        
        path = QPainterPath(pos)
        if self.startWidget != None:
            path.cubicTo(pos.x()+60, pos.y(), newPos.x()-60, newPos.y(), newPos.x(),newPos.y())
        else:
            path.cubicTo(pos.x()-60, pos.y(), newPos.x()+60, newPos.y(), newPos.x(),newPos.y())
        self.setPath(path)
        
    def remove(self):
        self.hide()
        self.startWidget = None
        self.endWidget = None
        
        self.prepareGeometryChange()
        
        if self.getDropShadow():
            self.setGraphicsEffect(None)
             
        for child in self.childItems():
            child.hide()
            child.setParentItem(None)
            self.scene().removeItem(child)
            
        self.hide()
        self.scene().removeItem(self)

# #######################################
# # CANVAS LINE
# #######################################
class CanvasLineColor():
    type2color = {}    
    @classmethod
    def getColorForType(cls, colorType):
        if colorType in cls.type2color:            
            return cls.type2color[colorType]

        a = random.randint(0, 255)
        b = random.randint(0, 255)
        c = random.randint(0, 255)
        cls.type2color[colorType] = (a, b, c)
        return cls.type2color[colorType]
        
class CanvasLine(QGraphicsPathItem):
    def __init__(self, canvasDlg, view, outWidget, inWidget, scene, lineType): #*args
        self.outWidget = outWidget
        self.inWidget = inWidget

        QGraphicsPathItem.__init__(self, None, None)

        self.canvasDlg = canvasDlg
        self.view = view
        self.setZValue(-10)
    
        self.caption = ""
        if lineType == None:
            self.lineType = Qt.SolidLine
            self.lineColor = Qt.black
            self.lineWidth = 4
        elif lineType == 'w2c':
            self.lineType = Qt.DashLine
            self.lineColor = Qt.blue
            self.lineWidth = 4
            self.caption = u"Class"
        elif lineType == 'c2w':
            self.lineType = Qt.DashLine
            self.lineColor = Qt.red
            self.lineWidth = 1
            self.caption = "Inst"                    
        elif  'c2c' in lineType:
            a, b, c = CanvasLineColor.getColorForType(lineType)     
            self.lineColor = QColor(a, b, c)
            self.lineType = Qt.SolidLine
            self.lineWidth = 4            
            head = 'c2c'
            self.caption = lineType[lineType.find(head)+len(head)+1:]            
 
        self.captionItem = QGraphicsTextItem(self)
        text_color = QColor(80, 80, 192)
        self.captionItem.setDefaultTextColor(text_color)
        self.captionItem.setHtml("<center>%s</center>" % self.caption)
        self.captionItem.setAcceptHoverEvents(False)
        self.captionItem.setVisible(bool(self.canvasDlg.settings["showSignalNames"]))
        self.captionItem.setAcceptedMouseButtons(Qt.NoButton)
        
        self.updateTooltip()
        
        self.setPen(QPen(QColor(192, 80, 80), 20, Qt.SolidLine))
        self.setAcceptHoverEvents(True)
        self.hoverState = False
            
        if scene is not None:
            scene.addItem(self)
                        
        self.setDropShadow(offset=QPointF(0.0, 0.0))
        
    setDropShadow = setDropShadow
    getDropShadow = getDropShadow
    
    def remove(self):
        self.hide()
        self.setToolTip("")
        self.outWidget = None
        self.inWidget = None
        
        self.prepareGeometryChange()
        
        if self.getDropShadow():
            self.setGraphicsEffect(None)
            
        for child in self.childItems():
            child.hide()
            child.setParentItem(None)
            self.scene().removeItem(child)
            
        self.hide()
        self.scene().removeItem(self)
        QApplication.instance().processEvents(QEventLoop.ExcludeUserInputEvents)
        
        return
              
    
    def updatePainterPath(self):
        p1 = self.outWidget.getRightEdgePoint()
        p2 = self.inWidget.getLeftEdgePoint()
        path = QPainterPath(p1)
        path.cubicTo(p1.x() + 60, p1.y(), p2.x() - 60, p2.y(), p2.x(), p2.y())
        self.setPath(path)
        metrics = QFontMetrics(self.captionItem.font())
        oddLineOffset = -metrics.lineSpacing() / 2 * (len(self.caption.strip().splitlines()) % 2)
        mid = self.path().pointAtPercent(0.5)
        rect = self.captionItem.boundingRect()
        self.captionItem.setPos(mid + QPointF(-rect.width() / 2.0, -rect.height() / 2.0 + oddLineOffset))
        self.update()
        
    def shape(self):
        stroke = QPainterPathStroker()
        stroke.setWidth(self.lineWidth)
        return stroke.createStroke(self.path())
    
    def boundingRect(self):
        rect = QGraphicsPathItem.boundingRect(self)
        if self.getDropShadow():
            textRect = self.captionItem.boundingRect() ## Should work without this but for some reason if using graphics effects the text gets clipped
            textRect.moveTo(self.captionItem.pos())
            return rect.united(textRect)
        else:
            return rect

    def paint(self, painter, option, widget = None):
        color2 = self.lineColor
        painter.setPen(QPen(color2, 2 , self.lineType, Qt.RoundCap))
        painter.drawPath(self.path())

    def updateTooltip(self):   
        self.updatePainterPath()


    def hoverEnterEvent(self, event):
        self.hoverState = True
        self.update()
    
    def hoverLeaveEvent(self, event):
        self.hoverState = False
        self.update()
        

# #######################################
# # CANVAS WIDGET
# #######################################
class CanvasWidget(QGraphicsRectItem):
    def __init__(self, scene, view, widgetInfo, defaultPic, canvasDlg, widgetSettings = {}, extra=None):
        # import widget class and create a class instance
        m = __import__(widgetInfo.fileName)
        self.instance = m.__dict__[widgetInfo.fileName].__new__(m.__dict__[widgetInfo.fileName], _owInfo=canvasDlg.settings["owInfo"],
                                                                _owWarning = canvasDlg.settings["owWarning"], _owError=canvasDlg.settings["owError"],
                                                                _owShowStatus = canvasDlg.settings["owShow"], _useContexts = canvasDlg.settings["useContexts"],
                                                                _category = widgetInfo.category, _settingsFromSchema = widgetSettings)
        self.instance.__init__(signalManager=None)
        self.instance.__dict__["widgetInfo"] = widgetInfo
        self.isProcessing = 0   # is this widget currently processing signals
        self.progressBarShown = 0
        self.progressBarValue = -1
        self.widgetSize = QSizeF(0, 0)
        self.widgetState = {}
        self.caption = widgetInfo.name
        self.extra = extra
        self.tooltip = ""
        self.widgetSettings = widgetSettings
        self.selected = False
        self.inLines = []               # list of connected lines on input
        self.outLines = []              # list of connected lines on output
        self.icon = canvasDlg.getWidgetIcon(widgetInfo)
        
        self.instance.setProgressBarHandler(view.progressBarHandler)   # set progress bar event handler
        self.instance.setProcessingHandler(view.processingHandler)
        self.instance.setWidgetStateHandler(self.updateWidgetState)
        self.instance.setEventHandler(canvasDlg.output.widgetEvents)
        self.instance.setWidgetIcon(canvasDlg.getFullWidgetIconName(widgetInfo))


        QGraphicsRectItem.__init__(self, None, None)
        self.widgetInfo = widgetInfo
        self.view = view
        self.canvasDlg = canvasDlg
        canvasPicsDir  = os.path.join(canvasDlg.canvasDir, "icons")
        self.imageLeftEdge = QPixmap(os.path.join(canvasPicsDir,"leftEdge.png"))
        self.imageRightEdge = QPixmap(os.path.join(canvasPicsDir,"rightEdge.png"))
        self.imageLeftEdgeG = QPixmap(os.path.join(canvasPicsDir,"leftEdgeG.png"))
        self.imageRightEdgeG = QPixmap(os.path.join(canvasPicsDir,"rightEdgeG.png"))
        self.imageLeftEdgeR = QPixmap(os.path.join(canvasPicsDir,"leftEdgeR.png"))
        self.imageRightEdgeR = QPixmap(os.path.join(canvasPicsDir,"rightEdgeR.png"))
        self.shownLeftEdge, self.shownRightEdge = self.imageLeftEdge, self.imageRightEdge
        self.imageFrame = QIcon(QPixmap(os.path.join(canvasPicsDir, "frame.png")))
        self.edgeSize = QSizeF(self.imageLeftEdge.size())
        self.resetWidgetSize()
        
        self.oldPos = self.pos()
        
        self.infoIcon = QGraphicsPixmapItem(self.canvasDlg.widgetIcons["Info"], self)
        self.warningIcon = QGraphicsPixmapItem(self.canvasDlg.widgetIcons["Warning"], self)
        self.errorIcon = QGraphicsPixmapItem(self.canvasDlg.widgetIcons["Error"], self)
        self.infoIcon.hide()
        self.warningIcon.hide()
        self.errorIcon.hide()
        
        self.captionItem = QGraphicsTextItem(self)
        self.captionItem.setHtml("<center>%s</center>" % self.caption)
        self.captionItem.document().setTextWidth(min(self.captionItem.document().idealWidth(), 200))
        
        self.captionItem.setPos(-self.captionItem.boundingRect().width()/2.0 + self.widgetSize.width() / 2.0, self.widgetSize.height() + 2)
        self.captionItem.setAcceptHoverEvents(False)
        
        # do we want to restore last position and size of the widget
        if self.canvasDlg.settings["saveWidgetsPosition"]:
            self.instance.restoreWidgetPosition()
            
        self.setAcceptHoverEvents(True)
        self.hoverState = False
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        if scene is not None:
            scene.addItem(self)
            
        self.setDropShadow()
        self.generateTooltip()
        self.setToolTip(self.tooltip)
        
    setDropShadow = setDropShadow
    getDropShadow = getDropShadow
    
    def resetWidgetSize(self):
        size = self.canvasDlg.schemeIconSizeList[self.canvasDlg.settings['schemeIconSize']]
        self.setRect(0,0, size, size)
        self.widgetSize = QSizeF(size, size)
        self.update()

    # get the list of connected signal names
    def getInConnectedSignalNames(self):
        return []


    # get the list of connected signal names
    def getOutConnectedSignalNames(self):
        return []


    def remove(self):
        self.hide()
        self.errorIcon.hide()
        self.warningIcon.hide()
        self.infoIcon.hide()

        # save settings
        if (self.instance != None):
            self.instance.close()
            self.instance.linksOut.clear()      # this helps python to more quickly delete the unused objects
            self.instance.linksIn.clear()
            self.instance.setProgressBarHandler(None)   # set progress bar event handler
            self.instance.setProcessingHandler(None)
            self.instance.setWidgetStateHandler(None)
            self.instance.setEventHandler(None)
            self.instance.onDeleteWidget()      # this is a cleanup function that can take care of deleting some unused objects
            
            # Schedule the widget instance for deletion
            self.instance.deleteLater()
            self.instance = None
            
        self.prepareGeometryChange()
        
        if self.getDropShadow():
            self.setGraphicsEffect(None)
        
        for child in self.childItems():
            child.hide()
            child.setParentItem(None)
            self.scene().removeItem(child)
        
        self.hide()
        self.scene().removeItem(self)
        
    def savePosition(self):
        self.oldPos = self.pos()

    def restorePosition(self):
        self.setPos(self.oldPos)

    def updateText(self, text):
        self.caption = text
        self.prepareGeometryChange()
        self.captionItem.setHtml("<center>%s</center>" % self.caption)
        self.captionItem.document().adjustSize()
        self.captionItem.document().setTextWidth(min(self.captionItem.document().idealWidth(), 200))
        
        self.captionItem.setPos(-self.captionItem.boundingRect().width()/2.0 + self.widgetSize.width() / 2.0, self.widgetSize.height() + 2)
        self.updateTooltip()
        self.update()

    def updateWidgetState(self):
        widgetState = self.instance.widgetState

        self.infoIcon.hide()
        self.warningIcon.hide()
        self.errorIcon.hide()

        yPos = - 21 - self.progressBarShown * 20
        iconNum = sum([widgetState.get("Info", {}).values() != [],  widgetState.get("Warning", {}).values() != [], widgetState.get("Error", {}).values() != []])

        if self.canvasDlg.settings["ocShow"]:        # if show icons is enabled in canvas options dialog
            startX = (self.rect().width()/2) - ((iconNum*(self.canvasDlg.widgetIcons["Info"].width()+2))/2)
            off  = 0
            if len(widgetState.get("Info", {}).values()) > 0 and self.canvasDlg.settings["ocInfo"]:
                off  = self.updateWidgetStateIcon(self.infoIcon, startX, yPos, widgetState["Info"])
            if len(widgetState.get("Warning", {}).values()) > 0 and self.canvasDlg.settings["ocWarning"]:
                off += self.updateWidgetStateIcon(self.warningIcon, startX+off, yPos, widgetState["Warning"])
            if len(widgetState.get("Error", {}).values()) > 0 and self.canvasDlg.settings["ocError"]:
                off += self.updateWidgetStateIcon(self.errorIcon, startX+off, yPos, widgetState["Error"])


    def updateWidgetStateIcon(self, icon, x, y, stateDict):
        icon.setPos(x,y)
        icon.show()
        icon.setToolTip(reduce(lambda x,y: x+'<br>'+y, stateDict.values()))
        return icon.pixmap().width() + 3

    # set coordinates of the widget
    def setCoords(self, x, y):
        if self.canvasDlg.settings["snapToGrid"]:
            x = round(x/10)*10
            y = round(y/10)*10
        self.setPos(x, y)
        self.updateWidgetState()
        
    def setPos(self, *args):
        QGraphicsRectItem.setPos(self, *args)
        for line in self.inLines + self.outLines:
            line.updatePainterPath()
            

    # we have to increase the default bounding rect so that we also repaint the name of the widget and input/output boxes
    def boundingRect(self):
        rect = QRectF(QPointF(0, 0), self.widgetSize).adjusted(-11, -6, 11, 6)
        rect.setTop(rect.top() - 20 - 21) ## Room for progress bar and warning, error, info icons
        if self.getDropShadow():
            textRect = self.captionItem.boundingRect() ## Should work without this but for some reason if using graphics effects the text gets clipped
            textRect.moveTo(self.captionItem.pos()) 
            return rect.united(textRect)
        else:
            return rect

    # is mouse position inside the left signal channel
    def mouseInsideLeftChannel(self, pos):
        if self.widgetInfo.inputs == []: return False

        boxRect = QRectF(self.x()-self.edgeSize.width(), self.y() + (self.widgetSize.height()-self.edgeSize.height())/2, self.edgeSize.width(), self.edgeSize.height())
        boxRect.adjust(-10,-10,5,10)       # enlarge the rectangle
        if isinstance(pos, QPointF) and boxRect.contains(pos): return True
        elif isinstance(pos, QRectF) and boxRect.intersects(pos): return True
        else: return False

    # is mouse position inside the right signal channel
    def mouseInsideRightChannel(self, pos):
        if self.widgetInfo.outputs == []: return False

        boxRect = QRectF(self.x()+self.widgetSize.width(), self.y() + (self.widgetSize.height()-self.edgeSize.height())/2, self.edgeSize.width(), self.edgeSize.height())
        boxRect.adjust(-5,-10,10,10)       # enlarge the rectangle
        if isinstance(pos, QPointF) and boxRect.contains(pos): return True
        elif isinstance(pos, QRectF) and boxRect.intersects(pos): return True
        else: return False
        
    def canConnect(self, outWidget, inWidget, dynamic=False):
        if outWidget == inWidget:
            return
        
        canConnect = True
        
        if outWidget == self:
            self.shownRightEdge = canConnect and self.imageRightEdgeG or self.imageRightEdgeR
        else:
            self.shownLeftEdge = canConnect and self.imageLeftEdgeG or self.imageLeftEdgeR

    def resetLeftRightEdges(self):
        self.shownLeftEdge = self.imageLeftEdge
        self.shownRightEdge = self.imageRightEdge
    
    
    # we know that the mouse was pressed inside a channel box. We only need to find
    # inside which one it was
    def getEdgePoint(self, pos):
        if self.mouseInsideLeftChannel(pos):
            return self.getLeftEdgePoint()
        elif self.mouseInsideRightChannel(pos):
            return self.getRightEdgePoint()

    def getLeftEdgePoint(self):
        return QPointF(self.x()+2- self.edgeSize.width(), self.y() + self.widgetSize.height()/2)

    def getRightEdgePoint(self):
        return QPointF(self.x()-2+ self.widgetSize.width() + self.edgeSize.width(), self.y() + self.widgetSize.height()/2)

    def getDistToLeftEdgePoint(self, point):
        p = self.getLeftEdgePoint()
        diff = point-p
        return math.sqrt(diff.x()**2 + diff.y()**2)
    
    def getDistToRightEdgePoint(self, point):
        p = self.getRightEdgePoint()
        diff = point-p
        return math.sqrt(diff.x()**2 + diff.y()**2)


    # draw the widget
    def paint(self, painter, option, widget = None):
        if self.isProcessing or self.isSelected() or getattr(self, "invalidPosition", False):
            painter.setPen(QPen(QBrush(QColor(125, 162, 206, 192)), 1, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(QBrush(QColor(217, 232, 252, 192)))
            painter.drawRoundedRect(-10, -5, self.widgetSize.width()+20, self.widgetSize.height()+10, 5, 5)

        if self.widgetInfo.inputs != []:
            painter.drawPixmap(-self.edgeSize.width()+1, (self.widgetSize.height()-self.edgeSize.height())/2, self.shownLeftEdge)
        if self.widgetInfo.outputs != []:
            painter.drawPixmap(self.widgetSize.width()-2, (self.widgetSize.height()-self.edgeSize.height())/2, self.shownRightEdge)
            
        if self.hoverState:
            color = QColor(125, 162, 206)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(-2, -2, self.widgetSize.width() + 4, self.widgetSize.height() + 4, 5, 5)
            
        painter.drawPixmap(0,0, self.icon.pixmap(self.widgetSize.width(), self.widgetSize.height()))
        
        yPos = -22
        if self.progressBarValue >= 0 and self.progressBarValue <= 100:
            rect = QRectF(0, yPos, self.widgetSize.width(), 16)
            painter.setPen(QPen(QColor(0,0,0)))
            painter.setBrush(QBrush(QColor(255,255,255)))
            painter.drawRect(rect)

            painter.setBrush(QBrush(QColor(0,128,255)))
            painter.drawRect(QRectF(0, yPos, self.widgetSize.width()*self.progressBarValue/100., 16))
            painter.drawText(rect, Qt.AlignCenter, "%d %%" % (self.progressBarValue))


    def addOutLine(self, line):
        self.outLines.append(line)

    def addInLine(self,line):
        self.inLines.append(line)

    def removeLine(self, line):
        if line in self.inLines:
            self.inLines.remove(line)
        elif line in self.outLines:
            self.outLines.remove(line)
        else:
            print "Orange Canvas: Error. Unable to remove line"

        self.updateTooltip()

    def setAllLinesFinished(self, finished):
        for line in self.inLines: line.finished = finished
        for line in self.outLines: line.finished = finished

    def generateTooltip(self):
        if self.extra is None:
            self.tooltip = u"<nobr><b>" + u'系统节点' + "</b></nobr>" 
            return
        
        if self.extra['type'] == 1:
            wtype = u'语义'
        else:
            wtype = u'词组'
        if 'words' not in self.extra:
            words =  u"( －－ )"
        else:
            words = u" ".join(self.extra['words'][:3]) + u" ...."

        if 'definition' not in self.extra:
            definition = u"( －－ )"
        else:
            definition = unicode(self.extra['definition'])
        length = len(definition)
        line1_start = 5
        line1_len = 30-line1_start
        line1 = definition[0:line1_len]
        length = length - line1_len
        lines = []
        lines.append(line1)
    
        for n in range(length/30+1):
            line =  definition[n*30+line1_len:(n+1)*30+line1_len]
            if line: lines.append(line)
        definition = u"<br>".join(lines)
        
        id = unicode(self.extra['id'])

        string = u"<nobr><b>" + wtype + u"</b> : <b>" + id + u"</b></nobr><hr>定义:<br>"
        string += u"<nobr> &nbsp; &nbsp; - " + definition + u"</nobr><hr>包含:<br>"
        string += u"<nobr> &nbsp; &nbsp; - " + words + u"</nobr><br>"
        self.tooltip = string
        
    def updateTooltip(self):
        pass

    def setProgressBarValue(self, value):
        self.progressBarValue = value
        if value < 0 or value > 100:
            self.updateWidgetState()
        self.update()

    def setProcessing(self, value):
        self.isProcessing = value
        self.update()

    def hoverEnterEvent(self, event):
        self.hoverState = True
        self.update()
        return QGraphicsRectItem.hoverEnterEvent(self, event)
        
    def hoverLeaveEvent(self, event):
        self.hoverState = False
        self.update()
        return QGraphicsRectItem.hoverLeaveEvent(self, event)        

class MyCanvasText(QGraphicsSimpleTextItem):
    def __init__(self, canvas, text, x, y, flags=Qt.AlignLeft, bold=0, show=1):
        QGraphicsSimpleTextItem.__init__(self, text, None, canvas)
        self.setPos(x,y)
        self.setPen(QPen(Qt.black))
        self.flags = flags
        if bold:
            font = self.font();
            font.setBold(1);
            self.setFont(font)
        if show:
            self.show()

    def paint(self, painter, option, widget = None):

        painter.setPen(self.pen())
        painter.setFont(self.font())

        xOff = 0; yOff = 0
        rect = painter.boundingRect(QRectF(0,0,2000,2000), self.flags, self.text())
        if self.flags & Qt.AlignHCenter: xOff = rect.width()/2.
        elif self.flags & Qt.AlignRight: xOff = rect.width()
        if self.flags & Qt.AlignVCenter: yOff = rect.height()/2.
        elif self.flags & Qt.AlignBottom:yOff = rect.height()
 
        painter.drawText(-xOff, -yOff, rect.width(), rect.height(), self.flags, self.text())
        
