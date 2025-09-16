from tkinter import ttk, INSERT
from platform import python_version
from translate import tr

class StatusBar(ttk.Frame):
    """
    Manages the status bar that gives some information about the current
    environment and editor
    """

    def __init__(self, parent, notebook, theme=None):
        self.theme = theme or {}
        ttk.Frame.__init__(self, parent, style='StatusBar.TFrame')
        self.UPDATE_PERIOD_POSITION = 100
        self.UPDATE_PERIOD_SAVE_CLEAR = 4000
        self.config(padding=(8, 6))

        self.python_label = ttk.Label(self,
                                      text="Python " + python_version(),
                                      width=13,
                                      anchor='center',
                                      style='StatusBarAccent.TLabel')
        self.position_label = ttk.Label(self, text="", width=13,
                                        anchor='center',
                                        style='StatusBar.TLabel')
        self.mode_label = ttk.Label(self, text="", width=13,
                                    anchor='center',
                                    style='StatusBarAccent.TLabel')
        self.save_label = ttk.Label(self, text="", anchor='w',
                                    style='StatusBar.TLabel')

        self.save_label.grid(row=0, column=0, sticky="ew", padx=(4, 12))
        self.mode_label.grid(row=0, column=1, padx=(0, 12))
        self.position_label.grid(row=0, column=2, padx=(0, 12))
        self.python_label.grid(row=0, column=3)

        self.columnconfigure(0, weight=1)

        self.notebook = notebook
        self.update_position()
        self.displaying_save = False
        self.callback_id = 0


    def update_save_label(self, filename):
        """ Display the saved file in the save_label """
        if self.displaying_save:
            self.after_cancel(self.callback_id)
        import os
        display_text = "   " + tr("Saving file") + " '" + os.path.basename(filename) + "'"
        self.save_label.config(text=display_text, style='StatusBarHighlight.TLabel')
        self.displaying_save = True
        # Then clear the text after a few seconds
        self.callback_id = self.after(self.UPDATE_PERIOD_SAVE_CLEAR,
                                      self.clear_save_label)


    def clear_save_label(self):
        """ Clear the save label text, used once the user has saved the file """
        self.save_label.config(text="", style='StatusBar.TLabel')
        self.displaying_save = False


    def update_position(self):
        """ Update the position displayed in the status bar, corresponding
            to the cursor position inside the current editor """
        position = ''
        if self.notebook.index("end") > 0:
            index = self.notebook.get_current_editor().index(INSERT)
            line, col = index.split('.')
            ncol = int(col) + 1
            position = "Li " + line + ", Col " + str(ncol)
        self.position_label.config(text=position)
        self.after(self.UPDATE_PERIOD_POSITION, self.update_position)


    def change_mode(self, mode):
        """ Change the current mode displayed in the mode_label """
        display_text = "mode " + tr(mode)
        self.mode_label.config(text=display_text, style='StatusBarAccent.TLabel')

    def update_theme(self, theme):
        """Refresh the appearance after the palette changed."""
        self.theme = theme or self.theme
        self.configure(style='StatusBar.TFrame')
        self.python_label.configure(style='StatusBarAccent.TLabel')
        self.mode_label.configure(style='StatusBarAccent.TLabel')
        if self.displaying_save:
            self.save_label.configure(style='StatusBarHighlight.TLabel')
        else:
            self.save_label.configure(style='StatusBar.TLabel')
        self.position_label.configure(style='StatusBar.TLabel')
