# -*- coding: utf8 -*-
# Author: Gregor Leban (gregor.leban@fri.uni-lj.si)
# Description:
#    document class - main operations (save, load, ...)
#
from __future__ import with_statement

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, os, os.path, traceback
from xml.dom.minidom import Document, parse
import orngView, orngCanvasItems, orngTabs
from orngDlgs import *
import cPickle, math, orngHistory
import orngWikidb,  orngEnviron
import re,  exceptions
eng_term_pattern = """[a-zA-Z0-9\\-_&']+"""

class SchemaDoc(QWidget):
    def __init__(self, canvasDlg, *args):
        QWidget.__init__(self, *args)
        self.canvasDlg = canvasDlg
        self.ctrlPressed = 0

        self.wiki = orngWikidb.CreateConceptDB(orngEnviron.defaultdbConfig)
        self.activeDbConfig = orngEnviron.defaultdbConfig
        self.wikitreeInst = 0
        
        self.wikinode = {}
        self.lines = []                         # list of orngCanvasItems.CanvasLine items
        self.widgets = []                       # list of orngCanvasItems.CanvasWidget items

        self.schemaPath = self.canvasDlg.settings["saveSchemaDir"]
        self.schemaName = ""
        self.loadedSettingsDict = {}
        self.setLayout(QVBoxLayout())
        self.canvas = QGraphicsScene()

        self.guide_text = self.canvas.addSimpleText("Right-click to add widgets")
        self.guide_text.setBrush(QBrush(QColor(235,235,235)))
        font = QFont()
        font.setStyleHint(QFont.SansSerif)
        font.setPixelSize(36)
        self.guide_text.setFont(font)

        oneItem = self.canvas.addRect(QRectF(0.0, 0.0, 300.0, 300.0)) # initial item so sceneRect always contains QPoint(0, 0)
        self.canvas.sceneRect() # call sceneRect so it updates the rect 
        self.canvas.removeItem(oneItem)
        
        self.canvasView = orngView.SchemaView(self, self.canvas, self)
        self.layout().addWidget(self.canvasView)
        self.layout().setMargin(0)
        self.schemaID = orngHistory.logNewSchema()

        #self.update_guide()

    def allocTreeInst(self):
        self.wikitreeInst += 1
        return self.wikitreeInst
        
    def selectDB(self,  dbConfig):
        if dbConfig != self.activeDbConfig:
            self.wiki = orngWikidb.CreateConceptDB(dbConfig)          
            self.activeDbConfig = dbConfig
    
    def find_wiki_node(self, inst, id):
        ids = self.wikinode.setdefault(inst, {})
        if id in ids: 
            return ids[id]
        return None
        
    def add_wiki_node(self, inst,  id,  widget):
        ids = self.wikinode.setdefault(inst, {})
        if id in ids:
            raise exceptions.Exception("%s has already created!" % unicode(id))
        ids[id] = widget
        return True
        
    def remove_wiki_node(self, inst, id):
        ids = self.wikinode.setdefault(inst, {})
        if id in ids:
            del ids[id]
        if len(ids) == 0:
           del self.wikinode[inst]
           
    def update_guide(self):
        """ Sets the visibility of the guide text """
        visible = not len(self.widgets)
        self.guide_text.setVisible(visible)
        if visible:
            self.canvasView.ensureVisible(self.guide_text)

    def isSchemaChanged(self):
        """ Is this schema document modified.
        """
        return self.loadedSettingsDict != dict([(widget.caption, widget.instance.saveSettingsStr()) for widget in self.widgets])
    
    def setSchemaModified(self, state):
        """ Set the modified document state flag.
        """
        # Update the loaded settings dict so we know if the widget
        # settings have changed from the last save when we quit 
        # the application (see closeEvent handler)
        if not state:
            self.loadedSettingsDict = dict([(widget.caption, widget.instance.saveSettingsStr()) for widget in self.widgets])
        else:
            self.loadedSettingsDict = {}
        
    def closeEvent(self, ce):
        if self.saveBeforeClose():
            self.clear()
            ce.accept()
        else:
            ce.ignore()
            return
            
        QWidget.closeEvent(self, ce)
        orngHistory.logCloseSchema(self.schemaID)
        

    # called to properly close all widget contexts
    def synchronizeContexts(self):
        for widget in self.widgets[::-1]:
            widget.instance.synchronizeContexts()

    # add line connecting widgets outWidget and inWidget
    # if necessary ask which signals to connect
    def addLine(self, outWidget, inWidget, enabled=True, lineType=None):
        if outWidget == inWidget: 
            return None
        # check if line already exists
        line = self.getLine(outWidget, inWidget)
        if line:
            #self.resetActiveSignals(outWidget, inWidget, None, enabled)
            return None

        self.addLink(outWidget, inWidget, "OUT", "IN", enabled, lineType=lineType)

        # if signals were set correctly create the line, update widget tooltips and show the line
        line = self.getLine(outWidget, inWidget)
        if line:
            outWidget.updateTooltip()
            inWidget.updateTooltip()

        return line


    # reset signals of an already created line
    def resetActiveSignals(self, outWidget, inWidget, newSignals = None, enabled = 1):
        #print "<extra>orngDoc.py - resetActiveSignals() - ", outWidget, inWidget, newSignals
        signals = []
#        for line in self.lines:
#            if line.outWidget == outWidget and line.inWidget == inWidget:
#                signals = line.getSignals()

        if newSignals == None:
            dialog = SignalDialog(self.canvasDlg, self.canvasDlg)
            dialog.setOutInWidgets(outWidget, inWidget)
            for (outName, inName) in signals:
                #print "<extra>orngDoc.py - SignalDialog.addLink() - adding signal to dialog: ", outName, inName
                dialog.addLink(outName, inName)

            # if there are multiple choices, how to connect this two widget, then show the dialog
            if dialog.exec_() == QDialog.Rejected:
                return

            newSignals = dialog.getLinks()

        for (outName, inName) in signals:
            if (outName, inName) not in newSignals:
                self.removeLink(outWidget, inWidget, outName, inName)
                signals.remove((outName, inName))

  
        for (outName, inName) in newSignals:
            if (outName, inName) not in signals:
                self.addLink(outWidget, inWidget, outName, inName, enabled)

        outWidget.updateTooltip()
        inWidget.updateTooltip()
        
    def addLink(self, outWidget, inWidget, outSignalName, inSignalName, enabled=1, lineType=None):
 
        existingSignals = False
        if not existingSignals:
            
            line = orngCanvasItems.CanvasLine(self.canvasDlg, self.canvasView, outWidget, inWidget, self.canvas, lineType)
            self.lines.append(line)
            line.show()
            outWidget.addOutLine(line)
            outWidget.updateTooltip()
            inWidget.addInLine(line)
            inWidget.updateTooltip()
        else:
            line = self.getLine(outWidget, inWidget)

        orngHistory.logAddLink(self.schemaID, outWidget, inWidget, outSignalName)

        line.updateTooltip()
        line.update()
        return 1


    # remove only one signal from connected two widgets. If no signals are left, delete the line
    def removeLink(self, outWidget, inWidget, outSignalName, inSignalName):
        self.removeLine(outWidget, inWidget)


    # remove line line
    def removeLine1(self, line):

        self.lines.remove(line)
        line.inWidget.removeLine(line)
        line.outWidget.removeLine(line)
        line.inWidget.updateTooltip()
        line.outWidget.updateTooltip()
        line.remove()
     
        qApp.processEvents(QEventLoop.ExcludeUserInputEvents)

    # remove line, connecting two widgets
    def removeLine(self, outWidget, inWidget):
        """ Remove the line connecting two widgets
        """
        #print "<extra> orngDoc.py - removeLine() - ", outWidget, inWidget
        line = self.getLine(outWidget, inWidget)
        if line:
            self.removeLine1(line)

    # add new widget
    def addWidget(self, widgetInfo, x= -1, y=-1, caption = "", widgetSettings = {}, extra=None):
        
        qApp.setOverrideCursor(Qt.WaitCursor)

        newwidget = orngCanvasItems.CanvasWidget(self.canvas, self.canvasView, widgetInfo, self.canvasDlg.defaultPic, self.canvasDlg, widgetSettings, extra)

        if x==-1 or y==-1:
            if self.widgets != []:
                x = self.widgets[-1].x() + 110
                y = self.widgets[-1].y()
            else:
                x = 30
                y = 150
        newwidget.setCoords(x, y)
        # move the widget to a valid position if necessary
        invalidPosition = (self.canvasView.findItemTypeCount(self.canvas.collidingItems(newwidget), orngCanvasItems.CanvasWidget) > 0)
        if invalidPosition:
            for r in range(20, 200, 20):
                for fi in [90, -90, 180, 0, 45, -45, 135, -135]:
                    xOff = r * math.cos(math.radians(fi))
                    yOff = r * math.sin(math.radians(fi))
                    rect = QRectF(x+xOff, y+yOff, 48, 48)
                    invalidPosition = self.canvasView.findItemTypeCount(self.canvas.items(rect), orngCanvasItems.CanvasWidget) > 0
                    if not invalidPosition:
                        newwidget.setCoords(x+xOff, y+yOff)
                        break
                if not invalidPosition:
                    break


        if caption == "":
            caption = newwidget.caption
        
        if self.getWidgetByCaption(caption):
            i = 2
            while self.getWidgetByCaption(caption + " (" + str(i) + ")"):
                i+=1
            caption = caption + " (" + str(i) + ")"
        newwidget.updateText(caption)
        newwidget.instance.setWindowTitle(caption)

        self.widgets.append(newwidget)
        self.canvas.update()

        try:
            newwidget.show()
            newwidget.updateTooltip()
            newwidget.setProcessing(1)
            if self.canvasDlg.settings["saveWidgetsPosition"]:
                newwidget.instance.restoreWidgetPosition()
            newwidget.setProcessing(0)
            orngHistory.logAddWidget(self.schemaID, id(newwidget), (newwidget.widgetInfo.category, newwidget.widgetInfo.name), newwidget.x(), newwidget.y())
        except:
            type, val, traceback = sys.exc_info()
            sys.excepthook(type, val, traceback)  # we pretend that we handled the exception, so that it doesn't crash canvas

        qApp.restoreOverrideCursor()
        #self.update_guide()
        return newwidget

    def addWidgetByFileName(self, widgetFileName, x, y, caption, widgetSettings = {}):
        for category in self.canvasDlg.widgetRegistry.keys():
            for name, widget in self.canvasDlg.widgetRegistry[category].items():
                if widget.fileName == widgetFileName:  
                    return self.addWidget(widget, x, y, caption, widgetSettings)
        return None

    def clearTree(self,  widget):
        if 'extra' not in dir(widget):
            return
        inst = widget.extra['inst']
        if inst not in self.wikinode:
            raise exceptions.Exception("The %d instance list of widget has Error")
        widgets = self.wikinode[inst]
        #must use items, since removeWidget will modify the dict
        for id, w in widgets.items():
            self.removeWidget(w) 
        self.update_guide()
        
    def unexpandWidget(self, widget):
        if 'expanded' not in dir(widget):
            return
            
        if 'extra' not in dir(widget):
            for oldwidget in widget.expanded:
                if oldwidget in self.widgets:
                    self.removeWidget(oldwidget) 
        else:
            inst = widget.extra['inst']
            for oldwidget in widget.expanded:
                if self.find_wiki_node(inst, oldwidget.extra['id']):            
                    self.removeWidget(oldwidget) 
        widget.expanded = []
        self.update_guide()
        
    # filter must be list
    def expand2RelationsFromConcept(self, show, widget, filter):
        
        relations = widget.extra['relations']
        inst = widget.extra['inst']
        relations_widget = widget.extra.setdefault('rela_widgets',  {})
        relas = [rela for rela in filter if rela in relations]
        total = 0

        if not relas:
            raise exceptions.Exception("expand relations using no type specified (All %s，Input %s)." % (str(relations), str(filter) ))            
            return
            
        for rela in relas:
            total += len(relations[rela])

        step = 110
        x0 = widget.x()
        y0 = widget.y()
        x0  += step
        y0  -= (total - 1) * step / 2 
        for rela in relas:
            relato = relations[rela]
            relawidgets = relations_widget.setdefault(rela,  [])
            if not show:
                for w in relawidgets:
                    if self.find_wiki_node(inst, w.extra['id']) is not None:
                        self.removeWidget(w)
                relawidgets = []
                del relations_widget[rela]
                        
            else:
                for id in relato:
                    oldwidget = self.find_wiki_node(inst, id)
                    if oldwidget is not None:
                        self.addLine(widget,  oldwidget, lineType='c2c:'+rela) 
                        continue
                    definition = self.wiki.get_definition_of_id(id)
                    relations = self.wiki.get_parsed_relations_of_id(id)
                    words = self.wiki.get_all_words_of_id(id)
                    info = {'type': 1, 'id':id , 'inst':inst,  'relations':relations, 'words':words, 'definition':definition}
                    if words:
                        caption = u'[[' + words[0] + u']]'
                        for word in words:
                            if re.match(eng_term_pattern, word) is None:
                                caption = u'[[' + word + u']]'
                                break
                    else:
                        caption = str(id)
                    newwidget = self.addWidget(widget.widgetInfo, x=x0,  y=y0, caption = caption , widgetSettings = widget.widgetSettings,  extra=info)
                    self.addLine(widget,  newwidget, lineType='c2c:'+rela)
                    self.add_wiki_node(inst,  id,  newwidget) 
                    relawidgets.append(newwidget)
                    y0 += step
        self.update_guide()
                     
    def expand2WordFromRoot(self, inst, widget, word):

        widget.expanded = []            
        step = 110        
        x0 = widget.x()
        y0 = widget.y()
        x0  += step
        if word is not None:
            # No need to check. Its inst is new
                
            ids = self.wiki.get_all_ids_of_word(word)
            info = {'type': 2, 'id':word, 'inst': inst, 'ids':ids}   
            caption = word        
            newwidget = self.addWidget(widget.widgetInfo, x=x0,  y=y0, caption = caption , widgetSettings = widget.widgetSettings,  extra=info)
            self.addLine(widget,  newwidget, lineType='c2w')  
            self.add_wiki_node(inst,  word,  newwidget)            
            widget.expanded.append(newwidget)            
            y0 += step 
        self.update_guide()
        
    def expand2ConceptsFromWord(self, widget):
        widget.expanded = [] 
        word = widget.extra['id']
        ids = widget.extra['ids']
        inst = widget.extra['inst']
        
        step = 110
        x0 = widget.x()
        y0 = widget.y()
        x0  += step
        y0  -= (len(ids) - 1) * step / 2 
        
        for id in ids:
            oldwidget = self.find_wiki_node(inst,  id)
            if oldwidget is not None:
                continue
            definition = self.wiki.get_definition_of_id(id)
            relations = self.wiki.get_parsed_relations_of_id(id)
            words = self.wiki.get_all_words_of_id(id)
            info = {'type': 1, 'id':id , 'inst': inst, 'relations':relations, 'words':words, 'definition':definition}
            if words:
                caption = u'[[' + words[0] + u']]'
                for word in words:
                    if re.match(eng_term_pattern, word) is None:
                        caption = u'[[' + word + u']]'
                        break    
            else:
                caption = str(id) 
            newwidget = self.addWidget(widget.widgetInfo, x=x0,  y=y0, caption = caption , widgetSettings = widget.widgetSettings,  extra=info)
            self.addLine(widget,  newwidget, lineType='w2c')
            self.add_wiki_node(inst,  id,  newwidget)            
            widget.expanded.append(newwidget)                
            y0 += step
        self.update_guide()
        
    def expand2WordsFromConcept(self, widget):
        widget.expanded = []         
        id = widget.extra['id']
        words = widget.extra['words']
        inst = widget.extra['inst']
        step = 110
        x0 = widget.x()
        y0 = widget.y()
        x0  += step
        y0  -= (len(words) - 1) * step / 2 
        
        for word in words:
            oldwidget = self.find_wiki_node(inst,  word)
            if oldwidget is not None:
                continue
            
            ids = self.wiki.get_all_ids_of_word(word)
            info = {'type': 2, 'id':word, 'inst': inst, 'ids':ids}   
            caption = word
 
            newwidget = self.addWidget(widget.widgetInfo, x=x0,  y=y0, caption = caption , widgetSettings = widget.widgetSettings,  extra=info)
            self.addLine(widget,  newwidget, lineType='c2w')
            self.add_wiki_node(inst,  word,  newwidget)            
            widget.expanded.append(newwidget)            
            y0 += step
        self.update_guide()
        
    # remove widget
    def removeWidget(self, widget):
        if not widget:
            return
        

        while widget.inLines != []: self.removeLine1(widget.inLines[0])
        while widget.outLines != []:  self.removeLine1(widget.outLines[0])
    
        if widget.extra is not None:
            self.remove_wiki_node(widget.extra['inst'],  widget.extra['id'])
            
        self.widgets.remove(widget)
        widget.remove()
   
        qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
        
        #self.update_guide()


       
    def clear(self):
        self.canvasDlg.setCaption()
        for widget in self.widgets[::-1]:   
            self.removeWidget(widget)   # remove widgets from last to first
        self.canvas.update()
        self.schemaPath = self.canvasDlg.settings["saveSchemaDir"]
        self.schemaName = ""
        self.loadedSettingsDict = {}

    def enableAllLines(self):

        for line in self.lines:
            line.update()
        self.canvas.update()

    def disableAllLines(self):
        for line in self.lines:
            line.update()
        self.canvas.update()
        
    def setFreeze(self, bool):
        pass

    # return a new widget instance of a widget with filename "widgetName"
    def addWidgetByFileName(self, widgetFileName, x, y, caption, widgetSettings = {}):
        for category in self.canvasDlg.widgetRegistry.keys():
            for name, widget in self.canvasDlg.widgetRegistry[category].items():
                if widget.fileName == widgetFileName:  
                    return self.addWidget(widget, x, y, caption, widgetSettings)
        return None

    # return the widget instance that has caption "widgetName"
    def getWidgetByCaption(self, widgetName):
        for widget in self.widgets:
            if type(widget.caption) == type(widgetName) and widget.caption == widgetName:
                return widget
        return None

    def getWidgetCaption(self, widgetInstance):
        for widget in self.widgets:
            if widget.instance == widgetInstance:
                return widget.caption
        print "Error. Invalid widget instance : ", widgetInstance
        return ""


    # get line from outWidget to inWidget
    def getLine(self, outWidget, inWidget):
        for line in self.lines:
            if line.outWidget == outWidget and line.inWidget == inWidget:
                return line
        return None


    # find orngCanvasItems.CanvasWidget from widget instance
    def findWidgetFromInstance(self, widgetInstance):
        for widget in self.widgets:
            if widget.instance == widgetInstance:
                return widget
        return None


    # ###########################################
    # SAVING, LOADING, ....
    # ###########################################
    def reportAll(self):
        for widget in self.widgets:
            widget = widget.instance
            if hasattr(widget, "sendReport"):
                widget.reportAndFinish()
            
    def saveDocument(self):
        if self.schemaName == "":
            self.saveDocumentAs()
        else:
            self.save()
            self.setSchemaModified(False)

    def saveDocumentAs(self):
        name = QFileDialog.getSaveFileName(self, "Save Orange Schema", os.path.join(self.schemaPath, self.schemaName or "Untitled.ows"), "Orange Widget Schema (*.ows)")
        name = unicode(name)
        if os.path.splitext(name)[0] == "":
            return
        if os.path.splitext(name)[1].lower() != ".ows":
            name = os.path.splitext(name)[0] + ".ows"
        self.save(name)
        self.setSchemaModified(False)
        
    # save the file
    def save(self, filename=None):
        return True

    def saveBeforeClose(self):
        return True

    # load a scheme with name "filename"
    def loadDocument(self, filename, caption = None, freeze = 0):
        self.clear()
        
        if not os.path.exists(filename):
            if os.path.splitext(filename)[1].lower() != ".tmp":
                QMessageBox.critical(self, 'Orange Canvas', 'Unable to locate file "'+ filename + '"',  QMessageBox.Ok)
            return

        # set cursor
        qApp.setOverrideCursor(Qt.WaitCursor)
        failureText = ""
        
        if os.path.splitext(filename)[1].lower() == ".ows":
            self.schemaPath, self.schemaName = os.path.split(filename)
            self.canvasDlg.setCaption(caption or self.schemaName)

        try:
            #load the data ...
            doc = parse(filename)
            schema = doc.firstChild
            widgets = schema.getElementsByTagName("widgets")[0]
            lines = schema.getElementsByTagName("channels")[0]
            settings = schema.getElementsByTagName("settings")
            settingsDict = eval(str(settings[0].getAttribute("settingsDictionary")))
            self.loadedSettingsDict = settingsDict
              
            # read widgets
            loadedOk = 1
            for widget in widgets.getElementsByTagName("widget"):
                name = widget.getAttribute("widgetName")
                settings = cPickle.loads(settingsDict[widget.getAttribute("caption")])
                tempWidget = self.addWidgetByFileName(name, int(widget.getAttribute("xPos")), int(widget.getAttribute("yPos")), widget.getAttribute("caption"), settings)
                if not tempWidget:
                    #QMessageBox.information(self, 'Orange Canvas','Unable to create instance of widget \"'+ name + '\"',  QMessageBox.Ok + QMessageBox.Default)
                    failureText += '<nobr>Unable to create instance of a widget <b>%s</b></nobr><br>' %(name)
                    loadedOk = 0
                qApp.processEvents()

            #read lines
            lineList = lines.getElementsByTagName("channel")
            for line in lineList:
                inCaption = line.getAttribute("inWidgetCaption")
                outCaption = line.getAttribute("outWidgetCaption")
                if freeze: enabled = 0
                else:      enabled = int(line.getAttribute("enabled"))
                signals = line.getAttribute("signals")
                inWidget = self.getWidgetByCaption(inCaption)
                outWidget = self.getWidgetByCaption(outCaption)
                if inWidget == None or outWidget == None:
                    failureText += "<nobr>Failed to create a signal line between widgets <b>%s</b> and <b>%s</b></nobr><br>" % (outCaption, inCaption)
                    loadedOk = 0
                    continue

                signalList = eval(signals)
                for (outName, inName) in signalList:
                    self.addLink(outWidget, inWidget, outName, inName, enabled)
                #qApp.processEvents()
        finally:
            qApp.restoreOverrideCursor()


        for widget in self.widgets:
            widget.updateTooltip()
        self.canvas.update()


        if not loadedOk:
            QMessageBox.information(self, 'Schema Loading Failed', 'The following errors occured while loading the schema: <br><br>' + failureText,  QMessageBox.Ok + QMessageBox.Default)

            
        # Store the loaded settings dict again 
        self.loadedSettingsDict = dict((widget.caption, widget.instance.saveSettingsStr()) for widget in self.widgets)
        self.canvasDlg.setWindowModified(False)

        # do we want to restore last position and size of the widget
        if self.canvasDlg.settings["saveWidgetsPosition"]:
            for widget in self.widgets:
                widget.instance.restoreWidgetStatus()
            
        

    # save document as application
    def saveDocumentAsApp(self, asTabs = 1):
        NotImplemented
        
        
    def dumpWidgetVariables(self):
        for widget in self.widgets:
            self.canvasDlg.output.write("<hr><b>%s</b><br>" % (widget.caption))
            v = vars(widget.instance).keys()
            v.sort()
            for val in v:
                self.canvasDlg.output.write("%s = %s" % (val, getattr(widget.instance, val)))

    def keyReleaseEvent(self, e):
        self.ctrlPressed = int(e.modifiers()) & Qt.ControlModifier != 0
        e.ignore()

    def keyPressEvent(self, e):
        self.ctrlPressed = int(e.modifiers()) & Qt.ControlModifier != 0
        if e.key() > 127 or e.key() < 0:
            #e.ignore()
            QWidget.keyPressEvent(self, e)
            return

        # the list could include (e.ShiftButton, "Shift") if the shift key didn't have the special meaning
        pressed = "-".join(filter(None, [int(e.modifiers()) & x and y for x, y in [(Qt.ControlModifier, "Ctrl"), (Qt.AltModifier, "Alt")]]) + [chr(e.key())])
        widgetToAdd = self.canvasDlg.widgetShortcuts.get(pressed)
        if widgetToAdd:
            self.addWidget(widgetToAdd)
            if e.modifiers() & Qt.ShiftModifier and len(self.widgets) > 1:
                self.addLine(self.widgets[-2], self.widgets[-1])
        else:
            #e.ignore()
            QWidget.keyPressEvent(self, e)

