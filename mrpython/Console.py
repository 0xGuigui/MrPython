from platform import python_version
from tkinter import *
from PyInterpreter import PyInterpreter
import io
import rpc

class Console:
    """
    Interactive console of MrPython, consisting of two widgets : output and input
    """

    from ModifiedColorDelegator import ModifiedColorDelegator
    from ModifiedUndoDelegator import ModifiedUndoDelegator
    from IdleHistory import History

    SHELL_TITLE = "Python " + python_version() + " Shell"
    TEXT_COLORS_BY_MODE = {
                            'run':'green',
                            'error':'red',
                            'normal':'black',
                            'warning':'orange'
                          }

    def __init__(self, parent, app):
        """
        Create and configure the shell (the text widget that gives informations
        and the interactive shell)
        """
        self.app = app
        # Creating output console
        self.frame_output = Frame(parent)
        self.scrollbar = Scrollbar(self.frame_output)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.output_console = Text(self.frame_output, height=15, state='disabled', 
                                   yscrollcommand=self.scrollbar.set)
        #self.frame_output.config(borderwidth=1, relief=GROOVE)
        self.output_console.pack(side=LEFT, fill=BOTH, expand=1)
        self.scrollbar.config(command=self.output_console.yview)
        # Creating input console
        self.frame_input = Frame(parent)
        self.arrows = Label(self.frame_input, text=" >>> ")
        self.input_console = Text(self.frame_input, background='#775F57',
                                  height=1, state='disabled', relief=FLAT)
        self.input_console.bind('<Control-Key-Return>', self.evaluate_action)
        self.input_console.bind('<Return>', self.evaluate_action)
        #self.frame_input.config(borderwidth=1, relief=GROOVE)
        self.eval_button = Button(self.frame_input, text="Eval",
                                  command=self.evaluate_action, width=7,
                                  state='disabled')
        self.arrows.config(borderwidth=1, relief=RIDGE)
        self.arrows.pack(side=LEFT, fill=Y)
        self.input_console.pack(side=LEFT, expand=1, fill=BOTH)
        self.eval_button.pack(side=LEFT, fill=Y)
		# Redirect the Python output, input and error stream to the console
        import IOBinding
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


    def configure_color_tags(self):
        """ Set the colors for the specific tags """
        self.output_console.tag_config('run', foreground='green')
        self.output_console.tag_config('error', foreground='red')
        self.output_console.tag_config('normal', foreground='black')
        self.output_console.tag_config('warning', foreground='orange')


    def reset_output(self):
        """ Clear all the output console """
        self.output_console.config(state=NORMAL)
        self.output_console.delete(1.0, END)
        self.begin()
        self.write("Current mode : %s mode\n\n" % (self.mode))
        self.output_console.config(state=DISABLED)


    def change_mode(self, mode):
        """ When the mode change : clear the output console and display
            the new mode """
        self.mode = mode
        self.reset_output()
        self.switch_input_status(False)


    def evaluate_action(self, *args):
        """ Evaluate the expression in the input console """
        output_file = open('interpreter_output', 'w+')
        original_stdout = sys.stdout
        sys.stdout = output_file
        expr = self.input_console.get(1.0, "end")
        while expr and (expr[0] == "\n"):
            expr = expr[1:]
        text, result = self.interpreter.run_evaluation(expr)
        self.input_console.delete(1.0, END)
        self.input_console.config(height=1)
        self.write(text, tags=(result))
        sys.stdout = original_stdout
        output_file.close()


    def switch_input_status(self, on):
        """ Enable or disable the evaluation bar and button """
        stat = None
        bg = None
        if on:
            stat = 'normal'
            bg = '#FFA500'
        else:
            stat = 'disabled'
            bg = '#775F57'
        self.input_console.config(state=stat, background=bg)
        self.eval_button.config(state=stat)


    def run(self, filename):
        """ Run the program in the current editor : execute, print results """
        # Reset the output first
        self.reset_output()
        # A new PyInterpreter is created each time code is run
        # It is then kept for other actions, like evaluation
        self.interpreter = PyInterpreter(self.app.mode, filename)
        # Change the output during execution
        output_file = open('interpreter_output', 'w+')
        original_stdout = sys.stdout
        sys.stdout = output_file
        text, result = self.interpreter.execute()
        self.write(text, tags=(result))
        sys.stdout = original_stdout
        output_file.close()
        # Enable or disable the evaluation bar according to the execution status
        if result == 'run':
            self.switch_input_status(True)
        else:
            self.switch_input_status(False)


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
            self.output_console.configure(state='normal')
            self.output_console.insert("iomark", s, tags)
            self.output_console.configure(state='disabled')
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
