# -*- coding: utf8 -*-
"""
<name>ConceptNet</name>
<description>ConceptNet</description>
<icon>icons/Concept.png</icon>
<priority>10</priority>
"""
from OWWidget import *
import OWGUI
from orngWidgetData import WidgetChannelData
    
class OWConceptNet(OWWidget):
    
    def __init__(self, parent=None, signalManager=None):
        OWWidget.__init__(self, parent, signalManager, 'ConceptNet')
        
        self.inputs = [("TEST1", WidgetChannelData, self.data)]
        self.outputs = [("TEST2", WidgetChannelData)]
        
        # GUI
        box = OWGUI.widgetBox(self.controlArea, u"信息")
        self.infoa = OWGUI.widgetLabel(box, u'万事俱备，只欠东风。')
        self.infob = OWGUI.widgetLabel(box, u'再见')
        self.resize(100,50) 

    def data(self, dataset):
        if dataset:
            self.infoa.setText('%d instances in input data set' % len(dataset))
            indices = orange.MakeRandomIndices2(p0=0.1)
            ind = indices(dataset)
            sample = dataset.select(ind, 0)
            self.infob.setText('%d sampled instances' % len(sample))
            #self.send("SEND MESSAGE", sample)
        else:
            self.infoa.setText('No data on input yet, waiting to get something.')
            self.infob.setText('')
            #self.send("SEND MESSAGE", None)
            

##############################################################################
# Test the widget, run from prompt

if __name__=="__main__":
    appl = QApplication(sys.argv)
    ow = OWConceptNet()
    ow.show()
    dataset = orange.ExampleTable('../datasets/iris.tab')
    ow.data(dataset)
    appl.exec_()
