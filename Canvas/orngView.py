# -*- coding: utf8 -*-
# Author: Gregor Leban (gregor.leban@fri.uni-lj.si)
# Description:
#    handling the mouse events inside documents
#
import orngCanvasItems
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import orngHistory, orngTabs, orngEnviron
        
class SchemaView(QGraphicsView):
    def __init__(self, doc, *args):
        apply(QGraphicsView.__init__,(self,) + args)
        self.doc = doc
        self.bWidgetDragging = False               # are we currently dragging a widget
        self.movingWidget = None
        self.mouseDownPosition = QPointF(0,0)
        self.tempLine = None
        self.widgetSelectionRect = None
        self.widgetsSelected = []
        self.selectedLine = None
        self.tempWidget = None
        self.setRenderHint(QPainter.Antialiasing)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.ensureVisible(0,0,1,1)


 
    # ###########################################
    # drag and drop events. You can open a document by dropping it on the canvas
    # ###########################################
    def containsOWSFile(self, name):
        name = name.strip("\x00")
        return name.lower().endswith(".ows")

    def dragEnterEvent(self, ev):
        if self.containsOWSFile(str(ev.mimeData().data("FileName"))):
            ev.accept()
        else: ev.ignore()
                
    def dragMoveEvent(self, ev):
        if self.containsOWSFile(str(ev.mimeData().data("FileName"))):
            ev.setDropAction(Qt.MoveAction)
            ev.accept()
        else:
            ev.ignore()

    def dropEvent(self, ev):
        name = str(ev.mimeData().data("FileName"))
        if self.containsOWSFile(name):
            name = name.strip("\x00")
            self.doc.loadDocument(name)
            ev.accept()
        else:
            ev.ignore()

    def onSelectionChanged(self):
        selected = self.scene().selectedItems()
        one_selected = len(selected) == 1
        n_selected = len(selected) > 0
        self.doc.canvasDlg.widgetPopup.setEnabled(n_selected)
        self.doc.canvasDlg.openActiveWidgetAction.setEnabled(one_selected)
        self.doc.canvasDlg.renameActiveWidgetAction.setEnabled(one_selected)
        self.doc.canvasDlg.removeActiveWidgetAction.setEnabled(n_selected)
        self.doc.canvasDlg.helpActiveWidgetAction.setEnabled(one_selected)
        
    def expandActiveWidget(self):
        widgets = self.getSelectedWidgets()
        if len(widgets) != 1: return
        widget = widgets[0]         
        if widget.extra is None:           
            text, ok =QInputDialog.getText(self, u"查找词语", u"请输入词语",QLineEdit.Normal, u"百度")
            if not ok:
                return
            inst = self.doc.allocTreeInst()
            self.doc.expand2WordFromRoot(inst, widget, unicode(text))
        elif widget.extra['type'] == 1:
            self.doc.expand2WordsFromConcept(widget)
        elif widget.extra['type'] == 2:
            self.doc.expand2ConceptsFromWord(widget)
 
    def unexpandActiveWidget(self, widget):
        self.doc.unexpandWidget(widget)
            
    # ###########################################
    # POPUP MENU - WIDGET actions
    # ###########################################

    # popMenuAction - user selected to show active widget
    def openActiveWidget(self):
        #if not self.tempWidget or self.tempWidget.instance == None: return
        widgets = self.getSelectedWidgets()
        if len(widgets) != 1: return
        widget = widgets[0]
        widget.instance.reshow()
        if widget.instance.isMinimized():  # if widget is minimized, show its normal size
            widget.instance.showNormal()

    def helpOnActiveWidget(self):
        #if not self.tempWidget or self.tempWidget.instance == None: return
        widgets = self.getSelectedWidgets()
        if len(widgets) != 1: return
        widget = widgets[0]
        widget.instance.openWidgetHelp()

    # popMenuAction - user selected to rename active widget
    def renameActiveWidget(self):
        widgets = self.getSelectedWidgets()
        if len(widgets) != 1: return
        widget = widgets[0]

        exName = str(widget.caption)
        (newName, ok) = QInputDialog.getText(self, "Rename Widget", "Enter new name for the '" + exName + "' widget:", QLineEdit.Normal, exName)
        newName = str(newName)
        if ok and newName != exName:
            for w in self.doc.widgets:
                if w != widget and w.caption == newName:
                    QMessageBox.information(self, 'Orange Canvas', 'Unable to rename widget. An instance with that name already exists.')
                    return
            widget.updateText(newName)
            widget.instance.setCaption(newName)

    # popMenuAction - user selected to delete active widget
    def removeActiveWidget(self):
        selectedWidgets = self.getSelectedWidgets()
        if selectedWidgets == []:
            selectedWidgets = [self.tempWidget]

        for item in selectedWidgets:
            self.doc.removeWidget(item)

        self.tempWidget = None


    # ###########################################
    # POPUP MENU - LINKS actions
    # ###########################################

    # popMenuAction - enable/disable link between two widgets
    def toggleEnabledLink(self):
        if self.selectedLine != None:
            oldEnabled = True
            raise "ChangeLinkState"
            self.selectedLine.updateTooltip()
            self.selectedLine.inWidget.updateTooltip()
            self.selectedLine.outWidget.updateTooltip()

    # popMenuAction - delete selected link
    def deleteSelectedLine(self):
        if not self.selectedLine: return

        self.deleteLine(self.selectedLine)
        self.selectedLine = None


    def deleteLine(self, line):
        if line != None:
            self.doc.removeLine1(line)

    def unselectAllWidgets(self):
        for item in self.doc.widgets:
            item.setSelected(False)
            
    def selectAllWidgets(self):
        for item in self.doc.widgets:
            item.setSelected(True)

    def getItemsAtPos(self, pos, itemType = None):
        if isinstance(pos, QGraphicsItem):
            items = self.scene().collidingItems(pos)
        else:
            items = self.scene().items(pos)

        if itemType is not None:
            items = [item for item in items if type(item) == itemType]
        return items

    # ###########################################
    # MOUSE events
    # ###########################################

    # mouse button was pressed
    def mousePressEvent(self, ev):
        self.mouseDownPosition = self.mapToScene(ev.pos())

        if self.widgetSelectionRect:
            self.widgetSelectionRect.hide()
            self.widgetSelectionRect = None

        # do we start drawing a connection line
        if ev.button() == Qt.LeftButton:
            widgets = [item for item in self.doc.widgets if item.mouseInsideRightChannel(self.mouseDownPosition) or item.mouseInsideLeftChannel(self.mouseDownPosition)]# + [item for item in self.doc.widgets if item.mouseInsideLeftChannel(self.mouseDownPosition)]           
            self.unselectAllWidgets()
            if widgets:
                self.tempWidget = widgets[0]

                self.tempLine = orngCanvasItems.TempCanvasLine(self.doc.canvasDlg, self.scene())
                if self.tempWidget.getDistToLeftEdgePoint(self.mouseDownPosition) < self.tempWidget.getDistToRightEdgePoint(self.mouseDownPosition):
                    self.tempLine.setEndWidget(self.tempWidget)
                    for widget in self.doc.widgets:
                        widget.canConnect(widget, self.tempWidget, dynamic=True)
                else:
                    self.tempLine.setStartWidget(self.tempWidget)
                    for widget in self.doc.widgets:
                        widget.canConnect(self.tempWidget, widget, dynamic=True)
                                                        
                return QGraphicsView.mousePressEvent(self, ev)
            
        items = self.scene().items(QRectF(self.mouseDownPosition, QSizeF(0 ,0)).adjusted(-2, -2, 2, 2))#, At(self.mouseDownPosition)
        items = [item for item in items if type(item) in [orngCanvasItems.CanvasWidget, orngCanvasItems.CanvasLine]]
        activeItem = items[0] if items else None
        if not activeItem:
            self.tempWidget = None
            rect = self.maxSelectionRect(QRectF(self.mouseDownPosition, self.mouseDownPosition))
            self.widgetSelectionRect = QGraphicsRectItem(rect, None, self.scene())
            self.widgetSelectionRect.setPen(QPen(QBrush(QColor(51, 153, 255, 192)), 0.4, Qt.SolidLine, Qt.RoundCap))
            self.widgetSelectionRect.setBrush(QBrush(QColor(168, 202, 236, 192)))
            self.widgetSelectionRect.setZValue(-100)
            self.widgetSelectionRect.show()
            self.unselectAllWidgets()
            # Generate a MENU of DB Selection
            if ev.button() == Qt.RightButton: 
                widgetPopup = QMenu("Concept", self)
                for dbConfig in orngEnviron.dbConfigs:
                    triggered = (dbConfig == self.doc.activeDbConfig)
                    menuItem = widgetPopup.addAction(dbConfig['DBNAME'])
                    menuItem.setCheckable(True)
                    menuItem.setChecked(triggered)                                
                    receiver = lambda show, dbConfig=dbConfig: self.selectDB(show, dbConfig)
                    self.connect(menuItem, SIGNAL('triggered(bool)'), receiver)  
                widgetPopup.addSeparator()
                menuItem = widgetPopup.addAction("Remove All")
                receiver = lambda : self.removeAll()
                self.connect(menuItem, SIGNAL('triggered()'), receiver)
                widgetPopup.popup(ev.globalPos())                        
                return
        # we clicked on a widget or on a line
        else:
            if type(activeItem) == orngCanvasItems.CanvasWidget:
                # if we clicked on a widget
                self.tempWidget = activeItem

                if ev.button() == Qt.LeftButton:
                    self.bWidgetDragging = True
                    if ev.modifiers() & Qt.ControlModifier:
                        activeItem.setSelected(not activeItem.isSelected())
                    elif activeItem.isSelected() == 0:
                        self.unselectAllWidgets()
                        activeItem.setSelected(True)

                    for w in self.getSelectedWidgets():
                        w.savePosition()
                        w.setAllLinesFinished(False)

                # is we clicked the right mouse button we show the popup menu for widgets
                elif ev.button() == Qt.RightButton:
                    if activeItem in self.widgetsSelected and len(self.widgetsSelected)>1:
                        widgetPopup = QMenu("Concept", self)
                        menuItem = widgetPopup.addAction("Remove these")
                        receiver = lambda ws=self.widgetsSelected: self.removeNormalList(ws)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)                        
                        widgetPopup.popup(ev.globalPos())
                        return
                        
                    if not ev.modifiers() & Qt.ControlModifier:
                        self.unselectAllWidgets() 
                    activeItem.setSelected(True)
                    # WUL: self.doc.canvasDlg.widgetPopup.popup(ev.globalPos())
                    widget = activeItem

                    if widget.extra is not None and widget.extra['type'] == 1:
                        widgetPopup = QMenu("Concept", self)                        
                        relations = widget.extra['relations'] 
                        triggers = widget.extra.setdefault('triggers',  {})
                        for relaType in relations:
                            if not relations[relaType]:
                                raise exceptions.Exception("WikiNet Database relations of %s" % relaType)
                            triggered = triggers.setdefault(relaType, False)
                            menuItem = widgetPopup.addAction(relaType)
                            menuItem.setCheckable(True)
                            menuItem.setChecked(triggered)                                
                            receiver = lambda show, r=relaType, w=widget: self.selectRelaType(show, r, w)
                            self.connect(menuItem, SIGNAL('triggered(bool)'), receiver)
                        widgetPopup.addSeparator()
                        menuItem = widgetPopup.addAction("Remove it")
                        receiver = lambda w=widget: self.removeConcept(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)
                        menuItem = widgetPopup.addAction("Remove expanded")
                        receiver = lambda w=widget: self.unexpandActiveWidget(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver) 
                        menuItem = widgetPopup.addAction("Remove whole tree")
                        receiver = lambda w=widget: self.removeTree(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)  
                        widgetPopup.popup(ev.globalPos())
                    else:
                        # Don't use widget.extra here
                        # here contain widget.extra is None, or type is 2 (word)
                        widgetPopup = QMenu("Concept", self)
                        menuItem = widgetPopup.addAction("Remove it")
                        receiver = lambda w=widget: self.removeNormal(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)    
                        menuItem = widgetPopup.addAction("Remove expanded")
                        receiver = lambda w=widget: self.unexpandActiveWidget(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)
                        menuItem = widgetPopup.addAction("Remove whole tree")
                        receiver = lambda w=widget: self.removeTree(w)
                        self.connect(menuItem, SIGNAL('triggered()'), receiver)                          
                        widgetPopup.popup(ev.globalPos())                        
                else:
                    self.unselectAllWidgets()
                return # Don't call QGraphicsView.mousePressEvent. It unselects the active item

            # if we right clicked on a line we show a popup menu
            elif type(activeItem) == orngCanvasItems.CanvasLine and ev.button() == Qt.RightButton:
                self.unselectAllWidgets()
                self.selectedLine = activeItem
            else:
                pass
                #self.unselectAllWidgets()

        return QGraphicsView.mousePressEvent(self, ev)

    def removeTree(self,  w):
        self.doc.clearTree(w)
        
    def removeAll(self):
        self.doc.clear()
        
    def selectDB(self, show, dbConfig):
        # show ... no use here
        self.doc.selectDB(dbConfig)
        
    def selectRelaType(self, show, r, w):
        filter = [r]
        self.doc.expand2RelationsFromConcept(show, w, filter)        
        triggers = w.extra.setdefault('triggers',  {})    
        triggers[r] = show

    def removeConcept(self, w):
        self.doc.removeWidget(w)

    def removeNormal(self, w):
        self.doc.removeWidget(w)
        
    def removeNormalList(self,  ws):
        for w in ws:
            self.removeNormal(w)
            
    # mouse button was pressed and mouse is moving ######################
    def mouseMoveEvent(self, ev):
        point = self.mapToScene(ev.pos())
        if self.bWidgetDragging:
            for item in self.getSelectedWidgets():
                newPos = item.oldPos + (point-self.mouseDownPosition)
                item.setCoords(newPos.x(), newPos.y())
            self.ensureVisible(QRectF(point, point + QPointF(1, 1)))

        elif self.tempLine:
            self.tempLine.updateLinePos(point)
            self.ensureVisible(QRectF(point, point + QPointF(1, 1)))

        elif self.widgetSelectionRect:
            selectionRect = self.maxSelectionRect(QRectF(self.mouseDownPosition, point).normalized())
            self.widgetSelectionRect.setRect(selectionRect)
            self.ensureVisible(QRectF(point, point + QPointF(1, 1)))

            # select widgets in rectangle
            widgets = self.getItemsAtPos(self.widgetSelectionRect, orngCanvasItems.CanvasWidget)
            self.widgetsSelected = widgets
            for widget in self.doc.widgets:
                widget.setSelected(widget in widgets)

        return QGraphicsView.mouseMoveEvent(self, ev)


    # mouse button was released #########################################
    def mouseReleaseEvent(self, ev):
        point = self.mapToScene(ev.pos())
        if self.widgetSelectionRect:
            self.widgetSelectionRect.hide()
            self.scene().removeItem(self.widgetSelectionRect)
            self.widgetSelectionRect = None

        # if we are moving a widget
        if self.bWidgetDragging:
            validPos = True
            for item in self.getSelectedWidgets():
                items = self.scene().collidingItems(item)
                validPos = validPos and (self.findItemTypeCount(items, orngCanvasItems.CanvasWidget) == 0)

            for item in self.getSelectedWidgets():
                if not validPos:
                    item.restorePosition()
                item.updateTooltip()
                item.setAllLinesFinished(True)
                orngHistory.logChangeWidgetPosition(self.doc.schemaID, id(item), (item.widgetInfo.category, item.widgetInfo.name), item.x(), item.y())

        # if we are drawing line
        elif self.tempLine:
            # show again the empty input/output boxes
            for widget in self.doc.widgets:
                widget.resetLeftRightEdges()
            
            start = self.tempLine.startWidget or self.tempLine.widget
            end = self.tempLine.endWidget or self.tempLine.widget
            self.tempLine.remove()
            self.tempLine = None

            # we must check if we have really connected some output to input
            if start and end and start != end:
                    self.doc.addLine(start, end)
            else:
                state = [self.doc.widgets[i].widgetInfo.name for i in range(min(len(self.doc.widgets), 5))]
                predictedWidgets = orngHistory.predictWidgets(state, 20)
                if start:
                    orngTabs.categoriesPopup.updatePredictedWidgets(predictedWidgets, 'inputClasses', start.widgetInfo.outputClasses)
                    orngTabs.categoriesPopup.updateWidgetsByInputs(start.widgetInfo)
                else:
                    orngTabs.categoriesPopup.updatePredictedWidgets(predictedWidgets, 'outputClasses', end.widgetInfo.inputClasses)
                    orngTabs.categoriesPopup.updateWidgesByOutputs(end.widgetInfo)
                    
                newCoords = QPoint(ev.globalPos())
                orngTabs.categoriesPopup.updateMenu()
                action = orngTabs.categoriesPopup.exec_(newCoords- QPoint(0, orngTabs.categoriesPopup.categoriesYOffset))
                if action and hasattr(action, "widgetInfo"):
                    xOff = -48 * bool(end)
                    newWidget = self.doc.addWidget(action.widgetInfo, point.x()+xOff, point.y()-24)
                    if newWidget != None:
                        self.doc.addLine(start or newWidget, end or newWidget)

        elif ev.button() == Qt.RightButton:
            activeItem = self.scene().itemAt(point)
            diff = self.mouseDownPosition - point
            if not activeItem and (diff.x()**2 + diff.y()**2) < 25:     # if no active widgets and we pressed and released mouse at approx same position
                newCoords = QPoint(ev.globalPos())
                orngTabs.categoriesPopup.showAllWidgets()
                state = [self.doc.widgets[i].widgetInfo.name for i in range(min(len(self.doc.widgets), 5))]
                predictedWidgets = orngHistory.predictWidgets(state, 20)
                orngTabs.categoriesPopup.updatePredictedWidgets(predictedWidgets, 'inputClasses')
                orngTabs.categoriesPopup.updateMenu()
                height = sum([orngTabs.categoriesPopup.actionGeometry(action).height() for action in orngTabs.categoriesPopup.actions()])
                action = orngTabs.categoriesPopup.exec_(newCoords - QPoint(0, orngTabs.categoriesPopup.categoriesYOffset))
                if action and hasattr(action, "widgetInfo"):
                    newWidget = self.doc.addWidget(action.widgetInfo, point.x(), point.y())
                    

        self.scene().update()
        self.bWidgetDragging = False
        return QGraphicsView.mouseReleaseEvent(self, ev)

    def mouseDoubleClickEvent(self, ev):
        point = self.mapToScene(ev.pos())
        items = self.scene().items(QRectF(point, QSizeF(0.0, 0.0)).adjusted(-2, -2, 2, 2))
        items = [item for item in items if type(item) in [orngCanvasItems.CanvasWidget, orngCanvasItems.CanvasLine]]
        activeItem = items[0] if items else None
        if type(activeItem) == orngCanvasItems.CanvasWidget:      
            self.tempWidget = activeItem
            self.expandActiveWidget()
        elif type(activeItem) == orngCanvasItems.CanvasLine:
            
            inWidget, outWidget = activeItem.inWidget, activeItem.outWidget
            raise "update line!"
            inWidget.updateTooltip()
            outWidget.updateTooltip()
            activeItem.updateTooltip()
            
        return QGraphicsView.mouseDoubleClickEvent(self, ev)

    # ###########################################
    # Functions for processing events
    # ###########################################

    def progressBarHandler(self, widgetInstance, value):
        for widget in self.doc.widgets:
            if widget.instance == widgetInstance:
                widget.setProgressBarValue(value)
                qApp.processEvents()        # allow processing of other events
                return

    def processingHandler(self, widgetInstance, value):
        for widget in self.doc.widgets:
            if widget.instance == widgetInstance:
                widget.setProcessing(value)
#                self.repaint()
#                widget.update()
                return

    # ###########################################
    # misc functions regarding item selection
    # ###########################################

    # return a list of widgets that are currently selected
    def getSelectedWidgets(self):
        return [widget for widget in self.doc.widgets if widget.isSelected()]

    # return number of items in "items" of type "type"
    def findItemTypeCount(self, items, Type):
        return sum([type(item) == Type for item in items])
    
    def maxSelectionRect(self, rect, penWidth=1):
        b_rect = self.scene().sceneRect() #.adjusted(-5, -5, 5, 5)
        minSize = self.viewport().size()
        minGeom = self.mapToScene(QRect(QPoint(0, 0), minSize)).boundingRect()
        sceneRect = minGeom.united(b_rect)
        return rect.intersected(sceneRect).adjusted(penWidth, penWidth, -penWidth, -penWidth)

    def keyPressEvent(self, event):
        if event == QKeySequence.SelectAll:
            self.selectAllWidgets()
        else:
            return QGraphicsView.keyPressEvent(self, event)
