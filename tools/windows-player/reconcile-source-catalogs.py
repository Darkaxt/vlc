"""Check/restore gettext-generated PO state in an owned build.

Build tools can merge/rewrap tracked PO files. Restore only when the build's
actual template merge produces identical messages and runtime locale metadata.
Never discard a changed translation or use this on the canonical working
checkout as a cleanup shortcut.
"""
import argparse
import gettext
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess


def messages(blob, template):
    merged = subprocess.run(['msgmerge', '--for-msgfmt', '-', str(template)], input=blob, capture_output=True)
    assert merged.returncode == 0, merged.stderr.decode(errors='replace')
    completed = subprocess.run(['msgfmt', '-o', '-', '-'], input=merged.stdout, capture_output=True)
    assert completed.returncode == 0, completed.stderr.decode(errors='replace')
    catalog = gettext.GNUTranslations(io.BytesIO(completed.stdout))
    translated = {key: value for key, value in catalog._catalog.items() if key != ''}
    metadata = {key: catalog._info.get(key) for key in ('plural-forms', 'content-type')}
    return translated, metadata, catalog._info.get('language')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--restore-equivalent-generated', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    assert source == Path('/work/src'), 'Use the explicitly owned isolated build source'

    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(source), *arguments])

    commit = git('rev-parse', args.commit + '^{commit}').decode().strip()
    names = git('diff', '--name-only', commit, '--', 'po').decode().splitlines()
    assert all(re.fullmatch(r'po/[^/]+\.po', name) for name in names), names
    entries = []
    # Validate every changed member before restoring any of them.
    originals = {}
    template = source / 'po/vlc.pot'
    assert template.is_file()
    for name in names:
        current = (source / name).read_bytes()
        original = git('show', commit + ':' + name)
        actual_messages, actual_metadata, generated_language = messages(current, template)
        source_messages, source_metadata, source_language = messages(original, template)
        if (actual_messages, actual_metadata) != (source_messages, source_metadata):
            differences = [repr(key) for key in set(actual_messages) | set(source_messages)
                if actual_messages.get(key) != source_messages.get(key)]
            failure = {'source_commit': commit, 'path': name, 'changed_message_count': len(differences),
                'changed_message_keys': sorted(differences)[:20], 'generated_metadata': actual_metadata,
                'source_metadata': source_metadata, 'restored': False}
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(failure, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(failure), flush=True)
            raise AssertionError('Effective translated messages/locale metadata changed: ' + name)
        originals[name] = original
        entries.append({'path': name, 'generated_sha256': hashlib.sha256(current).hexdigest(),
            'source_sha256': hashlib.sha256(original).hexdigest(), 'compiled_messages_equivalent': True,
            'language_header': {'generated': generated_language, 'source': source_language},
            'language_selection': 'Catalog path/locale chooses the language; msgmerge --lang rewrites this informational header. Preserve the committed header.'})
    if args.restore_equivalent_generated:
        for name, original in originals.items():
            (source / name).write_bytes(original)
        assert not git('diff', '--name-only', commit, '--', 'po').strip()
    report = {'source_commit': commit, 'changed_catalogs': entries,
        'restored_equivalent_generated': args.restore_equivalent_generated,
        'source_translations_preserved': True,
        'template_sha256': hashlib.sha256(template.read_bytes()).hexdigest(),
        'comparison': 'Same msgmerge --for-msgfmt template path used by the actual GNU gettext .po.gmo build rule, then actual msgfmt output catalog messages and runtime locale metadata.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'catalogs_equivalent': len(entries), 'restored': args.restore_equivalent_generated,
        'source_commit': commit}), flush=True)


if __name__ == '__main__':
    main()
