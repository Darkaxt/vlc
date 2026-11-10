"""Regression for waiting for the Git producer beyond the tar end marker."""
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tarfile
import unittest

MODULE = Path(__file__).with_name('package-source-release.py')
spec = importlib.util.spec_from_file_location('source_release', MODULE)
source_release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source_release)


class SourceArchiveCompletion(unittest.TestCase):
    def test_waits_for_actual_producer_eof(self):
        creation = {'creationflags': subprocess.CREATE_NO_WINDOW} if sys.platform == 'win32' else {}
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), '--producer'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, **creation)
        try:
            with tarfile.open(fileobj=child.stdout, mode='r|') as archive:
                self.assertEqual([member.name for member in archive], ['source.txt'])
            self.assertEqual(source_release.finish_archive_process(child), 0)
            self.assertEqual(child.stderr.read(), b'')
        finally:
            child.stdout.close()
            child.stderr.close()
            child.wait()


if __name__ == '__main__':
    if sys.argv[1:] == ['--producer']:
        payload = io.BytesIO()
        with tarfile.open(fileobj=payload, mode='w') as archive:
            entry = tarfile.TarInfo('source.txt')
            entry.size = 1
            archive.addfile(entry, io.BytesIO(b'x'))
        sys.stdout.buffer.write(payload.getvalue())
        # Valid archive padding exceeds the pipe and tar reader buffers.
        sys.stdout.buffer.write(bytes(1024 * 1024))
        sys.stdout.buffer.flush()
    else:
        unittest.main()
