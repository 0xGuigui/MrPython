from ModifiedInterpreter import ModifiedInterpreter
from platform import python_version
from tkinter import *
import io
import rpc

class Console:
    """
    Interactive console of MrPython, two widgets : output and input
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
                                  height=1, state='disabled')
        self.frame_input.config(borderwidth=1, relief=GROOVE)
        self.eval_button = Button(self.frame_input, text="Eval",
                                  command=self.evaluate_action, width=7,
                                  state='disabled')
        self.arrows.config(borderwidth=1, relief=RIDGE)
        self.arrows.pack(side=LEFT, fill=Y)
        self.input_console.pack(side=LEFT, expand=1, fill=BOTH)
        self.eval_button.pack(side=LEFT, fill=Y)
        # Create the variables used for delimiting the different regions
        # of the text, for displaying different colors
        # Index (x, y) of the beginning of the current tag (region)
        self.current_begin_index = "0.0"
        # Color of the current tag
        self.current_color = "black"
        self.current_tag = 0
        ### self.save_stdout = sys.stdout
        ### self.save_stderr = sys.stderr
        ### self.save_stdin = sys.stdin
		# Redirect the Python output, input and error stream to the console
        import IOBinding
        self.stdin = PseudoInputFile(self, "run", IOBinding.encoding)
        self.stdout = PseudoOutputFile(self, "normal", IOBinding.encoding)
        self.stderr = PseudoOutputFile(self, "error", IOBinding.encoding)
        self.console = PseudoOutputFile(self, "normal", IOBinding.encoding)
        #sys.stdout = self.stdout
        #sys.stderr = self.stderr
        #sys.stdin = self.stdin
        
        self.interp = ModifiedInterpreter(self)

        
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
        self.output_console.tag_config('run', foreground='green')
        self.output_console.tag_config('error', foreground='red')
        self.output_console.tag_config('normal', foreground='black')
        self.output_console.tag_config('warning', foreground='orange')


    def change_mode(self, mode):
        """ When the mode change : clear the output console and display
            the new one """
        self.output_console.config(state=NORMAL)
        self.output_console.delete(1.0, END)
        self.begin()
        self.write("Current mode : %s mode\n" % (mode))
        self.output_console.config(state=DISABLED)
        self.current_begin_index = "0.0"
        self.current_color = "black"
        self.current_tag = 0


    def evaluate_action(self):
        """ Evaluate the expression in the input console """
        self.interp.evaluate(self.input_console.get(1.0, END))


    def run(self, filename):
        """ Run the program in the current editor """
        self.interp.clear_environment()
        if self.app.mode == "full": #Full Python mode : normal execution
            result = self.interp.execfile(filename)
        else: #Student mode
            result = self.interp.exec_file_student_mode(filename)
        self.input_console.delete(1.0, END)
        # If errors, disable the interactive prompt
        if result:
            self.input_console.config(background='#775F57', state='disabled')
            self.eval_button.config(state='disabled')
        else:
            self.input_console.config(background='#FFC757', state='normal')
            self.eval_button.config(state='normal')


    def check_syntax(self, pyEditor):
        """ Check the syntax of the current editor """
        # TODO: correct this
        self.write("\n==== check %s ====\n" % (pyEditor.long_title()))
        self.interp.checksyntax(pyEditor)
        self.write("==== end check ====\n")
        self.showprompt()

    """
    def resetoutput(self):
        source = self.output_console.get("iomark", "end-1c")
        if self.history:
            self.history.store(source)
        if self.output_console.get("end-2c") != "\n":
            self.output_console.insert("end-1c", "\n")
        self.output_console.mark_set("iomark", "end-1c")"""

    
    def change_text_color(self, mode):
        """ Change the text color according to the specified mode :
            we get the color by accessing the dictonnary
            TEXT_COLORS_BY_MODE[mode] """
        """
        # Give the current color to the current tag
        tag_name = "tag" + str(self.current_tag)
        self.output_console.tag_add(tag_name, self.current_begin_index, END)
        self.output_console.tag_config(tag_name, foreground=self.current_color)
        # Change of color, we start a new tag that will be create on the next
        # change_text_color call
        self.current_color = self.TEXT_COLORS_BY_MODE[mode]
        self.current_begin_index = self.output_console.index(END)
        self.current_tag += 1
        self.output_console.configure(foreground=self.current_color)
    """
        

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
            count = self.writebis(s, tags, "iomark")
            self.output_console.mark_gravity("iomark", "left")
        except:
            raise ###pass  # ### 11Aug07 KBK if we are expecting exceptions
                           # let's find out what they are and be specific.
        if self.canceled:
            self.canceled = 0
            raise KeyboardInterrupt
        return count


    def writebis(self, s, tags=(), mark="insert"):
        if isinstance(s, (bytes, bytes)):
            s = s.decode(IOBinding.encoding, "replace")

        self.output_console.configure(state='normal')
        self.output_console.insert(mark, s, tags)
        self.output_console.configure(state='disabled')
        self.output_console.see(mark)
        self.output_console.update()
        return len(s)


    def showprompt(self):
        #self.resetoutput()
        try:
            s = str(sys.ps1)
        except:
            s = ""
        self.console.write(s)
        self.output_console.mark_set("insert", "end-1c")
        self.io.reset_undo()


    def begin(self):
        self.output_console.mark_set("iomark", "insert")
        # self.resetoutput()

        sys.displayhook = rpc.displayhook

        self.write("Python %s on %s\n" %
                   (sys.version, sys.platform))
        self.showprompt()
        import tkinter
        tkinter._default_root = None # 03Jan04 KBK What's this?
        return True


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
        self.resetoutput()
        if self.canceled:
            self.canceled = 0
            raise KeyboardInterrupt
        if self.endoffile:
            self.endoffile = 0
            line = ""
        return line


    #heritage PyEditor??
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
