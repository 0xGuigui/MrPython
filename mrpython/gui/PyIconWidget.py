from tkinter import ttk

from translate import tr
from .tooltip import ToolTip


class PyIconWidget(ttk.Frame):
    """
    Manages the PyIconFrame widget which contains the icons
    """
    def __init__(self, parent, root, theme=None):
        self.theme = theme or {}
        super().__init__(parent, style='Toolbar.TFrame', padding=(16, 12))
        self.root = root
        # Creating the buttons with tooltips
        self.icons = dict()  # dict[str:ToolTip]
        self.is_running = False
        self.current_mode = 'student'

        self._add_button('new_file', tr('New'), tr('New (Ctrl-N)'), column=0)
        self._add_button('open', tr('Open'), tr('Open (Ctrl-O)'), column=1)
        self._add_button('save', tr('Save'), tr('Save (Ctrl-S)'), column=2)

        self._add_separator(column=3)
        self._add_button('mode', tr('Student mode'), tr('Switch mode (Ctrl-M)'), column=4)

        self._add_separator(column=5)
        self._add_button('run', tr('Run'), tr('Run (Ctrl-R / F5)'), column=6, style='Accent.TButton')
        self._add_button('theme', tr('Light theme'), tr('Toggle theme (Ctrl-Shift-T)'), column=7)

        spacer = ttk.Frame(self, style='Toolbar.TFrame')
        spacer.grid(row=0, column=8, sticky='ew')
        self.grid_columnconfigure(8, weight=1)

    def enable_icon_running(self):
        self.is_running = True
        self.icons['run'].wdgt.config(text=tr('Stop'), style='Danger.TButton')

    def disable_icon_running(self):
        self.is_running = False
        self.icons['run'].wdgt.config(text=tr('Run'), style='Accent.TButton')

    def switch_icon_mode(self, mode):
        """Change label when switching mode."""
        self.current_mode = mode
        label = tr('Student mode') if mode == "student" else tr('Expert mode')
        self.icons['mode'].wdgt.config(text=label)

    def set_theme_target(self, theme_name):
        """Update the theme button label depending on the next theme."""
        label = tr('Dark theme') if theme_name == 'dark' else tr('Light theme')
        self.icons['theme'].wdgt.config(text=label)
        try:
            self.icons['theme'].msgVar.set(f"{tr('Toggle theme (Ctrl-Shift-T)')} -> {label}")
        except AttributeError:
            pass

    def update_theme(self, theme, next_theme):
        """Refresh styling after the palette changed."""
        self.theme = theme or self.theme
        self.configure(style='Toolbar.TFrame')
        for key, tooltip in self.icons.items():
            button = tooltip.wdgt
            default_style = 'Accent.TButton' if key == 'run' and not self.is_running else 'Toolbar.TButton'
            if key == 'run':
                button.config(style='Danger.TButton' if self.is_running else 'Accent.TButton')
                button.config(text=tr('Stop') if self.is_running else tr('Run'))
            else:
                button.config(style=default_style)
        self.switch_icon_mode(self.current_mode)
        self.set_theme_target(next_theme)

    def _add_button(self, key, text, tooltip_text, column, style='Toolbar.TButton'):
        button = ttk.Button(self, text=text, style=style)
        button.configure(cursor='hand2', padding=(14, 8))
        tooltip = ToolTip(button, msg=tooltip_text)
        self.icons[key] = tooltip
        tooltip.wdgt.grid(row=0, column=column, padx=6)

    def _add_separator(self, column):
        sep = ttk.Separator(self, orient='vertical', style='Toolbar.TSeparator')
        sep.grid(row=0, column=column, sticky='ns', padx=6, pady=4)
