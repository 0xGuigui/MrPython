from MenuManager import MenuManager
from PyEditor import PyEditor
from PyEditorList import PyEditorList
from PyShell import  PyShell
from tkinter.ttk import *
from tkinter import *

import tkinter.font

class MainView(object):

    def __init__(self,root):
        self.root=root
        self.recent_files_menu=None

        default_font = tkinter.font.nametofont("TkFixedFont")
        default_font.configure(size=12)

        ### XXX : a small hack to use a nicer default theme
        s = Style()
        #print("Themes = {}".format(s.theme_names()))
        import sys
        if sys.platform == 'linux' and 'clam' in s.theme_names():
            s.theme_use('clam')

        self.createview()

        self.menuManager=MenuManager(self)
        self.menuManager.createmenubar()

        self.pyEditorList.set_recent_files_menu(self.recent_files_menu)

        self.view.pack(fill=BOTH,expand=1)



    def show(self):
        self.root.mainloop()

    def createview(self):
        self.view=PanedWindow(self.root,width=800,height=700,orient=VERTICAL)
        self.createPyEditorList(self.view)
        self.createPyShell(self.view)


        self.view.add(self.pyEditorList)
        self.view.add(self.pyShell.entre)
        self.view.add(self.pyShell.text)


    def createPyEditorList(self,parent):
        self.pyEditorList = PyEditorList(parent)


    def createPyShell(self,parent):
        self.pyShell=PyShell(parent)

