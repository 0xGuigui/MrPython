from .PyIconWidget import PyIconWidget
from .Console import Console
from .PyEditorWidget import PyEditorWidget
from .StatusBar import StatusBar
from tkinter.ttk import Frame, Style, PanedWindow
from tkinter import BOTH, N, S, E, W, VERTICAL
import sys
import tkinter.font

class MainView:
    """
    The application window
    Creates the editor and shell interfaces
    """

    def __init__(self, app):
        self.root = app.root
        self.app = app
        self.themes = {
            'dark': {
                'background': '#0f172a',
                'surface': '#14213b',
                'surface_alt': '#162544',
                'border': '#1e293b',
                'toolbar': '#172b4d',
                'accent': '#6366f1',
                'accent_hover': '#818cf8',
                'accent_fg': '#f8fafc',
                'text': '#e2e8f0',
                'muted': '#94a3b8',
                'success': '#22c55e',
                'warning': '#facc15',
                'danger': '#f87171',
                'shadow': '#0b1222'
            },
            'light': {
                'background': '#f1f5f9',
                'surface': '#ffffff',
                'surface_alt': '#f8fafc',
                'border': '#d8e3f0',
                'toolbar': '#f0f4ff',
                'accent': '#2563eb',
                'accent_hover': '#1d4ed8',
                'accent_fg': '#ffffff',
                'text': '#1e293b',
                'muted': '#64748b',
                'success': '#16a34a',
                'warning': '#d97706',
                'danger': '#dc2626',
                'shadow': '#cbd5f5'
            }
        }
        self.current_theme_name = 'dark'
        self.theme = self.themes[self.current_theme_name]
        # Set the font size
        tkinter.font.nametofont("TkFixedFont").configure(size=12)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        self.root.option_add("*Font", default_font)

        # A small hack to use a nicer default theme
        self.style = Style()
        if sys.platform == 'linux' and 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
        self._configure_styles()
        self.root.configure(bg=self.theme['background'])
        self.create_view()
        self.apply_theme(self.current_theme_name)


    def show(self):
        """ Main loop of program """
        self.root.mainloop()


    def create_view(self):
        """ Create the window : editor and shell interfaces, menus """
        self.view = Frame(self.root, style='Main.TFrame', padding=12)
        # Create the widgets

        # 1) the toolbar
        self.create_icon_widget(self.view)
        self.icon_widget.grid(row=0, column=0, sticky=(E, W), pady=(0, 8), padx=8)

        # 2) editor and output within a soft card container
        content_card = Frame(self.view, style='SurfaceCard.TFrame', padding=12)
        content_card.grid(row=1, column=0, sticky=(N, S, E, W), padx=8, pady=(0, 8))
        self.content_card = content_card

        pw = PanedWindow(content_card, orient=VERTICAL, style='Modern.TPanedwindow')
        self.create_editor_widget(pw)
        pw.add(self.editor_widget, weight=3)

        # 3) console (with output and input)
        self.create_console(pw, content_card)
        self.editor_widget.console = self.console # XXX: a little bit hacky...

        pw.add(self.console.frame_output, weight=1)
        pw.grid(row=0, column=0, sticky=(N, S, E, W))

        self.console.frame_input.grid(row=1, column=0, sticky=(E, W), pady=(12, 0))

        content_card.rowconfigure(0, weight=1)
        content_card.columnconfigure(0, weight=1)

        # 4) status bar

        self.create_status_bar(self.view, self.editor_widget.py_notebook)
        self.status_bar.grid(row=2, column=0, sticky=(E, W), padx=8, pady=(4, 0))

        self.view.rowconfigure(1, weight=1)
        self.view.columnconfigure(0, weight=1)
        self.view.pack(fill=BOTH, expand=1)

    def create_status_bar(self, parent, notebook):
        """ Create the status bar on the bottom """
        self.status_bar = StatusBar(parent, notebook, theme=self.theme)

    def create_icon_widget(self, parent):
        """ Create the icon menu on the top """
        self.icon_widget = PyIconWidget(parent, self.root, theme=self.theme)

    def create_editor_widget(self, parent):
        """ Create the editor area : notebook, line number widget """
        self.editor_widget = PyEditorWidget(parent, theme=self.theme)

    def create_console(self, output_parent, input_parent):
        """ Create the interactive interface in the bottom """
        self.console = Console(output_parent, input_parent, self.app, theme=self.theme)

    def _configure_styles(self):
        """Configure ttk styles to create a modern dark theme."""
        accent = self.theme['accent']
        accent_hover = self.theme['accent_hover']
        accent_fg = self.theme['accent_fg']
        surface = self.theme['surface']
        surface_alt = self.theme['surface_alt']
        toolbar = self.theme.get('toolbar', surface)
        text = self.theme['text']
        muted = self.theme['muted']
        border = self.theme['border']
        self.style.configure('Main.TFrame', background=self.theme['background'])
        self.style.configure('Toolbar.TFrame', background=toolbar, borderwidth=0)
        self.style.configure(
            'Toolbar.TButton',
            background=toolbar,
            foreground=text,
            padding=(12, 8),
            borderwidth=0,
            font=tkinter.font.nametofont("TkDefaultFont")
        )
        self.style.map(
            'Toolbar.TButton',
            background=[('pressed', accent), ('active', accent_hover), ('disabled', border)],
            foreground=[('pressed', accent_fg), ('active', accent_fg), ('disabled', muted)],
            relief=[('pressed', 'flat'), ('!pressed', 'flat')]
        )
        self.style.configure('Toolbar.TSeparator', background=border)

        self.style.configure('Modern.TPanedwindow', background=self.theme['background'], borderwidth=0)
        self.style.configure('Modern.TPanedwindow.Pane', background=surface)

        self.style.configure('Console.Vertical.TScrollbar', background=surface, arrowcolor=text, troughcolor=self.theme['background'])
        self.style.map('Console.Vertical.TScrollbar', background=[('active', accent_hover)])

        self.style.configure('StatusBar.TFrame', background=surface_alt, borderwidth=0)
        self.style.configure('StatusBar.TLabel', background=surface_alt, foreground=muted, padding=(12, 6))
        self.style.configure('StatusBarAccent.TLabel', background=surface_alt, foreground=accent, padding=(12, 6))
        self.style.configure('StatusBarHighlight.TLabel', background=surface_alt, foreground=text, padding=(12, 6))

        self.style.configure('Console.TFrame', background=surface, borderwidth=0)
        self.style.configure('ConsoleInput.TFrame', background=surface, borderwidth=0)
        self.style.configure('ConsolePrompt.TLabel', background=surface, foreground=muted, padding=(12, 8))
        self.style.configure('SurfaceCard.TFrame', background=surface, borderwidth=0)

        self.style.configure('Accent.TButton', background=accent, foreground=accent_fg, padding=(16, 8), borderwidth=0)
        self.style.map('Accent.TButton',
                       background=[('active', accent_hover), ('disabled', border)],
                       foreground=[('disabled', muted)])

        self.style.configure('Danger.TButton', background=self.theme['danger'], foreground=accent_fg,
                             padding=(16, 8), borderwidth=0)
        self.style.map('Danger.TButton',
                       background=[('active', self.theme['danger']), ('disabled', border)],
                       foreground=[('disabled', muted)])

        tab_inactive = surface_alt
        self.style.configure('CustomNotebook', background=surface, borderwidth=0, tabmargins=(12, 8, 12, 0))
        self.style.configure('CustomNotebook.Tab', background=tab_inactive, foreground=muted,
                             padding=(20, 12), borderwidth=0, relief='flat')
        self.style.map('CustomNotebook.Tab',
                       background=[('selected', accent), ('active', accent_hover), ('!selected', tab_inactive)],
                       foreground=[('selected', accent_fg), ('!selected', muted)],
                       bordercolor=[('selected', accent), ('!selected', tab_inactive)])

    def apply_theme(self, theme_name):
        """Apply one of the predefined themes and propagate it to sub widgets."""
        if theme_name not in self.themes:
            return
        self.current_theme_name = theme_name
        self.theme = self.themes[theme_name]
        self._configure_styles()
        self.root.configure(bg=self.theme['background'])
        if hasattr(self, 'view'):
            self.view.configure(style='Main.TFrame')
        if hasattr(self, 'content_card'):
            self.content_card.configure(style='SurfaceCard.TFrame')
        next_theme = self._next_theme_name()
        if hasattr(self, 'icon_widget'):
            self.icon_widget.update_theme(self.theme, next_theme)
        if hasattr(self, 'editor_widget'):
            self.editor_widget.update_theme(self.theme)
        if hasattr(self, 'console'):
            self.console.update_theme(self.theme)
        if hasattr(self, 'status_bar'):
            self.status_bar.update_theme(self.theme)

    def toggle_theme(self, event=None):
        """Toggle between light and dark visual themes."""
        self.apply_theme(self._next_theme_name())

    def _next_theme_name(self):
        return 'light' if self.current_theme_name == 'dark' else 'dark'
