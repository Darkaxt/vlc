#!/usr/bin/env python3
"""Compile the pinned library's actual path functions for the repeated-root regression."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tarfile


def function(source, name):
    match = re.search(r'^std::(?:string|stack<std::string>) ' + name + r'\([^)]*\)\s*\{',
                      source, re.MULTILINE)
    if not match:
        raise RuntimeError('Pinned path function is missing: ' + name)
    depth = 1
    end = match.end()
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[match.start():end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--scratch', required=True, type=Path)
    parser.add_argument('--compiler', default='c++')
    parser.add_argument('--patch', type=Path)
    parser.add_argument('--expect-original-failure', action='store_true')
    args = parser.parse_args()
    if args.source.is_dir():
        source = (args.source / 'src/utils/Filename.cpp').read_text()
    else:
        with tarfile.open(args.source) as archive:
            member, = [row for row in archive.getmembers() if row.name.endswith('/src/utils/Filename.cpp')]
            source = archive.extractfile(member).read().decode()
    args.scratch.mkdir(parents=True, exist_ok=False)
    if args.patch:
        patched = args.scratch / 'patched-source'
        target = patched / 'src/utils/Filename.cpp'
        target.parent.mkdir(parents=True)
        target.write_text(source, newline='\n')
        subprocess.run(['git', 'apply', '--check', str(args.patch.resolve())], cwd=patched, check=True)
        subprocess.run(['git', 'apply', str(args.patch.resolve())], cwd=patched, check=True)
        source = target.read_text()
    names = ('directory', 'directoryName', 'parentDirectory', 'fileName', 'firstFolder',
             'toFolderPath', 'splitPath')
    functions = '\n\n'.join(function(source, name) for name in names)
    cases = [
        ('/home/runner/work/home/data/modern-vlc/vlc/ml/mlstorage/', True),
        ('/home/runner/work/home/data/library.db', False),
        ('/Users/runner/work/Users/Library/', True),
        ('/mnt/d/mnt/project/', True),
        ('/home/runner/.local/share/modern-vlc/vlc/ml/mlstorage/', True),
    ]
    rows = ',\n'.join('{' + json.dumps(path) + ', ' + str(directory).lower() + '}'
                      for path, directory in cases)
    program = '''#include <algorithm>
#include <cassert>
#include <iostream>
#include <stack>
#include <string>
#include <utility>
#undef _WIN32
#define DIR_SEPARATOR '/'
namespace medialibrary { namespace utils { namespace file {
''' + functions + '''
}}}
int main() {
    const std::pair<std::string, bool> cases[] = {
''' + rows + '''
    };
    int failures = 0;
    for (const auto &entry : cases) {
        auto parts = medialibrary::utils::file::splitPath(entry.first, entry.second);
        std::string actual;
        while (!parts.empty()) { actual += "/" + parts.top(); parts.pop(); }
        std::string expected = entry.first;
        if (expected.back() == '/') expected.pop_back();
        if (actual != expected) {
            ++failures;
            std::cout << "MISMATCH " << expected << " -> " << actual << '\\n';
        }
    }
    return failures ? 1 : 0;
}
'''
    unit = args.scratch / 'medialibrary-path-regression.cpp'
    unit.write_text(program, newline='\n')
    executable = args.scratch / 'medialibrary-path-regression.exe'
    subprocess.run([args.compiler, '-std=c++17', '-O3', '-g0', '-DNDEBUG', str(unit),
                    '-o', str(executable)], check=True)
    result = subprocess.run([str(executable)], text=True, capture_output=True)
    print(json.dumps({'native_exit_code': result.returncode, 'stdout': result.stdout,
                      'expected_original_failure': args.expect_original_failure}, indent=2))
    if result.returncode != (1 if args.expect_original_failure else 0):
        raise RuntimeError('Actual pinned path-function regression has an unexpected result')


if __name__ == '__main__':
    main()
