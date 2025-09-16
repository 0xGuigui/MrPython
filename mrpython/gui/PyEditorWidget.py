from tkinter import Frame, N, S, E, W
from .PyEditorList import PyEditorList

class PyEditorWidget(Frame):
    """
    Represents a tkinter Notebook widget with a bar widget displaying the line
    numbers on the left, and a status bar on the bottom
    """

    def __init__(self, parent, theme=None):
        self.theme = theme or {}
        surface = self.theme.get('surface', '#E8E8E8')
        border = self.theme.get('border', '#E8E8E8')
        Frame.__init__(self, parent, background=surface, highlightbackground=border,
                       highlightcolor=border, highlightthickness=1, bd=0)
        self.UPDATE_PERIOD = 100
        # Holds the text inside the line widget : the text simply
        # contains all the line numbers
        self.line_numbers = ''
        self.py_notebook = PyEditorList(self)
        self.py_notebook.grid(row=0, column=1, sticky=(N, S, E, W), padx=6, pady=6)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def update_theme(self, theme):
        self.theme = theme or self.theme
        surface = self.theme.get('surface', '#E8E8E8')
        border = self.theme.get('border', '#E8E8E8')
        self.configure(background=surface, highlightbackground=border,
                       highlightcolor=border)
        try:
            self.py_notebook.configure(style='CustomNotebook')
        except Exception:
            pass
