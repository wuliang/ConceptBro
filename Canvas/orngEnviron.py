import os

install_dir = os.path.dirname(os.path.abspath(__file__))  # ROOT/Canvas
install_dir = os.path.dirname(install_dir) # ROOT/

##### Level 1 ######
orangeDir = install_dir
canvasDir = os.path.join(orangeDir, "Canvas")
widgetDir =  os.path.join(orangeDir, "Widgets")
outputDir = os.path.join(orangeDir, "Environ")
settingDir = outputDir
docDir = os.path.join(orangeDir, "Doc")
#### Level 2 #######
picsDir = os.path.join(widgetDir, "icons")
widgetSettingsDir = os.path.join(outputDir, "WidgetsEnv")
canvasSettingsDir = os.path.join(outputDir, "CanvasEnv")
bufferDir = os.path.join(outputDir, "buffer")


directoryNames = dict(
orangeDir = orangeDir, 
canvasDir = canvasDir, 
widgetDir = widgetDir, 
picsDir = picsDir, 
outputDir = outputDir, 
widgetSettingsDir = widgetSettingsDir, 
canvasSettingsDir = canvasSettingsDir, 
bufferDir = bufferDir
)

# LANG1 for primary dictionary. 
# use LANG2 only if LANG1 has no result

# ** current supported languages  : en (English), cn(Chinese, jp (Japanese)
#  you can also set no language at all. the application will try all.
#  or you set any language the database not support. the application will try and get empty result.
#
# ** current supported database types : WordNet, WikiNet, JA-WordNet (to add)

dbConfig_wn1 = {
    'DBNAME' : "WordNet (English)", 
    'DBTYPE' : "wordnet" ,      
    'DBFILE'  : "/home/wl/tempdown/fat1/AI/database/wordnet30.db", 
    'LANG1'  : ['en'], 
    'LANG2'  : []
}

dbConfig_wk1 = {
    'DBNAME' : "WikiNet (All languages)", 
    'DBTYPE' : "wikinet", 
    'DBFILE' :  "/home/wl/tempdown/fat1/AI/database/abcRelation.db", 
    'LANG1'  : ['cn', 'en', 'jp'], 
    'LANG2'  : [] 
 }
 
dbConfig_wk2 = {
    'DBNAME' : "WikiNet (Chinese Primary)", 
    'DBTYPE' : "wikinet", 
    'DBFILE' :  "/home/wl/tempdown/fat1/AI/database/abcRelation.db", 
    'LANG1'  : ['cn'], 
    'LANG2'  : ['en', 'jp'] 
 }
 
dbConfig_wk3 = {
    'DBNAME' : "WikiNet (English Primary)", 
    'DBTYPE' : "wikinet", 
    'DBFILE' :  "/home/wl/tempdown/fat1/AI/database/abcRelation.db", 
    'LANG1'  : ['en'], 
    'LANG2'  : ['cn', 'jp'] 
}

dbConfig_wk4 = {
    'DBNAME' : "WikiNet (Japanese Primary)", 
    'DBTYPE' : "wikinet", 
    'DBFILE' :  "/home/wl/tempdown/fat1/AI/database/abcRelation.db", 
    'LANG1'  : ['jp'], 
    'LANG2'  : ['en', 'cn'] 
}

dbConfigs = [dbConfig_wn1,  dbConfig_wk1,  dbConfig_wk2,  dbConfig_wk3,  dbConfig_wk4]
defaultdbConfig = dbConfig_wk2 #dbConfig_wn1

