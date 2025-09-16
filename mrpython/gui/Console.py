from platform import python_version
from tkinter import *
from tkinter import ttk
from tkinter.font import Font, nametofont
from PyInterpreter import InterpreterProxy
from .WidgetRedirector import WidgetRedirector

from .HyperlinkManager import HyperlinkManager

import version
from translate import tr
import io
import rpc
import sys

class ConsoleHistory:
    def __init__(self, history_capacity=100):
        assert history_capacity > 0
        assert history_capacity < 10000
        self.history_capacity = history_capacity
        self.clear()

    def record(self, txt):
        #print("[History] record: " + txt)
        if not txt:
            return

        if self.history_size == self.history_capacity:
            self.history = self.history[1:]
            self.history_size -= 1

        self.history.append(txt)
        self.history_size += 1
        self.history_pos = self.history_size - 1

        #print(self)

    def move_past(self):
        if self.history_pos > 0:
            entry = self.history[self.history_pos]
            self.history_pos -= 1
            # print("[Move past]: " + entry)
            # print(self)

            return entry
        elif self.history_pos == 0:
            entry = self.history[self.history_pos]
            # print("[Move past] (last): " + entry)
            # print(self)

            return entry
        else:
            # print("[Move past]: no history...")
            # print(self)
            return None

    def move_future(self):
        if self.history_pos < self.history_size - 1:
            self.history_pos += 1
            entry = self.history[self.history_pos]
            # print("[Move future]: " + entry)
            # print(self)
            return entry
        elif self.history_pos == self.history_size - 1:
            # print("[Move future]: last...")
            # print(self)
            return ""
        else:
            # print("[Move future]: no history...")
            # print(self)
            return None

    def clear(self):
        self.history = []
        self.history_size = 0
        self.history_pos = -1

    def __str__(self):
        str = "History:["
        i = 0
        for entry in self.history:
            if i == self.history_pos:
                str += "<"
            str += "'{}'".format(entry)
            if i == self.history_pos:
                str += ">"

            if i < self.history_size:
                str += ", "

            i += 1

        str += "]"

        return str


class ErrorCallback:
    def __init__(self, src, error):
        self.src = src
        self.error = error

    def __call__(self):
        #print("error line=" + str(self.error.line))
        if self.error and self.error.line:
            self.src.app.goto_position(self.error.line, self.error.offset or 0)


# from: http://tkinter.unpythonic.net/wiki/ReadOnlyText
class ReadOnlyText(Text):
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        self.redirector = WidgetRedirector(self)
        self.insert = self.redirector.register("insert", lambda *args, **kw: "break")
        self.delete = self.redirector.register("delete", lambda *args, **kw: "break")

class Console:
    """
    Interactive console of MrPython, consisting of two widgets : output and input
    """

    from .ModifiedColorDelegator import ModifiedColorDelegator
    from .ModifiedUndoDelegator import ModifiedUndoDelegator
    from IdleHistory import History

    SHELL_TITLE = "Python " + python_version() + " Shell"
    TEXT_COLORS_BY_MODE = {
        'run': 'green'
        , 'error': 'red'
        , 'normal': 'black'
        , 'warning': 'orange'
        , 'info' : 'blue'    }

    def __init__(self, output_parent, input_parent, app, theme=None):
        """
        Create and configure the shell (the text widget that gives informations
        and the interactive shell)
        """
        self.app = app
        self.theme = theme or {
            'background': '#0f172a',
            'surface': '#111c3a',
            'surface_alt': '#162544',
            'border': '#1f2846',
            'accent': '#4f46e5',
            'accent_hover': '#6366f1',
            'accent_fg': '#f8fafc',
            'text': '#e2e8f0',
            'muted': '#94a3b8',
            'success': '#22c55e',
            'warning': '#facc15',
            'danger': '#f87171'
        }
        self.text_colors = {
            'run': self.theme['success'],
            'error': self.theme['danger'],
            'normal': self.theme['text'],
            'warning': self.theme['warning'],
            'info': self.theme['accent'],
            'stdout': self.theme['muted']
        }
        # Creating output console
        self.frame_output = Frame(output_parent, background=self.theme['surface'],
                                  highlightbackground=self.theme['border'],
                                  highlightcolor=self.theme['border'],
                                  highlightthickness=1, bd=0,
                                  padx=14, pady=12)
        self.scrollbar = ttk.Scrollbar(self.frame_output, orient=VERTICAL,
                                       style='Console.Vertical.TScrollbar')
        self.scrollbar.grid(row=0, column=1, sticky=(N, S))

        self.output_console = ReadOnlyText(
            self.frame_output,
            height=15,
            yscrollcommand=self.scrollbar.set,
            background=self.theme['surface_alt'],
            foreground=self.theme['text'],
            insertbackground=self.theme['accent'],
            selectbackground=self.theme['accent'],
            selectforeground=self.theme['accent_fg'],
            relief=FLAT,
            borderwidth=0,
            highlightthickness=0,
            wrap=WORD,
            padx=16,
            pady=12
        )

        self.hyperlinks = HyperlinkManager(self.output_console)
        self.output_console.grid(row=0, column=0, sticky=(N, S, E, W))
        self.scrollbar.config(command=self.output_console.yview)

        self.frame_output.rowconfigure(0, weight=1)
        self.frame_output.columnconfigure(0, weight=1)

        # Creating input console
        self.frame_input = Frame(input_parent, background=self.theme['surface'],
                                 highlightbackground=self.theme['border'],
                                 highlightcolor=self.theme['border'],
                                 highlightthickness=1, bd=0)
        self.frame_input.configure(padx=14, pady=12)
        self.arrows = Label(self.frame_input, text=">>>",
                            background=self.theme['surface'],
                            foreground=self.theme['muted'],
                            padx=12, pady=6)
        self.input_console = Entry(
            self.frame_input,
            background=self.theme['surface_alt'],
            foreground=self.theme['text'],
            insertbackground=self.theme['accent'],
            disabledbackground=self.theme['surface_alt'],
            disabledforeground=self.theme['muted'],
            relief=FLAT,
            highlightthickness=0,
            borderwidth=0,
            state='disabled'
        )
        self.input_console.bind('<Return>', self.evaluate_action)
        self.input_history = ConsoleHistory()
        self.input_console.bind('<Up>', self.history_up_action)
        self.input_console.bind('<Down>', self.history_down_action)
        self.eval_button = ttk.Button(
            self.frame_input,
            text=tr('Eval'),
            style='Accent.TButton',
            command=self.evaluate_action
        )
        self.eval_button.state(['disabled'])
        self.eval_button.configure(cursor='hand2')
        self.arrows.grid(row=0, column=0, sticky=(W, E))
        self.input_console.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.eval_button.grid(row=0, column=2)

        self.frame_input.columnconfigure(1, weight=1)

	# Redirect the Python output, input and error stream to the console
        import gui.IOBinding as IOBinding
        self.stdin = PseudoInputFile(self, "error", IOBinding.encoding)
        self.stdout = PseudoOutputFile(self, "error", IOBinding.encoding)
        self.stderr = PseudoOutputFile(self, "error", IOBinding.encoding)
        self.console = PseudoOutputFile(self, "error", IOBinding.encoding)
        #sys.stdout = self.stdout
        #sys.stderr = self.stderr
        #sys.stdin = self.stdin
        # The current Python mode 
        self.mode = "student"

        self.reading = False
        self.executing = False
        self.canceled = False
        self.endoffile = False
        self.closing = False
        self._stop_readling_flag = False

        self.history = self.History(self.output_console)
        self.undo = undo = self.ModifiedUndoDelegator()
        self.io = IOBinding.IOBinding(self)
        self.begin()
        self.configure_color_tags()
        self.switch_input_status(True)
        self.interpreter = None

    def change_font(self, nfont):
        self.output_console.configure(font=nfont)
        self.input_console.configure(font=nfont)

    def configure_color_tags(self):
        """ Set the colors for the specific tags """
        self.output_console.tag_config('run', foreground=self.text_colors['run'])
        self.output_console.tag_config('error', foreground=self.text_colors['error'])
        self.output_console.tag_config('normal', foreground=self.text_colors['normal'])
        self.output_console.tag_config('warning', foreground=self.text_colors['warning'])
        self.output_console.tag_config('info', foreground=self.text_colors['info'])
        self.output_console.tag_config('stdout', foreground=self.text_colors['stdout'])

    def reset_output(self):
        """ Clear all the output console """
        #self.output_console.config(state=NORMAL)
        self.output_console.delete(1.0, END)
        self.begin()

        self.write("MrPython v.{} -- mode {}\n".format(version.version_string(),
                                                       tr(self.mode)))
        #self.output_console.config(state=DISABLED)


    def change_mode(self, mode):
        """ When the mode change : clear the output console and display
            the new mode """
        self.mode = mode
        self.reset_output()
        self.hyperlinks.reset()
        #self.switch_input_status(False)

    def write_report(self, status, report, exec_mode):
        tag = 'run'
        if not status:
            tag = 'error'
            
        self.hyperlinks.reset()

        self.write(report.header, tags=(tag))
        #self.write("\n")
        
        has_convention_error = False
        
        # show convention errors, if any
        for error in report.convention_errors:
            if error.severity == "error" and not has_convention_error:
                self.write(tr("-----\nPython101 convention errors:\n-----\n"), tags='info')
                has_convention_error = True

            hyper, hyper_spec = self.hyperlinks.add(ErrorCallback(self, error))
            #print("hyper={}".format(hyper))
            #print("hyper_spec={}".format(hyper_spec))
            self.write("\n")
            self.write(str(error), tags=(error.severity, hyper, hyper_spec))
            self.write("\n")

        # show compilation errors, if any
        has_compilation_error = False
        for error in report.compilation_errors:
            if error.severity == "error" and not has_compilation_error:
                self.write(tr("\n-----\nCompilation errors (Python interpreter):\n-----\n"), tags='info')
                has_compilation_error = True
            hyper, hyper_spec = self.hyperlinks.add(ErrorCallback(self, error))
            self.write("\n")
            self.write(str(error), tags=(error.severity, hyper, hyper_spec))
            self.write("\n")

        # write the stdout that has been generated
        self.write(str(report.output), tags=('stdout'))
            
        # show execution errors, if any
        has_execution_error = False
        for error in report.execution_errors:
            if error.severity == "error" and not has_execution_error:
                self.write(tr("\n-----\nExecution errors (Python interpreter):\n-----\n"), tags='info')
                has_execution_error = True
                    
            hyper, hyper_spec = self.hyperlinks.add(ErrorCallback(self, error))
            self.write("\n")
            self.write(str(error), tags=(error.severity, hyper, hyper_spec))
            self.write("\n")

        # show evaluation result
        if status and report.result is not None:
            self.write(repr(report.result), tags=('normal'))

        if exec_mode == 'exec' and status and self.mode == tr('student') and report.nb_defined_funs > 0:
            if report.nb_passed_tests > 1:
                self.write("==> " + tr("All the {} tests passed with success").format(report.nb_passed_tests), tags=('run'))
            elif report.nb_passed_tests == 1:
                self.write("==> " + tr("Only one (successful) test found, it's probably not enough"), tags=('warning'))
            else:
                self.write("==> " + tr("There is no test! you have to write tests!"), tags=('error'))
        
        self.write(report.footer, tags=(tag))

    def evaluate_action(self, *args):
        """ Evaluate the expression in the input console """
        expr = self.input_console.get()
        if not expr:
            return
        local_interpreter = False
        if self.interpreter is None:
            self.interpreter = InterpreterProxy(self.app.root, self.app.mode, "<<console>>")
            local_interpreter = True
            self.app.running_interpreter_proxy = self.interpreter

        callback_called = False

        # the call back
        def callback(ok, report):
            nonlocal callback_called
            if callback_called:
                return
            else:
                callback_called = True

            if ok:
                self.input_history.record(expr)

            self.input_console.delete(0, END)
            self.write_report(ok, report, 'eval')

            if local_interpreter:
                self.interpreter.kill()
                self.interpreter = None
                self.app.running_interpreter_proxy = None

            self.app.icon_widget.disable_icon_running()
            self.app.running_interpreter_callback = None

        # non-blocking call
        self.app.icon_widget.enable_icon_running()
        self.app.running_interpreter_callback = callback
        self.interpreter.run_evaluation(expr, callback)

    def history_up_action(self, event=None):
        entry = self.input_history.move_past()
        if entry is not None:
            self.input_console.delete(0, END)
            self.input_console.insert(0, entry)

    def history_down_action(self, event=None):
        entry = self.input_history.move_future()
        if entry is not None:
            self.input_console.delete(0, END)
            self.input_console.insert(0, entry)

    def switch_input_status(self, on):
        """ Enable or disable the evaluation bar and button """
        if on:
            self.input_console.config(state='normal', background=self.theme['surface_alt'],
                                      foreground=self.theme['text'])
            self.eval_button.state(['!disabled'])
        else:
            self.input_console.config(state='disabled', background=self.theme['surface_alt'],
                                      foreground=self.theme['muted'])
            self.eval_button.state(['disabled'])

    def update_theme(self, theme):
        """Refresh console colors when the global palette changes."""
        self.theme = theme or self.theme
        self.text_colors = {
            'run': self.theme['success'],
            'error': self.theme['danger'],
            'normal': self.theme['text'],
            'warning': self.theme['warning'],
            'info': self.theme['accent'],
            'stdout': self.theme['muted']
        }
        self.frame_output.configure(background=self.theme['surface'],
                                    highlightbackground=self.theme['border'],
                                    highlightcolor=self.theme['border'])
        self.scrollbar.configure(style='Console.Vertical.TScrollbar')
        self.output_console.configure(background=self.theme['surface_alt'],
                                      foreground=self.theme['text'],
                                      insertbackground=self.theme['accent'],
                                      selectbackground=self.theme['accent'],
                                      selectforeground=self.theme['accent_fg'])
        self.configure_color_tags()
        self.frame_input.configure(background=self.theme['surface'],
                                   highlightbackground=self.theme['border'],
                                   highlightcolor=self.theme['border'])
        self.arrows.configure(background=self.theme['surface'], foreground=self.theme['muted'])
        self.input_console.configure(disabledbackground=self.theme['surface_alt'],
                                     disabledforeground=self.theme['muted'])
        self.eval_button.configure(style='Accent.TButton')
        is_enabled = str(self.input_console['state']) == 'normal'
        self.switch_input_status(is_enabled)

    def run(self, filename):
        """ Run the program in the current editor : execute, print results """
        # Reset the output first
        self.reset_output()
        # A new PyInterpreter is created each time code is run
        # It is then kept for other actions, like evaluation
        if self.interpreter is not None:
            self.interpreter.kill()
            self.app.running_interpreter_proxy = None

            
        self.interpreter = InterpreterProxy(self.app.root, self.app.mode, filename)
        self.app.running_interpreter_proxy = self.interpreter

        callback_called = False
        
        def callback(ok, report):
            # XXX: the ok is not trustable
            if report.has_compilation_error() or report.has_execution_error():
                ok = False
            
            nonlocal callback_called
            if callback_called:
                return
            else:
                callback_called = True

            #print("[console] CALLBACK: exec ok ? {}  report={}".format(ok, report))
            self.write_report(ok, report, 'exec')
            self.output_console.see('1.0')

            # Enable or disable the evaluation bar according to the execution status
            if report.has_compilation_error(): # XXX: only for compilation ? , otherwise:  or report.has_execution_error():
                # kill the interpreter
                self.interpreter.kill()
                self.interpreter = None
                self.app.running_interpreter_proxy = None            
            else:
                self.input_console.focus_set()
                #self.switch_input_status(True)

            self.app.icon_widget.disable_icon_running()
            self.app.running_interpreter_callback = None
                
        # non-blocking call
        self.app.icon_widget.enable_icon_running()
        self.app.running_interpreter_callback = callback
        self.interpreter.execute(callback)

    def no_file_to_run_message(self):
        self.reset_output()
        self.write("=== No file to run ===", "error")


    def write(self, s, tags=()):
        """ Write into the output console """
        if isinstance(s, str) and len(s) and max(s) > '\uffff':
            # Tk doesn't support outputting non-BMP characters
            # Let's assume what printed string is not very long,
            # find first non-BMP character and construct informative
            # UnicodeEncodeError exception.
            for start, char in enumerate(s):
                if char > '\uffff':
                    break
            raise UnicodeEncodeError("UCS-2", char, start, start+1,
                                     'Non-BMP character not supported in Tk')
        try:
            self.output_console.mark_gravity("iomark", "right")
            if isinstance(s, (bytes, bytes)):
                s = s.decode(IOBinding.encoding, "replace")
            #self.output_console.configure(state='normal')
            self.output_console.insert("iomark", s, tags)
            #self.output_console.configure(state='disabled')
            self.output_console.see("iomark")
            self.output_console.update()
            self.output_console.mark_gravity("iomark", "left")
        except:
            raise
        if self.canceled:
            self.canceled = 0
            raise KeyboardInterrupt


    def begin(self):
        """ Display some informations in the output console at the beginning """
        self.output_console.mark_set("iomark", "insert")
        sys.displayhook = rpc.displayhook
        self.write("Python %s on %s\n" %
                   (sys.version, sys.platform))


    def readline(self):
        save = self.READING
        try:
            self.READING = 1
        finally:
            self.READING = save
        if self._stop_readline_flag:
            self._stop_readline_flag = False
            return ""
        line = self.output_console.get("iomark", "end-1c")
        if len(line) == 0:  # may be EOF if we quit our mainloop with Ctrl-C
            line = "\n"
        self.reset_output()
        if self.canceled:
            self.canceled = 0
            raise KeyboardInterrupt
        if self.endoffile:
            self.endoffile = 0
            line = ""
        return line


    def reset_undo(self):
        self.undo.reset_undo()


class PseudoFile(io.TextIOBase):

    def __init__(self, shell, tags, encoding=None):
        self.shell = shell
        self.tags = tags
        self._encoding = encoding


    @property
    def encoding(self):
        return self._encoding


    @property
    def name(self):
        return '<%s>' % self.tags


    def isatty(self):
        return True


class PseudoOutputFile(PseudoFile):

    def writable(self):
        return True


    def write(self, s):
        if self.closed:
            raise ValueError("write to closed file")
        if type(s) is not str:
            if not isinstance(s, str):
                raise TypeError('must be str, not ' + type(s).__name__)
            # See issue #19481
            s = str.__str__(s)
        return self.shell.write(s, self.tags)


class PseudoInputFile(PseudoFile):

    def __init__(self, shell, tags, encoding=None):
        PseudoFile.__init__(self, shell, tags, encoding)
        self._line_buffer = ''


    def readable(self):
        return True


    def read(self, size=-1):
        if self.closed:
            raise ValueError("read from closed file")
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        result = self._line_buffer
        self._line_buffer = ''
        if size < 0:
            while True:
                line = self.shell.readline()
                if not line: break
                result += line
        else:
            while len(result) < size:
                line = self.shell.readline()
                if not line: break
                result += line
            self._line_buffer = result[size:]
            result = result[:size]
        return result


    def readline(self, size=-1):
        if self.closed:
            raise ValueError("read from closed file")
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        line = self._line_buffer or self.shell.readline()
        if size < 0:
            size = len(line)
        eol = line.find('\n', 0, size)
        if eol >= 0:
            size = eol + 1
        self._line_buffer = line[size:]
        return line[:size]


    def close(self):
        self.shell.close()
