
from  ModifiedInterpreter import ModifiedInterpreter
import io
from tkinter import *
import rpc
from platform import python_version
from tkinter import *

class PyShell(Widget):

    shell_title = "Python " + python_version() + " Shell"

    from ModifiedColorDelegator import ModifiedColorDelegator
    from ModifiedUndoDelegator import ModifiedUndoDelegator
    from IdleHistory import History

    def __init__(self,parent):

        self.entre=Text(parent,height=1,background='#FFC757')

        self.text=Text(parent)
        self.text.configure(state='disabled')

        self.scroll=scroll=Scrollbar(self.text)
        scroll['command'] = self.text.yview
        scroll.pack(side=RIGHT, fill=Y)
        self.text['yscrollcommand'] = scroll.set


        self.warning_stream=sys.__stderr__
        self.tkinter_vars = {}  # keys: Tkinter event names
                                    # values: Tkinter variable instances
        self.interp = ModifiedInterpreter(self)

        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        self.save_stdin = sys.stdin
        import IOBinding
        self.stdin = PseudoInputFile(self, "stdin", IOBinding.encoding)
        self.stdout = PseudoOutputFile(self, "stdout", IOBinding.encoding)
        self.stderr = PseudoOutputFile(self, "stderr", IOBinding.encoding)
        self.console = PseudoOutputFile(self, "console", IOBinding.encoding)

        sys.stdout = self.stdout
        sys.stderr = self.stderr
        sys.stdin = self.stdin

        self.history = self.History(self.text)
        self.pollinterval = 50  # millisec
        ##heritage pyEditor?
        self.undo = undo = self.ModifiedUndoDelegator()

        self.io = io = IOBinding.IOBinding(self)
        self.begin()


    reading = False
    executing = False
    canceled = False
    endoffile = False
    closing = False
    _stop_readline_flag = False
    COPYRIGHT = 'Type "copyright", "credits" or "license()" for more information.'

    def set_warning_stream(self, stream):
        global warning_stream
        warning_stream = stream

    def get_warning_stream(self):
        return self.warning_stream

    def get_var_obj(self, name, vartype=None):
        var = self.tkinter_vars.get(name)
        if not var and vartype:
            # create a Tkinter variable object with self.text as master:
            self.tkinter_vars[name] = var = vartype(self.text)
        return var

    def run(self,filename):
        self.write("\n==== run %s ====\n" % (filename))
        self.interp.execfile(filename)
        self.write("==== end run ====\n")
        self.showprompt()

    def runit(self,filename=None):
        self.interp.execfile(filename)
        self.interp.execfile(filename,self.entre.get(1.0,END))
        self.entre.delete(1.0,END)


    def check(self,pyEditor):
        self.write("\n==== check %s ====\n" % (pyEditor.long_title()))
        self.interp.checksyntax(pyEditor)
        self.write("==== end check ====\n")
        self.showprompt()

    def beginexecuting(self):
        "Helper for ModifiedInterpreter"
        self.resetoutput()
        self.executing = 1

    def endexecuting(self):
        "Helper for ModifiedInterpreter"
        self.executing = 0
        self.canceled = 0
        self.showprompt()

    def resetoutput(self):
        source = self.text.get("iomark", "end-1c")
        if self.history:
            self.history.store(source)
        if self.text.get("end-2c") != "\n":
            self.text.insert("end-1c", "\n")
        self.text.mark_set("iomark", "end-1c")

    def write(self, s, tags=()):
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
            self.text.mark_gravity("iomark", "right")
            count = self.writebis(s, tags, "iomark")
            self.text.mark_gravity("iomark", "left")
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

        self.text.configure(state='normal')
        self.text.insert(mark, s, tags)
        self.text.configure(state='disabled')
        self.text.see(mark)
        self.text.update()
        return len(s)

    def showprompt(self):
        self.resetoutput()
        try:
            s = str(sys.ps1)
        except:
            s = ""
        self.console.write(s)
        self.text.mark_set("insert", "end-1c")
        self.io.reset_undo()

    def begin(self):
        self.text.mark_set("iomark", "insert")
        self.resetoutput()
        sys.displayhook = rpc.displayhook

        self.write("Python %s on %s\n%s\n" %
                   (sys.version, sys.platform, self.COPYRIGHT))
        self.showprompt()
        import tkinter
        tkinter._default_root = None # 03Jan04 KBK What's this?
        return True

    def readline(self):
        save = self.reading
        try:
            self.reading = 1
        finally:
            self.reading = save
        if self._stop_readline_flag:
            self._stop_readline_flag = False
            return ""
        line = self.text.get("iomark", "end-1c")
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
