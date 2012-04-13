# -*- coding: utf8 -*-
import orngEnviron
from PyQt4.QtCore import *
from PyQt4.QtGui import *
    
import sys, os, cPickle, orngRegistry,  OWGUI, OWReport 
import orngTabs, orngDoc, orngDlgs, orngOutput, orngHelp
import  user
import gc
import utils.addons

RedR = False

product =  "Blue Stone "

class OrangeCanvasDlg(QMainWindow):
    def __init__(self, app, parent=None, flags=0):
        QMainWindow.__init__(self, parent)
        self.debugMode = 1        # print extra output for debuging
        self.setWindowTitle(u"      语义网浏览器 － 〖 青石科技 〗 2012")
        self.windows = []    # list of id for windows in Window menu
        self.recentDocs = []
        self.iconNameToIcon = {}
        self.toolbarIconSizeList = [16, 32, 40, 48, 60]
        self.schemeIconSizeList = [32, 40, 48]
        self.widgetsToolBar = None
        self.originalPalette = QApplication.palette()

        self.__dict__.update(orngEnviron.directoryNames)

        self.defaultReportsDir = self.outputDir
        self.defaultPic = os.path.join(self.picsDir, "Unknown.png")
        self.defaultBackground = os.path.join(self.picsDir, "frame.png")
        canvasPicsDir = os.path.join(self.orangeDir, "icons")
        canvasIconName = os.path.join(canvasPicsDir, "Trinity.png")        

        if os.path.exists(canvasIconName):
            self.setWindowIcon(QIcon(canvasIconName))
            
        self.settings = {}
        self.loadSettings()


        # output window
        self.output = orngOutput.OutputWindow(self)
        self.output.catchOutput(1)
        
        # Fetch widget information???
        self.updateWidgetRegistry()

        # create error and warning icons
        informationIconName = os.path.join(canvasPicsDir, "information.png")
        warningIconName = os.path.join(canvasPicsDir, "warning.png")
        errorIconName = os.path.join(canvasPicsDir, "error.png")
        if os.path.exists(errorIconName) and os.path.exists(warningIconName) and os.path.exists(informationIconName):
          
            self.errorIcon = QPixmap(errorIconName)
            self.warningIcon = QPixmap(warningIconName)
            self.informationIcon = QPixmap(informationIconName)
            self.widgetIcons = {"Info": self.informationIcon, "Warning": self.warningIcon, "Error": self.errorIcon}
        else:
            self.errorIcon = None
            self.warningIcon = None
            self.informationIcon = None
            self.widgetIcons = None
            print "Unable to load all necessary icons. Please reinstall Orange."
        
        #########
        # Actions
        #########
        self.showMainToolbarAction = QAction("Main Toolbar", self)
        self.showMainToolbarAction.setCheckable(True)
        self.showMainToolbarAction.setChecked(self.settings.get("showToolbar", True))
        self.connect(self.showMainToolbarAction,
                     SIGNAL("triggered(bool)"),
                     self.menuItemShowToolbar)
        
        self.showWidgetToolbarAction = QAction("Widget Toolbar", self)
        self.showWidgetToolbarAction.setCheckable(True)
        self.showWidgetToolbarAction.setChecked(self.settings.get("showWidgetToolbar", True))
        self.connect(self.showWidgetToolbarAction,
                     SIGNAL("triggered(bool)"),
                     self.menuItemShowWidgetToolbar)
        
        # TODO: Move other actions currently defined elsewhere
        
        self.setStatusBar(MyStatusBar(self))
        self.statusBar().setVisible(self.settings.get("showStatusBar", True))
        self.sizeGrip = SizeGrip(self)
        self.sizeGrip.setVisible(not self.settings.get("showStatusBar", True))
        
        self.updateStyle()
        
        self.eventNotifier = EventNotifier(parent=self)
        # create toolbar
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.setOrientation(Qt.Horizontal)
#        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        if not self.settings.get("showToolbar", True):
            self.toolbar.hide()
        
        # create a schema
        self.schema = orngDoc.SchemaDoc(self)
        # A corner widget to reserve space for the size grip when
        # the status bar is hidden
        self.schema.canvasView.setCornerWidget(QWidget())
        
        self.setCentralWidget(self.schema)
        self.schema.setFocus()

        # Restore geometry before calling createWidgetsToolbar.
        # On Mac OSX with unified title bar the canvas can move up on restarts
        state = self.settings.get("CanvasMainWindowGeometry", None)
        if state is not None:
            state = self.restoreGeometry(QByteArray(state))
            width, height = self.width(), self.height()
        
        if not state:
            width, height = self.settings.get("canvasWidth", 700), self.settings.get("canvasHeight", 600)

        # center window in the desktop
        # on multiheaded desktops if it does not fit
        
        desktop = qApp.desktop()
        space = desktop.availableGeometry(self)
        geometry, frame = self.geometry(), self.frameGeometry()
        
        #Fit the frame size to fit in space
        width = min(space.width() - (frame.width() - geometry.width()), geometry.width())
        height = min(space.height() - (frame.height() - geometry.height()), geometry.height())
        
        self.resize(width, height)
        
        self.addToolBarBreak()
        orngTabs.constructCategoriesPopup(self)
        self.createWidgetsToolbar()
        self.readShortcuts()
        
        def addOnRefreshCallback():
            self.updateWidgetRegistry()
            orngTabs.constructCategoriesPopup(self)
            self.createWidgetsToolbar()
        utils.addons.addon_refresh_callback.append(addOnRefreshCallback)

        
        #move to center if frame not fully contained in space
        if not space.contains(self.frameGeometry()):
            x = max(0, space.width() / 2 - width / 2)
            y = max(0, space.height() / 2 - height / 2)
            
            self.move(x, y)

        self.helpWindow = orngHelp.HelpWindow(self)
        self.reportWindow = OWReport.ReportWindow()
        self.reportWindow.widgets = self.schema.widgets
        self.reportWindow.saveDir = self.settings["reportsDir"]
        

        # did Orange crash the last time we used it? If yes, you will find a tempSchema.tmp file
        if not RedR:
            if os.path.exists(os.path.join(self.canvasSettingsDir, "tempSchema.tmp")):
                mb = QMessageBox('%s Canvas' % product, "Your previous %s Canvas session was not closed successfully.\nYou can choose to reload your unsaved work or start a new session.\n\nIf you choose 'Reload', the links will be disabled to prevent reoccurence of the crash.\nYou can enable them by clicking Options/Enable all links." % product, QMessageBox.Information, QMessageBox.Ok | QMessageBox.Default, QMessageBox.Cancel | QMessageBox.Escape, QMessageBox.NoButton)
                mb.setButtonText(QMessageBox.Ok, "Reload")
                mb.setButtonText(QMessageBox.Cancel, "New schema")
                if mb.exec_() == QMessageBox.Ok:
                    self.schema.loadDocument(os.path.join(self.canvasSettingsDir, "tempSchema.tmp"), freeze=1)
        
        if self.schema.widgets == [] and len(sys.argv) > 1 and os.path.exists(sys.argv[-1]) and os.path.splitext(sys.argv[-1])[1].lower() == ".ows":
            self.schema.loadDocument(sys.argv[-1])
        
        # Raise the size grip so it is above all other widgets
        self.sizeGrip.raise_()
        
        # show message box if no numpy
        qApp.processEvents()
        self.output.catchException(1)

    def updateWidgetRegistry(self):
        """ Update the widget registry and add new category tabs to the
        settings dict.  
        """
        # The default Widget tabs order
        if not self.settings.has_key("WidgetTabs") or self.settings["WidgetTabs"] == []:
            f = open(os.path.join(self.canvasDir, "WidgetTabs.txt"), "r")
            defaultTabs = [c for c in [line.split("#")[0].strip() for line in f.readlines()] if c!=""]
            for i in xrange(len(defaultTabs)-1,0,-1):
                if defaultTabs[i] in defaultTabs[0:i]:
                    del defaultTabs[i]
            self.settings["WidgetTabs"] = [(name, Qt.Checked) for name in defaultTabs] 
            
        widgetTabList = self.settings["WidgetTabs"]
        self.widgetRegistry = orngRegistry.readCategories()
        
        extraTabs = [(name, 1) for name in self.widgetRegistry.keys() if name not in [tab for (tab, s) in widgetTabList]]
        extraTabs = sorted(extraTabs)
        
     
        widgetTabList = widgetTabList + extraTabs
        self.settings["WidgetTabs"] = widgetTabList
            
    def createWidgetsToolbar(self):
        barstate, treestate = None, None
        if self.widgetsToolBar:
            self.settings["showWidgetToolbar"] = self.widgetsToolBar.isVisible()
            if isinstance(self.widgetsToolBar, QToolBar):
                self.removeToolBar(self.widgetsToolBar)
                barstate = (self.tabs.currentIndex(), )
            elif isinstance(self.widgetsToolBar, orngTabs.WidgetToolBox):
                self.settings["toolboxWidth"] = self.widgetsToolBar.toolbox.width()
                self.removeDockWidget(self.widgetsToolBar)
                barstate = (self.tabs.toolbox.currentIndex(), )
            elif isinstance(self.widgetsToolBar, orngTabs.WidgetTree):
                self.settings["toolboxWidth"] = self.widgetsToolBar.treeWidget.width()
                self.removeDockWidget(self.widgetsToolBar)
                treestate = ( [self.tabs.treeWidget.topLevelItem(i).isExpanded()
                               for i in range(self.tabs.treeWidget.topLevelItemCount())], )
            
        if self.settings["widgetListType"] == 0:
            self.tabs = self.widgetsToolBar = orngTabs.WidgetToolBox(self, self.widgetRegistry)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.widgetsToolBar)
        elif self.settings["widgetListType"] in [1, 2]:
            self.tabs = self.widgetsToolBar = orngTabs.WidgetTree(self, self.widgetRegistry)
            self.addDockWidget(Qt.LeftDockWidgetArea, self.widgetsToolBar)
        else:
            self.widgetsToolBar = self.addToolBar("Widgets")
            self.insertToolBarBreak(self.widgetsToolBar)
            self.tabs = orngTabs.WidgetTabs(self, self.widgetRegistry, self.widgetsToolBar)
            self.widgetsToolBar.addWidget(self.tabs)
            
        # find widgets and create tab with buttons
        self.tabs.createWidgetTabs(self.settings["WidgetTabs"], self.widgetRegistry, self.widgetDir, self.picsDir, self.defaultPic)
        if not self.settings.get("showWidgetToolbar", True): 
            self.widgetsToolBar.hide()
        if barstate:
            if self.settings["widgetListType"] == 0:
                self.tabs.toolbox.setCurrentIndex(barstate[0])
            elif self.settings["widgetListType"] in [1, 2]:
                widget = self.tabs.treeWidget
                widget.scrollToItem(widget.topLevelItem(barstate[0]),
                                    QAbstractItemView.PositionAtTop)
            else:
                self.tabs.setCurrentIndex(barstate[0])
        if treestate and self.settings["widgetListType"] in [1, 2]:
            for i, e in enumerate(treestate[0]):
                self.tabs.treeWidget.topLevelItem(i).setExpanded(e)


    def readShortcuts(self):
        self.widgetShortcuts = {}
        shfn = os.path.join(self.canvasSettingsDir, "shortcuts.txt")
        if os.path.exists(shfn):
            for t in file(shfn).readlines():
                key, info = [x.strip() for x in t.split(":")]
                if len(info) == 0: continue
                if info[0] == "(" and info[-1] == ")":
                    cat, widgetName = eval(info)            # new style of shortcuts are of form F: ("Data", "File")
                else:
                    cat, widgetName = info.split(" - ")   # old style of shortcuts are of form F: Data - File
                if self.widgetRegistry.has_key(cat) and self.widgetRegistry[cat].has_key(widgetName):
                    self.widgetShortcuts[key] = self.widgetRegistry[cat][widgetName]

        
    def setDebugMode(self):   # RedR specific
        if self.output.debugMode:
            self.output.debugMode = 0
        else:
            self.output.debugMode = 1
    def importSchema(self):   # RedR specific
        name = QFileDialog.getOpenFileName(self, "Import File", self.settings["saveSchemaDir"], "Orange Widget Scripts (*.ows)")
        if name.isEmpty():
            return
        name = unicode(name)
        self.schema.clear()
        self.schema.loadDocument(name, freeze = 0, importBlank = 1)
        self.addToRecentMenu(name)
    
    def openSchema(self, filename):
        if self.schema.isSchemaChanged() and self.schema.widgets:
            ret = QMessageBox.warning(self, "Orange Canvas", "Changes to your present schema are not saved.\nSave them?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if ret == QMessageBox.Save:
                self.schema.saveDocument()
            elif ret == QMessageBox.Cancel:
                return
        self.schema.clear()
        dirname = os.path.dirname(filename)
        os.chdir(dirname)
        self.schema.loadDocument(filename)
        


    def updateSnapToGrid(self):
        if self.settings["snapToGrid"]:
            for widget in self.schema.widgets:
                widget.setCoords(widget.x(), widget.y())
            self.schema.canvas.update()

    def menuItemEnableAll(self):
        self.schema.enableAllLines()

    def menuItemDisableAll(self):
        self.schema.disableAllLines()


    def menuItemNewScheme(self):
        if self.schema.saveBeforeClose():
            self.schema.clear()
            self.schema.removeTempDoc()

    def dumpVariables(self):
        self.schema.dumpWidgetVariables()

    def menuItemShowOutputWindow(self):
        self.output.show()
        self.output.raise_()
#        self.output.activateWindow()

    def menuItemClearOutputWindow(self):
        self.output.textOutput.clear()
        self.statusBar().showMessage("")

    def menuItemSaveOutputWindow(self):
        qname = QFileDialog.getSaveFileName(self, "Save Output To File", self.canvasSettingsDir + "/Output.html", "HTML Document (*.html)")
        if qname.isEmpty(): return
        
        text = str(self.output.textOutput.toHtml())
        #text = text.replace("</nobr>", "</nobr><br>")

        file = open(unicode(name), "wt")
        file.write(text)
        file.close()

    def menuItemShowToolbar(self, show=True):
        self.toolbar.setVisible(show)
        self.settings["showToolbar"] = show
        self.showMainToolbarAction.setChecked(show)

    def menuItemShowWidgetToolbar(self, show=True):
        self.widgetsToolBar.setVisible(show)
        self.settings["showWidgetToolbar"] = show
        self.showWidgetToolbarAction.setChecked(show)
        
    def createPopupMenu(self):
        """ Create a menu with show toolbar entries.
        """
        toolbars = QMenu("Show Toolbars", self)
        toolbars.addAction(self.showMainToolbarAction)
        toolbars.addAction(self.showWidgetToolbarAction)
        return toolbars
        
    def toogleToolbarState(self):
        """ Toogle the toolbar state (Mac OSX specific). This gets called when
        the toolbar button in the unified title bar was clicked.
        """
        state = not self.settings["showToolbar"]
        self.settings["showToolbar"] = state
        self.showMainToolbarAction.setChecked(state)
        


    def menuItemDeleteWidgetSettings(self):
        if QMessageBox.warning(self, 'Orange Canvas', 'Delete all settings?\nNote that for a complete reset there should be no open schema with any widgets.', QMessageBox.Ok | QMessageBox.Default, QMessageBox.Cancel | QMessageBox.Escape) == QMessageBox.Ok:
            if os.path.exists(self.widgetSettingsDir):
                for f in os.listdir(self.widgetSettingsDir):
                    if os.path.splitext(f)[1].lower() == ".ini":
                        os.remove(os.path.join(self.widgetSettingsDir, f))

    def menuOpenLocalOrangeHelp(self):
        import webbrowser
        webbrowser.open("file:///" + os.path.join(self.orangeDir, "doc/reference/default.htm"))

    def menuOpenLocalWidgetCatalog(self):
        import webbrowser
        webbrowser.open("file:///" + os.path.join(self.orangeDir, "doc/catalog/index.html"))

    def menuOpenLocalCanvasHelp(self):
        import webbrowser
        webbrowser.open(os.path.join(self.orangeDir, "doc/canvas/default.htm"))

    def menuOpenOnlineOrangeReference(self):
        import webbrowser
        webbrowser.open("http://orange.biolab.si/doc/reference/")
        
    def menuOpenOnlineOrangeHelp(self):
        import webbrowser
        webbrowser.open("http://orange.biolab.si/doc/widgets/")

    def menuOpenOnlineCanvasHelp(self):
        import webbrowser
        #webbrowser.open("http://orange.biolab.si/orangeCanvas") # to be added on the web
        webbrowser.open("http://orange.biolab.si")

    def menuCheckForUpdates(self):
        import updateOrange
        self.updateDlg = updateOrange.updateOrangeDlg(None)#, Qt.WA_DeleteOnClose)

    def menuItemAboutOrange(self):
        dlg = orngDlgs.AboutDlg(self)
        dlg.exec_()


    def menuItemCanvasOptions(self):
        dlg = orngDlgs.CanvasOptionsDlg(self, self)

        if dlg.exec_() == QDialog.Accepted:
            if self.settings["snapToGrid"] != dlg.settings["snapToGrid"]:
                self.updateSnapToGrid()

            if self.settings["widgetListType"] != dlg.settings["widgetListType"]:
                self.settings["widgetListType"] = dlg.settings["widgetListType"]
                self.createWidgetsToolbar()
                self.widgetListTypeCB.setCurrentIndex(self.settings["widgetListType"])
            self.settings.update(dlg.settings)
            self.updateStyle()
                        
            # update settings in widgets in current documents
            for widget in self.schema.widgets:
                widget.instance._useContexts = self.settings["useContexts"]
                widget.instance._owInfo = self.settings["owInfo"]
                widget.instance._owWarning = self.settings["owWarning"]
                widget.instance._owError = self.settings["owError"]
                widget.instance._owShowStatus = self.settings["owShow"]
                widget.instance.updateStatusBarState()
                widget.resetWidgetSize()
                widget.updateWidgetState()
                
            # update tooltips for lines in all documents
            for line in self.schema.lines:
                line.showSignalNames = self.settings["showSignalNames"]
                line.updateTooltip()
            
            self.schema.canvasView.repaint()
        
            # save tab order settings
            newTabList = [(str(dlg.tabOrderList.item(i).text()), int(dlg.tabOrderList.item(i).checkState())) for i in range(dlg.tabOrderList.count())]
            if newTabList != self.settings["WidgetTabs"]:
                self.settings["WidgetTabs"] = newTabList
                self.createWidgetsToolbar()
                orngTabs.constructCategoriesPopup(self)

    def menuItemAddOns(self):
        import time
        t = time.time()
        lastRefresh = self.settings["lastAddonsRefresh"]
        if t - lastRefresh > 7*24*3600:
            if QMessageBox.question(self, "Refresh",
                                    "List of add-ons in repositories has %s. Do you want to %s the lists now?" %
                                    (("not yet been loaded" if lastRefresh==0 else "not been refreshed for more than a week"),
                                     ("download" if lastRefresh==0 else "reload")),
                                     QMessageBox.Yes | QMessageBox.Default,
                                     QMessageBox.No | QMessageBox.Escape) == QMessageBox.Yes:
                
                anyFailed = False
                anyDone = False
                for r in Orange.utils.addons.available_repositories:
                    #TODO: # Should show some progress (and enable cancellation)
                    try:
                        if r.refreshdata(force=True):
                            anyDone = True
                        else:
                            anyFailed = True
                    except Exception, e:
                        anyFailed = True
                        print "Unable to refresh repository %s! Error: %s" % (r.name, e)
                
                if anyDone:
                    self.settings["lastAddonsRefresh"] = t
                if anyFailed:
                    QMessageBox.warning(self,'Download Failed', "Download of add-on list has failed for at least one repostitory.")
        
        dlg = orngDlgs.AddOnManagerDialog(self, self)
        if dlg.exec_() == QDialog.Accepted:
            for (id, addOn) in dlg.addOnsToRemove.items():
                try:
                    addOn.uninstall(refresh=False)
                    if id in dlg.addOnsToAdd.items():
                        Orange.utils.addons.install_addon_from_repo(dlg.addOnsToAdd[id], global_install=False, refresh=False)
                        del dlg.addOnsToAdd[id]
                except Exception, e:
                    print "Problem %s add-on %s: %s" % ("upgrading" if id in dlg.addOnsToAdd else "removing", addOn.name, e)
            for (id, addOn) in dlg.addOnsToAdd.items():
                if id.startswith("registered:"):
                    try:
                        Orange.utils.addons.register_addon(addOn.name, addOn.directory, refresh=False, systemwide=False)
                    except Exception, e:
                        print "Problem registering add-on %s: %s" % (addOn.name, e)
                else:
                    try:
                        Orange.utils.addons.install_addon_from_repo(dlg.addOnsToAdd[id], global_install=False, refresh=False)
                    except Exception, e:
                        print "Problem installing add-on %s: %s" % (addOn.name, e)
            if len(dlg.addOnsToAdd)+len(dlg.addOnsToRemove)>0:
                Orange.utils.addons.refresh_addons(reload_path=True)
                
    def menuItemShowStatusBar(self):
        state = self.showStatusBarAction.isChecked()
        self.statusBar().setVisible(state)
        self.sizeGrip.setVisible(not state)
        self.sizeGrip.raise_()
        self.settings["showStatusBar"] = state

    def updateStyle(self):
        QApplication.setStyle(QStyleFactory.create(self.settings["style"]))
#        qApp.setStyleSheet(" QDialogButtonBox { button-layout: 0; }")       # we want buttons to go in the "windows" direction (Yes, No, Cancel)
        if self.settings["useDefaultPalette"]:
            QApplication.setPalette(qApp.style().standardPalette())
        else:
            QApplication.setPalette(self.originalPalette)


    def setStatusBarEvent(self, text):
        if text == "" or text == None:
            self.statusBar().showMessage("")
            return
        elif text == "\n": return
        #text = str(text)
        text = unicode(text)
        text = text.replace("<nobr>", ""); text = text.replace("</nobr>", "")
        text = text.replace("<b>", ""); text = text.replace("</b>", "")
        text = text.replace("<i>", ""); text = text.replace("</i>", "")
        text = text.replace("<br>", ""); text = text.replace("&nbsp", "")
        #self.statusBar().showMessage("Last event: " + str(text), 5000)
        self.statusBar().showMessage("Last event: " + unicode(text), 5000)

    # Loads settings from the widget's .ini file
    def loadSettings(self):
        self.settings = {"widgetListType": 4, "iconSize": "40 x 40", "toolbarIconSize": 2, "toolboxWidth": 200, 'schemeIconSize': 1,
                       "snapToGrid": 1, "writeLogFile": 1, "dontAskBeforeClose": 0, "saveWidgetsPosition": 1,
                       "reportsDir": self.defaultReportsDir, "saveSchemaDir": self.canvasSettingsDir, "saveApplicationDir": self.canvasSettingsDir,
                       "showSignalNames": 1, "useContexts": 1, "enableCanvasDropShadows": 0,
                       "canvasWidth": 700, "canvasHeight": 600, "useDefaultPalette": 0,
                       "focusOnCatchException": 1, "focusOnCatchOutput": 0, "printOutputInStatusBar": 1, "printExceptionInStatusBar": 1,
                       "outputVerbosity": 0, "synchronizeHelp": 1,
                       "ocShow": 1, "owShow": 0, "ocInfo": 1, "owInfo": 1, "ocWarning": 1, "owWarning": 1, "ocError": 1, "owError": 1,
                       "lastAddonsRefresh": 0}

        try:
            filename = os.path.join(self.canvasSettingsDir, "orngCanvas.ini")
            self.settings.update(cPickle.load(open(filename, "rb")))
        except:
            pass

        if not self.settings.has_key("style"):
            items = [str(n) for n in QStyleFactory.keys()]
            lowerItems = [str(n).lower() for n in QStyleFactory.keys()]
            currStyle = str(qApp.style().objectName()).lower()
            self.settings.setdefault("style", items[lowerItems.index(currStyle)])


    # Saves settings to this widget's .ini file
    def saveSettings(self):
        filename = os.path.join(self.canvasSettingsDir, "orngCanvas.ini")
        file = open(filename, "wb")
        if self.settings["widgetListType"] == 1:        # tree view
            self.settings["treeItemsOpenness"] = dict([(key, self.tabs.tabDict[key].isExpanded()) for key in self.tabs.tabDict.keys()])
        cPickle.dump(self.settings, file)
        file.close()

    def closeEvent(self, ce):
        # save the current width of the toolbox, if we are using it
        if isinstance(self.widgetsToolBar, orngTabs.WidgetToolBox):
            self.settings["toolboxWidth"] = self.widgetsToolBar.toolbox.width()
        self.settings["showWidgetToolbar"] = self.widgetsToolBar.isVisible()
        self.settings["showToolbar"] = self.toolbar.isVisible()
        self.settings["reportsDir"] = self.reportWindow.saveDir

        closed = self.schema.close()
        if closed:
            self.canvasIsClosing = 1        # output window (and possibly report window also) will check this variable before it will close the window
            
            self.helpWindow.close()
            self.reportWindow.close()
            
            self.output.catchOutput(False)
            self.output.catchException(False)
            self.output.hide()
            self.output.logFile.close()
            
            ce.accept()
            
        else:
            ce.ignore()
        
        self.reportWindow.removeTemp()
        
        size = self.geometry().size()
        self.settings["canvasWidth"] = size.width()
        self.settings["canvasHeight"] = size.height()
        self.settings["CanvasMainWindowGeometry"] = str(self.saveGeometry())
        
        self.saveSettings()
        
    def wheelEvent(self, event):
        """ Silently accept the wheel event. This is to ensure combo boxes
        and other controls that have focus don't receive this event unless
        the cursor is over them.
        
        """
        event.accept()
        

    def setCaption(self, caption=""):
        if caption:
            caption = caption.split(".")[0]
            self.setWindowTitle(caption + " - %s Canvas" % product)
        else:
            self.setWindowTitle("%s Canvas" % product)
    
    def getWidgetIcon(self, widgetInfo):
        if self.iconNameToIcon.has_key(widgetInfo.icon):
            return self.iconNameToIcon[widgetInfo.icon]
        
        iconNames = self.getFullWidgetIconName(widgetInfo)
        iconBackgrounds = self.getFullIconBackgroundName(widgetInfo)
        icon = QIcon()
        if len(iconNames) == 1:
            iconSize = QPixmap(iconNames[0]).width()
            iconBackgrounds = [name for name in iconBackgrounds if QPixmap(name).width() == iconSize]
        for name, back in zip(iconNames, iconBackgrounds):
            image = QPixmap(back).toImage()
            painter = QPainter(image)
            painter.drawPixmap(0, 0, QPixmap(name))
            painter.end()
            icon.addPixmap(QPixmap.fromImage(image))
        if iconNames != [self.defaultPic]:
            self.iconNameToIcon[widgetInfo.icon] = icon
        return icon
            
    
    def getFullWidgetIconName(self, widgetInfo):
        iconName = widgetInfo.icon
        names = []
        name, ext = os.path.splitext(iconName)
        for num in [16, 32, 40, 48, 60]:
            names.append("%s_%d%s" % (name, num, ext))
            
        widgetDir = str(widgetInfo.directory)  #os.path.split(self.getFileName())[0]
        fullPaths = []
        for paths in [(self.widgetDir, widgetInfo.category), (self.widgetDir,), (self.picsDir,), tuple(), (widgetDir,), (widgetDir, "icons")]:
            for name in names + [iconName]:
                fname = os.path.join(*paths + (name,))
                if os.path.exists(fname):
                    fullPaths.append(fname)
            if len(fullPaths) > 1 and fullPaths[-1].endswith(iconName):
                fullPaths.pop()     # if we have the new icons we can remove the default icon
            if fullPaths != []:
                return fullPaths
        return [self.defaultPic]
    
    def getFullIconBackgroundName(self, widgetInfo):
        widgetDir = str(widgetInfo.directory)
        fullPaths = []
        for paths in [(widgetDir, "icons"), (self.widgetDir, widgetInfo.category, "icons"), (self.widgetDir, "icons"), (self.picsDir,), tuple(), (widgetDir,), (widgetDir, "icons")]:
            for name in ["background_%d.png" % num for num in [16, 32, 40, 48, 60]]:
                fname = os.path.join(*paths + (name,))
#                print fname
                if os.path.exists(fname):
                    fullPaths.append(fname)
            if fullPaths != []:
                return fullPaths    
        return [self.defaultBackground]
    
class MyStatusBar(QStatusBar):
    def __init__(self, parent):
        QStatusBar.__init__(self, parent)
        self.parentWidget = parent

    def mouseDoubleClickEvent(self, ev):
        self.parentWidget.menuItemShowOutputWindow()
        
class SizeGrip(QSizeGrip):
    def __init__(self, mainwindow):
        QSizeGrip.__init__(self, mainwindow)
        mainwindow.installEventFilter(self)
        self.updateMyPos(mainwindow)
        
    def eventFilter(self, obj, event):
        if obj is self.parent() and isinstance(event, QResizeEvent):
            self.updateMyPos(obj)
            
        return QSizeGrip.eventFilter(self, obj, event)
    
    def updateMyPos(self, mainwindow):
        window_size = mainwindow.size()
        mysize = self.size()
        self.move(window_size.width() - mysize.width(),
                  window_size.height() - mysize.height())
            
from collections import defaultdict
class EventNotifier(QObject):
    """ An Qt event notifier.
    """
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self._filtering = set()
        self._attached = defaultdict(list)
        
    def attach(self, obj, event, slot):
        if hasattr(event, "__iter__"):
            events = list(event)
        else:
            events = [event]
        for e in events:
            self._attached[obj, e].append(slot)
        
        if obj not in self._filtering:
            self._filtering.add(obj)
            obj.installEventFilter(self)
            
    def detach(self, obj, event, slot=None):
        if hasattr(event, "__iter__"):
            events = list(event)
        else:
            events = [event]
        for e in events:
            slots = self._attached.get((obj, e), [])
            if slot is None:
                slots_to_remove = slots
            else:
                slots_to_remove = [slot]
            for s in slots_to_remove: 
                if s in slots:
                    slots.remove(s)
            if not slots:
                del self._attached[obj, e]
        
        if not any([s for (obj_, _), s in self._attached.items() \
                    if obj_ == obj]):
            # If obj has no more slots
            self._filtering.remove(obj)
            obj.removeEventFilter(self)
            
    def eventFilter(self, obj, event):
        if obj in self._filtering:
            if (obj, type(event)) in self._attached or (obj, event.type()) in self._attached:
                slots = self._attached.get((obj, type(event)), []) + \
                        self._attached.get((obj, event.type()), [])
                for slot in slots:
                    slot()
        return False
    
        
class OrangeQApplication(QApplication):
    def __init__(self, *args):
        # Use Font of (Chinese) Kai-Ti First. 
        font_list = ['AR PL UKai HK', 'AR PL KaitiM HK',  '']
        QApplication.__init__(self, *args)
        for font in font_list:
            cfont = QFont(font)
            if cfont: break
        if not cfont:
            assert (False)  
            
        self.setFont (cfont)
        

def main(argv=None):
    if argv == None:
        argv = sys.argv
    
    app = OrangeQApplication(sys.argv)
    dlg = OrangeCanvasDlg(app)
    qApp.canvasDlg = dlg
    dlg.show()
    for arg in sys.argv[1:]:
        if arg == "-reload":
            dlg.menuItemOpenLastSchema()

    translator = QTranslator()
    # If not Chinese, prepare the language package you needed.
    transfile = os.path.join(orngEnviron.canvasDir, 'qt_zh_CN.qm')

    translator.load(transfile)
    app.installTranslator(translator)
    r = app.exec_()
    app.closeAllWindows()
    
    del qApp.canvasDlg
    del dlg
    
    app.processEvents()
    
    
    gc.collect()
    del app
    
    return r

if __name__ == "__main__":
    sys.exit(main())
