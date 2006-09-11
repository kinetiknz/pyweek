# This is an example setup.py file
# run it from the windows command line like so:
# > C:\Python2.4\python.exe setup.py py2exe
 
from distutils.core import setup
 
import py2exe, glob
import sys
 
sys.path.append("thirdparty")
  
opts = { 
 "py2exe": { 
   # if you import .py files from subfolders of your project, then those are
   # submodules.  You'll want to declare those in the "includes"
   'includes':[
               'hci',
               'pgu'
              ],
 } 
} 
 
setup(
 
  #this is the file that is run when you start the game from the command line.  
  console=['tet.py'],
 
  #options as defined above
  options=opts,
 
  #data files - these are the non-python files, like images and sounds
  #the glob module comes in handy here.
  data_files = [
    ("data", glob.glob("data\\*.*")),
    ("data/fonts", glob.glob("data\\fonts\\*") ),
    ("data/maps", glob.glob("data\\maps\\*") ),
    ("data/music", glob.glob("data\\music\\*") ),
    ("data/paths", glob.glob("data\\paths\\*") ),
    ("data/screens", glob.glob("data\\screens\\*") ),
    ("data/sfx", glob.glob("data\\sfx\\*") ),
    ("data/tilesets", glob.glob("data\\tilesets\\*") ),
    ("data/sprites", glob.glob("data\\sprites\\*.*") ),
    ("data/sprites/alien", glob.glob("data\\sprites\\alien\\*") ),
    ("data/sprites/characters", glob.glob("data\\sprites\\characters\\*") ),
  ],
 
  #this will pack up a zipfile instead of having a glut of files sitting
  #in a folder.
  zipfile="lib/shared.zip"
)