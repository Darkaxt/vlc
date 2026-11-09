"""GDB-only, read-only unwinding of the observed x86 Mesa JIT call boundary.

Used after the original fault registers and automatic stacks have been recorded.
Only that exact PC/RBP pair is recognized. No inferior registers or core bytes
are changed, and unrelated frames retain GDB's normal unwinders.
"""
from types import SimpleNamespace
import gdb
import gdb.unwinder


class ObservedJitBoundary(gdb.unwinder.Unwinder):
    def __init__(self):
        super().__init__('vlc-observed-x86-jit-boundary')
        self.pc = int(gdb.parse_and_eval('$jit_pc'))
        self.rbp = int(gdb.parse_and_eval('$jit_rbp'))
        self.word = gdb.lookup_type('unsigned long long')

    def __call__(self, frame):
        if int(frame.read_register('rip')) != self.pc or int(frame.read_register('rbp')) != self.rbp:
            return None
        saved = gdb.Value(self.rbp).cast(self.word.pointer())
        stack = gdb.Value(self.rbp + 16).cast(self.word)
        info = frame.create_unwind_info(SimpleNamespace(sp=stack, pc=gdb.Value(self.pc)))
        info.add_saved_register('rip', saved[1])
        info.add_saved_register('rsp', stack)
        info.add_saved_register('rbp', saved[0])
        return info


if gdb.newest_frame().architecture().name() == 'i386:x86-64':
    gdb.unwinder.register_unwinder(None, ObservedJitBoundary(), replace=True)
    gdb.invalidate_cached_frames()
    gdb.write('Read-only stack through the observed x86 JIT boundary:\n')
    gdb.execute('bt')
