"""M2 complete-workflow native acceptance on owned inactive Windows desktops.

Reuses the app-owned Qt event bridge and one isolated binary copy. Test profiles
are moved only after confirmed native exit; originals/delivered profiles are never
selected. No OS input, activation, desktop switching or execution-kill deadline.
"""
import argparse
import ctypes
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from ctypes import wintypes as W
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from PIL import Image
from app_icon_checks import executable_icon, window_icon
from isolated_desktop import IsolatedProcess, input_desktop, u, k
from settings_layout_checks import check_settings_layout

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--fixtures', type=Path, required=True)
parser.add_argument('--policies', type=Path, help='Native production-policy test executable from this same managed assembly')
parser.add_argument('--case', choices=['idle', 'welcome', 'shortcuts', 'onboarding-shortcuts', 'playback', 'subtitles', 'subtitles-mpv', 'preview', 'icons', 'sidebar', 'menus', 'settings', 'settings-survey', 'settings-backdrop', 'preview-icons', 'correction', 'updates', 'playback-subtitles', 'seek-policy', 'integration-diagnostic', 'subtitle-tracks-diagnostic', 'all'], default='all')
parser.add_argument('--preview-media', type=Path, help='Read-only actual reported media for preview acceptance')
parser.add_argument('--resume-settings-after-desktop-change', action='store_true',
    help='Resume the closed settings pass after its completed150%% matrix lost the input-desktop preservation check')
parser.add_argument('--resume-settings-history', action='store_true',
    help='Continue the closed settings pass at its unfinished history workflow')
parser.add_argument('--resume-settings-behaviour', action='store_true',
    help='Retain the completed100%% matrix and continue after the native option-browser count check')
parser.add_argument('--collect-settings-layouts', action='store_true',
    help='Keep the reproduced font/focus failures; collect remaining DPI/font/history checks without replaying100%% layouts')
parser.add_argument('--settings-input-repair', action='store_true',
    help='Verify repaired focus/input/save workflows and Privacy at all DPI values; reuse the reviewed unchanged category layouts')
parser.add_argument('--resume-settings-input',action='store_true',
    help='Continue the closed input repair after correcting Qt focus-proxy observation; retain completed100%% Privacy/focus evidence')
parser.add_argument('--resume-menu-quit',action='store_true',
    help='Retain the completed menu workflow and resume its closed clipped-viewport quit check')
parser.add_argument('--resume-idle-checker',action='store_true',
    help='Resume the closed idle pass after correcting its pre-dispatch observation target')
args = parser.parse_args()
root, source, fixtures = args.root.resolve(), args.runtime.resolve(), args.fixtures.resolve()
assert root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s8-')
resume_empty_survey=args.case=='settings-survey' and (root/'result.json').is_file()
resume_settings=args.resume_settings_after_desktop_change
resume_history=args.resume_settings_history
resume_behaviour=args.resume_settings_behaviour
collect_layouts=args.collect_settings_layouts
resume_input=args.resume_settings_input
resume_menu_quit=args.resume_menu_quit
resume_idle=args.resume_idle_checker
assert sum((resume_settings,resume_history,resume_behaviour,collect_layouts,resume_input,resume_menu_quit,resume_idle))<=1
assert not resume_idle or args.case=='idle'
assert not resume_menu_quit or args.case=='menus'
assert not (resume_settings or resume_history or resume_behaviour or collect_layouts) or args.case=='settings'
assert not args.settings_input_repair or (args.case=='settings' and not any((resume_settings,resume_history,resume_behaviour,collect_layouts)))
assert not resume_input or (args.case=='settings' and args.settings_input_repair)
assert not root.exists() or resume_empty_survey or resume_settings or resume_history or resume_behaviour or collect_layouts or resume_input or resume_menu_quit or resume_idle
assert fixtures.is_dir() and (source / 'portable').is_dir() and not any((source / 'portable').iterdir())
plugin = source / 'plugins/gui/libqt_plugin.dll'
assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
runtime = root / 'runtime'
if resume_idle:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='idle' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert set(previous['failures'])=={'idle'}
    resume_idle_stop='observation_cancelled_action_not_undone' in previous['failures']['idle']
    resume_idle_eof_viewport='clipped_target_rejected_before_dispatch' in previous['failures']['idle'] and 'after-eof-editor' in previous['failures']['idle']
    resume_idle_eof='Rendered loader source differs from the expected URL' in previous['failures']['idle'] or resume_idle_eof_viewport
    if resume_idle_stop or resume_idle_eof:
        assert len(previous['cases'])==2
        assert previous['cases'][0]['engine']=='vlc' and previous['cases'][0]['passed']
        assert previous['cases'][1]['engine']=='mpv'
        if resume_idle_stop:
            assert 'stop-video' in previous['failures']['idle'] and previous['cases'][1]['steps'][-2]['label']=='video-surface'
            proof=json.loads((root/'idle-customization-mpv-resumed/evidence/053b2d2db82143ce953167e5075feaa2.json').read_text())
            assert proof['core']['state']==0 and not proof['core']['audio_tracks'] and not proof['core']['video_tracks']
            assert proof['observation_boundary']=='UI dispatcher during pending observation; no new frame awaited'
        else:
            if resume_idle_eof_viewport:
                assert previous['cases'][1]['steps'][-2]['label']=='after-eof-menu'
                assert any(row['label']=='natural-eof' for row in previous['cases'][1]['steps'])
            else:
                assert 'natural-eof' in previous['failures']['idle'] and previous['cases'][1]['steps'][-2]['label']=='play-to-eof'
                assert {'empty-cancel-cone','empty-escape-cone','empty-save-cone','paused-artwork','video-surface','stopped-video-cone'} <= {row['label'] for row in previous['cases'][1]['steps']}
    else:
        assert 'Expected one observation target; matched 0' in previous['failures']['idle']
        assert len(previous['cases'])==1 and previous['cases'][0]['steps'][-2]['label']=='empty-cancel-menu'
    assert all(row['exit_code']==0 and row['owned_desktop_never_observed_as_input'] for row in previous['cases'])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/('result-before-idle-eof-viewport.json' if resume_idle_eof_viewport else 'result-before-idle-eof-observer.json' if resume_idle_eof else 'result-before-idle-stop-observer.json' if resume_idle_stop else 'result-before-idle-checker.json')
    assert not historical.exists(),'Continue original idle checker repair'
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_menu_quit:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='menus' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert set(previous['failures'])=={'menus'} and 'clipped_target_rejected_before_dispatch' in previous['failures']['menus']
    assert 'quit-native-menu-settings' in previous['failures']['menus'] and len(previous['cases'])==2
    completed,clipped=previous['cases']
    assert completed['name']=='figma-player-menus' and completed['passed'] and completed['exit_code']==0
    assert completed['native_command_menu_composition'] and len(completed['native_submenu_composition'])>len(completed['native_command_menu_composition'])
    assert clipped['name']=='native-menu-open-quit' and clipped['exit_code']==0 and clipped['owned_desktop_never_observed_as_input']
    assert clipped['steps'][-2]['label']=='quit-native-menu-main-menu'
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/'result-before-menu-quit-viewport.json'
    assert not historical.exists(),'Resume the original viewport correction'
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_input:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['source_commit']=='c1380668f2f89dcc6531cd3e0e9dfe3cfa784d18'
    assert previous['scope']=='settings' and not previous['passed']
    if not previous['protected_profiles_unchanged']:
        witness_path=root/'external-nuvio-change.json'
        witness=json.loads(witness_path.read_text(encoding='utf-8'))
        assert witness['source_result_sha256']==hashlib.sha256((root/'result.json').read_bytes()).hexdigest()
        assert witness['no_vlc_processes'] and witness['all_owned_native_cases_closed0'] and witness['vlc_profiles_and_windows_language_unchanged']
        assert set(previous['failures'])=={'settings','protected_profiles'}
    else:assert set(previous['failures'])=={'settings'}
    input_disclosure_recovery=previous['failures']['settings']=="AssertionError(('value-extra-options', []))"
    assert len(previous['cases'])==(2 if input_disclosure_recovery else 1)
    completed=previous['cases'][0]
    assert completed['name']=='settings-1' and completed['exit_code']==0 and completed['owned_desktop_never_observed_as_input']
    assert completed['category_selection_focus']['passed'] and not completed['passed']
    if input_disclosure_recovery:
        failed=previous['cases'][-1]
        assert failed['name']=='settings-1-input-behaviour-resumed' and failed['exit_code']==0 and failed['owned_desktop_never_observed_as_input']
        before=next(row for row in failed['steps'] if row['label']=='save-advanced-reveal-locate')
        after=next(row for row in failed['steps'] if row['label']=='save-advanced')
        for step,checked in ((before,True),(after,False)):
            observed=json.loads((root/step['response']).read_text(encoding='utf-8'))
            assert next(row for row in observed['widgets'] if row['id']=='preferencesAdvanced0')['checked'] is checked
    else:
        assert 'Expected one snapshot Tab target' in previous['failures']['settings']
        assert completed['steps'][-2]['label'].startswith('snapshot-dimensions-reveal-scroll-')
        observation=json.loads((root/completed['steps'][-2]['response']).read_text(encoding='utf-8'))
        focused=[row for row in observation['widgets'] if row['focused']]
        assert len(focused)==2 and focused[0]['id']=='preferencesCategories' and focused[1]['parent']==focused[0]['node']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/('result-before-disclosure-checker.json' if input_disclosure_recovery else 'result-before-focus-proxy-checker.json')
    assert not historical.exists(),'Continue the original input-checker recovery'
    historical.write_bytes((root/'result.json').read_bytes())
elif collect_layouts:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='settings' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert previous['failures']=={'settings-category-focus':['Mouse did not clear the keyboard-only outline'],'settings':'AssertionError()'}
    assert len(previous['cases'])==2 and previous['cases'][-1]['name']=='settings-1-behaviour-resumed'
    assert all(case['exit_code']==0 and case['owned_desktop_never_observed_as_input'] for case in previous['cases'])
    stopped=previous['cases'][-1]
    assert stopped['steps'][-2]['label']=='native-track-invalid-save'
    response=json.loads((root/stopped['steps'][-2]['response']).read_text(encoding='utf-8'))
    assert any(row['type']=='QMessageBox' and row['name']=='Invalid font size' for row in response['widgets'])
    assert any(row['id']=='value-audio-track' and row['text']=='-' for row in response['widgets'])
    completed=previous['cases'][0]
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/'result-before-font-size-blocker.json'
    assert not historical.exists(),'Keep the original remaining-layout collection'
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_behaviour:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='settings' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert previous['failures']=={'settings-category-focus':['Mouse did not clear the keyboard-only outline'],'settings':'AssertionError()'}
    assert len(previous['cases'])==1
    completed=previous['cases'][0]
    assert completed['name']=='settings-1' and completed['exit_code']==0 and completed['owned_desktop_never_observed_as_input']
    assert completed['steps'][-2]['label']=='all-settings-browser' and completed['steps'][-1]['label']=='quit'
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/'result-before-native-browser-count.json'
    assert not historical.exists(),'Continue the original behaviour recovery instead of duplicating it'
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_history:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='settings' and not previous['passed'] and previous['protected_profiles_unchanged']
    failure=previous['failures']
    assert set(failure)=={'settings'} and any(label in failure['settings'] for label in ('history-recent','history-expand-library')) and 'Expected one observation target; matched 0' in failure['settings']
    history_view_recovery=previous['cases'][-1]['name']=='settings-clear-history-resumed'
    assert previous['cases'][-1]['name'] in ('settings-clear-history','settings-clear-history-resumed')
    assert previous['cases'][-1]['exit_code']==0 and previous['cases'][-1]['input_desktop_preserved']
    assert previous['cases'][-1]['steps'][-2]['label']=='history-library-mounted'
    assert all(case['passed'] and case['exit_code']==0 for case in previous['cases'][:-1])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/('result-before-history-view-target.json' if history_view_recovery else 'result-before-history-navigation.json')
    assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_settings:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    historical=root/'result-before-desktop-change.json'
    resume_external_transition=historical.exists()
    if resume_external_transition:
        # The first bounded closure probe reproduced the same equality error.
        # Preserve it before using the corrected no-activation predicate.
        assert previous['failures']=={'settings':"AssertionError('Input desktop unexpectedly changed')"}
        assert previous['cases'][-1]['name']=='settings-1-5-lifecycle'
        assert previous['cases'][-1]['exit_code']==0 and not previous['cases'][-1]['input_desktop_preserved']
        assert previous['protected_profiles_unchanged']
        closure_history=root/'result-lifecycle-before-desktop-transition-handling.json'
        assert not closure_history.exists()
        closure_history.write_bytes((root/'result.json').read_bytes())
        previous=json.loads(historical.read_text(encoding='utf-8'))
    assert previous['scope']=='settings' and not previous['passed']
    assert previous['failures']=={'settings':"AssertionError('Input desktop unexpectedly changed')"}
    assert previous['protected_profiles_unchanged']
    assert previous['verification_helper_sha256']=='f7e57eda4e3fd0022a9b833c07314e1217388e69004018ee190e9ff24c990fb7'
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert [case['name'] for case in previous['cases']]==['settings-1',
        'saved-extra-startup-vlc','explicit-extra-priority-vlc',
        'saved-extra-startup-mpv','explicit-extra-priority-mpv','settings-1-5']
    assert all(case['passed'] and case['exit_code']==0 for case in previous['cases'][:-1])
    completed=previous['cases'][-1]
    assert completed['exit_code']==0 and completed['input_desktop_preserved'] is False
    assert completed['steps'][-2]['label']=='close-settings-False' and completed['steps'][-1]['label']=='quit'
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    if not resume_external_transition:
        historical.write_bytes((root/'result.json').read_bytes())
elif resume_empty_survey:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='settings-survey' and previous['diagnostic_only'] and not previous['cases']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/'result-empty-dispatch.json'
    assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
else:
    root.mkdir()
    shutil.copytree(source, runtime, ignore=lambda path, names: ['sdk'] if Path(path).resolve() == source else [])
portable = runtime / 'portable'
repo = Path(__file__).resolve().parents[2]
inspector = Path(__file__).with_name('inspect-player.py')
records = {'schema': 'vlc_redesign.m2_native_acceptance.v1', 'scope': args.case,
    'qt_plugin_sha256': hashlib.sha256(plugin.read_bytes()).hexdigest(), 'cases': [],
    'no_os_input_or_desktop_switching': True, 'passed': False}
records['verification_helper_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
records['source_commit']=json.loads((source/'VLC-PLUGIN-BUILDINFO.json').read_text())['source_commit']
version_header=subprocess.check_output(['git','-C',str(repo),'show',records['source_commit']+':modules/gui/qt/dialogs/help/fork_release.hpp'],text=True)
fork_version=re.search(r'currentVersion\[\] = "([0-9.]+)"',version_header).group(1)
newer_version='.'.join(map(str,(*map(int,fork_version.split('.')[:2]),int(fork_version.split('.')[2])+1)))
production=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',records['source_commit'],'--',
    'include','src','lib','compat','modules','share','configure.ac','Makefile.am','extras/package/win32'])
records['production_tree_sha256']=hashlib.sha256(production).hexdigest()
if resume_idle:
    assert previous['source_commit']==records['source_commit'] and previous['production_tree_sha256']==records['production_tree_sha256']
    records['resumed_idle_checker']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'stop_observer_repair':resume_idle_stop,'eof_observer_repair':resume_idle_eof}
    if resume_idle_stop or resume_idle_eof:records['cases']=[previous['cases'][0]]
elif resume_menu_quit:
    assert previous['source_commit']==records['source_commit'] and previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=[previous['cases'][0]]
    records['resumed_menu_quit']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'source_commit':records['source_commit'],
        'scope':'Retain the completed full menu/native submenu/normal exit workflow. The new quit case was rejected before Settings dispatch because its viewport clipped the menu. Fresh quit with the same reference viewport follows; the failed original remains unchanged.'}
elif resume_input:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases']
    records['reused_input_layouts']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'source_commit':records['source_commit'],'case':'settings-1','original_case_passed':False,
        'scope':'Completed100% Privacy layout/scroll/theme and category mouse/Tab/mouse paint checks. Original failed overall/cases remain false. Canonical focus ownership and observed disclosure state replace invalid checker assumptions; fresh complete behaviour/save/restart and remaining DPI workflows follow.'}
    if input_disclosure_recovery:records['reused_input_layouts']['previous_recovery']=previous['reused_input_layouts']
    if not previous['protected_profiles_unchanged']:
        records['external_profile_rebaseline']={'witness':str(witness_path),
            'witness_sha256':hashlib.sha256(witness_path.read_bytes()).hexdigest(),
            'scope':'Original failed full comparison remains false. External Nuvio changes continued after VLC exit. A fresh full protected-profile baseline is required and is compared normally at this continuation end; no path is excluded.'}
elif collect_layouts:
    assert previous['source_commit']==records['source_commit'] and previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases']
    records['failures']=previous['failures']
    records['reused_settings_rendering']=previous['reused_settings_rendering']
    records['incomplete_behaviour_preserved']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'source_commit':records['source_commit'],
        'reason':'The displayed125% custom font value is rejected on later Save. Preserve the actual font/focus failures and collect only independent remaining DPI/font/history checks before one coherent source rebuild.'}
elif resume_behaviour:
    assert previous['source_commit']==records['source_commit'] and previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases']
    records['failures']={'settings-category-focus':previous['failures']['settings-category-focus']}
    records['reused_settings_rendering']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'case':'settings-1','rendering_assertions_completed':True,'original_case_passed':False,
        'limits':'The complete100% theme/viewport/category matrix is retained. Mouse-return focus remains failed; the later browser-count assertion is corrected against native shortcut declarations. Resume behaviour and remaining DPI/font/history workflows without replaying that matrix.'}
elif resume_history:
    assert previous['source_commit']==records['source_commit']
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases'][:-1]
    records['reused_settings_rendering']=previous['reused_settings_rendering']
    records['resumed_history_navigation']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'Observe the actually mounted compactLibrary/fullLibrary owner after EOF. Recent and native history clearing work in either layout; retain completed layout/behavior/font checks.'}
elif resume_settings:
    assert previous['source_commit']==records['source_commit']
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases'][:-1]
    records['reused_settings_rendering']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'case':'settings-1-5','rendering_assertions_completed':True,
        'original_input_desktop_preserved':False,
        'original_case_passed':False,
        'limits':'All150% layout/scroll assertions completed before clean exit0; the input desktop changed. Preserve that historical failure and independently recheck150% owned lifecycle against no activation. User lock/unlock is not a test-desktop activation. Do not replay its completed layout matrix.'}
    if resume_external_transition:
        records['reused_settings_rendering']['historical_closure_probe']=str(closure_history)
        records['reused_settings_rendering']['historical_closure_probe_sha256']=hashlib.sha256(closure_history.read_bytes()).hexdigest()


def profiles():
    spec=importlib.util.spec_from_file_location('installed_profile',Path(__file__).with_name('check-installed-profile.py'))
    helper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    result=helper.snapshot(include_nuvio=True)
    folder=Path('D:/VLC-Redesign/releases/1.1.1/Modern-VLC-Fork-1.1.1-win64-portable/portable')
    result['delivered_portable']=[helper.file_record(file) for file in sorted(folder.rglob('*')) if file.is_file()]
    return result


records['protected_profiles_before'] = profiles()
active_cases=set()

def save():
    (root / 'result.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

class Peer(BaseHTTPRequestHandler):
    mode = 'current'
    calls = []
    def do_GET(self):
        if self.path=='/english.srt':
            Peer.calls.append({'mode':'remote-subtitle','path':self.path})
            payload=(fixtures/'english.srt').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','application/x-subrip')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        assert self.path == '/releases/latest'
        Peer.calls.append({'mode': Peer.mode, 'path': self.path})
        payload = (fixtures / 'github-latest.json').read_bytes()
        item=json.loads(payload)
        old=item['tag_name'][len('redesign-v'):]
        payload=json.dumps(item).replace('redesign-v'+old,'redesign-v'+fork_version).replace('Modern-VLC-Fork-'+old,'Modern-VLC-Fork-'+fork_version).encode('utf-8')
        status = 200
        if Peer.mode == 'unavailable': status, payload = 503, b'Unavailable test peer'
        elif Peer.mode == 'malformed': payload = b'{broken'
        elif Peer.mode == 'newer':
            item = json.loads(payload)
            old = item['tag_name'][len('redesign-v'):]
            encoded = json.dumps(item).replace('redesign-v' + old, 'redesign-v'+newer_version).replace('Modern-VLC-Fork-' + old, 'Modern-VLC-Fork-'+newer_version)
            payload = encoded.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def log_message(self, *values): pass

server = ThreadingHTTPServer(('127.0.0.1', 0), Peer)
server.daemon_threads = True
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

class Case:
    def __init__(self, name, *, scale='1', engine='vlc', welcome=False, media=None, updates=False, live_updates=False, reused_profile=None, extra=()):
        self.path = root / name
        assert not self.path.exists()
        self.path.mkdir()
        for name in ('evidence', 'tmp', 'qml'): (self.path / name).mkdir()
        self.evidence = self.path / 'evidence'
        self.session = self.evidence / 'session.json'
        self.record = {'name': self.path.name, 'scale': scale, 'engine': engine, 'steps': [], 'passed': False}
        records['cases'].append(self.record)
        assert portable.resolve().is_relative_to(root) and not any(portable.iterdir())
        if reused_profile:
            assert reused_profile.resolve().is_relative_to(root)
            shutil.copytree(reused_profile, portable, dirs_exist_ok=True)
        self.token = uuid.uuid4().hex + uuid.uuid4().hex
        env = {name: value for name, value in os.environ.items() if not name.startswith('VLC_PLAYER_DIAGNOSTICS')}
        for name in ('VLC_PLUGIN_PATH', 'QT_SCREEN_SCALE_FACTORS', 'LC_ALL', 'LC_MESSAGES', 'LANGUAGE'): env.pop(name, None)
        env.update(TEMP=str(self.path / 'tmp'), TMP=str(self.path / 'tmp'), VLC_DATA_PATH=str(runtime),
            VLC_USERDATA_PATH=str(portable), QML_DISK_CACHE_PATH=str(self.path / 'qml'), QT_DISABLE_SHADER_DISK_CACHE='1',
            QSG_RHI_DISABLE_SHADER_DISK_CACHE='1', QT_FORCE_STDERR_LOGGING='1', QT_ENABLE_HIGHDPI_SCALING='0',
            QT_FONT_DPI='96', QT_SCALE_FACTOR=scale, VLC_PLAYER_DIAGNOSTICS_DIR=str(self.evidence),
            VLC_PLAYER_DIAGNOSTICS_TOKEN=self.token, VLC_PLAYER_DIAGNOSTICS_BUILD=records['qt_plugin_sha256'])
        if not live_updates: env['VLC_PLAYER_DIAGNOSTICS_UPDATE_URL'] = 'http://127.0.0.1:' + str(server.server_port) + '/releases/latest'
        command = [str(runtime / 'vlc.exe'), '--intf=qt', '--language=en', '--no-one-instance', '--no-plugins-cache',
            '--no-metadata-network-access', '--restore-playback-pos=0', '--no-volume-save', '--mmdevice-volume=0',
            '--aout=mmdevice', '--mmdevice-backend=wasapi', '--no-video-title-show', '--start-paused',
            '--qt-playback-engine=' + engine, '--verbose=2', '--file-logging', '--log-verbose=2',
            '--logfile=' + str(self.evidence / 'native-ui.log')]
        if not welcome: command.append('--no-qt-privacy-ask')
        if not updates: command.append('--no-qt-updates-notif')
        command.extend(extra)
        if media: command.append(str(media))
        (self.evidence / 'launch-argv.json').write_text(json.dumps(command, indent=2) + '\n')
        self.stdout = (self.evidence / 'stdout.log').open('wb')
        self.stderr = (self.evidence / 'stderr.log').open('wb')
        self.player = IsolatedProcess(command, runtime, env, self.stdout, self.stderr)
        active_cases.add(self)
        self.session.write_text(json.dumps({'pid': self.player.pid, 'executable': str(runtime / 'vlc.exe'), 'token': self.token}))
        self.closed = False
        save()

    def inspect(self, label, op='snapshot', *options):
        if not self.record['steps'] and label != 'view-mounted' and op != 'quit':
            self.inspect('view-mounted','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
        if op=='click' and '--name' in options:
            name=options[options.index('--name')+1]
            if name in ('Show Subtitle Timeline on Seekbar','VLC','MPV'):
                self.inspect(label+'-reveal','focus','--name',name)
        self.record['pending'] = {'label': label, 'op': op, 'options': list(map(str, options))}
        save()
        command = [sys.executable, '-B', str(inspector), '--session', str(self.session), op, *map(str, options)]
        before = time.perf_counter_ns()
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
        elapsed = (time.perf_counter_ns() - before) / 1000000.
        (self.evidence / (label + '.client.log')).write_text(process.stdout + process.stderr, encoding='utf-8')
        assert process.returncode == 0, (label, process.stdout, process.stderr)
        path = Path(re.search(r'^Response: (.+)$', process.stdout, re.M).group(1).strip())
        result = json.loads(path.read_text(encoding='utf-8'))
        assert not result.get('qml_errors'), (label, result.get('qml_errors'))
        assert '"before": false, "after": false' in process.stdout, 'Owned player gained OS foreground'
        self.record['steps'].append({'label': label, 'response': str(path.relative_to(root)), 'client_elapsed_ms': elapsed})
        self.record.pop('pending', None)
        save()
        print(json.dumps({'case': self.path.name, 'step': label, 'status': result['status']}), flush=True)
        return result

    def click(self, label, target, *options): return self.inspect(label, 'click', '--target', target, *options)
    def native(self, label, target, *options): return self.inspect(label, 'widget_click', '--target', target, *options)
    def reveal(self,label,target,scroll):
        snapshot=self.inspect(label+'-locate','snapshot')
        seen=set()
        while True:
            widgets={item['node']:item for item in snapshot['widgets']}
            found=[item for item in widgets.values() if item['id']==target]
            assert len(found)==1,(target,found)
            if found[0]['center_visible']:return snapshot
            area=next(item for item in widgets.values() if item['id']==scroll)
            state=area['scroll_value']
            assert state not in seen,('native control cannot be revealed',target,area)
            seen.add(state)
            def y(item):
                result=item['y']
                while item['parent']>=0:
                    item=widgets[item['parent']];result+=item['y']
                return result
            delta=120 if y(found[0])<y(area) else -120
            snapshot=self.inspect(label+'-scroll-'+str(len(seen)),'widget_scroll','--target',scroll,'--delta',str(delta))
    def key(self, label, key, *, target='playButton', modifiers=0, text='', **unused):
        self.inspect(label + '-focus', 'focus', '--target', target)
        return self.inspect(label, 'key', '--target', target, '--key', hex(key), '--modifiers', hex(modifiers), '--text', text)
    def close(self, passed=False):
        if self.closed: return
        try:
            if k.WaitForSingleObject(self.player.handle, 0) != 0: self.inspect('quit', 'quit')
        finally:
            try:
                # Every app-owned event independently rejects OS foreground.
                # A user lock/unlock may change the input desktop while this
                # unrelated inactive desktop is running. Record that transition
                # truthfully instead of requiring the user's desktop to freeze.
                self.player.wait(permit_external_desktop_transition=True)
            finally:
                # A user/screensaver transition can fail the preservation
                # assertion after native exit and handle closure. Retain that
                # failure, but still record known exit and release our profile.
                if self.player.resources_closed:
                    self.record['exit_code'] = self.player.exit_code
                    active_cases.remove(self)
                    self.closed = True
                    self.stdout.close(); self.stderr.close()
                    target = self.path / 'profile'
                    assert not target.exists() and portable.resolve().is_relative_to(root) and target.resolve().is_relative_to(root)
                    portable.rename(target)
                    portable.mkdir()
                    current=input_desktop()
                    self.record['input_desktop_before'] = self.player.before
                    self.record['input_desktop_after'] = current
                    self.record['input_desktop_preserved'] = current == self.player.before
                    self.record['owned_desktop_never_observed_as_input'] = current != self.player.desktop_name
                    self.record['passed'] = passed and self.player.exit_code == 0 and self.record['owned_desktop_never_observed_as_input']
                    save()
            assert self.record['exit_code'] == 0, self.record

def nodes(snapshot, identity): return [node for node in snapshot['tree'] if node['id'] == identity and node['visible']]
def service(snapshot, name='redesignMediaTools'): return snapshot['media_tools'][name]


def verify_executable_icon():
    records['executable_icon']=executable_icon(runtime/'vlc.exe',repo/'share/icons/vlc.ico')


def owned_main_window(case, snapshot):
    u.GetAncestor.argtypes=[W.HWND,W.UINT]
    u.GetAncestor.restype=W.HWND
    hwnd=u.GetAncestor(W.HWND(int(snapshot['window']['native_id_hex'],16)),2)
    assert hwnd, 'Qt surface has no native root window'
    pid=W.DWORD()
    u.GetWindowThreadProcessId(W.HWND(hwnd),ctypes.byref(pid))
    assert pid.value==case.player.pid, 'Native root belongs to a different process'
    return W.HWND(hwnd)


def owned_native_read(case, reader):
    """Bind a new reader thread to the owned inactive desktop, without switching it."""
    before=input_desktop()
    u.GetThreadDesktop.argtypes=[W.DWORD]
    u.GetThreadDesktop.restype=W.HANDLE
    u.SetThreadDesktop.argtypes=[W.HANDLE]
    u.SetThreadDesktop.restype=W.BOOL
    def read():
        original=u.GetThreadDesktop(k.GetCurrentThreadId())
        assert original and u.SetThreadDesktop(case.player.desktop),ctypes.WinError(ctypes.get_last_error())
        u.SetThreadDpiAwarenessContext.argtypes=[W.HANDLE]
        u.SetThreadDpiAwarenessContext.restype=W.HANDLE
        dpi_context=u.SetThreadDpiAwarenessContext(W.HANDLE(-4))
        assert dpi_context,ctypes.WinError(ctypes.get_last_error())
        try:return reader()
        finally:
            assert u.SetThreadDpiAwarenessContext(dpi_context),ctypes.WinError(ctypes.get_last_error())
            assert u.SetThreadDesktop(original),ctypes.WinError(ctypes.get_last_error())
    with ThreadPoolExecutor(max_workers=1) as worker:
        result=worker.submit(read).result()
    assert input_desktop()==before
    return result


def verify_window_icon(case, snapshot):
    case.record['native_window_icon']=owned_native_read(case,lambda:window_icon(owned_main_window(case,snapshot),case.player.pid,
        repo/'modules/gui/qt/pixmaps/redesign/app.png',case.evidence/'native-window-icon.png'))


def settings_window_region(case, dialog):
    """Reject the legacy raster/region path without claiming composed pixels."""
    ready=case.inspect('content-backdrop-'+dialog['native_id'],'snapshot',
        '--await-service','nativeBackdrop','--await-property','status',
        '--await-value','["ready","failed","unavailable"]','--await-comparison','one_of')
    assert ready['native_backdrop_state']=='ready',ready.get('widgets')
    dialog=next(row for row in ready['widgets'] if row.get('native_id')==dialog['native_id'])
    assert dialog['surface_alpha_bits']>=8,'Settings native surface was created without an alpha channel'
    assert dialog['surface_type']==6,'Settings must present a Direct3D composition surface'
    assert dialog['backdrop_requested'],'Native backdrop request failed'
    assert dialog['content_backdrop_ready'],'The live content visual was not committed'
    content=dialog['content_backdrop']
    assert content['hresult']==0 and content['source_pid']==case.player.pid and content['live_window_content']
    assert content['source_native_id']!=dialog['native_id'],'A backdrop must not sample itself'
    assert abs(content['sigma_px']-25*dialog['dpr'])<.01
    radius=14 if dialog['type'] in ('PrefsDialog','QMenu','VLCMenu') else 6
    assert abs(content['radius_px']-radius*dialog['dpr'])<.01,(dialog['type'],content)
    def read():
        hwnd=W.HWND(int(dialog['native_id'],16))
        pid=W.DWORD()
        u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        assert pid.value==case.player.pid
        gdi=ctypes.WinDLL('gdi32',use_last_error=True)
        gdi.CreateRectRgn.argtypes=[ctypes.c_int]*4
        gdi.CreateRectRgn.restype=W.HANDLE
        gdi.PtInRegion.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_int]
        gdi.PtInRegion.restype=W.BOOL
        gdi.GetRgnBox.argtypes=[W.HANDLE,ctypes.POINTER(W.RECT)]
        gdi.DeleteObject.argtypes=[W.HANDLE]
        u.GetWindowRgn.argtypes=[W.HWND,W.HANDLE]
        region=gdi.CreateRectRgn(0,0,0,0)
        assert region
        try:
            assert u.GetWindowRgn(hwnd,region)==0,'An integer region still clips the antialiased corners'
            u.GetWindowLongPtrW.argtypes=[W.HWND,ctypes.c_int]
            u.GetWindowLongPtrW.restype=ctypes.c_ssize_t
            style=u.GetWindowLongPtrW(hwnd,-20)
            assert not style & 0x80000,'Settings still uses a legacy layered bitmap'
            assert style & 0x200000,'Settings has no composition-only native surface'
            dwm=ctypes.WinDLL('dwmapi',use_last_error=True)
            dwm.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
            dwm.DwmGetWindowAttribute.restype=ctypes.c_long
            corners=W.DWORD()
            assert dwm.DwmGetWindowAttribute(hwnd,33,ctypes.byref(corners),ctypes.sizeof(corners))==0
            assert corners.value==1,'A second system corner clip is still enabled'
            border=W.DWORD()
            border_hr=dwm.DwmGetWindowAttribute(hwnd,34,ctypes.byref(border),ctypes.sizeof(border))
            # Windows accepts setting DWMWA_BORDER_COLOR but this host rejects
            # its getter with E_INVALIDARG (independently reproduced). An
            # unavailable readback is not a failed setter or pixel evidence.
            assert border_hr in (0,ctypes.c_long(0x80070057).value),hex(border_hr&0xffffffff)
            if border_hr==0:
                assert border.value==0xfffffffe,'A system border still paints outside the content clip'
            return {'native_id':dialog['native_id'],'region':'none','extended_style':hex(style),
                'system_corner_preference':corners.value,
                'system_border_color':hex(border.value) if border_hr==0 else None,
                'system_border_query_hresult':hex(border_hr&0xffffffff),
                'single_content_clip':content,'actual_corner_pixels_verified':False,
                'limit':'Native composition configuration; border getter may be unsupported. Actual composed corner/border pixels remain a separate required gate.'}
        finally:gdi.DeleteObject(region)
    return owned_native_read(case,read)


def assert_window(case, snapshot):
    return owned_native_read(case,lambda:assert_window_on_desktop(case,snapshot))


def assert_window_on_desktop(case, snapshot):
    window = snapshot['window']
    hwnd = owned_main_window(case,snapshot)
    actual_pid = W.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(actual_pid))
    assert actual_pid.value == case.player.pid
    # These read-only calls use physical pixels for both rectangles. They do
    # not change the app's DPI mode or any global Windows display setting.
    u.SetThreadDpiAwarenessContext.argtypes = [W.HANDLE]
    u.SetThreadDpiAwarenessContext.restype = W.HANDLE
    original = u.SetThreadDpiAwarenessContext(W.HANDLE(-4))
    class MonitorInfo(ctypes.Structure):
        _fields_ = [('size', W.DWORD), ('monitor', W.RECT), ('work', W.RECT), ('flags', W.DWORD)]
    u.MonitorFromWindow.argtypes = [W.HWND, W.DWORD]
    u.MonitorFromWindow.restype = W.HANDLE
    u.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
    u.GetMonitorInfoW.argtypes = [W.HANDLE, ctypes.POINTER(MonitorInfo)]
    rect, visible, monitor = W.RECT(), W.RECT(), MonitorInfo()
    monitor.size = ctypes.sizeof(monitor)
    try:
        assert u.GetWindowRect(hwnd, ctypes.byref(rect))
        dwm=ctypes.WinDLL('dwmapi',use_last_error=True)
        dwm.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
        dwm.DwmGetWindowAttribute.restype=ctypes.c_long
        assert dwm.DwmGetWindowAttribute(hwnd,9,ctypes.byref(visible),ctypes.sizeof(visible))==0
        handle = u.MonitorFromWindow(hwnd, 2)
        assert u.GetMonitorInfoW(handle, ctypes.byref(monitor))
        # GetWindowRect includes Windows' invisible resize borders. The DWM
        # extended frame is the visible frame/chrome required to fit the screen.
        assert visible.left >= monitor.work.left and visible.top >= monitor.work.top and visible.right <= monitor.work.right and visible.bottom <= monitor.work.bottom, (list((visible.left,visible.top,visible.right,visible.bottom)), list((monitor.work.left,monitor.work.top,monitor.work.right,monitor.work.bottom)))
    finally:
        if original: u.SetThreadDpiAwarenessContext(original)
    case.record.setdefault('window_checks', []).append({'qt': window, 'physical': [rect.left,rect.top,rect.right,rect.bottom],
        'visible_physical':[visible.left,visible.top,visible.right,visible.bottom],
        'work': [monitor.work.left,monitor.work.top,monitor.work.right,monitor.work.bottom]})

def welcome():
    def wizard_capture(case, label, option):
        case.inspect(label+'-reveal','focus','--target','onboardingShortcut_'+option)
        result=case.click(label,'onboardingShortcut_'+option,'--capture')
        assert nodes(result,'onboardingShortcutCapture')[0]['focused']
        assert not any(w['id'] in ('redesignPreferences','keyInputDialog') for w in result['widgets'])
        return result
    def wizard_key(case,label,key,modifiers=0,text=''):
        result=case.inspect(label,'key','--target','onboardingShortcutCapture','--key',hex(key),'--modifiers',hex(modifiers),'--text',text)
        assert not any(w['id'] in ('redesignPreferences','keyInputDialog') for w in result['widgets'])
        return result
    for scale in ('1', '1.5', '2'):
        case = Case('welcome-' + scale.replace('.', ''), scale=scale, welcome=True)
        try:
            initial = case.inspect('welcome', 'snapshot', '--capture')
            assert initial['customization']['onboardingVisible']
            assert_window(case, initial)
            verify_window_icon(case, initial)
            for identity in ('onboardingNext','onboardingSkip'):
                control = nodes(initial, identity)
                assert len(control) == 1 and control[0]['width'] > 0 and control[0]['height'] > 0
                assert control[0]['x'] >= 0 and control[0]['y'] >= 0 and control[0]['x']+control[0]['width'] <= initial['window']['width']+1 and control[0]['y']+control[0]['height'] <= initial['window']['height']+1
            case.inspect('reveal-optional-folder','focus','--target','onboardingFolder','--capture')
            case.click('theme-page', 'onboardingNext')
            case.click('font-page', 'onboardingNext')
            case.inspect('reveal-font-choice','focus','--target','onboardingFontFallback')
            shortcuts = case.click('shortcut-page', 'onboardingFontFallback', '--capture')
            assert nodes(shortcuts,'onboardingNext')[0]['text']=='Finish'
            assert not any(n['visible'] for n in nodes(shortcuts,'onboardingSkip'))
            face=nodes(shortcuts,'onboardingKeyFace_key-play-pause_0')[0]
            shadow=nodes(shortcuts,'onboardingKeyShadow_key-play-pause_0')[0]
            key_scale=face['height']/42
            assert abs(shadow['y']-face['y']-6*key_scale)<0.1
            caption=nodes(shortcuts,'onboardingShortcutCaption_key-play-pause')[0]
            # Popup itself is a QObject; only its rendered children are in
            # the QQuickItem tree. Its 40px window inset determines the width.
            if shortcuts['window']['width']>=1040*key_scale:
                assert abs(face['x']-caption['x']-240*key_scale)<0.1, 'The label must not stretch and push keycaps right'
            assert nodes(shortcuts,'onboardingKeyLabel_key-toggle-fullscreen_0')[0]['text']=='F'
            left=nodes(shortcuts,'onboardingShortcut_key-jump-short')[0]
            right=nodes(shortcuts,'onboardingShortcut_key-jump+short')[0]
            assert abs(left['y']-right['y'])<0.1 and right['x']>left['x']+left['width']
            assert nodes(shortcuts,'onboardingKeyLabel_key-jump-short_1')[0]['text']=='←'
            assert nodes(shortcuts,'onboardingKeyLabel_key-snapshot_0')[0]['text']=='SHIFT'
            assert nodes(shortcuts,'onboardingKeyLabel_key-snapshot_1')[0]['text']=='S'
            case.record['shortcut_visual_contract']={'key_face':face,'lower_edge':shadow,'paired_left':left,'paired_right':right,
                'reference_frame':'1902:6770','rendered_comparison_required':True}
            for option in ('key-toggle-fullscreen','qt-key-toggle-browser','qt-key-toggle-queue'):
                assert len(nodes(shortcuts, 'onboardingShortcut_' + option)) == 1
                revealed=case.inspect('reveal-shortcut-'+option,'focus','--target','onboardingShortcut_'+option,'--capture')
                item=nodes(revealed,'onboardingShortcut_'+option)[0]
                assert 0<=item['y'] and item['y']+item['height']<=revealed['window']['height']
            if scale == '1':
                wizard_capture(case,'edit-fullscreen','key-toggle-fullscreen')
                wizard_key(case,'capture-fullscreen',0x39,0xe000000,'9')
                case.click('assign-fullscreen','onboardingShortcutAssign')
                wizard_capture(case,'unset-browser','qt-key-toggle-browser')
                case.click('unset-browser-key','onboardingShortcutUnset')
                unassigned = case.inspect('unassigned-is-editable')
                assert any(node['visible'] and node.get('text') == 'Unassigned' for node in unassigned['tree'])
                wizard_capture(case,'assign-unassigned-browser','qt-key-toggle-browser')
                conflict=wizard_key(case,'capture-stream-conflict',0x53,0x4000000,'s')
                assert 'Stream' in nodes(conflict,'onboardingShortcutConflict')[0]['text']
                assert nodes(conflict,'onboardingShortcutAssign')[0]['text']=='Reassign'
                case.click('reassign-stream-to-browser','onboardingShortcutAssign')
                wizard_capture(case,'assign-browser','qt-key-toggle-browser')
                wizard_key(case,'capture-browser',0x38,0xe000000,'8')
                case.click('assign-browser','onboardingShortcutAssign')
                wizard_capture(case,'conflicting-browser','qt-key-toggle-browser')
                conflict=wizard_key(case,'conflict-fullscreen',0x39,0xe000000,'9')
                assert nodes(conflict,'onboardingShortcutConflict')[0]['text']
                case.click('cancel-conflict','onboardingShortcutCancel')
                wizard_capture(case,'escape-capture','qt-key-toggle-browser')
                wizard_key(case,'escape-cancels-only-capture',0x1000000)
                unchanged=case.inspect('wizard-still-open')
                assert unchanged['customization']['onboardingVisible']
                assert not nodes(unchanged,'onboardingShortcutCapture')
            else:
                wizard_capture(case,'keyboard-cancel','key-toggle-fullscreen')
                wizard_key(case,'modifier-only',0x1000021,0x4000000)
                wizard_key(case,'tab-to-unset',0x1000001)
                case.inspect('tab-to-cancel','key','--key','0x1000001')
                cancelled=case.inspect('keyboard-cancel','key','--key','0x1000004')
                assert cancelled['customization']['onboardingVisible']
                assert not nodes(cancelled,'onboardingShortcutCapture')
            case.click('finish-without-root', 'onboardingNext')
            case.close(True)
            profile = case.path / 'profile'
            for dbfile in profile.rglob('*.db'):
                with sqlite3.connect(dbfile.as_uri() + '?mode=ro', uri=True) as db:
                    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if 'Folder' in tables: assert db.execute('SELECT COUNT(*) FROM Folder').fetchone()[0] == 0
            restarted = Case('restart-empty-' + scale.replace('.', ''), scale=scale, welcome=True, reused_profile=profile)
            try:
                result = restarted.inspect('second-start', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
                verify_window_icon(restarted, result)
                assert not result['customization']['onboardingVisible']
                assert not result['library']['indexing']
                if scale == '1':
                    config_file=next(profile.rglob('vlcrc'))
                    saved_config=config_file.read_text(encoding='utf-8')
                    assert re.search(r'^qt-key-stream=$',saved_config,re.M), 'Explicit reassignment must remove Stream binding'
                    drop_fixture(restarted,'shortcut-playback','control.mkv')
                    restarted.inspect('shortcut-key-focus','focus','--target','playButton')
                    restarted.inspect('saved-fullscreen-shortcut','key','--key','0x39','--modifiers','0xe000000','--text','9',
                        '--await-core','fullscreen','--await-value','true')
                    restarted.inspect('leave-fullscreen','key','--key','0x1000000','--await-core','fullscreen','--await-value','false')
                    restarted.inspect('saved-browser-shortcut','key','--key','0x38','--modifiers','0xe000000','--text','8')
                    restarted.inspect('browser-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true','--capture')
                    closed=restarted.inspect('close-browser-shortcut','key','--key','0x38','--modifiers','0xe000000','--text','8')
                    assert not any(node['id']=='compactLibrary' and node['visible'] for node in closed['tree'])
                    restarted.inspect('queue-shortcut','key','--key','0x4c','--modifiers','0x4000000','--text','l',
                        '--await-target','playqueueToggle','--await-property','checked','--await-value','true')
                    restarted.inspect('close-queue-shortcut','key','--key','0x4c','--modifiers','0x4000000','--text','l',
                        '--await-target','playqueueToggle','--await-property','checked','--await-value','false')
                restarted.close(True)
            finally: restarted.close()
        finally: case.close()
    cancelled=Case('wizard-failed-save-cancel',welcome=True,reused_profile=profile,extra=('--qt-privacy-ask',))
    try:
        cancelled.inspect('welcome-ready')
        cancelled.click('theme-page','onboardingNext')
        cancelled.click('font-page','onboardingNext')
        cancelled.inspect('font-fallback-focus','focus','--target','onboardingFontFallback')
        cancelled.click('shortcuts','onboardingFontFallback')
        wizard_capture(cancelled,'edit-before-failure','key-toggle-fullscreen')
        wizard_key(cancelled,'capture-before-failure',0x53,0x4000000,'s')
        cancelled.click('stage-reassignment','onboardingShortcutAssign')
        config=next(portable.rglob('vlcrc'))
        original=cancelled.path/'vlcrc-before-failed-save'
        config.rename(original)
        config.mkdir()
        try:
            failed=cancelled.click('failed-finish','onboardingNext')
            assert failed['customization']['onboardingVisible']
            assert nodes(failed,'onboardingStatus')[0]['text']
        finally:
            config.rename(cancelled.path/'blocked-vlcrc-directory')
            original.rename(config)
        cancelled.inspect('cancel-setup-after-failure','key','--key','0x1000000')
        cancelled.close(True)
        text=next((cancelled.path/'profile').rglob('vlcrc')).read_text(encoding='utf-8')
        assert not re.search(r'^qt-key-stream=$',text,re.M)
        assert not re.search(r'^key-toggle-fullscreen=Ctrl\+s$',text,re.M|re.I)
    finally: cancelled.close()
    if args.case=='onboarding-shortcuts':return
    skipped = Case('skip-empty', welcome=True)
    try:
        skipped.inspect('welcome-ready')
        skipped.click('skip-without-root', 'onboardingSkip')
        empty = skipped.inspect('empty-idle', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'ready', '--await-value', 'true', '--capture')
        assert not empty['library']['indexing']
        skipped.click('add-root-menu', 'libraryAddItem')
        skipped.inspect('index-folder-dialog', 'click', '--name', 'Index library folder…')
        skipped.inspect('enter-synthetic-root', 'key', '--target', 'libraryDialogInput', '--key', '0', '--text', str(fixtures))
        skipped.click('submit-root', 'libraryDialogSubmit','--await-target','fullLibrary','--await-property','indexing','--await-value','true')
        skipped.click('all-videos-menu', 'libraryAddItem')
        skipped.inspect('all-videos', 'click', '--name', 'All videos')
        indexed = skipped.inspect('discovered-videos', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'itemCount', '--await-value', '8', '--await-comparison', 'at_least')
        skipped.inspect('discovery-idle', 'snapshot', '--await-target', 'fullLibrary', '--await-property', 'indexing', '--await-value', 'false', '--capture')
        skipped.record['indexed_videos'] = indexed['library']['indexed_model_count']
        skipped.record['busy_to_idle_observed']=True
        skipped.close(True)
    finally: skipped.close()


def interface_shortcuts():
    case=Case('interface-shortcuts')
    try:
        case.inspect('library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
        case.inspect('shortcut-menu','click','--name','Main menu')
        case.inspect('open-shortcuts','click','--name','Keyboard Shortcuts')
        case.native('search-focus','keyboardShortcutsSearch')
        case.inspect('search-ctrl-s','widget_key','--target','keyboardShortcutsSearch','--key','0','--text','Ctrl+S')
        case.native('filtered-table-focus','keyboardShortcutsTable')
        result=case.inspect('filtered-interface-rows','widget_key','--target','keyboardShortcutsTable','--key','0x1000011','--capture')
        assert any(row['columns'][0]=='Stream' for row in widget(result,'keyboardShortcutsTable')['rendered_rows'])
        case.native('search-again','keyboardShortcutsSearch')
        case.inspect('select-search','widget_key','--target','keyboardShortcutsSearch','--key','0x41','--modifiers','0x4000000')
        case.inspect('search-stream','widget_key','--target','keyboardShortcutsSearch','--key','0','--text','Stream')
        case.native('table-focus','keyboardShortcutsTable')
        selected=case.inspect('select-stream','widget_key','--target','keyboardShortcutsTable','--key','0x1000011')
        assert [row['columns'][0] for row in widget(selected,'keyboardShortcutsTable')['rendered_rows'] if row['selected']]==['Stream']
        opened=case.inspect('edit-stream','widget_key','--target','keyboardShortcutsTable','--key','0x1000004')
        assert widget(opened,'shortcutCapture')
        cancelled=case.inspect('cancel-standalone-capture','widget_key','--target','shortcutCapture','--key','0x1000000')
        assert not any(w['id']=='keyInputDialog' for w in cancelled['widgets'])
        case.inspect('edit-stream-again','widget_key','--target','keyboardShortcutsTable','--key','0x1000004')
        case.inspect('new-stream-binding','widget_key','--target','shortcutCapture','--key','0x37','--modifiers','0xe000000','--text','7')
        case.native('assign-stream','assignShortcut')
        case.native('save-stream','preferencesSave')
        case.close(True)
        profile=case.path/'profile'
        assert re.search(r'^qt-key-stream=Ctrl\+Alt\+Shift\+7$',next(profile.rglob('vlcrc')).read_text(encoding='utf-8'),re.M)
        restarted=Case('interface-shortcuts-restart',reused_profile=profile)
        try:
            restarted.inspect('restart-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
            result=restarted.inspect('real-stream-dispatch','key','--key','0x37','--modifiers','0xe000000','--text','7','--capture')
            opened=[w for w in result['widgets'] if w['type']=='OpenDialog']
            assert len(opened)==1 and 'Stream' in opened[0].get('window_title',''), opened
            restarted.inspect('cancel-stream','widget_key','--node',str(opened[0]['node']),'--key','0x1000000')
            restarted.close(True)
        finally: restarted.close()
    finally: case.close()

def playback():
    for engine in ('vlc','mpv'):
        for name in ('wide.mkv','portrait.mkv','preview-4k-long-gop.mkv'):
            case=Case('drop-' + engine + '-' + name.split('.')[0], engine=engine)
            try:
                case.inspect('full-library-viewport','resize','--width','1280','--height','800')
                initial=case.inspect('library-ready', 'snapshot', '--await-target','fullLibrary','--await-property','ready','--await-value','true')
                drop_fixture(case,'drop-video',name)
                result=case.inspect('main-player-visible','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
                assert (initial['window']['width'],initial['window']['height'])==(result['window']['width'],result['window']['height']), 'Default video open resized the chosen window'
                try:assert_window(case,result)
                except AssertionError as failure:
                    if args.case!='integration-diagnostic':raise
                    case.record['known_geometry_failure']=repr(failure)
                    case.close(False)
                    continue
                case.record['source']=name
                case.close(True)
            finally: case.close()
        fixed=Case('fixed-size-'+engine,engine=engine)
        try:
            fixed.inspect('full-library-viewport','resize','--width','1280','--height','800')
            before=fixed.inspect('library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
            drop_fixture(fixed,'fixed-size-video','wide.mkv')
            after=fixed.inspect('fixed-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            assert (before['window']['width'],before['window']['height'])==(after['window']['width'],after['window']['height'])
            fixed.click('fullscreen','fullscreenButton','--await-core','fullscreen','--await-value','true')
            replacement=drop_fixture(fixed,'fullscreen-new-input','portrait.mkv')
            assert replacement['core']['fullscreen'] and replacement['window']['visibility']==5
            windowed=fixed.inspect('restore-windowed','key','--key','0x1000000','--await-core','fullscreen','--await-value','false')
            assert (windowed['window']['width'],windowed['window']['height'])==(before['window']['width'],before['window']['height'])
            fixed.inspect('intentional-library-view','click','--name','Back to media','--await-target','viewLoader',
                '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
            library=fixed.inspect('intentional-mini-player','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1','--capture')
            assert nodes(library,'libraryReturnToPlayer'),'Intentional library browsing lost the mini player'
            drop_fixture(fixed,'fresh-video-from-library','wide.mkv')
            if engine=='mpv':
                fixed.inspect('library-before-audio','click','--name','Back to media','--await-target','viewLoader',
                    '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
                fixed.inspect('replace-with-audio','drop','--target','mainInterface','--url',(fixtures/'audio-only.mka').as_uri(),
                    '--await-core','url','--await-value',json.dumps((fixtures/'audio-only.mka').as_uri()))
                audio=fixed.inspect('audio-input-ready','snapshot','--await-core','mpv_history_ready','--await-value','true')
                assert audio['core']['audio_tracks'] and not audio['core']['video_tracks'] and not audio['core']['mpv_video_ready']
                fixed.inspect('audio-library-preserved','snapshot','--await-target','viewLoader','--await-property','source',
                    '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
                drop_fixture(fixed,'video-after-audio','portrait.mkv')
            fixed.close(True)
        finally: fixed.close()
        opted=Case('opt-in-video-size-'+engine,engine=engine,extra=['--qt-video-autoresize'])
        try:
            opted.inspect('library-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true')
            drop_fixture(opted,'opt-in-wide-video','wide.mkv')
            resized=opted.inspect('opt-in-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            assert_window(opted,resized)
            opted.close(True)
        finally: opted.close()
    for engine,scale in (('vlc','1.5'),('mpv','2')):
        case=Case('scaled-video-'+engine,engine=engine,scale=scale)
        try:
            case.inspect('library-ready','snapshot','--await-target','compactLibrary','--await-property','ready','--await-value','true')
            drop_fixture(case,'scaled-video','wide.mkv')
            result=case.inspect('scaled-main-view','snapshot','--await-target','playerView','--await-property','visible','--await-value','true','--capture')
            try:assert_window(case,result)
            except AssertionError as failure:
                if args.case!='integration-diagnostic':raise
                case.record['known_geometry_failure']=repr(failure)
                case.close(False)
                continue
            case.close(True)
        finally: case.close()

def open_vlc_commands(case,label):
    case.inspect(label+'-main-menu','click','--name','Main menu')
    case.click(label+'-settings','mainMenuGlobalSettings')
    case.reveal(label+'-reveal-advanced','preferencesAdvanced0','preferencesScroll0')
    case.native(label+'-advanced','preferencesAdvanced0')
    case.reveal(label+'-reveal-commands','preferencesAction-vlc-commands','preferencesScroll0')
    return case.native(label+'-commands','preferencesAction-vlc-commands')

def subtitle_menu(case, label, enabled):
    open_vlc_commands(case,label)
    result=case.inspect(label + '-submenu', 'widget_click', '--menu-action', 'Subtitles', '--capture')
    actions=[action for widget in result['widgets'] for action in widget.get('actions', [])]
    tracks=[action for action in actions if action['text'].replace('&','').split('\t')[0]=='Sub Track']
    assert len(tracks)==1 and tracks[0]['enabled']==enabled, tracks
    assert any(action['enabled'] and action['text'].replace('&','').startswith('Add Subtitle File') for action in actions)
    case.inspect(label + '-dismiss','key','--key','0x1000000')
    case.inspect(label + '-dismiss-root','key','--key','0x1000000')
    case.native(label+'-close-settings','preferencesClose')


def subtitle_choices(snapshot):
    tree={node['node']:node for node in snapshot['tree']}
    def inside(node):
        while node['parent'] >= 0:
            node=tree[node['parent']]
            if node['id']=='subtitleTracksBody': return True
        return False
    return [node for node in snapshot['tree'] if node['visible'] and node['enabled'] and node.get('actions') and node.get('role') in (44,45) and 'selected' in node and inside(node)]


def cue_result(case, label, count):
    result=case.inspect(label,'snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps(str(count)+' embedded source cues; positions follow the selected track and subtitle delay.'))
    assert len(service(result)['cues'])==count
    return result


def select_available_subtitle(case, label, snapshot):
    tracks=snapshot['core']['subtitle_tracks']
    assert tracks,'Fixture has no native subtitle track'
    if any(track['selected'] for track in tracks):return snapshot
    case.inspect(label+'-track-viewport','resize','--width','960','--height','720')
    choices=case.click(label+'-track-choice','subtitleButton')
    rows=[node for node in subtitle_choices(choices) if node.get('name')!='None']
    assert len(rows)==len(tracks),rows
    selected=case.inspect(label+'-select-track','click','--name',rows[0]['name'],
        '--await-property','selected','--await-value','true')
    case.inspect(label+'-close-track-choice','key','--key','0x1000000')
    return selected


def drop_fixture(case, label, file):
    case.inspect(label,'drop','--target','mainInterface','--url',(fixtures/file).as_uri(),
        '--await-core','url','--await-value',json.dumps((fixtures/file).as_uri()))
    case.inspect(label+'-seekable','snapshot','--await-core','seekable','--await-value','true')
    case.inspect(label+'-main-source','snapshot','--await-target','viewLoader','--await-property','source',
        '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
    ready=case.inspect(label+'-main-ready','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
    # --start-paused applies only to the first input. Pause replacement items
    # through the real control rather than waiting for an impossible state.
    if ready['core']['state']==2:
        if ready['core']['fullscreen']:
            # Dropping a replacement focuses the player itself. Use its real
            # Space shortcut when the fullscreen toolbar is auto-hidden.
            return case.inspect(label+'-pause','key','--key','0x20','--text',' ',
                '--await-core','state','--await-value','3')
        return case.click(label+'-pause','playButton','--await-core','state','--await-value','3')
    return case.inspect(label+'-paused','snapshot','--await-core','state','--await-value','3')


def idle():
    """Idle customization must not masquerade as an audio-only input."""
    for engine in ('vlc', 'mpv'):
        if resume_idle and (resume_idle_stop or resume_idle_eof) and engine=='vlc':continue
        suffix='-eof-viewport-resumed' if resume_idle and resume_idle_eof_viewport else '-eof-resumed' if resume_idle and resume_idle_eof else '-stop-observer-resumed' if resume_idle and resume_idle_stop else '-resumed' if resume_idle else ''
        eof_only=resume_idle and resume_idle_eof
        case=Case('idle-customization-'+engine+suffix, engine=engine,media=fixtures/'wide.mkv' if eof_only else None)
        def customize(label, action):
            case.inspect(label+'-menu','click','--name','Main menu')
            case.inspect(label+'-editor','click','--name','Customize Player')
            case.inspect(label+'-player','snapshot','--await-target','viewLoader','--await-property','source',
                '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
            case.inspect(label+'-mounted','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
            opened=case.inspect(label+'-ready','snapshot','--await-target','playerLayoutEditor',
                '--await-property','ready','--await-value','true')
            assert opened['customization']['editing']
            if action=='escape':
                result=case.inspect(label+'-escape','key','--key','0x1000000')
            else:
                result=case.click(label+'-'+action,'layoutSave' if action=='save' else 'layoutCancel')
            assert not result['customization']['editing']
        def idle_canvas(label):
            result=case.inspect(label,'snapshot','--await-target','playerIdleCone',
                '--await-property','status','--await-value','1','--capture')
            assert nodes(result,'playerIdleView') and nodes(result,'playerIdleCone')
            assert nodes(result,'playerIdleView')[0]['color']=='#000000'
            assert not nodes(result,'playerAudioView') and not nodes(result,'audioControls')
            assert not nodes(result,'playerVideoSurface')
            return result
        def finish_eof():
            case.click('seek-near-end','progressSlider','--fraction-x','.95')
            case.click('play-to-eof','playButton','--await-core','state','--await-value','2')
            if engine=='mpv':
                # Unlike idle-active, video readiness has an explicit MPV
                # changed-signal subscription in the existing observer.
                case.inspect('natural-eof','snapshot','--await-core','mpv_video_ready','--await-value','false')
            else:case.inspect('natural-eof','snapshot','--await-core','state','--await-value','0')
            customize('after-eof','cancel')
            assert idle_canvas('after-eof-cone')['core']['state']==0
        try:
            if eof_only:
                case.inspect('reference-viewport','resize','--width','1280','--height','900')
                case.inspect('paused-video','snapshot','--await-core','state','--await-value','3')
                finish_eof()
                case.record['reused_idle_audio_stop']=records['resumed_idle_checker']
                case.record['idle_audio_video_customization_transitions']=True
                case.close(True)
                continue
            case.inspect('reference-viewport','resize','--width','1280','--height','900')
            for action in ('cancel','escape','save'):
                customize('empty-'+action,action)
                result=idle_canvas('empty-'+action+'-cone')
                assert result['core']['state']==0
            # Open real audio through the same drop path as the user, then
            # return from the intentionally preserved library/mini-player view.
            case.inspect('audio-drop','drop','--target','mainInterface','--url',(fixtures/'audio-only.mka').as_uri(),
                '--await-core','url','--await-value',json.dumps((fixtures/'audio-only.mka').as_uri()))
            mounted=case.inspect('audio-seekable','snapshot','--await-core','seekable','--await-value','true')
            if nodes(mounted,'libraryReturnToPlayer'):
                case.click('audio-main-view','libraryReturnToPlayer')
            audio=case.inspect('audio-artwork','snapshot','--await-target','playerAudioView',
                '--await-property','visible','--await-value','true','--capture')
            assert audio['core']['audio_tracks'] and not audio['core']['video_tracks']
            assert not nodes(audio,'playerIdleView')
            if audio['core']['state']==2:
                case.click('pause-audio','playButton','--await-core','state','--await-value','3')
            customize('paused-audio','cancel')
            assert nodes(case.inspect('paused-artwork','snapshot','--capture'),'playerAudioView')
            drop_fixture(case,'replace-with-video','wide.mkv')
            video=case.inspect('video-surface','snapshot','--await-target','playerVideoSurface',
                '--await-property','visible','--await-value','true','--capture')
            assert not nodes(video,'playerAudioView') and not nodes(video,'playerIdleView')
            case.inspect('stop-video','key','--key','0x53','--text','s')
            customize('stopped-video','cancel')
            idle_canvas('stopped-video-cone')
            drop_fixture(case,'reopen-video','wide.mkv')
            finish_eof()
            case.record['idle_audio_video_customization_transitions']=True
            case.close(True)
        finally: case.close()


def subtitles(verify_navigation=True, engines=('vlc','mpv')):
    for engine in engines:
        case=Case('timeline-' + engine, engine=engine, media=fixtures/'embedded-text.mkv')
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            case.click('open-playback-tools','toolsButton')
            timeline=case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
            assert len(service(timeline)['cues'])==3
            case.inspect('close-settings','key','--key','0x1000000')
            shown=case.inspect('timeline-controls','snapshot','--capture')
            for identity in ('previousSubtitleCue','nextSubtitleCue','subtitleDelayEarlier','subtitleDelayLater'):
                assert len(nodes(shown,identity))==1
            buttons=[nodes(shown,identity)[0] for identity in ('previousSubtitleCue','subtitleDelayEarlier','subtitleDelayLater','nextSubtitleCue')]
            assert all(left['x']+left['width']<=right['x']+.5 for left,right in zip(buttons,buttons[1:]))
            graph=nodes(shown,'subtitleTimelineOffset')[0]
            assert graph['width']>0 and 0<=graph['x'] and graph['x']+graph['width']<=shown['window']['width']
            assert 0<=graph['y'] and graph['y']+graph['height']<=shown['window']['height']
            base=shown['core']['subtitle_delay_ms']
            case.click('delay-later','subtitleDelayLater','--await-core','subtitle_delay_ms','--await-value',base+50,'--await-tolerance','0.001')
            case.click('delay-earlier','subtitleDelayEarlier','--await-core','subtitle_delay_ms','--await-value',base,'--await-tolerance','0.001')
            # Allow the native paused clock's precision on this12fps fixture;
            # a one-second buffering offset must fail this bound.
            if verify_navigation:
                case.click('next-cue','nextSubtitleCue','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
                case.click('next-cue-again','nextSubtitleCue','--await-core','time_seconds','--await-value','4','--await-tolerance','0.2')
                case.click('previous-cue','previousSubtitleCue','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
            # The narrow case above proves the cue row fits. Use a full popup
            # viewport for the separate multi-track and native file workflows.
            case.inspect('track-selection-viewport','resize','--width','960','--height','720')
            subtitle_menu(case,'embedded-track-menu',True)
            tracks=case.click('open-track-choice','subtitleButton')
            alternate=[node for node in subtitle_choices(tracks) if node.get('name')!='None' and not node['selected']]
            assert len(alternate)==1, alternate
            case.inspect('select-second-track','click','--name',alternate[0]['name'],'--await-property','selected','--await-value','true')
            second=cue_result(case,'second-track-cues',2)
            assert service(second)['cues'][0]['start']==2000
            disabled=case.inspect('disable-selected-track','click','--name','None','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('No subtitle track selected.'))
            assert not service(disabled)['cues'] and not any(track['selected'] for track in disabled['core']['subtitle_tracks'])
            case.inspect('restore-second-track','click','--name',alternate[0]['name'],'--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('2 embedded source cues; positions follow the selected track and subtitle delay.'))
            case.inspect('dismiss-track-popup','key','--key','0x1000000')
            other='mpv' if engine=='vlc' else 'vlc'
            for target in (other,engine):
                case.click('switch-tools-'+target,'toolsButton')
                case.inspect('choose-engine-'+target,'click','--name','MPV' if target=='mpv' else 'VLC')
                settled=case.inspect('engine-settled-'+target,'snapshot','--await-core','engine_switching','--await-value','false')
                assert settled['core']['engine']==target and settled['core']['state']==3
                # Track ids/default selections belong to each backend. R82
                # requires the timeline to follow the incoming selected track,
                # while R67 preserves position and pause across the switch.
                selected=[track for track in settled['core']['subtitle_tracks'] if track['selected']]
                assert len(selected)==1 and selected[0]['language'] in ('eng','deu'),selected
                german=selected[0]['language']=='deu'
                handover=cue_result(case,'handover-cues-'+target,2 if german else 3)
                assert service(handover)['cues'][0]['start']==(2000 if german else 1000)
                case.inspect('dismiss-engine-tools-'+target,'key','--key','0x1000000')
                subtitle_menu(case,'handover-menu-'+target,True)
            for file in ('embedded-ass.mkv','embedded-text.mp4'):
                opened=drop_fixture(case,'open-'+file,file)
                select_available_subtitle(case,'open-'+file,opened)
                decoded=cue_result(case,'native-cues-'+file,3)
                assert service(decoded)['cues'][0]['start']==1000
            opened=drop_fixture(case,'open-image','embedded-image.mkv')
            select_available_subtitle(case,'open-image',opened)
            image=case.inspect('image-limit','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('Image subtitles keep playing normally; a text cue timeline is unavailable.'))
            assert not service(image)['cues'] and image['core']['subtitle_tracks']
            drop_fixture(case,'open-no-track','control.mkv')
            no_track=case.inspect('no-track-cues','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('No subtitle track selected.'))
            assert not service(no_track)['cues']
            subtitle_menu(case,'no-track-menu',False)
            case.inspect('drop-external-subtitle','drop','--target','mainInterface','--url',(fixtures/'english.srt').as_uri(),
                '--await-service','redesignMediaTools','--await-property','subtitleLoaded','--await-value','true')
            external=case.inspect('external-cues','snapshot','--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert len(service(external)['cues'])==3
            subtitle_menu(case,'external-track-menu',True)
            open_vlc_commands(case,'native-add-subtitle')
            case.inspect('native-subtitle-submenu','widget_click','--menu-action','Subtitles')
            case.inspect('native-add-subtitle-dialog','widget_click','--menu-action','Add Subtitle File...')
            case.native('native-file-name-focus','fileNameEdit')
            case.inspect('select-file-name','widget_key','--target','fileNameEdit','--key','0x41','--modifiers','0x4000000','--text','a')
            case.inspect('enter-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0','--text',str(fixtures/'german.srt'))
            chosen=case.inspect('accept-native-subtitle-file','widget_key','--target','fileNameEdit','--key','0x1000004',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('2 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert service(chosen)['subtitleLoaded'] and len(service(chosen)['cues'])==2
            case.native('close-native-subtitle-settings','preferencesClose')
            case.inspect('external-track-viewport','resize','--width','960','--height','720')
            available=case.click('reopen-external-track-choice','subtitleButton')
            earlier=[node for node in subtitle_choices(available) if node.get('name')!='None' and not node['selected']]
            assert len(earlier)==1,earlier
            restored=case.inspect('select-earlier-external-track','click','--name',earlier[0]['name'],
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            assert 'English first' in service(restored)['cues'][0]['text']
            case.inspect('dismiss-external-track-choice','key','--key','0x1000000')
            remote=case.inspect('preserve-remote-subtitle-drop','drop','--target','mainInterface','--url','http://127.0.0.1:'+str(server.server_port)+'/english.srt',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('Text cue timelines require a local subtitle file; subtitle playback is unchanged.'))
            assert remote['core']['state']==3 and service(remote)['subtitleLoaded'] and not service(remote)['cues']
            case.close(True)
            restarted=Case('timeline-restart-'+engine,engine=engine,media=fixtures/'embedded-text.mkv',reused_profile=case.path/'profile')
            try:
                initial=restarted.inspect('paused','snapshot','--await-core','state','--await-value','3')
                assert service(initial)['timelineVisible'], 'Timeline preference did not survive restart'
                select_available_subtitle(restarted,'restart-subtitle',initial)
                observed=restarted.inspect('restart-track-observed')
                selected=[track for track in observed['core']['subtitle_tracks'] if track['selected']]
                assert len(selected)==1 and selected[0]['language'] in ('eng','deu'),selected
                restored=cue_result(restarted,'restored-timeline',2 if selected[0]['language']=='deu' else 3)
                assert service(restored)['timelineVisible'] and len(nodes(restored,'subtitleDelayLater'))==1
                restarted.close(True)
            finally: restarted.close()
        finally: case.close()

def preview():
    media=args.preview_media.resolve() if args.preview_media else fixtures/'preview-4k-long-gop.mkv'
    assert media.is_file()
    case=Case('seek-preview',media=media)
    try:
        paused=case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        position=311/paused['core']['length_seconds'] if args.preview_media else .55
        case.record['input_sha256']=hashlib.file_digest(media.open('rb'),'sha256').hexdigest()
        def popup_pixels(snapshot):
            frame=nodes(snapshot,'seekPreviewImage')
            assert len(frame)==1 and frame[0]['status']=='Ready', frame
            picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
            ratio=picture.width/snapshot['window']['width']
            item=frame[0]
            bounds=tuple(round(value*ratio) for value in (item['x'],item['y'],item['x']+item['width'],item['y']+item['height']))
            pixels=picture.crop(bounds).resize((160,90)).convert('RGB')
            values=list(pixels.getdata())
            # The reported 5:11 frame is a dark menu on a mostly black video.
            # Reject blank output from luminance variation, not an assumption
            # that a large part of every legitimate frame must be bright.
            levels=[max(rgb) for rgb in values]
            assert max(levels)-min(levels)>32 and len(set(levels))>32, 'Rendered popup is blank/black'
            return pixels
        cold=case.inspect('cold-preview','move','--target','progressSlider','--fraction-x',position,
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        first=service(cold,'redesignMediaAnalysis')
        assert first['previewSource'] and abs(first['previewPosition']-position)<.02
        first_pixels=popup_pixels(cold)
        case.inspect('leave-preview','move','--target','playButton')
        warm=case.inspect('cached-preview','move','--target','progressSlider','--fraction-x',position,
            '--await-service','redesignMediaAnalysis','--await-property','previewStatus','--await-value','""','--capture')
        cached=service(warm,'redesignMediaAnalysis')
        assert cached['previewLatencyMS']<16.7, cached
        case.record['cold_decode_ms']=first['previewLatencyMS']
        case.record['cached_publication_ms']=cached['previewLatencyMS']
        assert first['previewLatencyMS']<1000, 'Uncached local preview still takes several seconds'
        assert popup_pixels(warm).tobytes()==first_pixels.tobytes(), 'Cached rendered frame changed'
        if args.preview_media:
            second=case.inspect('distinct-actual-frame','move','--target','progressSlider','--fraction-x',693/paused['core']['length_seconds'],
                '--await-service','redesignMediaAnalysis','--await-property','previewPosition',
                '--await-value',693/paused['core']['length_seconds'],'--await-tolerance','0.001','--capture')
            second_pixels=popup_pixels(second)
            difference=sum(abs(a-b) for a,b in zip(first_pixels.tobytes(),second_pixels.tobytes()))/len(first_pixels.tobytes())
            assert difference>10, ('Different source positions returned the same/incorrect frame',difference)
            case.record['actual_frame_mean_difference']=difference
        for position in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
            case.inspect('continuous-' + str(position),'move','--target','progressSlider','--fraction-x',position)
        latest=case.inspect('latest-preview','snapshot','--await-service','redesignMediaAnalysis','--await-property','previewPosition','--await-value','0.9','--await-tolerance','.02','--capture')
        case.record['latest_preview']=service(latest,'redesignMediaAnalysis')
        assert abs(case.record['latest_preview']['previewPosition']-.9)<.02
        cleared=drop_fixture(case,'change-preview-input','control.mkv')
        # A stationary hover may already request and publish the new input's
        # frame while the drop finishes. Its revision must replace the old
        # input; the actual new blue pixels are checked below.
        assert service(cleared,'redesignMediaAnalysis')['previewSource']!=case.record['latest_preview']['previewSource'], 'Previous input preview survived invalidation'
        case.inspect('leave-old-preview','move','--target','playButton')
        blue=case.inspect('fresh-input-preview','move','--target','progressSlider','--fraction-x','.55',
            '--await-service','redesignMediaAnalysis','--await-property','previewPosition','--await-value','0.55','--await-tolerance','0.001','--capture')
        frame=nodes(blue,'seekPreviewImage')
        assert len(frame)==1
        picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
        ratio=picture.width/blue['window']['width']
        item=frame[0]
        center=picture.getpixel((round((item['x']+item['width']/2)*ratio),round((item['y']+item['height']/2)*ratio)))
        assert max(abs(actual-expected) for actual,expected in zip(center,(32,64,128)))<16, ('New input preview does not show its actual blue frame',center)
        case.record['new_input_preview_rgb']=center
        case.click('preview-engine-tools','toolsButton')
        case.inspect('preview-switch-mpv','click','--name','MPV')
        switched=case.inspect('preview-engine-settled','snapshot','--await-core','engine_switching','--await-value','false')
        assert switched['core']['engine']=='mpv'
        case.inspect('close-preview-tools','key','--key','0x1000000')
        unavailable=case.inspect('mpv-preview-disclosure','move','--target','progressSlider','--fraction-x','.55','--capture')
        disclosure=service(unavailable,'redesignMediaAnalysis')
        assert not disclosure['previewSource'] and 'require VLC playback' in disclosure['previewStatus']
        case.close(True)
    finally: case.close()

def icons():
    for scale in ('1','1.25','1.5','2'):
        case=Case('transport-icons-'+scale,scale=scale,media=fixtures/'control.mkv',
            extra=(str(fixtures/'control.mkv'),str(fixtures/'embedded-text.mkv')))
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            case.inspect('middle-item','click','--name','Next','--await-core','url',
                '--await-value',json.dumps((fixtures/'embedded-text.mkv').as_uri()))
            case.inspect('middle-item-playing','snapshot','--await-core','state','--await-value','2')
            case.click('pause-middle-item','playButton','--await-core','state','--await-value','3')
            for state in ('play','pause'):
                case.inspect(state+'-controls','move','--target','playButton')
                snapshot=case.inspect(state+'-native-sampling','snapshot','--capture')
                glyphs=[node for node in snapshot['tree'] if node['visible'] and node['id'].startswith('playerGlyph-')]
                assert any(node['id']=='playerGlyph-'+state for node in glyphs)
                for node in glyphs:
                    assert not node['mipmap'] and not node['smooth'], node
                if state=='play':
                    case.click('play-action','playButton','--await-core','state','--await-value','2')
            case.click('pause-action','playButton','--await-core','state','--await-value','3')
            case.inspect('main-menu-viewport','resize','--width','1280','--height','800')
            menu=case.inspect('main-menu-native-scale','click','--name','Main menu','--capture')
            assert nodes(menu,'mainMenuGlobalSettings'), 'Direct Settings entry missing at this display scale'
            case.inspect('close-main-menu-native-scale','key','--key','0x1000000')
            case.close(True)
        finally: case.close()

def sidebar():
    for engine in ('vlc','mpv'):
        case=Case('sidebar-transition-'+engine,engine=engine,media=fixtures/'control.mkv')
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            for playing in (False,True):
                if playing:
                    case.click('start-playing','playButton','--await-core','state','--await-value','2')
                state='playing' if playing else 'paused'
                for opened in (True,False):
                    label=state+('-open' if opened else '-collapse')
                    snapshot=case.inspect(label,'click','--name','Media browser','--capture')
                    surfaces=nodes(snapshot,'playerVideoSurface')
                    assert len(surfaces)==1
                    surface=surfaces[0]
                    dpr=snapshot['window']['dpr']
                    actual=snapshot['video_backdrop']['surface_at_placement_px']
                    assert abs(actual['width']-surface['width']*dpr)<=1, (label,actual,surface)
                    assert abs(actual['height']-surface['height']*dpr)<=1, (label,actual,surface)
                    if opened: assert surface['x']>0
                    else: assert abs(surface['x'])<1 and abs(surface['width']-snapshot['window']['width'])<1
                    case.record.setdefault('surface_transitions',[]).append({
                        'state':state,'opened':opened,'surface_at_placement_px':actual,
                        'qml_viewport':{key:surface[key] for key in ('x','y','width','height')}})
            case.close(True)
        finally: case.close()

def menus_normal():
    """Reference menu, real Settings route and Playback controls as one workflow."""
    case=Case('figma-player-menus',media=fixtures/'control.mkv',extra=('--qt-accent-color=#2f87b5',))
    def video_context(engine):
        case.click('video-context-'+engine,'playerVideoSurface','--button','right')
        ready=case.inspect('video-context-ready-'+engine,'snapshot',
            '--await-service','nativeBackdrop','--await-property','status',
            '--await-value','["ready","failed","unavailable"]','--await-comparison','one_of','--capture')
        assert ready['native_backdrop_state']=='ready',ready.get('widgets')
        menu=next(row for row in ready['widgets'] if 'menu_construction_ms' in row)
        labels=[row['text'].replace('&','').split('\t')[0] for row in menu['actions']]
        for label in ('Playback','Video','Audio','Subtitle','More Settings','Queue','Open Media'):
            assert label in labels,(engine,label,labels)
        assert menu['redesignMenuPaintDispatchedMs']>=menu['menu_construction_ms']
        assert menu['redesignMenuPaintDispatchedMs']<1000,('multi-second native popup latency',engine,menu)
        composition=settings_window_region(case,menu)
        case.record.setdefault('video_context_menus',[]).append({'engine':engine,
            'construction_ms':menu['menu_construction_ms'],
            'paint_dispatch_ms':menu['redesignMenuPaintDispatchedMs'],
            'composition':composition,'pixel_proof':'Separate composed capture required'})
        opened=case.inspect('video-context-submenu-'+engine,'widget_click','--menu-action','Video','--capture')
        menus=[row for row in opened['widgets'] if row['type'] in ('QMenu','VLCMenu')]
        assert len({row['native_id'] for row in menus})>=2,'Deferred video submenu did not open'
        assert any(row['type']=='QMenu' and row['actions'] for row in menus),'Deferred video submenu is empty'
        for row in menus:settings_window_region(case,row)
        case.inspect('video-context-submenu-close-'+engine,'key','--key','0x1000000')
        case.inspect('video-context-close-'+engine,'key','--key','0x1000000')
    try:
        case.inspect('reference-viewport','resize','--width','1280','--height','900')
        snapshot=case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        saved_presentation=snapshot['presentation']
        assert saved_presentation['accent']=='#2f87b5' and snapshot['rendered_accent']=='#2f87b5'
        # The visual review launcher used a dummy output with no volume callback.
        # This case uses the real WASAPI owner, paused and initially silent.
        case.inspect('volume-focus','focus','--target','volumeSlider')
        # Accessibility focus deliberately leaves global player shortcuts active.
        # Establish actual Tab focus before asking the Slider to handle arrows.
        case.inspect('volume-backtab','key','--key','0x1000002','--modifiers','0x2000000')
        focused=case.inspect('volume-tab','key','--key','0x1000001')
        assert nodes(focused,'volumeSlider')[0]['focused']
        case.inspect('volume-increase','key','--key','0x1000014',
            '--await-core','audio_session_volume','--await-value','0.05','--await-tolerance','.005')
        case.inspect('volume-restore-silence','key','--key','0x1000012',
            '--await-core','audio_session_volume','--await-value','0','--await-tolerance','.005')
        maximum=nodes(snapshot,'volumeSlider')[0]['to']
        case.inspect('volume-mouse-wedge','click','--target','volumeSlider','--fraction-x','.5',
            '--await-core','audio_session_volume','--await-value',maximum/2,'--await-tolerance','.03')
        case.inspect('volume-mouse-restore','click','--target','volumeSlider','--fraction-x','0',
            '--await-core','audio_session_volume','--await-value','0','--await-tolerance','.005')
        case.record['real_output_volume_control']=True
        recent_initial=next(node for node in snapshot['tree'] if node['id']=='recentSource')
        assert recent_initial.get('status') in ('Ready','Loading',1,2), ('Recent model is not loading',recent_initial)
        recent=case.inspect('recent-model-ready','snapshot','--await-target','recentSource',
            '--await-property','status','--await-value','1')
        recent_loader=next(node for node in recent['tree'] if node['id']=='recentSource')
        assert recent_loader['source'].rsplit('/',1)[-1]=='PlayerRecentMenuModel.qml',recent_loader
        case.record['deferred_recent_model_ready']=True
        elapsed=nodes(snapshot,'playerElapsedTime')
        assert len(elapsed)==1 and re.fullmatch(r'\d{2,}:\d{2}:\d{2}',elapsed[0]['text']), elapsed
        opened=case.inspect('main-menu','click','--name','Main menu','--capture')
        expected=['Open File(s)','Open Folder','Open Network Stream','Open Disc','Open Capture Device',
            'Convert','Open Recent','Profile','Keyboard Shortcuts','Customize Player','Settings','About VLC']
        rows=[]
        for label in expected:
            matches=[item for item in opened['tree'] if item['visible'] and item.get('name')==label and item.get('actions')]
            assert len(matches)==1, (label,matches)
            rows.append(matches[0])
        assert [item['y'] for item in rows]==sorted(item['y'] for item in rows)
        assert all(abs(item['height']-48)<1 for item in rows), rows
        assert max(item['x'] for item in rows)-min(item['x'] for item in rows)<1
        primary=[item for item in opened['tree'] if item['visible'] and item.get('actions') and
                 abs(item.get('x',-1000)-rows[0]['x'])<1 and item.get('height',0)>24]
        assert len(primary)==12, primary
        case.record['reference_menu_rows']=rows
        case.inspect('recent-submenu','click','--name','Open Recent','--capture')
        case.inspect('close-recent-submenu','key','--key','0x1000000')
        settings=case.click('direct-global-settings','mainMenuGlobalSettings','--capture')
        assert any(widget['id']=='redesignPreferences' for widget in settings['widgets'])
        assert any(widget['id']=='preferencesHeading' and widget.get('text')=='Global Settings' for widget in settings['widgets'])
        case.native('cancel-global-settings','preferencesClose')
        case.inspect('keyboard-main-menu-focus','focus','--name','Main menu')
        # Accessibility SetFocus uses OtherFocusReason, which intentionally
        # preserves player hotkeys. Traverse with Tab to establish keyboard
        # visual focus through the real Qt navigation path before Space.
        case.inspect('keyboard-main-menu-backtab','key','--key','0x1000002','--modifiers','0x2000000')
        focused=case.inspect('keyboard-main-menu-tab','key','--key','0x1000001')
        assert any(item.get('name')=='Main menu' and item.get('focused') and item['visible'] for item in focused['tree'])
        reopened=case.inspect('reopen-main-menu','key','--key','0x20','--text',' ')
        assert nodes(reopened,'mainMenuGlobalSettings'), 'Keyboard did not open the main menu'
        case.inspect('profile-keyboard-focus','focus','--name','Profile')
        profile=case.inspect('profile-submenu','key','--key','0x1000014','--capture')
        assert any(item['visible'] and item.get('name')=='New / Manage Profiles…' for item in profile['tree'])
        case.inspect('close-profile-submenu','key','--key','0x1000000')
        case.inspect('close-main-menu','key','--key','0x1000000')
        playback=case.click('playback-panel','toolsButton','--capture')
        assert len(playback['video_backdrop']['regions'])==playback['video_backdrop']['regions_bound_at_content'], 'Popup background was attached after presentation'
        labels=['Show Subtitle Timeline on Seekbar','Show Statistics','Reverse','Sleep Timer','Audio Visualizer','Speed']
        positions=[]
        for label in labels:
            matches=[item for item in playback['tree'] if item['visible'] and item.get('text')==label]
            assert matches, label
            positions.append(min(item['y'] for item in matches))
        assert positions==sorted(positions), positions
        case.inspect('timer-dropdown-glass','click','--name','Sleep timer','--capture')
        case.inspect('timer-dropdown-dismiss','key','--key','0x1000000')
        timer=case.inspect('timer-focus','focus','--name','Sleep timer')
        case.inspect('timer-arm','key','--key','0x1000015','--await-service','redesignMediaTools','--await-property','sleepMinutes','--await-value','1')
        case.inspect('timer-cancel','key','--key','0x1000010','--await-service','redesignMediaTools','--await-property','sleepMinutes','--await-value','0')
        case.inspect('speed-value-focus','focus','--name','Playback speed value')
        case.inspect('speed-value-select','key','--key','0x41','--modifiers','0x4000000','--text','a')
        case.inspect('speed-value-input','key','--key','0','--text','1.25x')
        edited=case.inspect('speed-value-apply','key','--key','0x1000004','--await-core','rate','--await-value','1.25','--await-tolerance','.001')
        slider=nodes(edited,'speedSlider')[0]
        fraction=(4+(slider['width']-8)*(.75-.25)/1.75)/slider['width']
        case.inspect('speed-slider-apply','click','--target','speedSlider','--fraction-x',fraction,'--await-core','rate','--await-value','0.75','--await-tolerance','.011')
        case.inspect('speed-reset-focus','focus','--name','Playback speed value')
        case.inspect('speed-reset-select','key','--key','0x41','--modifiers','0x4000000','--text','a')
        case.inspect('speed-reset-input','key','--key','0','--text','1x')
        case.inspect('speed-reset-apply','key','--key','0x1000004','--await-core','rate','--await-value','1','--await-tolerance','.001')
        for engine in ('mpv','vlc'):
            case.inspect('menu-engine-'+engine,'click','--name','MPV' if engine=='mpv' else 'VLC')
            settled=case.inspect('menu-engine-settled-'+engine,'snapshot',
                '--await-core','engine_switching','--await-value','false','--capture')
            assert settled['core']['engine']==engine and settled['core']['state']==3
            assert settled['rendered_accent']==('#420042' if engine=='mpv' else '#2f87b5')
            assert settled['presentation']==saved_presentation, 'Engine selection rewrote the saved appearance'
            glyph=nodes(settled,'playerGlyph-'+('mpv' if engine=='mpv' else 'vlc'))
            assert len(glyph)==1 and glyph[0]['source'].endswith('/'+('mpv' if engine=='mpv' else 'vlc')+'.svg'),glyph
            playing=case.click('panel-play-retained-'+engine,'playButton','--await-core','state','--await-value','2')
            assert nodes(playing,'mediaSettingsBody'), 'Play dismissed the settings panel'
            paused=case.click('panel-pause-retained-'+engine,'playButton','--await-core','state','--await-value','3')
            assert nodes(paused,'mediaSettingsBody'), 'Pause dismissed the settings panel'
            case.record.setdefault('engine_presentation',[]).append({'engine':engine,'accent':settled['rendered_accent'],
                'glyph':glyph[0]['source'],'saved_appearance_preserved':True,'play_pause_kept_panel_open':True})
            case.inspect('context-playback-close-'+engine,'key','--key','0x1000000')
            video_context(engine)
            case.click('context-playback-reopen-'+engine,'toolsButton')
        closed=case.click('gear-closes-playback-panel','toolsButton')
        assert not nodes(closed,'mediaSettingsBody')
        reopened=case.click('gear-reopens-playback-panel','toolsButton')
        assert nodes(reopened,'mediaSettingsBody')
        case.inspect('close-playback-panel','key','--key','0x1000000')
        for panel,identity in (('audio','audioButton'),('subtitles','subtitleButton'),('queue','playqueueToggle')):
            case.click(panel+'-panel-glass',identity,'--capture')
            if panel=='queue':case.click(panel+'-panel-dismiss',identity)
            else:case.inspect(panel+'-panel-dismiss','key','--key','0x1000000')
        commands=open_vlc_commands(case,'native-command-glass')
        # The native widget visitor already excludes every hidden widget.
        native_menus=[widget for widget in commands['widgets'] if widget['type']=='QMenu']
        assert native_menus,'The themed native commands menu did not open'
        case.record['native_command_menu_composition']=[settings_window_region(case,widget) for widget in native_menus]
        submenu=case.inspect('native-submenu-glass','widget_click','--menu-action','Subtitles','--capture')
        native_submenus=[widget for widget in submenu['widgets'] if widget['type']=='QMenu']
        assert len(native_submenus)>len(native_menus),'Native submenu did not open'
        case.record['native_submenu_composition']=[settings_window_region(case,widget) for widget in native_submenus]
        case.inspect('native-submenu-dismiss','key','--key','0x1000000')
        case.inspect('native-command-dismiss','key','--key','0x1000000')
        case.native('native-command-settings-close','preferencesClose')
        case.inspect('library-menu-route','click','--name','Back to media','--await-target','viewLoader',
            '--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'))
        case.inspect('library-menu-ready','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
        library_menu=case.inspect('library-main-menu','click','--name','Main menu','--capture')
        assert nodes(library_menu,'mainMenuGlobalSettings')
        library_settings=case.click('library-direct-global-settings','mainMenuGlobalSettings','--capture')
        assert any(widget['id']=='redesignPreferences' for widget in library_settings['widgets'])
        case.native('cancel-library-global-settings','preferencesClose')
        case.close(True)
    finally: case.close()

def menus():
    if not resume_menu_quit:
        menus_normal()
        initial=Case('mpv-startup-presentation',engine='mpv',media=fixtures/'control.mkv',extra=('--qt-accent-color=#2f87b5',))
        try:
            snapshot=initial.inspect('mpv-initial-identity','snapshot','--await-core','state','--await-value','3','--capture')
            assert snapshot['core']['engine']=='mpv' and snapshot['rendered_accent']=='#420042'
            assert snapshot['presentation']['accent']=='#2f87b5'
            assert len(nodes(snapshot,'playerGlyph-mpv'))==1
            initial.record['initial_engine_identity_verified']=True
            initial.close(True)
        finally: initial.close()
    # Native command menus contain variable callbacks into the interface. Quit
    # with the parentless Settings window and its menu still open, exercising
    # their real destruction before core interface variables are released.
    case=Case('native-menu-open-quit-resumed' if resume_menu_quit else 'native-menu-open-quit',media=fixtures/'control.mkv')
    try:
        case.inspect('reference-viewport','resize','--width','1280','--height','900')
        case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        commands=open_vlc_commands(case,'quit-native-menu')
        native_menus=[widget for widget in commands['widgets'] if widget['type']=='QMenu']
        assert native_menus
        case.record['quit_with_native_menu_open']=True
        case.record['native_command_menu_composition']=[settings_window_region(case,widget) for widget in native_menus]
        case.close(True)
    finally: case.close()


def settings_backdrop():
    """Read the owned window's DWM request; never confuse it with pixel proof."""
    records['diagnostic_only']=True
    case=Case('settings-backdrop',media=fixtures/'control.mkv')
    try:
        snapshot=case.inspect('backdrop-settings','key','--key','0x50','--modifiers','0x4000000','--capture')
        dialog=next(row for row in snapshot['widgets'] if row['id']=='redesignPreferences')
        region=settings_window_region(case,dialog)
        def read_backdrop():
            hwnd=W.HWND(int(dialog['native_id'],16))
            pid=W.DWORD()
            u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            assert pid.value==case.player.pid
            dwm=ctypes.WinDLL('dwmapi',use_last_error=True)
            dwm.DwmGetWindowAttribute.argtypes=[W.HWND,W.DWORD,ctypes.c_void_p,W.DWORD]
            dwm.DwmGetWindowAttribute.restype=ctypes.c_long
            backdrop=W.DWORD()
            hr=dwm.DwmGetWindowAttribute(hwnd,38,ctypes.byref(backdrop),ctypes.sizeof(backdrop))
            u.GetWindowLongPtrW.argtypes=[W.HWND,ctypes.c_int]
            u.GetWindowLongPtrW.restype=ctypes.c_ssize_t
            style=u.GetWindowLongPtrW(hwnd,-20)
            return {'get_system_backdrop_hresult':f'0x{hr & 0xffffffff:08x}',
                'system_backdrop_type':backdrop.value if hr==0 else None,
                'extended_style':hex(style),'layered':bool(style & 0x80000),
                'native_region':region,'actual_blurred_picture_verified':False,
                'limit':'Readback proves the DWM request only; inactive desktop and QWidget captures cannot establish its composed pixels.'}
        case.record['backdrop_diagnostic']=owned_native_read(case,read_backdrop)
        save()
        case.native('backdrop-close','preferencesClose')
        case.close(True)
    finally:case.close()


def settings():
    """All reference categories, real scrolling, DPI/theme and retained edits."""
    reference=json.loads((repo/'doc/redesign/resources/m4-settings-reference.json').read_text())
    corrections={key.casefold():value for key,value in reference['copy_corrections'].items()}
    categories=reference['categories']
    survey=args.case=='settings-survey'
    if resume_settings or resume_behaviour or collect_layouts:
        labels={row['label'] for row in completed['settings_views']}
        required={theme+'-'+width+'-'+str(index)+'-'+kind
            for theme in ('dark','light') for width in ('normal','narrow')
            for index in range(len(categories))
            for kind in (('basic','expanded','page-0') if categories[index].get('advanced_disclosure',True) else ('basic','page-0'))}
        assert required<=labels,(required-labels)
        assert all((root/completed['name']/'evidence'/row['capture']).is_file()
            for row in completed['settings_views'])
    def text(value):
        value=value.strip().rstrip(':').casefold()
        return corrections.get(value,value).casefold()
    def widget(snapshot,identity):
        matches=[row for row in snapshot['widgets'] if row['id']==identity]
        assert len(matches)==1,(identity,matches)
        return matches[0]
    def select(case,index,label):
        result=case.native(label+'-nav','preferencesCategories')
        names=[row['category'] for row in categories]
        seen=set()
        while True:
            selected=[row['columns'][0] for row in widget(result,'preferencesCategories')['rendered_rows'] if row['selected']]
            assert len(selected)==1 and selected[0] in names,selected
            current=names.index(selected[0])
            if current==index:break
            assert current not in seen,('category keyboard navigation did not advance',label,selected)
            seen.add(current)
            # Home targets the disabled section heading at model row0 in Qt's
            # QListView. Use real Up/Down navigation, which skips section rows,
            # and terminate from the observed selection rather than a key count.
            result=case.inspect(label+'-navigate-'+str(len(seen)),'widget_key',
                '--target','preferencesCategories','--key','0x1000013' if current>index else '0x1000015')
        return result
    def check_labels(snapshot,index,expanded):
        frames=categories[index]['frames']
        widgets={row['node']:row for row in snapshot['widgets']}
        area=widget(snapshot,'preferencesScroll'+str(index))
        def belongs(row):
            while row['parent']>=0:
                row=widgets[row['parent']]
                if row['node']==area['node']:return True
            return False
        def y(row):
            result=row['y']
            while row['parent']>=0:
                row=widgets[row['parent']];result+=row['y']
            return result
        rows=[row for row in widgets.values() if belongs(row)]
        # Lazy hidden sections are not substitutes for the category under test.
        label_rows=[row for row in sorted(rows,key=lambda row:(y(row),row['x']))
                if row['type']=='QLabel' and not row['id'].startswith(('description-','equalizerValue'))
                and (not row['id'].startswith('equalizerFrequency') or row['id']=='equalizerFrequencyPreamp')]
        labels=[text(row.get('text','')) for row in label_rows]
        for frame in frames[:2 if expanded else 1]:
            information={text(row['text']):row['information'] for row in frame['labels']}
            if index==2:information['last.fm password']=information.get('last.fm username',True)
            expected=[row['text'] for row in frame['labels']]
            if not expanded and categories[index]['category']=='Performance':expected=expected[:expected.index('Developer')]
            expected=[text(label) for label in expected if label not in ('Search','12.0 dB')]
            if index==2:
                names=[i for i,label in enumerate(expected) if label=='last.fm username']
                if len(names)==2:expected[names[1]]='last.fm password'
            if index==3:
                # The prototype repeats its wheel controls under Remotes.
                expected=list(dict.fromkeys(expected))
            position=0
            for label in expected:
                assert label in labels[position:],(categories[index]['category'],frame['source_frame'],label,labels[position:])
                position=labels.index(label,position)
                caption=label_rows[position]
                owner=caption
                while owner['parent']>=0 and not owner['id'].startswith('preference-'):
                    owner=widgets[owner['parent']]
                if owner['id'].startswith('preference-'):
                    observed=any(row['id'].startswith('help-') and row['parent']==caption['parent'] for row in rows)
                    assert observed==information[label],('Reference information glyph differs',categories[index]['category'],label,observed,information[label])
                position+=1
        ids=[row['id'] for row in snapshot['widgets'] if row['id'].startswith(('preference-','value-'))]
        assert len(ids)==len(set(ids)),('duplicate settings view identities',ids)
        if index==2:
            password=widget(snapshot,'value-lastfm-password')
            assert password.get('text')=='[redacted]'
    def capture(case,label,index,dark):
        result=case.inspect(label,'snapshot','--capture')
        if not categories[index].get('advanced_disclosure',True):
            assert not any(row['id']=='preferencesAdvanced'+str(index)
                for row in result['widgets']),('Unexpected reference disclosure',categories[index]['category'])
        dialog=widget(result,'redesignPreferences')
        assert abs(dialog['dpr']-float(case.record['scale']))<0.01
        native_region=settings_window_region(case,dialog)
        try:
            layout_fields=check_settings_layout(result,index,compact=dialog['width']<900)
        except AssertionError as failure:
            if not survey:raise
            layout_fields=[]
            case.record.setdefault('layout_diagnostic_failures',[]).append({'label':label,'failure':repr(failure)})
            records.setdefault('failures',{})['settings-layout']='Original geometry assertions failed; inspect layout_diagnostic_failures. This survey cannot establish acceptance.'
        file=next(row for row in result['widget_captures'] if row['widget']==dialog['node'])
        assert file['saved']
        with Image.open(case.evidence/file['file']) as original:
            image=original.convert('RGBA')
            if dialog.get('content_backdrop_ready'):
                # QWidget::grab omits the composition root. Its header is now
                # painted once as a rectangle, then rounded together with the
                # live blur/UI by that root. Require the separate composed gate.
                assert image.getpixel((0,0))[3]==255,('unexpected raw header alpha',label)
            else:
                assert image.getpixel((0,0))[3]==0,('opaque outside rounded settings card',label)
            rgb=image.getpixel((round(image.width*0.7),round(30*dialog['dpr'])))[:3]
            expected=(7,7,7) if dark else (213,213,213)
            assert max(abs(a-b) for a,b in zip(rgb,expected))<=1,('header band',label,rgb)
            # Original999:5047 is#0e0e0e at95% over background blur. Check
            # the actual paint alpha in the blank gutter; this establishes the
            # tint only, never the Windows compositor's blurred picture.
            surface=image.getpixel((round(225*dialog['dpr']),round(70*dialog['dpr'])))
            expected_surface=(14,14,14,242) if dark else (231,231,231,242)
            assert max(abs(a-b) for a,b in zip(surface,expected_surface))<=1,('Reference translucent surface',label,surface,expected_surface)
        case.record.setdefault('settings_views',[]).append({'label':label,'category':categories[index]['category'],'capture':file['file'],'dpr':dialog['dpr'],'native_region':native_region,'reference_fields_checked':layout_fields})
        return result
    def selection_focus(case):
        # Exercise Qt's real mouse/Tab path and inspect the painted item edge.
        # Verify the input-device transition, including returning to the mouse.
        def outline(label):
            snapshot=case.inspect(label,'snapshot','--capture')
            nav=widget(snapshot,'preferencesCategories')
            assert nav['focused'],('Category view did not receive real focus',label)
            selected=[row for row in nav['rendered_rows'] if row['selected']]
            assert len(selected)==1,(label,selected)
            row=selected[0]
            viewport=next(item for item in snapshot['widgets'] if item['parent']==nav['node']
                and item['id']=='qt_scrollarea_viewport')
            nodes={item['node']:item for item in snapshot['widgets']}
            dialog=widget(snapshot,'redesignPreferences')
            x=y=0
            current=viewport
            while current['node']!=dialog['node']:
                x+=current['x'];y+=current['y']
                current=nodes[current['parent']]
            dpr=dialog['dpr']
            left=round((x+row['x']+row['width']-8)*dpr)
            right=round((x+row['x']+row['width'])*dpr)
            top=round((y+row['y']+row['height']/3)*dpr)
            bottom=round((y+row['y']+row['height']*2/3)*dpr)
            capture=next(item for item in snapshot['widget_captures'] if item['widget']==dialog['node'])
            assert capture['saved']
            accent=tuple(bytes.fromhex(dialog['palette_highlight'].removeprefix('#')))
            with Image.open(case.evidence/capture['file']) as original:
                image=original.convert('RGB')
                assert 0<=left<right<=image.width and 0<=top<bottom<=image.height
                pixels=sum(max(abs(a-b) for a,b in zip(image.getpixel((px,py)),accent))<=2
                    for px in range(left,right) for py in range(top,bottom))
            return snapshot,pixels,capture['file']
        case.native('category-focus-mouse','preferencesCategories')
        mouse,mouse_pixels,mouse_capture=outline('category-focus-mouse-painted')
        snapshot=case.native('category-focus-tab-start','preferencesSearch')
        seen=set()
        while not widget(snapshot,'preferencesCategories')['focused']:
            focused=[item for item in snapshot['widgets'] if item['focused']]
            assert len(focused)==1,('Expected one native Tab target',focused)
            target=focused[0]
            identity=(target['node'],target['id'])
            assert identity not in seen,('Tab traversal never reached categories',seen)
            seen.add(identity)
            snapshot=case.inspect('category-focus-tab-'+str(len(seen)),'widget_key',
                '--node',str(target['node']),'--key','0x1000001')
        keyboard,keyboard_pixels,keyboard_capture=outline('category-focus-keyboard-painted')
        case.native('category-focus-mouse-return','preferencesCategories')
        returned,returned_pixels,returned_capture=outline('category-focus-mouse-return-painted')
        failures=[]
        if mouse_pixels:failures.append('Mouse selection has a keyboard outline')
        if not keyboard_pixels:failures.append('Keyboard category selection lost its visible focus outline')
        if returned_pixels:failures.append('Mouse did not clear the keyboard-only outline')
        case.record['category_selection_focus']={'mouse_outline_pixels':mouse_pixels,
            'keyboard_outline_pixels':keyboard_pixels,'mouse_return_outline_pixels':returned_pixels,
            'captures':[mouse_capture,keyboard_capture,returned_capture],
            'failures':failures,'passed':not failures,
            'scope':'Actual painted item-edge pixels after mouse/Tab/mouse events on the owned inactive desktop.'}
        if failures:
            # Preserve this failure while collecting the remaining independent
            # category/layout/behavior checks from the same completed assembly.
            # It still rejects both this case and the overall acceptance result.
            records.setdefault('failures',{})['settings-category-focus']=failures
        save()
    def edit(case,label,target,value,scroll):
        case.reveal(label+'-reveal',target,scroll)
        case.native(label+'-focus',target)
        case.inspect(label+'-select','widget_key','--target',target,'--key','0x41','--modifiers','0x4000000')
        case.inspect(label+'-type','widget_key','--target',target,'--key','0','--text='+str(value))
        return case.inspect(label+'-commit','widget_key','--target',target,'--key','0x1000001')
    def behaviour(case):
        opened=case.inspect('behaviour-open','key','--key','0x50','--modifiers','0x4000000')
        original_config=opened['settings_config']
        first=select(case,2,'behaviour-privacy')
        assert widget(first,'value-save-playback-position')['checked']
        case.reveal('scrobbler-reveal','value-extraintf-audioscrobbler','preferencesScroll2')
        scoped=case.native('scrobbler-stage','value-extraintf-audioscrobbler')
        assert widget(scoped,'value-lastfm-username')['enabled']
        select(case,3,'behaviour-controls')
        case.reveal('remote-reveal','value-extraintf-http','preferencesScroll3')
        scoped=case.native('remote-stage','value-extraintf-http')
        assert widget(scoped,'value-http-port')['enabled']
        # Search exercises the native module route, not a second configuration
        # owner. Both presentation switches must track edits to that same key.
        case.native('search-shared-focus','preferencesSearch')
        case.inspect('search-shared-type','widget_key','--target','preferencesSearch','--key','0','--text','extraintf')
        case.native('search-shared-results','preferencesResults')
        case.inspect('search-shared-first','widget_key','--target','preferencesResults','--key','0x1000010')
        shared=case.inspect('search-shared-open','widget_key','--target','preferencesResults','--key','0x1000004')
        modules=widget(shared,'value-native-extraintf')['text'].split(':')
        assert 'audioscrobbler' in modules and 'http' in modules,modules
        edit(case,'shared-native-edit','value-native-extraintf','gestures','preferencesScroll2')
        scoped=select(case,2,'shared-privacy')
        assert not widget(scoped,'value-extraintf-audioscrobbler')['checked']
        scoped=select(case,3,'shared-controls')
        assert not widget(scoped,'value-extraintf-http')['checked']
        case.native('cancel-shared-draft','preferencesCancel')
        case.inspect('reopen-after-cancel','key','--key','0x50','--modifiers','0x4000000')
        scoped=select(case,2,'cancelled-privacy')
        assert not widget(scoped,'value-extraintf-audioscrobbler')['checked']
        select(case,0,'all-settings-general')
        advanced=case.reveal('all-settings-advanced-reveal','preferencesAdvanced0','preferencesScroll0')
        if not widget(advanced,'preferencesAdvanced0')['checked']:
            case.native('all-settings-expand','preferencesAdvanced0')
        case.reveal('all-settings-commands-reveal','preferencesAction-vlc-commands','preferencesScroll0')
        case.native('all-settings-commands','preferencesAction-vlc-commands')
        browser=case.inspect('all-settings-browser','widget_click','--menu-action','All VLC settings…')
        inventory=widget(browser,'redesignPreferences')
        keys=set(inventory['option_keys'])
        assert len(keys)==inventory['option_count']
        # CONFIG_ITEM_KEY entries use the dedicated shortcut editor. Derive
        # their exact names from this runtime's pinned native declarations,
        # including the fork's qt-key-* entries; a key-name prefix is not a type.
        declared_shortcuts=set()
        for name in ('src/libvlc-module.c','modules/gui/qt/qt.cpp'):
            native_source=subprocess.check_output(['git','-C',str(repo),'show',records['source_commit']+':'+name],text=True)
            for key in re.findall(r'\badd_key\(\s*"([^"]+)"',native_source):
                declared_shortcuts.update((key,'global-'+key))
            declared_shortcuts.update(re.findall(r'add_string_inner\(\s*CONFIG_ITEM_KEY\s*,\s*"([^"]+)"',native_source))
        catalog=subprocess.check_output(['git','-C',str(repo),'show',records['source_commit']+':modules/gui/qt/util/vlchotkeyconverter.hpp'],text=True)
        declared_shortcuts.update('qt-key-'+key for key in re.findall(r'^\s*X\("([^"]+)"',catalog,re.M))
        shortcut_keys=keys & declared_shortcuts
        count=widget(browser,'preferencesResults')['model_count']
        assert count==len(keys-shortcut_keys),('Native non-shortcut option coverage',count,len(keys),sorted(shortcut_keys))
        case.record['native_option_browser']={'public_native_options':len(keys),
            'non_shortcut_browser_rows':count,'dedicated_shortcut_option_keys':sorted(shortcut_keys),
            'shortcut_route':'Controls / Edit Keyboard Shortcuts; preserved native hotkey editor'}
        case.native('engine-search-focus','preferencesSearch')
        case.inspect('engine-search-type','widget_key','--target','preferencesSearch','--key','0','--text','qt-playback-engine')
        case.native('engine-search-results','preferencesResults')
        case.inspect('engine-search-first','widget_key','--target','preferencesResults','--key','0x1000010')
        engine=case.inspect('engine-search-open','widget_key','--target','preferencesResults','--key','0x1000004')
        assert widget(engine,'value-native-qt-playback-engine')['current_text'] in ('VLC','MPV')
        reference=select(case,4,'return-reference-playback')
        assert not any(row['id']=='preferencesAllOptions4' for row in reference['widgets'])
        select(case,7,'color-subtitles')
        edit(case,'color-invalid','value-freetype-color','#12','preferencesScroll7')
        invalid=case.native('color-invalid-save','preferencesSave')
        assert any('six-digit hexadecimal' in row.get('text','') for row in invalid['widgets'])
        case.inspect('color-invalid-dismiss','widget_click','--widget-text','OK')
        edit(case,'color-correct','value-freetype-color','#A1B2C3','preferencesScroll7')
        edit(case,'language-custom','value-sub-language','jpn,eng','preferencesScroll7')
        edit(case,'font-size-invalid','value-sub-text-scale-size','9','preferencesScroll7')
        invalid=case.native('font-size-invalid-save','preferencesSave')
        assert any('10–500' in row.get('text','') for row in invalid['widgets'])
        case.inspect('font-size-invalid-dismiss','widget_click','--widget-text','OK')
        automatic=edit(case,'font-size-automatic','value-sub-text-scale-size','Automatic','preferencesScroll7')
        assert widget(automatic,'value-sub-text-scale-size')['current_text']=='Automatic'
        literal=edit(case,'font-size-percent-label','value-sub-text-scale-size','150%','preferencesScroll7')
        assert widget(literal,'value-sub-text-scale-size')['current_text']=='150%'
        resized=edit(case,'font-size-custom','value-sub-text-scale-size','125','preferencesScroll7')
        assert widget(resized,'value-sub-text-scale-size')['current_text']=='125%'
        assert widget(resized,'value-sub-text-scale-size')['item_count']>=5
        select(case,5,'snapshot-dimensions')
        focused=case.reveal('snapshot-dimensions-reveal','value-snapshot-width-size','preferencesScroll5')
        visited=set()
        while not widget(focused,'value-snapshot-width-size')['focused']:
            rows={row['node']:row for row in focused['widgets']}
            def focused_ancestor(row):
                while row['parent']>=0:
                    row=rows[row['parent']]
                    if row['focused']:return True
                return False
            # A focus proxy and its owner can both report hasFocus(). Keep the
            # outer focused owner that receives the real native Tab event.
            targets=[row for row in rows.values() if row['focused'] and not focused_ancestor(row)]
            assert len(targets)==1,('Expected one snapshot Tab target',targets)
            target=targets[0]
            identity=(target['node'],target['id'])
            assert identity not in visited,('Tab traversal never reached snapshot size',visited)
            visited.add(identity)
            focused=case.inspect('snapshot-focus-tab-'+str(len(visited)),'widget_key',
                '--node',str(target['node']),'--key','0x1000001')
        case.inspect('snapshot-original-first','widget_key','--target','value-snapshot-width-size','--key','0x1000010')
        preset=case.inspect('snapshot-preset','widget_key','--target','value-snapshot-width-size','--key','0x1000015')
        assert widget(preset,'value-snapshot-width-size')['current_text']=='1920 × 1080'
        original=case.inspect('snapshot-original-restore','widget_key','--target','value-snapshot-width-size','--key','0x1000010')
        assert widget(original,'value-snapshot-width-size')['current_text']=='Original size'
        select(case,4,'native-track-chooser')
        edit(case,'native-track-invalid','value-audio-track','-','preferencesScroll4')
        invalid=case.native('native-track-invalid-save','preferencesSave')
        assert any('track index' in row.get('text','') for row in invalid['widgets'])
        case.inspect('native-track-invalid-dismiss','widget_click','--widget-text','OK')
        edit(case,'native-track-index','value-audio-track','0','preferencesScroll4')
        select(case,2,'privacy-after-color')
        edit(case,'history-exclusion','value-history-exclude','private-*;*.secret','preferencesScroll2')
        case.reveal('position-off-reveal','value-save-playback-position','preferencesScroll2')
        case.native('position-off','value-save-playback-position')
        select(case,3,'save-controls')
        edit(case,'short-jump','value-short-jump-size','7','preferencesScroll3')
        select(case,6,'save-audio')
        case.reveal('equalizer-reveal','preferencesAction-equalizer','preferencesScroll6')
        case.native('equalizer-open','preferencesAction-equalizer')
        edit(case,'equalizer-band','equalizerValue0','2.5','preferencesScroll6')
        select(case,1,'save-interface')
        case.reveal('tree-view-reveal','value-playlist-tree','preferencesScroll1')
        case.native('tree-view-stage','value-playlist-tree')
        select(case,0,'save-general')
        advanced=case.reveal('save-advanced-reveal','preferencesAdvanced0','preferencesScroll0')
        if not widget(advanced,'preferencesAdvanced0')['checked']:
            case.native('save-advanced','preferencesAdvanced0')
        edit(case,'invalid-extra','value-extra-options','--m4-invalid-option=1','preferencesScroll0')
        failed=case.native('reject-invalid-save','preferencesSave')
        assert any('m4-invalid-option' in row.get('text','') for row in failed['widgets'])
        case.inspect('dismiss-invalid-save','widget_click','--widget-text','OK')
        scoped=select(case,2,'failed-save-retains-draft')
        assert widget(scoped,'value-history-exclude')['text']=='private-*;*.secret'
        select(case,0,'correct-extra-general')
        edit(case,'valid-extra','value-extra-options','--rate=1.5','preferencesScroll0')
        config_file=portable/'vlcrc'
        original_file=hashlib.sha256(config_file.read_bytes()).hexdigest()
        k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,W.LPVOID,W.DWORD,W.DWORD,W.HANDLE]
        k.CreateFileW.restype=W.HANDLE
        held=k.CreateFileW(str(config_file),0x80000000,1,None,3,0x80,None)
        assert held and held!=ctypes.c_void_p(-1).value,ctypes.WinError(ctypes.get_last_error())
        try:
            failed=case.native('locked-save-rejected','preferencesSave')
            assert any('staged edits remain' in row.get('text','') for row in failed['widgets'])
            assert failed['settings_config']==original_config,('Native configuration was not rolled back',failed['settings_config'],original_config)
            assert hashlib.sha256(config_file.read_bytes()).hexdigest()==original_file
        finally:assert k.CloseHandle(held)
        case.inspect('locked-save-dismiss','widget_click','--widget-text','OK')
        retained=select(case,2,'locked-save-retains-privacy-draft')
        assert widget(retained,'value-history-exclude')['text']=='private-*;*.secret'
        assert not widget(retained,'value-save-playback-position')['checked']
        saved=case.native('save-settings-draft','preferencesSave')
        assert saved['settings_config']=={'save-playback-position':0,'short-jump-size':7,'playlist-tree':1}
        case.click('tree-queue-open','playqueueToggle')
        queue=case.inspect('tree-queue-ready','snapshot','--await-target','playlistpopup','--await-property','width',
            '--await-value','300','--await-comparison','at_least','--capture')
        folders=[row for row in queue['tree'] if row['id'].startswith('queueFolder-') and row['visible']]
        assert len(folders)==1,folders
        folder=folders[0]['id']
        collapsed=case.click('tree-folder-collapse',folder,'--capture')
        assert not any(row['visible'] and row['id']=='delegate' and row.get('url')==(fixtures/'control.mkv').as_uri()
                       for row in collapsed['tree'])
        expanded=case.click('tree-folder-expand',folder,'--capture')
        assert any(row['visible'] and row['id']=='delegate' and row.get('url')==(fixtures/'control.mkv').as_uri()
                   for row in expanded['tree'])
        case.click('tree-queue-close','playqueueToggle')
        case.inspect('readback-saved-settings','key','--key','0x50','--modifiers','0x4000000')
        scoped=select(case,2,'saved-privacy')
        assert widget(scoped,'value-history-exclude')['text']=='private-*;*.secret'
        assert not widget(scoped,'value-save-playback-position')['checked']
        scoped=select(case,3,'saved-controls')
        assert widget(scoped,'value-short-jump-size')['value']==7
        scoped=select(case,4,'saved-native-track')
        assert widget(scoped,'value-audio-track')['text']=='0'
        scoped=select(case,5,'saved-snapshot-size')
        assert widget(scoped,'value-snapshot-width-size')['current_text']=='Original size'
        case.reveal('saved-snapshot-picture-reveal','value-snapshot-width-size','preferencesScroll5')
        case.inspect('saved-snapshot-picture','snapshot','--capture')
        saved_text=config_file.read_text(encoding='utf-8')
        for key in ('snapshot-width','snapshot-height'):
            # Native Save comments values equal to the compiled default.
            assert re.search(r'^#?'+key+r'=-1\s*$',saved_text,re.M),('Original snapshot dimensions were not saved',key)
        scoped=select(case,7,'saved-subtitles-color')
        assert widget(scoped,'value-freetype-color')['text']=='#A1B2C3'
        assert widget(scoped,'value-sub-language')['current_text']=='jpn,eng'
        assert widget(scoped,'value-sub-text-scale-size')['current_text']=='125%'
        case.reveal('saved-font-picture-reveal','value-sub-text-scale-size','preferencesScroll7')
        case.inspect('saved-font-picture','snapshot','--capture')
        select(case,6,'saved-audio')
        case.reveal('saved-equalizer-reveal','preferencesAction-equalizer','preferencesScroll6')
        scoped=case.native('saved-equalizer-open','preferencesAction-equalizer')
        assert widget(scoped,'equalizerValue0')['value']==2.5
        select(case,10,'plugin-rescan-performance')
        case.reveal('plugin-rescan-reveal','preferencesAction-rescan-plugins','preferencesScroll10')
        scanned=case.native('plugin-rescan','preferencesAction-rescan-plugins','--await-service','redesignPreferences',
            '--await-property','pluginScanActive','--await-value','false')
        assert any('plugin cache has been rebuilt' in row.get('text','') for row in scanned['widgets'])
        case.inspect('plugin-rescan-dismiss','widget_click','--widget-text','OK')
        case.native('behaviour-close','preferencesClose')
        case.record['settings_behaviour']={'shared_native_and_reference_draft':True,'cancel':True,
            'invalid_save_preserves_draft':True,'locked_save_rolls_back_native_memory_and_file':True,
            'failed_save_preserves_draft_for_retry':True,'typed_save_readback':True,'equalizer':True,'native_plugin_rescan':True,
            'invalid_color_rejected':True,'color_and_custom_language_readback':True,'native_track_validation_readback':True,
            'formatted_font_size_readback':True,'original_snapshot_dimensions_readback':True}
    def check_saved_startup(case):
        for name,engine,extra,rate in [(name+'-'+engine,engine,extra,rate) for engine in ('vlc','mpv')
                for name,extra,rate in [('saved-extra-startup',(),1.5),('explicit-extra-priority',('--rate=1.75',),1.75)]]:
            restarted=Case(name,engine=engine,media=fixtures/'control.mkv',reused_profile=case.path/'profile',extra=extra)
            try:
                result=restarted.inspect('saved-rate-effective','snapshot','--await-core','rate','--await-value',str(rate))
                assert abs(result['core']['rate']-rate)<0.001
                restarted.inspect('restart-settings','key','--key','0x50','--modifiers','0x4000000')
                result=select(restarted,2,'restart-privacy')
                assert widget(result,'value-history-exclude')['text']=='private-*;*.secret'
                assert not widget(result,'value-save-playback-position')['checked']
                result=select(restarted,7,'restart-subtitles')
                assert widget(result,'value-freetype-color')['text']=='#A1B2C3'
                assert widget(result,'value-sub-language')['current_text']=='jpn,eng'
                assert widget(result,'value-sub-text-scale-size')['current_text']=='125%'
                result=select(restarted,5,'restart-snapshot-size')
                assert widget(result,'value-snapshot-width-size')['current_text']=='Original size'
                result=select(restarted,4,'restart-track')
                assert widget(result,'value-audio-track')['text']=='0'
                restarted.native('restart-close-settings','preferencesClose')
                restarted.close(True)
            finally:restarted.close()
    if resume_behaviour or resume_input:
        recovery_name=('settings-1-input-disclosure-resumed' if input_disclosure_recovery else 'settings-1-input-behaviour-resumed') if resume_input else 'settings-1-behaviour-resumed'
        recovery=Case(recovery_name,scale='1',media=fixtures/'control.mkv',reused_profile=root/('settings-1-input-behaviour-resumed/profile' if resume_input and input_disclosure_recovery else 'settings-1/profile'))
        try:
            behaviour(recovery)
            recovery.close(True)
        finally:recovery.close()
        check_saved_startup(recovery)
    if resume_settings:
        lifecycle=Case('settings-1-5-lifecycle-resumed' if resume_external_transition else 'settings-1-5-lifecycle',scale='1.5',media=fixtures/'control.mkv')
        try:
            lifecycle.inspect('recheck-open','key','--key','0x50','--modifiers','0x4000000')
            select(lifecycle,0,'recheck-general')
            lifecycle.native('recheck-dark','preferencesTheme2')
            lifecycle.native('recheck-save','preferencesSave')
            lifecycle.inspect('recheck-reopen','key','--key','0x50','--modifiers','0x4000000')
            lifecycle.inspect('recheck-size','widget_resize','--target','redesignPreferences','--width','1048','--height','865')
            capture(lifecycle,'recheck-dark-normal-0-basic',0,True)
            lifecycle.native('recheck-close','preferencesClose')
            lifecycle.close(True)
        finally:lifecycle.close()
        records['reused_settings_rendering']['fresh_lifecycle_case']=lifecycle.record['name']
        assert lifecycle.record['passed'] and lifecycle.record['owned_desktop_never_observed_as_input']
    for scale in (() if resume_history else ('1.5','2') if resume_behaviour or collect_layouts or resume_input else ('2',) if resume_settings else ('1',) if survey else ('1','1.5','2')):
        case=Case('settings-'+scale.replace('.','-'),scale=scale,media=fixtures/'control.mkv')
        try:
            for dark in ((True,) if survey else (True,False)):
                case.inspect('open-theme-'+str(dark),'key','--key','0x50','--modifiers','0x4000000')
                select(case,0,'theme-general-'+str(dark))
                case.native('stage-theme-'+str(dark),'preferencesTheme'+('2' if dark else '1'))
                case.native('save-theme-'+str(dark),'preferencesSave')
                case.inspect('reopen-theme-'+str(dark),'key','--key','0x50','--modifiers','0x4000000')
                if dark and (scale=='1' or args.settings_input_repair) and not survey:
                    selection_focus(case)
                for narrow in ((False,) if survey else (False,True)):
                    case.inspect('viewport-'+str(dark)+'-'+str(narrow),'widget_resize','--target','redesignPreferences',
                                 '--width','740' if narrow else '1048','--height','700' if narrow else '865')
                    for index,category in enumerate(categories):
                        if args.settings_input_repair and index!=2:continue
                        label=('dark' if dark else 'light')+('-narrow-' if narrow else '-normal-')+str(index)
                        snapshot=select(case,index,label)
                        disclosure=category.get('advanced_disclosure',True)
                        if not disclosure:
                            assert not any(row['id']=='preferencesAdvanced'+str(index) for row in snapshot['widgets']),('Unexpected empty advanced disclosure',index)
                        button=widget(snapshot,'preferencesAdvanced'+str(index)) if disclosure else None
                        if disclosure and button.get('checked'):
                            case.reveal(label+'-reveal-collapse',button['id'],'preferencesScroll'+str(index))
                            case.native(label+'-collapse',button['id'])
                        if index==6:
                            eq=widget(snapshot,'preferencesAction-equalizer')
                            if eq.get('checked'):
                                case.reveal(label+'-reveal-close-equalizer',eq['id'],'preferencesScroll6')
                                case.native(label+'-close-equalizer',eq['id'])
                        case.inspect(label+'-top','widget_scroll','--target','preferencesScroll'+str(index),'--delta','24000')
                        snapshot=capture(case,label+'-basic',index,dark)
                        check_labels(snapshot,index,False)
                        if index==0 and not narrow and not survey:
                            popup=case.native(label+'-language-popup-open','preferencesLanguage')
                            animation_observations=0
                            while not any(item['id']=='preferencesLanguage-choices' for item in popup['widgets']):
                                # Qt's combo roll effect temporarily owns the
                                # visible surface while the real list is hidden.
                                # Observe its actual transition, without another
                                # click, a fixed delay or repeated image captures.
                                assert any(item['type']=='QRollEffect' for item in popup['widgets']),('Choice list absent outside popup animation',label)
                                animation_observations+=1
                                popup=case.inspect(label+'-language-popup-transition-'+str(animation_observations),'snapshot')
                            popup=case.inspect(label+'-language-popup','snapshot','--capture')
                            choices=widget(popup,'preferencesLanguage-choices')
                            assert choices['rendered_rows'],('No actual choice rows rendered',label)
                            assert choices['palette_text'].lower()==('#8f8f8f' if dark else '#2e2e2e'),('Popup text does not follow the settings palette',label,choices['palette_text'])
                            assert all(any(column for column in row['columns']) for row in choices['rendered_rows'])
                            case.inspect(label+'-language-popup-close','widget_key','--target',choices['id'],'--key','0x1000000')
                            case.record.setdefault('settings_choice_popups',[]).append({'label':label,'palette_text':choices['palette_text'],'visible_rows':len(choices['rendered_rows'])})
                        if disclosure:
                            case.reveal(label+'-reveal-advanced','preferencesAdvanced'+str(index),'preferencesScroll'+str(index))
                            expanded=case.native(label+'-expand','preferencesAdvanced'+str(index))
                        if index==6:
                            eq=widget(expanded,'preferencesAction-equalizer')
                            if not eq.get('checked'):
                                case.reveal(label+'-reveal-equalizer',eq['id'],'preferencesScroll6')
                                case.native(label+'-equalizer',eq['id'])
                        if disclosure:
                            snapshot=capture(case,label+'-expanded',index,dark)
                            check_labels(snapshot,index,True)
                        case.inspect(label+'-expanded-top','widget_scroll','--target','preferencesScroll'+str(index),'--delta','24000')
                        seen=set()
                        while not survey:
                            snapshot=capture(case,label+'-page-'+str(len(seen)),index,dark)
                            area=widget(snapshot,'preferencesScroll'+str(index))
                            state=area['scroll_value']
                            if state==area['scroll_maximum']:break
                            assert state not in seen,('settings page cannot scroll to end',label,area)
                            seen.add(state)
                            # A real wheel event advances the owned Qt viewport;
                            # observed scrollbar state, not elapsed time, ends it.
                            case.inspect(label+'-scroll-'+str(len(seen)),'widget_scroll','--target',area['id'],'--delta','-480')
                case.native('close-settings-'+str(dark),'preferencesClose')
            if scale=='1' and not survey:behaviour(case)
            case.close(not case.record.get('category_selection_focus',{}).get('failures'))
        finally:case.close()
        if survey:
            return # A bounded all-category diagnosis, never stage acceptance.
        if scale=='1':
            check_saved_startup(case)

    # A displayed font fallback must not replace the user's unavailable font
    # when the new menu saves an unrelated native setting.
    if not resume_history:
        seed=root/'settings-missing-font-seed'
        seed.mkdir()
        families={'freetype-font':'M4 Missing Family 20261103',
                  'freetype-monofont':'M4 Missing Mono Family 20261103'}
        (seed/'vlcrc').write_text('metadata-network-access=0\n'+
            ''.join(key+'='+value+'\n' for key,value in families.items()),encoding='utf-8')
        legacy=Case('settings-missing-font-preservation',media=fixtures/'control.mkv',reused_profile=seed)
        try:
            legacy.inspect('legacy-font-open','key','--key','0x50','--modifiers','0x4000000')
            select(legacy,7,'legacy-font-subtitles')
            legacy.reveal('legacy-font-advanced-reveal','preferencesAdvanced7','preferencesScroll7')
            legacy.native('legacy-font-advanced','preferencesAdvanced7')
            select(legacy,2,'legacy-font-unrelated-privacy')
            legacy.reveal('legacy-font-position-reveal','value-save-playback-position','preferencesScroll2')
            legacy.native('legacy-font-unrelated-edit','value-save-playback-position')
            legacy.native('legacy-font-save','preferencesSave')
            legacy.close(True)
            saved=(legacy.path/'profile/vlcrc').read_text(encoding='utf-8')
            for key,value in families.items():
                found=re.search(r'^'+re.escape(key)+r'=(.*)$',saved,re.M)
                assert found and found.group(1).strip()==value,('Missing font was replaced',key,found.group(1) if found else None)
            legacy.record['missing_native_fonts_preserved']=families
            save()
        finally:legacy.close()

    # Seed history through real playback, then use the new native Privacy
    # action. Its cancel/confirm paths must update the existing ML owner rather
    # than merely clearing a rendered list or deleting media records/files.
    media=fixtures/'control.mkv'
    media_hash=hashlib.sha256(media.read_bytes()).hexdigest()
    history=Case(('settings-clear-history-view-target' if history_view_recovery else 'settings-clear-history-resumed') if resume_history else 'settings-clear-history',media=media,extra=('--media-library','--save-recentplay'))
    try:
        history.inspect('history-paused','snapshot','--await-core','state','--await-value','3')
        history.click('history-play','playButton','--await-core','state','--await-value','2')
        ended=history.inspect('history-natural-eof','snapshot','--await-core','state','--await-value','0')
        library='qrc:///qt/qml/VLC/Player/PlayerLibraryDisplay.qml'
        if not any(row['id']=='viewLoader' and row.get('source')==library for row in ended['tree']):
            history.inspect('history-open-library','click','--name','Back to media',
                '--await-target','viewLoader','--await-property','source','--await-value',json.dumps(library))
        mounted=history.inspect('history-library-mounted','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
        library_target=mounted['library']['id']
        assert library_target in ('compactLibrary','fullLibrary')
        before=history.click('history-recent','libraryNav_recent','--await-target',library_target,
            '--await-property','itemCount','--await-value','1','--await-comparison','at_least')
        assert before['library']['id']==library_target
        count=before['library']['indexed_model_count']
        history.inspect('history-open-settings','key','--key','0x50','--modifiers','0x4000000')
        select(history,2,'history-privacy')
        history.reveal('history-clear-reveal','preferencesAction-clear-history','preferencesScroll2')
        history.native('history-clear-request','preferencesAction-clear-history')
        history.inspect('history-clear-cancel','widget_click','--widget-text','Cancel')
        preserved=history.native('history-cancel-close','preferencesClose','--await-target',library_target,
            '--await-property','itemCount','--await-value',str(count))
        assert preserved['library']['indexed_model_count']==count
        history.inspect('history-confirm-open-settings','key','--key','0x50','--modifiers','0x4000000')
        select(history,2,'history-confirm-privacy')
        history.reveal('history-confirm-reveal','preferencesAction-clear-history','preferencesScroll2')
        history.native('history-confirm-request','preferencesAction-clear-history')
        history.inspect('history-clear-confirm','widget_click','--widget-text','Yes','--await-target',library_target,
            '--await-property','itemCount','--await-value','0')
        cleared=history.native('history-confirm-close','preferencesClose')
        assert cleared['library']['indexed_model_count']==0
        history.close(True)
        databases=[]
        for path in (history.path/'profile').rglob('*.db'):
            with path.open('rb') as stream:
                if stream.read(16)!=b'SQLite format 3\0':continue
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as database:
                if not database.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='Media'").fetchone():continue
                rows=database.execute('SELECT id_media,play_count,last_played_date FROM Media').fetchall()
                assert rows and all(row[1]==0 and row[2] is None for row in rows),rows
                databases.append({'database':str(path.relative_to(history.path/'profile')),'retained_media':len(rows)})
        assert len(databases)==1,databases
        assert hashlib.sha256(media.read_bytes()).hexdigest()==media_hash
        history.record['native_history_clear']={'cancel_retains_recent_count':count,
            'confirmed_recent_count':0,'native_database':databases[0],'media_sha256_unchanged':media_hash}
        save()
    finally:history.close()

    # Documentation uses an empty owned library and no file-logging path. Keep
    # the native pixels unchanged; do not put test paths or media in the README.
    documentation=Case('settings-readme',extra=('--no-file-logging','--logfile='))
    try:
        documentation.inspect('documentation-open-settings','key','--key','0x50','--modifiers','0x4000000')
        select(documentation,0,'documentation-general')
        documentation.native('documentation-dark-theme','preferencesTheme2')
        documentation.native('documentation-save-theme','preferencesSave')
        documentation.inspect('documentation-reopen-settings','key','--key','0x50','--modifiers','0x4000000')
        select(documentation,0,'documentation-final-general')
        documentation.inspect('documentation-reference-size','widget_resize','--target','redesignPreferences',
            '--width','1048','--height','865')
        capture(documentation,'readme-general',0,True)
        documentation.native('documentation-close-settings','preferencesClose')
        documentation.close(True)
    finally:documentation.close()


def seek_policy():
    """Diagnostic comparison of VLC's public absolute-time seek and cue position seek."""
    case=Case('absolute-time-seek-probe',media=fixtures/'embedded-text.mkv')
    try:
        case.inspect('paused','snapshot','--await-core','state','--await-value','3')
        case.click('open-playback-tools','toolsButton')
        case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
            '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
        case.inspect('close-settings','key','--key','0x1000000')
        base=case.inspect('before-delay')['core']['subtitle_delay_ms']
        case.click('delay-later','subtitleDelayLater','--await-core','subtitle_delay_ms','--await-value',base+50)
        case.click('delay-earlier','subtitleDelayEarlier','--await-core','subtitle_delay_ms','--await-value',base)
        case.key('open-goto-time',0x54,modifiers=0x4000000,text='t')
        snapshot=case.inspect('time-editor')
        editors=[widget for widget in snapshot['widgets'] if widget['type']=='QTimeEdit']
        assert len(editors)==1,editors
        node=editors[0]['node']
        case.inspect('focus-time-editor','widget_click','--node',node)
        case.inspect('select-seconds','widget_key','--node',node,'--key','0x1000011')
        edited=case.inspect('one-second','widget_key','--node',node,'--key','0x1000013')
        assert any(widget['type']=='QTimeEdit' and widget.get('text')=='00H:00m:01s' for widget in edited['widgets']), 'Go to Time diagnostic did not enter one second'
        case.inspect('absolute-time-result','widget_click','--widget-text','Go','--await-core','time_seconds','--await-value','1','--await-tolerance','0.2')
        case.close(True)
    finally:case.close()


def updates():
    for mode, expected in [('unavailable',4),('malformed',4),('current',2),('newer',3)]:
        Peer.mode=mode
        reused=None
        if mode=='unavailable':
            first=Case('updates-first-welcome',welcome=True,updates=True)
            calls_before=len(Peer.calls)
            try:
                initial=first.inspect('first-welcome')
                assert initial['customization']['onboardingVisible']
                for page in ('theme','font'): first.click('next-'+page,'onboardingNext')
                first.inspect('reveal-free-font','focus','--target','onboardingFontFallback')
                first.click('shortcut-page','onboardingFontFallback')
                first.click('finish-first-start','onboardingNext')
                first.close(True)
                assert len(Peer.calls)==calls_before, 'Privacy setup did not defer the automatic request'
                reused=first.path/'profile'
            finally: first.close()
        case=Case('updates-' + mode,updates=True,welcome=reused is not None,reused_profile=reused)
        try:
            result=case.inspect('automatic-result','snapshot','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value',expected,'--capture')
            if reused: assert not result['customization']['onboardingVisible']
            if expected!=3:
                assert not any(node.get('name') in ('Re-check','Open release page') and node['visible'] for node in result['tree'])
                assert not any(widget['type']=='UpdateDialog' for widget in result['widgets'])
            case.record['observed_status']=result['update']['status']
            if expected==3:
                assert result['update']['url']=='https://github.com/Darkaxt/vlc/releases/tag/redesign-v'+newer_version
                assert any(node.get('name')=='Open release page' and node['visible'] for node in result['tree']) or any(
                    widget.get('text','').replace('&','')=='Open release page' for widget in result['widgets'])
            if mode == 'unavailable':
                case.inspect('manual-check-library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
                open_vlc_commands(case,'retained-vlc')
                case.inspect('open-help','widget_click','--menu-action','Help')
                failure=case.inspect('explicit-check-error','widget_click','--menu-action','Check for Updates...', '--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','4','--capture')
                assert any(node.get('name')=='Re-check' and node['visible'] for node in failure['tree']) or any(widget.get('text')=='&Recheck version' for widget in failure['widgets'])
                Peer.mode='current'
                if any(node.get('name')=='Re-check' and node['visible'] for node in failure['tree']):
                    retried=case.inspect('manual-retry','click','--name','Re-check','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2','--capture')
                else:
                    retried=case.inspect('manual-retry','widget_click','--widget-text','Recheck version','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2','--capture')
                assert retried['update']['status']==2
                labels=[node.get('text','') for node in retried['tree'] if node['visible'] and 'You have the latest version' in node.get('text','')]
                labels += [widget.get('text','') for widget in retried['widgets'] if 'latest available Modern VLC Fork release' in widget.get('text','')]
                case.record['manual_current_version_labels']=labels
                assert labels and all(fork_version in text for text in labels), 'Update result does not show the fork version'
            case.close(True)
        finally: case.close()
    live=Case('updates-real-https',updates=True,live_updates=True)
    try:
        result=live.inspect('actual-https-result','snapshot','--await-service','forkUpdateModel','--await-property','updateStatus','--await-value','2')
        live.record['actual_https_status']=result['update']['status']
        live.close(True)
    finally: live.close()

try:
    if args.policies:
        assert args.policies.is_file()
        with (root / 'policies.stdout.json').open('wb') as output, (root / 'policies.stderr.log').open('wb') as errors:
            environment = dict(os.environ, TEMP=str(root), TMP=str(root))
            process = IsolatedProcess([str(args.policies.resolve()), str(fixtures)], root, environment, output, errors)
            policy_exit=process.wait()
        records['native_policy_exit_code']=policy_exit
        records['native_policy_executable_sha256']=hashlib.sha256(args.policies.read_bytes()).hexdigest()
        if policy_exit!=0:
            records.setdefault('failures',{})['native_policies']='Native production-policy executable exited '+str(policy_exit)+'; inspect policies.stdout.json and policies.stderr.log'
        else:
            records['native_policies'] = json.loads((root / 'policies.stdout.json').read_text())
            if not records['native_policies']['passed']:
                records.setdefault('failures',{})['native_policies']='Native policy result did not pass'
        save()
    try:
        verify_executable_icon()
    except AssertionError as failure:
        records.setdefault('failures',{})['executable_icon']=repr(failure)
        save()
    for name, operation in [('idle',idle),('settings-backdrop',settings_backdrop),('settings',settings),('menus',menus),('welcome',welcome),('shortcuts',interface_shortcuts),('playback',playback),('subtitles',subtitles),('preview',preview),('icons',icons),('sidebar',sidebar),('updates',updates),('seek-policy',seek_policy)]:
        if name=='settings-backdrop' and args.case!='settings-backdrop':continue
        if args.case=='settings-survey':
            if name!='settings':continue
            records['diagnostic_only']=True
        if args.case=='preview-icons' and name not in ('preview','icons','sidebar'):continue
        if args.case=='correction' and name not in ('playback','preview','icons','sidebar','menus','updates'):continue
        if args.case=='subtitles-mpv':
            if name!='subtitles':continue
            operation=lambda:subtitles(engines=('mpv',))
        if args.case=='playback-subtitles' and name not in ('playback','subtitles'):continue
        if args.case=='subtitle-tracks-diagnostic':
            if name!='subtitles':continue
            operation=lambda:subtitles(False)
        if args.case=='integration-diagnostic':
            if name not in ('welcome','playback','subtitles'):continue
            if name=='subtitles':operation=lambda:subtitles(False)
        if args.case=='onboarding-shortcuts' and name not in ('welcome','shortcuts'):continue
        if name=='seek-policy' and args.case!='seek-policy':continue
        if args.case not in ('all','onboarding-shortcuts','subtitles-mpv','playback-subtitles','integration-diagnostic','subtitle-tracks-diagnostic','preview-icons','correction','settings-survey',name): continue
        try:
            operation()
        except Exception as failure:
            records.setdefault('failures',{})[name]=repr(failure)
            save()
            print(json.dumps({'workflow':name,'failure':repr(failure)}),flush=True)
            # Collect independent acceptance failures from this one complete
            # assembly, but never start another consumer after uncertain exit.
            assert not active_cases and not any(portable.iterdir()), 'Original native consumer/profile has not been released'
    records['passed']=not records.get('failures') and not records.get('diagnostic_only')
finally:
    records['http_peer_calls']=Peer.calls
    server.shutdown();server.server_close();thread.join()
    records['protected_profiles_after'] = profiles()
    records['protected_profiles_unchanged'] = records['protected_profiles_before'] == records['protected_profiles_after']
    if not records['protected_profiles_unchanged']:
        records.setdefault('failures',{})['protected_profiles']='Protected settings changed during observation; attribute the writer before accepting preservation'
        records['passed']=False
    save()
print(json.dumps({'passed':records['passed'],'result':str(root/'result.json')}),flush=True)
raise SystemExit(0 if records['passed'] else 1)
