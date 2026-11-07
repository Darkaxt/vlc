"""M2 complete-workflow native acceptance on owned inactive Windows desktops.

Reuses the app-owned Qt event bridge and one isolated binary copy. Test profiles
are moved only after confirmed native exit; originals/delivered profiles are never
selected. No OS input, activation, desktop switching or execution-kill deadline.
"""
import argparse
import ctypes
import colorsys
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from ctypes import wintypes as W
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import uuid
from PIL import Image
from app_icon_checks import executable_icon, window_icon, qml_mpv_icon_pixels
from isolated_desktop import IsolatedProcess, input_desktop, u, k
from settings_layout_checks import check_settings_layout

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--fixtures', type=Path, required=True)
parser.add_argument('--policies', type=Path, help='Native production-policy test executable from this same managed assembly')
parser.add_argument('--case', choices=['volume-dismiss', 'inline-subtitle-tracks', 'inline-subtitles', 'floating-contrast', 'floating-queue', 'player-panels', 'floating-player', 'm7-regressions', 'audio-visualizer', 'no-library', 'engine-accents', 'engine-icon-pixels', 'engine-icons', 'idle', 'media-previews', 'welcome', 'shortcuts', 'onboarding-shortcuts', 'playback', 'subtitles', 'subtitles-mpv', 'preview', 'icons', 'sidebar', 'menus', 'settings', 'settings-survey', 'settings-backdrop', 'preview-icons', 'correction', 'updates', 'playback-subtitles', 'seek-policy', 'integration-diagnostic', 'subtitle-tracks-diagnostic', 'all'], default='all')
parser.add_argument('--preview-media', type=Path, help='Read-only actual reported media for preview acceptance')
parser.add_argument('--skip-documentation-capture',action='store_true',help='Reuse unchanged completed documentation captures during PNG rendering repair')
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
parser.add_argument('--resume-onboarding-checker',action='store_true',
    help='Retain passed100%% wizard/restart evidence; continue closed150%% keyboard and standalone checks')
parser.add_argument('--resume-media-previews-checker',action='store_true',
    help='Resume closed photo acceptance after correcting keyboard targeting or animation-clock observation')
parser.add_argument('--resume-m7-checker',action='store_true',
    help='Resume closed M7 native acceptance after the client service whitelist and Settings-close selector correction')
parser.add_argument('--resume-m7-lifecycle',action='store_true',
    help='Retain completed modes and VLC no-library cases; finish handover, DPI and the remaining no-library paths')
parser.add_argument('--visualizer-options-only',action='store_true',help='Inspect the complete Figma visualizer/EQ option rendering on the real player')
parser.add_argument('--resume-floating-stopped-observer',action='store_true',help='Retain completed VLC100%% miniplayer evidence after correcting STOPPING versus STOPPED in the observer')
parser.add_argument('--resume-player-panels-observation',action='store_true',
    help='Preserve completed same-binary panel cases and the closed unexpected-minimize evidence; observe only unfinished engine/DPI cases')
parser.add_argument('--resume-floating-hover-observation',action='store_true',
    help='Preserve the closed unsupported-opacity observation and resume the same miniplayer binary')
parser.add_argument('--resume-inline-observation',action='store_true',
    help='Retain completed VLC cases and the closed exact-float MPV observation; resume the same binary with numeric tolerance')
parser.add_argument('--resume-inline-tracks-observation',action='store_true',
    help='Preserve the closed missing snapshot-field failure; verify target clipping through actual click dispatch')
parser.add_argument('--resume-volume-observation',action='store_true',
    help='Preserve the closed unavailable-color-selector failure; resume the same binary using an offered palette color')
args = parser.parse_args()
assert not args.visualizer_options_only or args.case=='m7-regressions'
root, source, fixtures = args.root.resolve(), args.runtime.resolve(), args.fixtures.resolve()
resume_visualizer_options=args.visualizer_options_only and (root/'result.json').is_file()
options_utf8_repair=False
assert root.parent.parent == Path('D:/Temp') and root.parent.name.startswith('vlc-s8-')
resume_empty_survey=args.case=='settings-survey' and (root/'result.json').is_file()
resume_settings=args.resume_settings_after_desktop_change
resume_history=args.resume_settings_history
resume_behaviour=args.resume_settings_behaviour
collect_layouts=args.collect_settings_layouts
resume_input=args.resume_settings_input
resume_menu_quit=args.resume_menu_quit
resume_idle=args.resume_idle_checker
resume_onboarding=args.resume_onboarding_checker
resume_media=args.resume_media_previews_checker
resume_m7=args.resume_m7_checker
resume_m7_lifecycle=args.resume_m7_lifecycle
resume_floating=args.resume_floating_stopped_observer
resume_panels=args.resume_player_panels_observation
resume_hover=args.resume_floating_hover_observation
resume_inline=args.resume_inline_observation
resume_inline_tracks=args.resume_inline_tracks_observation
resume_volume=args.resume_volume_observation
assert not resume_inline or args.case=='inline-subtitles'
assert not resume_hover or args.case=='floating-queue'
assert not resume_panels or args.case=='player-panels'
assert not resume_panels or not any((resume_settings,resume_history,resume_behaviour,collect_layouts,resume_input,resume_menu_quit,resume_idle,resume_onboarding,resume_media,resume_m7,resume_m7_lifecycle,resume_floating,resume_visualizer_options))
assert not resume_floating or args.case=='floating-player'
assert not resume_m7_lifecycle or args.case=='m7-regressions'
assert not resume_m7 or args.case=='m7-regressions'
assert sum((resume_settings,resume_history,resume_behaviour,collect_layouts,resume_input,resume_menu_quit,resume_idle,resume_onboarding,resume_media,resume_m7,resume_m7_lifecycle))<=1
assert not resume_media or args.case=='media-previews'
assert not resume_onboarding or args.case=='onboarding-shortcuts'
assert not resume_idle or args.case=='idle'
assert not resume_menu_quit or args.case=='menus'
assert not (resume_settings or resume_history or resume_behaviour or collect_layouts) or args.case=='settings'
assert not args.settings_input_repair or (args.case=='settings' and not any((resume_settings,resume_history,resume_behaviour,collect_layouts)))
assert not resume_input or (args.case=='settings' and args.settings_input_repair)
assert not root.exists() or resume_volume or resume_inline_tracks or resume_inline or resume_hover or resume_panels or resume_floating or resume_empty_survey or resume_settings or resume_history or resume_behaviour or collect_layouts or resume_input or resume_menu_quit or resume_idle or resume_onboarding or resume_media or resume_m7 or resume_m7_lifecycle or resume_visualizer_options
assert fixtures.is_dir() and (source / 'portable').is_dir() and not any((source / 'portable').iterdir())
plugin = source / 'plugins/gui/libqt_plugin.dll'
assert b'VLC_PLAYER_DIAGNOSTICS_DIR' in plugin.read_bytes()
runtime = root / 'runtime'
m7_observer_repair=False
m7_final_path=False
if resume_volume:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert args.case=='volume-dismiss' and previous['scope']==args.case
    assert not previous['passed'] and previous['protected_profiles_unchanged']
    assert 'Expected one named native widget; matched 0' in previous['failures']['volume-dismiss']
    assert len(previous['cases'])==1 and previous['cases'][0]['exit_code']==0
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/'result-before-unoffered-color-selector.json';assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_inline_tracks:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert args.case=='inline-subtitle-tracks' and previous['scope']==args.case
    assert not previous['passed'] and previous['protected_profiles_unchanged']
    assert previous['failures']['inline-subtitle-tracks']==repr(KeyError('center_visible'))
    assert len(previous['cases'])==1 and previous['cases'][0]['exit_code']==0
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/'result-before-missing-snapshot-field.json';assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_inline:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='inline-subtitles' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert len(previous['cases'])==4 and all(c['passed'] and c['exit_code']==0 for c in previous['cases'][:3])
    assert previous['cases'][-1]['name']=='inline-subtitles-mpv-1' and previous['cases'][-1]['exit_code']==0
    assert 'observation_cancelled_action_not_undone' in previous['failures']['inline-subtitles']
    actual=json.loads((root/'inline-subtitles-mpv-1/evidence/3189d1d4a61c448a8ce44e3e752a827a.json').read_text(encoding='utf-8'))
    assert abs(actual['core']['subtitle_delay_ms']-50)<.001
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/'result-before-exact-float-observation.json';assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_hover:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='floating-queue' and not previous['passed'] and previous['protected_profiles_unchanged']
    hover_eof_resume=len(previous['cases'])==4
    if hover_eof_resume:
        assert all(c['passed'] and c['exit_code']==0 for c in previous['cases'][:3])
        assert previous['cases'][-1]['exit_code']==0
        assert "'state': 0" in previous['failures']['floating-queue']
        assert 'MPV natural EOF reached' in (root/previous['cases'][-1]['name']/'evidence/native-ui.log').read_text(encoding='utf-8')
    else:
        assert len(previous['cases'])==1 and previous['cases'][0]['exit_code']==0
        assert "invalid choice: 'opacity'" in previous['failures']['floating-queue']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/('result-before-hover-fixture-eof.json' if hover_eof_resume else 'result-before-hover-observation.json');assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_panels:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='player-panels' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert [case['name'] for case in previous['cases']]==['player-panels-vlc-1','player-panels-vlc-1.5','player-panels-vlc-2']
    assert all(case['passed'] for case in previous['cases'][:2]) and not previous['cases'][-1]['passed']
    assert all(case['exit_code']==0 and case['owned_desktop_never_observed_as_input'] for case in previous['cases'])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    failed=previous['cases'][-1]
    transition=json.loads((root/next(step['response'] for step in failed['steps'] if step['label']=='render-Video')).read_text(encoding='utf-8'))
    assert transition['window']['visibility']==3 and transition['frame_observed_ms'] is None
    assert not transition.get('capture_saved') and transition['observation_boundary']=='UI dispatcher; no visible render window'
    assert not any((runtime/'portable').iterdir())
    historical=root/'result-before-panel-window-observation.json';assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_floating:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='floating-player' and not previous['passed'] and previous['protected_profiles_unchanged']
    floating_eof_repair='replay' in previous['failures']['floating-player']
    floating_mpv_seek_repair=previous['cases'][-1]['name']=='floating-mpv-1'
    floating_eof_scope_repair=previous['failures']['floating-player']==repr(NameError("name 'current' is not defined"))
    floating_eof_notification_repair=previous['cases'][-1]['name']=='floating-eof-mpv-scope-resumed' and 'natural-eof' in previous['failures']['floating-player']
    assert all(c['exit_code']==0 and c['owned_desktop_never_observed_as_input'] for c in previous['cases'])
    if floating_eof_notification_repair:
        assert len(previous['cases'])==10 and all(c['passed'] for c in previous['cases'][:9])
    elif floating_eof_scope_repair:
        assert len(previous['cases'])==10 and all(c['passed'] for c in previous['cases'][:9])
        assert previous['cases'][-1]['name']=='floating-eof-mpv' and previous['cases'][-1]['steps'][-2]['label']=='minimize'
    elif floating_mpv_seek_repair:
        assert len(previous['cases'])==7 and all(c['passed'] for c in previous['cases'][:6])
        assert previous['cases'][-1]['steps'][-2]['label']=='seek-floating'
    elif floating_eof_repair:
        assert len(previous['cases'])==4 and all(c['passed'] for c in previous['cases'][:3])
        assert previous['cases'][-1]['name']=='floating-eof-vlc'
        assert previous['cases'][-1]['steps'][-2]['label']=='natural-eof'
    else:
        assert len(previous['cases'])==1 and previous['cases'][0]['name']=='floating-vlc-1'
        completed=previous['cases'][0]
        assert completed['steps'][-2]['label']=='dismiss' and 'dismiss-stopped' in previous['failures']['floating-player']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    terminal=root/'floating-vlc-1/evidence/fdfc0a02fb344a44b215c2daf9516d39.json'
    dismissed=json.loads(terminal.read_text())
    assert dismissed['core']['state']==0 and dismissed['main_window']['visibility']==3
    assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in dismissed['windows'])
    historical=root/('result-before-mpv-eof-notification.json' if floating_eof_notification_repair else 'result-before-eof-observer-scope.json' if floating_eof_scope_repair else 'result-before-mpv-seek-readiness.json' if floating_mpv_seek_repair else 'result-before-replay-start-paused.json' if floating_eof_repair else 'result-before-stopped-observer.json');assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_visualizer_options:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='visualizer-options' and not previous['passed'] and previous['protected_profiles_unchanged']
    options_utf8_repair=previous['failures']['audio-visualizer'].startswith('UnicodeDecodeError(')
    if options_utf8_repair:
        assert len(previous['cases'])==1 and previous['cases'][0]['name']=='original-visualizer-eq-options-eq-resumed'
        assert previous['cases'][0]['steps'][-2]['label']=='playback-panel'
        assert previous['resumed_visualizer_options']['completed_visualizer_capture']
    else:
        assert previous['failures']=={'audio-visualizer':repr(TypeError("argument of type 'NoneType' is not a container or iterable"))}
        assert len(previous['cases'])==1 and previous['cases'][0]['steps'][-2]['label']=='visualizer-options'
    assert previous['cases'][0]['exit_code']==0 and previous['cases'][0]['owned_desktop_never_observed_as_input']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/('result-before-options-utf8-checker.json' if options_utf8_repair else 'result-before-options-snapshot-checker.json');assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_m7_lifecycle:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='m7-regressions' and not previous['passed'] and previous['protected_profiles_unchanged']
    m7_final_path=set(previous['failures'])=={'no-library'}
    if m7_final_path:
        assert 'browse-during-video-ready' in previous['failures']['no-library'] and 'observed_item_destroyed' in previous['failures']['no-library']
        assert previous['cases'][-1]['name']=='no-library-video-mpv'
        assert all(case['passed'] for case in previous['cases'][:-1])
        assert previous['reused_m7_complete_modes']['inversion']
    else:
        assert set(previous['failures'])=={'audio-visualizer','no-library'}
        assert 'handover-vlc-focus' in previous['failures']['audio-visualizer'] and 'Expected one visible enabled target; matched 0' in previous['failures']['audio-visualizer']
        assert 'return-to-video' in previous['failures']['no-library'] and 'Expected one observation target; matched 0' in previous['failures']['no-library']
        assert [case['name'] for case in previous['cases']]==['audio-visualizer-1','no-library-vlc-1','no-library-restart-vlc','no-library-vlc-1.5','no-library-vlc-2','no-library-video-vlc']
        assert all(case['passed'] for case in previous['cases'][1:5])
        assert set(previous['cases'][0]['visualizer_inversion'])=={'spectrometer','scope','spectrum','waveform'}
        assert 'disabled-pause' in {step['label'] for step in previous['cases'][0]['steps']}
    assert all(case['exit_code']==0 and case['owned_desktop_never_observed_as_input'] for case in previous['cases'])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/('result-before-m7-input-ready.json' if m7_final_path else 'result-before-m7-lifecycle-checker.json');assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_m7:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='m7-regressions' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert set(previous['failures'])=={'audio-visualizer','no-library'}
    m7_observer_repair='spectrometer-seek' in previous['failures']['audio-visualizer']
    if m7_observer_repair:
        assert "invalid loads value: '.3'" in previous['failures']['audio-visualizer']
        assert 'direct-network-library' in previous['failures']['no-library'] and 'Expected one observation target; matched 0' in previous['failures']['no-library']
        assert [case['name'] for case in previous['cases']]==['audio-visualizer-1-client-fixed','no-library-vlc-1-client-fixed','no-library-restart-vlc']
        assert previous['cases'][1]['passed']
    else:
        assert 'invalid choice' in previous['failures']['audio-visualizer'] and 'redesignAudioVisualizer' in previous['failures']['audio-visualizer']
        assert 'settings-cancel' in previous['failures']['no-library'] and 'matched 0' in previous['failures']['no-library']
        assert [case['name'] for case in previous['cases']]==['audio-visualizer-1','no-library-vlc-1']
    assert all(case['exit_code']==0 and case['owned_desktop_never_observed_as_input'] for case in previous['cases'])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    historical=root/('result-before-m7-observer-fix.json' if m7_observer_repair else 'result-before-m7-client-fix.json');assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_media:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert not previous['passed'] and previous['scope']=='media-previews' and previous['protected_profiles_unchanged']
    photo_mpv_clock=len(previous['cases'])==5 and previous['cases'][-1]['name']=='image-preview-mpv'
    if photo_mpv_clock:
        assert all(row['passed'] for row in previous['cases'][:4])
        assert previous['cases'][-1]['steps'][-2]['label']=='animation-controls'
    else:
        assert len(previous['cases'])==1 and previous['cases'][0]['name'] in ('image-preview-vlc','image-preview-vlc-focus','image-preview-vlc-window-key','image-preview-vlc-gif-observation')
    assert all(row['exit_code']==0 and row['owned_desktop_never_observed_as_input'] for row in previous['cases'])
    photo_focus_unavailable='focus_action_unavailable_rejected_before_dispatch' in previous['failures']['media-previews']
    photo_eof_race='second-animation-frame' in previous['failures']['media-previews'] and 'input_changed_or_ended_during_observation' in previous['failures']['media-previews']
    assert not photo_mpv_clock or photo_eof_race
    photo_tab_duplicates='theme-0-vlc-rendered' in previous['failures']['media-previews'] and 'Expected one observation target; matched 4' in previous['failures']['media-previews']
    assert photo_tab_duplicates or photo_eof_race or photo_focus_unavailable or 'Expected one visible focused Qt key target; matched 0' in previous['failures']['media-previews']
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    historical=root/('result-before-tab-observer.json' if photo_tab_duplicates else 'result-before-gif-observation.json' if photo_eof_race else 'result-before-photo-window-key.json' if photo_focus_unavailable else 'result-before-photo-focus-checker.json')
    assert not historical.exists()
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_onboarding:
    previous=json.loads((root/'result.json').read_text(encoding='utf-8'))
    assert previous['scope']=='onboarding-shortcuts' and not previous['passed'] and previous['protected_profiles_unchanged']
    assert previous['cases'][0]['name']=='welcome-1' and previous['cases'][1]['name']=='restart-empty-1'
    assert all(row['passed'] for row in previous['cases'][:2])
    assert all(row['exit_code']==0 and row['owned_desktop_never_observed_as_input'] for row in previous['cases'])
    assert previous['qt_plugin_sha256']==hashlib.sha256(plugin.read_bytes()).hexdigest()
    assert not any((runtime/'portable').iterdir())
    assert hashlib.sha256((runtime/'plugins/gui/libqt_plugin.dll').read_bytes()).hexdigest()==previous['qt_plugin_sha256']
    historical=root/'result-before-onboarding-checker.json'
    assert not historical.exists(),'Resume the original onboarding checker correction'
    historical.write_bytes((root/'result.json').read_bytes())
elif resume_idle:
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
if resume_volume:
    records['previous_volume_observation']={'path':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'The requested test-only #2f87b5 value is not an offered settings swatch. Observe actual offered blue #1b4e9d; production unchanged.'}
if resume_inline_tracks:
    records['previous_inline_track_observation']={'path':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'QML snapshots do not have the native-widget center_visible field. Actual click dispatch enforces clipping instead.'}
if resume_inline:
    records['cases']=previous['cases'][:3]
    records['reused_inline_observation']={'path':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'Closed exact-float observer required50 despite actual49.99999999999999; same production binary, completed VLC cases retained.'}
if resume_hover:
    if hover_eof_resume:records['cases']=previous['cases'][:3]
    records['reused_observation_failure']={'path':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'Preserve the original client-opacity failure or short-fixture natural EOF; resume only unfinished same-binary cases. Production unchanged.'}
if args.visualizer_options_only:records['scope']='visualizer-options'
records['source_commit']=json.loads((source/'VLC-PLUGIN-BUILDINFO.json').read_text())['source_commit']
version_header=subprocess.check_output(['git','-C',str(repo),'show',records['source_commit']+':modules/gui/qt/dialogs/help/fork_release.hpp'],text=True)
fork_version=re.search(r'currentVersion\[\] = "([0-9.]+)"',version_header).group(1)
newer_version='.'.join(map(str,(*map(int,fork_version.split('.')[:2]),int(fork_version.split('.')[2])+1)))
production=subprocess.check_output(['git','-C',str(repo),'ls-tree','-r','-z',records['source_commit'],'--',
    'include','src','lib','compat','modules','share','configure.ac','Makefile.am','extras/package/win32'])
records['production_tree_sha256']=hashlib.sha256(production).hexdigest()
if resume_panels:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases'][:2]
    records['resumed_player_panels']={'historical_result':str(historical),
        'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'scope':'Reuse passed VLC100/150% on identical production source and binary; observe VLC200% and MPV100/150/200% once. Original minimized-window cause remains unproven; no production workaround or automatic restore/retry.'}
if resume_floating:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    if floating_eof_scope_repair or floating_eof_notification_repair:records['cases']=previous['cases'][:9]
    elif floating_mpv_seek_repair:records['cases']=previous['cases'][:6]
    elif floating_eof_repair:records['cases']=previous['cases'][:3]
    else:
        completed['passed']=True
        completed['verified_terminal_snapshot']=str(terminal.relative_to(root))
        records['cases']=[completed]
    records['resumed_floating']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'scope':'Reuse completed same-binary VLC100% minimize/seek/queue/bounds/restore/reopen/navigation/dismiss evidence; terminal stopped0 independently observed. Finish remaining DPI/engine/EOF/exclusion cases.'}
if resume_visualizer_options:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['resumed_visualizer_options']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'completed_visualizer_capture':previous['resumed_visualizer_options']['completed_visualizer_capture'] if options_utf8_repair else previous['cases'][0]['steps'][-2]['response'],'scope':'Validate the captured original visualizer popup and finish the untested EQ popup. Source/Qt binary unchanged.'}
if resume_m7_lifecycle:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    if m7_final_path:
        records['cases']=previous['cases'][:-1]
        records['reused_m7_complete_modes']=previous['reused_m7_complete_modes']
        records['resumed_m7_input_readiness']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
            'scope':'Retain all complete native cases. The last MPV navigation started in OPENING, before video readiness; finish only that untested playing-video browse/return path.'}
    else:
        records['cases']=previous['cases'][1:5]
        records['reused_m7_complete_modes']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
            'source_commit':previous['source_commit'],'qt_plugin_sha256':previous['qt_plugin_sha256'],
            'completed_steps':previous['cases'][0]['steps'],'inversion':previous['cases'][0]['visualizer_inversion'],
            'scope':'All four100% modes: live PCM, one vout, geometry, changing/frozen frames, actual black/accent pixels, seek/reset/resume and disable. Handover and remaining DPI/engine paths are not reused.'}
if resume_m7:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    if m7_observer_repair:
        records['reused_m7_navigation']=previous['reused_m7_navigation']
        records['cases']=[previous['cases'][1]]
        records['resumed_m7_observers']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
            'scope':'Preserve the completed100% VLC no-library case; correct JSON numeric arguments and observe the library only after its loader has been mounted by the actual click.'}
    else:
        completed={step['label']:step['response'] for step in previous['cases'][1]['steps']}
        labels=[prefix+section for section in ('home','videos','music','network','playlists','recent') for prefix in ('navigate-','no-indexing-')]
        assert all(label in completed for label in labels)
        records['reused_m7_navigation']={'historical_result':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
            'steps':{label:completed[label] for label in labels},'scope':'Unchanged100% VLC disabled-library category rendering and no-indexing observations only. Original failed overall result remains false.'}
if resume_media:
    assert previous['production_tree_sha256']==records['production_tree_sha256']
    records['previous_failed_acceptance']={'path':str(historical),'sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'reason':'Closed keyboard-target or last-frame animation observation failure; original result remains false. Completed photo/identity evidence is preserved.'}
    if photo_mpv_clock:
        records['cases']=previous['cases'][:4]
if resume_onboarding:
    assert previous['source_commit']==records['source_commit'] and previous['production_tree_sha256']==records['production_tree_sha256']
    records['cases']=previous['cases'][:2]
    records['resumed_onboarding_checker']={'historical_result':str(historical),
        'historical_result_sha256':hashlib.sha256(historical.read_bytes()).hexdigest(),
        'scope':'Qt Quick button activation uses Space; standalone library viewport explicitly1280x800. No production change.'}
elif resume_idle:
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
        if self.path=='/control.mkv':
            Peer.calls.append({'mode':'direct-network-playback','path':self.path})
            payload=(fixtures/'control.mkv').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','video/x-matroska')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers();self.wfile.write(payload)
            return
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
            '--verbose=2', '--file-logging', '--log-verbose=2',
            '--logfile=' + str(self.evidence / 'native-ui.log')]
        if engine is not None: command.append('--qt-playback-engine=' + engine)
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
def mpv_frame(source): return re.search(r'/mpv-(16|24|32|48|64|256)\.png$',source) is not None


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
    engine=snapshot['core']['engine']
    name='mpv-display.ico' if engine=='mpv' else 'app.png'
    result=owned_native_read(case,lambda:window_icon(owned_main_window(case,snapshot),case.player.pid,
        repo/'modules/gui/qt/pixmaps/redesign'/name,case.evidence/('native-window-icon-'+engine+'.png')))
    case.record.setdefault('native_window_icons',[]).append(result)
    from app_icon_checks import shell_identity
    identity=owned_native_read(case,lambda:shell_identity(owned_main_window(case,snapshot),case.player.pid,
        engine,runtime/'vlc.exe',repo/'modules/gui/qt/pixmaps/redesign/mpv-display.ico'))
    case.record.setdefault('native_shell_identities',[]).append(identity)


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
    suffix='-resumed' if resume_onboarding else ''
    for scale in (('1.5','2') if resume_onboarding else ('1','1.5','2')):
        case = Case('welcome-' + scale.replace('.', '')+suffix, scale=scale, welcome=True)
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
                cancelled=case.inspect('keyboard-cancel','key','--key','0x20','--text',' ')
                assert cancelled['customization']['onboardingVisible']
                assert not nodes(cancelled,'onboardingShortcutCapture')
            case.click('finish-without-root', 'onboardingNext')
            case.close(True)
            profile = case.path / 'profile'
            for dbfile in profile.rglob('*.db'):
                with sqlite3.connect(dbfile.as_uri() + '?mode=ro', uri=True) as db:
                    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                    if 'Folder' in tables: assert db.execute('SELECT COUNT(*) FROM Folder').fetchone()[0] == 0
            restarted = Case('restart-empty-' + scale.replace('.', '')+suffix, scale=scale, welcome=True, reused_profile=profile)
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
    cancelled=Case('wizard-failed-save-cancel'+suffix,welcome=True,reused_profile=profile,extra=('--qt-privacy-ask',))
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
    suffix='-resumed' if resume_onboarding else ''
    case=Case('interface-shortcuts'+suffix)
    def widget(snapshot,identity):
        matches=[row for row in snapshot['widgets'] if row['id']==identity]
        assert len(matches)==1,(identity,matches)
        return matches[0]
    def focus_table(label):
        # Clicking the table's centre can activate an editable hotkey cell.
        # Follow the actual native Tab chain from the already focused search.
        observed=case.inspect(label+'-tab','widget_key','--target','keyboardShortcutsSearch','--key','0x1000001')
        visited=set()
        while not any(w['id']=='keyboardShortcutsTable' and w['focused'] for w in observed['widgets']):
            focused=[w for w in observed['widgets'] if w['focused']]
            state=tuple((w['id'],w['type']) for w in focused)
            assert focused and state not in visited,('Shortcut table is absent from native Tab order',state)
            visited.add(state)
            observed=case.inspect(label+'-tab-'+str(len(visited)),'widget_key','--node',str(focused[-1]['node']),'--key','0x1000001')
        return observed
    try:
        case.inspect('library-viewport','resize','--width','1280','--height','800')
        case.inspect('library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
        case.inspect('shortcut-menu','click','--name','Main menu')
        case.inspect('open-shortcuts','click','--name','Keyboard Shortcuts')
        case.native('search-focus','keyboardShortcutsSearch')
        case.inspect('search-ctrl-s','widget_key','--target','keyboardShortcutsSearch','--key','0','--text','Ctrl+S')
        focus_table('filtered-table-focus')
        result=case.inspect('filtered-interface-rows','widget_key','--target','keyboardShortcutsTable','--key','0x1000011','--capture')
        assert any(row['columns'][0]=='Stream' for row in widget(result,'keyboardShortcutsTable')['rendered_rows'])
        case.native('search-again','keyboardShortcutsSearch')
        case.inspect('select-search','widget_key','--target','keyboardShortcutsSearch','--key','0x41','--modifiers','0x4000000')
        case.inspect('search-stream','widget_key','--target','keyboardShortcutsSearch','--key','0','--text','Stream')
        focus_table('table-focus')
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
        restarted=Case('interface-shortcuts-restart'+suffix,reused_profile=profile)
        try:
            restarted.inspect('restart-viewport','resize','--width','1280','--height','800')
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


def media_previews():
    """Real image/video replacement and engine identity, with no ten-second EOF."""
    suffix='tab-node' if resume_media and photo_tab_duplicates else 'gif-observation' if resume_media and photo_eof_race else 'window-key' if resume_media and photo_focus_unavailable else 'focus' if resume_media else ''
    images = root / ('image-fixtures'+('-'+suffix if suffix else ''))
    images.mkdir()
    photo = Image.new('RGB', (640, 360), '#296fba')
    for x in range(320, 640):
        for y in range(360): photo.putpixel((x, y), (230, 140, 45))
    photo.save(images / 'still.jpg', quality=95)
    photo.save(images / 'still.png')
    # Long distinct frames permit native controls/state inspection without
    # racing an animation's EOF. Both engines must retain animation playback.
    # Keep a later frame after the observed second-frame boundary: VLC may end
    # at the last frame's timestamp instead of holding its final GIF delay.
    frames = [Image.new('RGB', (320, 180), color) for color in ('#f02d38', '#28a867', '#276ee7')]
    frames[0].save(images / 'animated.gif', save_all=True, append_images=frames[1:], duration=6000, loop=0)

    def no_clock(snapshot):
        assert snapshot['core']['still_image_preview']
        for identity in ('playerElapsedTime', 'layoutAction-duration', 'progressSlider', 'playButton'):
            assert not any(item['visible'] for item in nodes(snapshot, identity)), identity
        assert nodes(snapshot, 'playerVideoSurface')

    def identity(case, snapshot, engine, media=True):
        application=('MPV' if engine=='mpv' else 'VLC')+' Media Player'
        assert snapshot['core']['engine']==engine
        assert snapshot['window']['title'].endswith(application),snapshot['window']
        if not media: assert snapshot['window']['title']==application
        def read_title():
            title=ctypes.create_unicode_buffer(4096)
            u.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,ctypes.c_int]
            u.GetWindowTextW.restype=ctypes.c_int
            assert u.GetWindowTextW(owned_main_window(case,snapshot),title,len(title)),ctypes.WinError(ctypes.get_last_error())
            return title.value
        native_title=owned_native_read(case,read_title)
        assert native_title==snapshot['window']['title'],(native_title,snapshot['window']['title'])
        verify_window_icon(case,snapshot)

    def theme_icon(case, label, engine, custom=True):
        opened=case.click(label+'-open', 'toolsButton')
        visible_icons=nodes(opened,'playerPlaybackTabIcon')
        assert len(visible_icons)==1,visible_icons
        snapshot=case.inspect(label+'-rendered','snapshot','--await-node',str(visible_icons[0]['node']),
            '--await-property','status','--await-value','1','--capture')
        icon=nodes(snapshot,'playerPlaybackTabIcon')[0]
        assert icon['source'].startswith('image://'),icon
        picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
        ratio=picture.width/snapshot['window']['width']
        crop=picture.crop(tuple(round(value*ratio) for value in
            (icon['x'],icon['y'],icon['x']+icon['width'],icon['y']+icon['height'])))
        crop.save(case.evidence/(label+'-tab.png'))
        pixels=list(crop.getdata())
        colored=[rgb for rgb in pixels if max(rgb)-min(rgb)>20]
        assert colored, 'Playback tab accent is missing'
        if custom or engine=='mpv':
            assert not any(r>100 and r>g*1.2 and g>b*1.2 for r,g,b in colored),'Fixed orange accent remains'
        if engine=='mpv':
            expected=colorsys.rgb_to_hsv(152/255,89/255,173/255)[0]
            assert any(abs(colorsys.rgb_to_hsv(r/255,g/255,b/255)[0]-expected)<.035 for r,g,b in colored),'MPV purple absent'
        elif custom: assert any(b>r*1.3 and b>g for r,g,b in colored),'Custom blue absent'
        else: assert any(r>100 and r>g*1.2 and g>b*1.2 for r,g,b in colored),'Default amber absent'
        assert any(max(rgb)-min(rgb)<4 and min(abs(rgb[0]-143),abs(rgb[0]-46))<5 for rgb in pixels),'Neutral outline lost'
        case.inspect(label+'-close','key','--key','0x1000000')

    saved_profiles={'vlc':root/'image-preview-vlc/profile'} if resume_media and photo_mpv_clock else {}
    for engine in ('vlc', 'mpv'):
        if resume_media and photo_mpv_clock and engine=='vlc':continue
        case = Case('image-preview-' + engine + ('-'+suffix if suffix else ''), engine=engine, media=images / 'still.jpg',extra=('--qt-accent-color=#3b82f6',))
        try:
            case.inspect('reference-viewport', 'resize', '--width', '1280', '--height', '800')
            if engine=='mpv':
                case.inspect('photo-native-video-ready','snapshot','--await-core','mpv_video_ready','--await-value','true')
            case.inspect('photo-video-surface','snapshot','--await-target','playerVideoSurface','--await-property','visible','--await-value','true')
            ready = case.inspect('still-preview', 'snapshot', '--await-core', 'still_image_preview', '--await-value', 'true', '--capture')
            no_clock(ready)
            identity(case,ready,engine)
            # Player is a focus scope, not an accessible focus action. Send the
            # real shortcut to its window, as the existing Escape checks do.
            case.inspect('play-photo', 'key', '--key', '0x20', '--text', ' ',
                '--await-core', 'state', '--await-value', '2')
            started = time.monotonic_ns()
            # This bounded observation is the explicit beyond-old-10s acceptance
            # window. Expiry does not cancel the player or prove picture/state;
            # the subsequent actual native snapshot must also pass.
            assert k.WaitForSingleObject(case.player.handle, 11000) == 258, 'Player exited during image preview'
            after = case.inspect('past-old-image-duration', 'snapshot', '--capture')
            assert after['core']['state'] == 2
            no_clock(after)
            case.record['image_survival_observation_ms'] = (time.monotonic_ns() - started) / 1000000
            case.inspect('png-replacement', 'drop', '--target', 'mainInterface', '--url', (images / 'still.png').as_uri(),
                '--await-core', 'url', '--await-value', json.dumps((images / 'still.png').as_uri()))
            no_clock(case.inspect('png-preview', 'snapshot', '--await-core', 'still_image_preview', '--await-value', 'true', '--capture'))
            drop_fixture(case, 'replace-photo-with-video', 'control.mkv')
            movie = case.inspect('restored-video-controls', 'snapshot', '--await-core', 'still_image_preview', '--await-value', 'false', '--capture')
            assert any(item['visible'] for item in nodes(movie, 'progressSlider'))
            assert any(item['visible'] for item in nodes(movie, 'playerElapsedTime'))
            case.inspect('animated-image', 'drop', '--target', 'mainInterface', '--url', (images / 'animated.gif').as_uri(),
                '--await-core', 'url', '--await-value', json.dumps((images / 'animated.gif').as_uri()))
            animated = case.inspect('animation-controls', 'snapshot', '--await-core', 'still_image_preview', '--await-value', 'false', '--capture')
            assert any(item['visible'] for item in nodes(animated, 'playButton'))
            assert any(item['visible'] for item in nodes(animated, 'progressSlider'))
            # MPV time-pos advances at the sparse frame timestamps, not at a
            # continuous UI clock. Observe the actual second-frame PTS (6s),
            # which the independent pinned-runtime renderer also confirms.
            case.inspect('second-animation-frame','snapshot','--await-core','time_seconds','--await-value','6',
                '--await-comparison','at_least','--capture')
            case.inspect('stop-animation', 'key', '--key', '0x53', '--text', 's')
            case.inspect('customize-menu', 'click', '--name', 'Main menu')
            case.inspect('customize-player', 'click', '--name', 'Customize Player')
            case.inspect('editor-ready', 'snapshot', '--await-target', 'playerLayoutEditor', '--await-property', 'ready', '--await-value', 'true')
            case.click('close-editor', 'layoutCancel')
            for index,target in enumerate((engine, 'mpv' if engine == 'vlc' else 'vlc', engine)):
                label=str(index)+'-'+target
                if target != case.inspect('engine-before-' + label)['core']['engine']:
                    case.click('engine-panel-' + label, 'toolsButton')
                    case.inspect('choose-engine-' + label, 'click', '--name', 'MPV' if target == 'mpv' else 'VLC')
                    case.inspect('engine-settled-' + label, 'snapshot', '--await-core', 'engine_switching', '--await-value', 'false')
                    case.inspect('close-engine-panel-' + label, 'key', '--key', '0x1000000')
                idle = case.inspect('centered-logo-' + label, 'snapshot', '--await-target', 'playerIdleCone',
                    '--await-property', 'status', '--await-value', '1', '--capture')
                logo=nodes(idle, 'playerIdleCone')[0]['source']
                assert mpv_frame(logo) if target == 'mpv' else logo.endswith('/app.svg')
                identity(case,idle,target,False)
                theme_icon(case,'theme-'+label,target)
            case.record['untimed_image_replacement_animation_and_engine_branding'] = True
            case.close(True)
        finally: case.close()

        profile=case.path/'profile'
        saved_profiles[engine]=profile
        restarted=Case('saved-engine-restart-'+engine,engine=None,media=fixtures/'control.mkv',reused_profile=profile)
        try:
            snapshot=restarted.inspect('saved-engine','snapshot','--await-core','state','--await-value','3','--capture')
            identity(restarted,snapshot,engine)
            restarted.record['saved_engine_without_cli_override']=engine
            restarted.close(True)
        finally: restarted.close()
        override='vlc' if engine=='mpv' else 'mpv'
        overridden=Case('explicit-engine-override-'+engine,engine=override,media=fixtures/'control.mkv',
            reused_profile=profile,extra=('--no-qt-name-in-title',))
        try:
            snapshot=overridden.inspect('explicit-engine','snapshot','--await-core','state','--await-value','3','--capture')
            identity(overridden,snapshot,override,False)
            overridden.record['explicit_engine_and_title_preference_preserved']=True
            overridden.close(True)
        finally: overridden.close()

        timed = Case('explicit-timed-image-' + engine, engine=engine, media=images / 'still.jpg', extra=('--image-duration=1',))
        try:
            timed.inspect('reference-viewport', 'resize', '--width', '1280', '--height', '800')
            ready = timed.inspect('timed-paused-image', 'snapshot', '--await-core', 'state', '--await-value', '3', '--capture')
            ready = timed.inspect('timed-duration-known','snapshot','--await-core','length_seconds','--await-value','1','--await-tolerance','0.05')
            assert not ready['core']['still_image_preview']
            assert any(item['visible'] for item in nodes(ready, 'progressSlider'))
            timed.click('start-timed-image', 'playButton', '--await-core', 'state', '--await-value', '2')
            if engine == 'mpv':
                timed.inspect('timed-image-eof', 'snapshot', '--await-core', 'mpv_video_ready', '--await-value', 'false')
            else:
                timed.inspect('timed-image-eof', 'snapshot', '--await-core', 'state', '--await-value', '0')
            timed.record['explicit_timed_image_natural_eof'] = True
            timed.close(True)
        finally: timed.close()

    default=Case('default-accent-vlc',media=fixtures/'control.mkv')
    try:
        default.inspect('default-paused','snapshot','--await-core','state','--await-value','3')
        theme_icon(default,'default-theme','vlc',custom=False)
        default.close(True)
    finally: default.close()

    # A real incompatible compositor rejects MPV before any engine preference
    # write. This is a supported native VLC path, not a diagnostic fake failure.
    saved_vlc=saved_profiles['vlc']
    rejected=Case('rejected-engine-preserves-choice',engine=None,media=fixtures/'control.mkv',
        reused_profile=saved_vlc,extra=('--qt-compositor=win7',))
    try:
        rejected.inspect('vlc-running','snapshot','--await-core','state','--await-value','3')
        before=(portable/'vlcrc').read_bytes()
        rejected.click('open-engine-panel','toolsButton')
        rejected.inspect('reject-incompatible-engine','click','--name','MPV')
        snapshot=rejected.inspect('engine-still-vlc','snapshot','--capture')
        assert snapshot['core']['engine']=='vlc' and not snapshot['core']['engine_switching']
        assert (portable/'vlcrc').read_bytes()==before
        rejected.record['rejected_switch_did_not_write_config']=True
        rejected.close(True)
    finally: rejected.close()

    failed=Case('engine-save-failure',engine=None,media=fixtures/'control.mkv',reused_profile=saved_vlc)
    try:
        failed.inspect('vlc-ready','snapshot','--await-core','state','--await-value','3')
        config=portable/'vlcrc'
        before=config.read_bytes()
        k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,W.LPVOID,W.DWORD,W.DWORD,W.HANDLE]
        k.CreateFileW.restype=W.HANDLE
        held=k.CreateFileW(str(config),0x80000000,1,None,3,0x80,None)
        assert held and held!=ctypes.c_void_p(-1).value,ctypes.WinError(ctypes.get_last_error())
        try:
            failed.click('open-engine-panel','toolsButton')
            failed.inspect('switch-with-locked-config','click','--name','MPV')
            snapshot=failed.inspect('session-only-choice','snapshot','--await-core','engine_switching','--await-value','false','--capture')
            assert snapshot['core']['engine']=='mpv'
            assert config.read_bytes()==before
            assert any(row.get('text')=='Playback engine' and row.get('visible') for row in snapshot['tree']), 'Save failure notification absent'
        finally: assert k.CloseHandle(held)
        failed.record['failed_save_preserved_file_and_reported_session_only_choice']=True
        failed.close(True)
    finally: failed.close()
    restored=Case('failed-save-next-launch',engine=None,media=fixtures/'control.mkv',reused_profile=failed.path/'profile')
    try:
        snapshot=restored.inspect('old-choice-restored','snapshot','--await-core','state','--await-value','3')
        identity(restored,snapshot,'vlc')
        restored.close(True)
    finally: restored.close()


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

def engine_accents():
    """Both engine palettes, live icon resources, cancellation and saved restart."""
    case=Case('engine-accent-settings')
    def empty_player(label):
        case.inspect(label+'-viewport','resize','--width','1280','--height','900')
        case.inspect(label+'-menu','click','--name','Main menu')
        case.inspect(label+'-customize','click','--name','Customize Player')
        case.inspect(label+'-editor','snapshot','--await-target','playerLayoutEditor','--await-property','ready','--await-value','true')
        case.click(label+'-cancel-editor','layoutCancel')
    def settings(label):
        case.inspect(label+'-open','key','--key','0x50','--modifiers','0x4000000')
        ready=case.inspect(label+'-ready','snapshot')
        assert any(w['id']=='redesignPreferences' for w in ready['widgets'])
        return ready
    def color(label,engine,value):
        return case.inspect(label,'widget_click','--widget-name',engine+' accent color '+value)
    def identity(label,engine,accent,custom):
        snapshot=case.inspect(label,'snapshot','--await-core','engine_switching','--await-value','false','--capture')
        assert snapshot['core']['engine']==engine and snapshot['rendered_accent']==accent
        if not custom:verify_window_icon(case,snapshot);return snapshot
        reference=Path(snapshot['engine_shell_icon'])
        assert reference.is_relative_to(runtime/'portable') and reference.name==engine+'.ico'
        assert accent[1:] in reference.parent.name
        from app_icon_checks import shell_identity
        case.record.setdefault('custom_native_icons',[]).append(owned_native_read(case,lambda:window_icon(
            owned_main_window(case,snapshot),case.player.pid,reference,case.evidence/(label+'-window.png'),custom=True)))
        case.record.setdefault('custom_shell_icons',[]).append(owned_native_read(case,lambda:shell_identity(
            owned_main_window(case,snapshot),case.player.pid,engine,runtime/'vlc.exe',reference,custom_resource=reference)))
        ico=Image.open(io.BytesIO(reference.read_bytes()))
        assert ico.ico.sizes()=={(n,n) for n in (16,24,32,48,64,256)}
        if engine=='mpv':
            mounted=nodes(snapshot,'playerGlyph-mpv');assert len(mounted)==1
            snapshot=case.inspect(label+'-qml-ready','snapshot','--await-node',str(mounted[0]['node']),
                '--await-property','status','--await-value','1','--capture')
            picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png'))
            ratio=picture.width/snapshot['window']['width']
            for target in ('playerGlyph-mpv','playerIdleCone'):
                visible=nodes(snapshot,target);assert len(visible)==1
                node=visible[0];assert node['source'].startswith(snapshot['engine_icon_root'])
                crop=case.evidence/(label+'-'+target+'.png')
                picture.crop(tuple(round(v*ratio) for v in (node['x'],node['y'],node['x']+node['width'],node['y']+node['height']))).save(crop)
                pixels=qml_mpv_icon_pixels(crop,reference,tuple(math.floor(node[k]*ratio)-round(node[k]*ratio) for k in ('x','y')))
                case.record.setdefault('custom_qml_icons',[]).append(dict(pixels,label=label,target=target))
            original=Image.open(repo/'modules/gui/qt/pixmaps/redesign/mpv-display.ico')
            for size in sorted(ico.ico.sizes()):
                observed=ico.ico.getimage(size).convert('RGBA');expected=original.ico.getimage(size).convert('RGBA')
                assert observed.getchannel('A').tobytes()==expected.getchannel('A').tobytes()
                chromatic=0;stable_hue_pixels=0
                for actual,wanted in zip(observed.get_flattened_data(),expected.get_flattened_data()):
                    hue,light,saturation=colorsys.rgb_to_hls(*[v/255 for v in wanted[:3]])
                    if not wanted[3] or saturation<.12:
                        assert max(abs(a-b) for a,b in zip(actual,wanted))<=1
                    else:
                        chromatic+=1
                        actual_hue,actual_light,actual_saturation=colorsys.rgb_to_hls(*[v/255 for v in actual[:3]])
                        assert abs(actual_light-light)<.01
                        target_hue=colorsys.rgb_to_hls(*[v/255 for v in bytes.fromhex(accent[1:])])[0]
                        # Near-white 8-bit pixels can have HSL saturation1
                        # despite only one RGB level of chroma. Their hue is
                        # quantization noise, not a visible accent deviation.
                        if actual_saturation>.15 and max(actual[:3])-min(actual[:3])>=8:
                            stable_hue_pixels+=1
                            assert min(abs(actual_hue-target_hue),1-abs(actual_hue-target_hue))<.035
                assert chromatic>0
                assert stable_hue_pixels>0
        return snapshot
    def switch(label,engine):
        case.click(label+'-panel','toolsButton')
        case.inspect(label+'-select','click','--name',engine.upper())
        snapshot=case.inspect(label+'-settled','snapshot','--await-core','engine_switching','--await-value','false')
        assert snapshot['core']['engine']==engine
        case.inspect(label+'-close','key','--key','0x1000000')
    def menu(label,accent):
        snapshot=case.inspect(label,'click','--name','Main menu','--capture')
        path=root/case.record['steps'][-1]['response'];picture=Image.open(path.with_suffix('.png')).convert('RGB')
        ratio=picture.width/snapshot['window']['width']
        icons=[n for n in snapshot['tree'] if n['visible'] and 'menu-' in (n.get('source') or '') and n.get('width')==24]
        assert len(icons)==12
        wanted=colorsys.rgb_to_hsv(*[v/255 for v in bytes.fromhex(accent[1:])])[0]
        checks=[]
        for n in icons:
            box=tuple(round(v*ratio) for v in (n['x'],n['y'],n['x']+n['width'],n['y']+n['height']))
            pixels=list(picture.crop(box).get_flattened_data())
            colored=[p for p in pixels if max(p)-min(p)>12]
            assert colored
            for p in colored:
                hue=colorsys.rgb_to_hsv(*[v/255 for v in p])[0]
                assert min(abs(hue-wanted),1-abs(hue-wanted))<.035
            def luminance(p):
                linear=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in p]
                return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
            peak=max((luminance(p)+.05)/(luminance((14,14,14))+.05) for p in colored)
            if accent=='#9859ad':assert peak>=1.8,(label,n['source'],peak)
            checks.append({'glyph':n['source'],'peak_accent_contrast':peak})
        case.record.setdefault('menu_palettes',[]).append({'label':label,'accent':accent,'icons':checks})
        case.inspect(label+'-close','key','--key','0x1000000')
    try:
        empty_player('empty-player')
        case.inspect('reference-viewport','resize','--width','1280','--height','900')
        identity('vlc-default','vlc','#d37918',False)
        settings('separate-palettes')
        color('vlc-green','VLC','#167329');color('mpv-blue','MPV','#1b4e9d')
        case.native('save-independent-colors','preferencesSave')
        snapshot=identity('vlc-green-applied','vlc','#167329',True)
        assert snapshot['presentation']['accent']=='#167329' and snapshot['presentation']['mpvAccent']=='#1b4e9d'
        menu('vlc-green-menu','#167329')
        switch('live-mpv','mpv');identity('mpv-blue-applied','mpv','#1b4e9d',True)
        menu('mpv-blue-menu','#1b4e9d')
        settings('cancel-palette');color('cancel-red','MPV','#a4381f');case.native('cancel-color','preferencesCancel')
        identity('mpv-blue-after-cancel','mpv','#1b4e9d',True)
        case.close(True)
    finally:case.close()
    prior=case.path/'profile'
    case=Case('engine-accent-restart',engine=None,reused_profile=prior)
    try:
        empty_player('saved-empty-player')
        snapshot=identity('saved-mpv-blue','mpv','#1b4e9d',True)
        assert snapshot['presentation']['accent']=='#167329' and snapshot['presentation']['mpvAccent']=='#1b4e9d'
        settings('restore-mpv-default');case.native('mpv-default','preferencesMpvAccentDefault');case.native('save-mpv-default','preferencesSave')
        identity('mpv-original-restored','mpv','#9859ad',False)
        menu('readable-mpv-purple','#9859ad')
        switch('return-vlc','vlc');identity('vlc-green-preserved','vlc','#167329',True)
        settings('restore-vlc-default');case.native('vlc-default','preferencesVlcAccentDefault');case.native('save-vlc-default','preferencesSave')
        identity('vlc-original-restored','vlc','#d37918',False)
        case.close(True)
    finally:case.close()


def inline_subtitles():
    """Cue synchronization and ordinary seeking share one reference-height bar."""
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            if resume_inline and engine=='vlc':continue
            case=Case('inline-subtitles-'+engine+'-'+scale+('-numeric-resumed' if resume_inline else ''),engine=engine,scale=scale,media=fixtures/'embedded-text.mkv')
            try:
                initial=case.inspect('paused','snapshot','--await-core','state','--await-value','3')
                case.inspect('full-width','resize','--width','1280','--height','720')
                initial=case.inspect('bar-before','snapshot')
                before=nodes(initial,'playerControlBar')[0]
                case.click('open-tools','toolsButton')
                case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
                    '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
                case.inspect('close-tools','key','--key','0x1000000')
                state=case.inspect('inline-layout','snapshot','--capture')
                slider=nodes(state,'progressSlider')[0]
                bar=nodes(state,'playerControlBar')[0]
                graph=nodes(state,'subtitleTimelineOffset')[0]
                assert abs(bar['height']-before['height'])<.5
                assert abs(graph['y']-slider['y'])<.5 and abs(graph['height']-slider['height'])<.5
                assert graph['width']>100
                buttons=[nodes(state,key)[0] for key in ('previousSubtitleCue','subtitleDelayEarlier','subtitleDelayLater','nextSubtitleCue')]
                assert all(slider['x']-.5<=b['x'] and b['x']+b['width']<=slider['x']+slider['width']+.5 for b in buttons)
                base=state['core']['subtitle_delay_ms']
                case.click('later','subtitleDelayLater','--await-core','subtitle_delay_ms','--await-value',base+50,'--await-tolerance','.001')
                case.click('earlier','subtitleDelayEarlier','--await-core','subtitle_delay_ms','--await-value',base,'--await-tolerance','.001')
                case.key('keyboard-later',0x1000014,target='subtitleTimelineOffset')
                state=case.key('keyboard-earlier',0x1000012,target='subtitleTimelineOffset')
                assert abs(state['core']['subtitle_delay_ms']-base)<.001
                duration=state['core']['length_seconds']*1000
                cues=service(state)['cues']
                fraction=(cues[0]['start']+cues[0]['end'])/2/duration
                case.inspect('cue-press','press','--target','subtitleTimelineOffset','--fraction-x',fraction)
                moved=case.inspect('cue-drag','move','--target','subtitleTimelineOffset','--fraction-x',fraction+.1)
                case.inspect('cue-release','release','--target','subtitleTimelineOffset','--fraction-x',fraction+.1)
                expected=base+round(duration*.1)
                assert abs(moved['core']['subtitle_delay_ms']-expected)<=40,moved['core']['subtitle_delay_ms']
                delay=moved['core']['subtitle_delay_ms']
                # A gap, rather than a cue, must retain the slider's seek owner.
                sought=case.inspect('gap-seek','click','--target','subtitleTimelineOffset','--fraction-x','.02')
                assert abs(sought['core']['subtitle_delay_ms']-delay)<.001
                assert abs(nodes(sought,'progressSlider')[0]['value']-.02)<.02
                case.click('next-cue','nextSubtitleCue')
                case.click('previous-cue','previousSubtitleCue')
                case.inspect('narrow-window','resize','--width','600','--height','420')
                narrow=case.inspect('narrow-inline','snapshot','--capture')
                assert nodes(narrow,'subtitleTimelineOffset')[0]['width']>0
                case.click('tools-to-disable','toolsButton')
                case.inspect('disable-timeline','click','--name','Show Subtitle Timeline on Seekbar')
                case.inspect('close-disabled-tools','key','--key','0x1000000')
                regular=case.inspect('regular-bar','snapshot','--capture')
                assert not nodes(regular,'subtitleTimelineOffset')
                case.record['inline_geometry_seek_sync']=True
                case.close(True)
            finally:case.close()


def inline_subtitle_tracks():
    """Selected/external cues, no-track state and a narrow customized top seekbar."""
    for engine in ('vlc','mpv'):
        suffix='-observation-resumed' if resume_inline_tracks else ''
        seed=root/('top-layout-profile-'+engine+suffix)
        (seed/'vlc').mkdir(parents=True)
        layout={'topLeft':['more','browser','divider','folder'],'topCenter':['seek'],'topRight':['fullscreen'],
            'bottomLeft':['previous','play','next'],'bottomCenter':['elapsed','filename','duration'],
            'bottomRight':['mute','volume','audio','subtitles','tools','queue']}
        store={'version':1,'layout':layout,'profiles':[],'selected':''}
        (seed/'vlc/vlc-qt-interface.ini').write_text('[redesign]\ncustomization-v1='+json.dumps(json.dumps(store,separators=(',',':')))+'\n',encoding='utf-8')
        case=Case('inline-tracks-'+engine+suffix,engine=engine,media=fixtures/'embedded-text.mkv',reused_profile=seed)
        try:
            case.inspect('paused','snapshot','--await-core','state','--await-value','3')
            case.inspect('viewport','resize','--width','960','--height','720')
            case.click('tools','toolsButton')
            case.inspect('enable-timeline','click','--name','Show Subtitle Timeline on Seekbar',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 embedded source cues; positions follow the selected track and subtitle delay.'))
            case.inspect('close-tools','key','--key','0x1000000')
            top=case.inspect('custom-top-inline','snapshot','--capture')
            graph=nodes(top,'subtitleTimelineOffset')[0]
            assert graph['y']<100 and graph['width']>100
            case.inspect('narrow-top','resize','--width','600','--height','420')
            for key in ('previousSubtitleCue','subtitleDelayEarlier','subtitleDelayLater','nextSubtitleCue'):
                focused=case.inspect('focus-'+key,'focus','--target',key)
                case.click('activate-'+key,key)
            case.inspect('restore-viewport','resize','--width','960','--height','720')
            tracks=case.click('tracks','subtitleButton')
            alternate=[node for node in subtitle_choices(tracks) if node.get('name')!='None' and not node['selected']]
            assert len(alternate)==1
            case.inspect('select-alternate','click','--name',alternate[0]['name'])
            selected=cue_result(case,'alternate-cues',2)
            assert service(selected)['cues'][0]['start']==2000
            case.inspect('disable-track','click','--name','None',
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('No subtitle track selected.'))
            case.inspect('dismiss-tracks','key','--key','0x1000000')
            none=case.inspect('no-track-ordinary-bar','snapshot','--capture')
            assert not nodes(none,'subtitleTimelineOffset') and nodes(none,'progressSlider')
            case.inspect('external-subtitles','drop','--target','mainInterface','--url',(fixtures/'english.srt').as_uri(),
                '--await-service','redesignMediaTools','--await-property','timelineStatus','--await-value',json.dumps('3 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.'))
            external=case.inspect('external-inline','snapshot','--capture')
            assert len(service(external)['cues'])==3 and nodes(external,'subtitleTimelineOffset')
            case.close(True)
        finally:case.close()


def volume_accent_and_dismissal():
    """Engine-themed original wedge plus background-only miniplayer dismissal."""
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            case=Case('volume-dismiss-'+engine+'-'+scale+('-palette-resumed' if resume_volume else ''),engine=engine,media=fixtures/'miniplayer-long.mkv',scale=scale)
            try:
                case.inspect('paused','snapshot','--await-core','state','--await-value','3')
                case.inspect('viewport','resize','--width','1280','--height','720')
                case.click('volume-level','volumeSlider','--fraction-x','.8')
                def rendered(label,expected):
                    before=case.inspect(label+'-image','snapshot')
                    item=nodes(before,'volumeGradient')[0]
                    state=case.inspect(label,'snapshot','--await-node',item['node'],'--await-property','status','--await-value','1','--capture')
                    assert state['rendered_accent']==expected
                    picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
                    ratio=picture.width/state['window']['width']
                    item=nodes(state,'volumeGradient')[0]
                    points=[picture.getpixel((round((item['x']+item['width']*fraction)*ratio),round((item['y']+item['height']/2)*ratio))) for fraction in (.2,.65)]
                    wanted=colorsys.rgb_to_hsv(*[v/255 for v in bytes.fromhex(expected[1:])])[0]
                    for pixel in points:
                        hue,saturation,value=colorsys.rgb_to_hsv(*[v/255 for v in pixel])
                        assert saturation>.2 and value>.15 and min(abs(hue-wanted),1-abs(hue-wanted))<.04,(expected,points)
                    assert max(points[0])-max(points[1])>8,points
                    case.record.setdefault('gradient_pixels',[]).append({'label':label,'accent':expected,'pixels':points})
                    return state
                default='#9859ad' if engine=='mpv' else '#d37918'
                rendered('default-gradient',default)
                case.inspect('open-settings','key','--key','0x50','--modifiers','0x4000000')
                case.inspect('custom-color','widget_click','--widget-name',engine.upper()+' accent color #1b4e9d')
                case.native('save-color','preferencesSave')
                rendered('custom-gradient','#1b4e9d')
                case.click('mute','muteButton')
                muted=case.inspect('muted-wedge','snapshot')
                assert abs(nodes(muted,'volumeWedge')[0]['opacity']-.45)<.001
                case.click('unmute','muteButton')
                case.key('keyboard-volume-down',0x1000012,target='volumeSlider')
                case.key('keyboard-volume-up',0x1000014,target='volumeSlider')
                other='vlc' if engine=='mpv' else 'mpv'
                case.click('handover-tools','toolsButton')
                case.inspect('handover-engine','click','--name',other.upper())
                case.inspect('handover-settled','snapshot','--await-core','engine_switching','--await-value','false')
                case.inspect('dismiss-tools','key','--key','0x1000000')
                case.click('handover-volume','volumeSlider','--fraction-x','.8')
                rendered('handover-gradient','#9859ad' if other=='mpv' else '#d37918')
                case.click('play','playButton','--await-core','state','--await-value','2')
                case.click('minimize','playerMinimize')
                case.inspect('floating-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                case.inspect('hover','move','--target','floatingVideoSurface')
                case.click('close-only-mini','floatingClose')
                background=case.inspect('background-playing','snapshot','--await-core','state','--await-value','2')
                assert background['main_window']['visibility']==3
                assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in background['windows'])
                case.inspect('next-input-while-dismissed','drop','--target','mainInterface','--url',(fixtures/'embedded-text.mkv').as_uri(),
                    '--await-core','url','--await-value',json.dumps((fixtures/'embedded-text.mkv').as_uri()))
                next_input=case.inspect('dismiss-stays-minimized','snapshot','--await-core','state','--await-value','2')
                assert next_input['main_window']['visibility']==3
                assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in next_input['windows'])
                case.inspect('explicit-window-restore','restore')
                restored=case.inspect('main-restored','snapshot')
                assert restored['main_window']['visibility']!=3
                case.click('new-minimize-cycle','playerMinimize')
                case.inspect('new-floating-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                case.click('restore-from-mini','floatingRestore')
                case.close(True)
            finally:case.close()


def floating_contrast():
    """Real compact/expanded hover readability, without replaying unchanged geometry/drag acceptance."""
    def luminance(byte):
        value=byte/255
        return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            case=Case('floating-contrast-'+engine+'-'+scale,engine=engine,scale=scale,extra=(str(fixtures/'miniplayer-long.mkv'),))
            try:
                case.inspect('video-ready','snapshot','--await-core','state','--await-value','3')
                case.click('play','playButton','--await-core','state','--await-value','2')
                case.click('minimize','playerMinimize')
                case.inspect('floating-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                for expanded in (False,True):
                    if expanded:case.click('expand-queue','floatingQueueToggle')
                    label='expanded' if expanded else 'compact'
                    case.inspect(label+'-hover','move','--target','floatingVideoSurface','--fraction-x','.25','--fraction-y','.25')
                    state=case.inspect(label+'-painted','snapshot','--capture')
                    assert nodes(state,'floatingVideoControls')[0]['opacity']==1
                    ratios=[]
                    for glyph in ('close','expand-library','previous','pause','next'):
                        icon=nodes(state,'playerGlyph-'+glyph)[0]
                        backing=nodes(state,'floatingVideoBacking-'+glyph)[0]
                        assert icon['color']=='#f0f0f0' and backing['color']=='#000000'
                        assert backing['width']>=icon['width']+6 and backing['height']>=icon['height']+6
                        if icon['enabled']:
                            worst=255*(1-backing['opacity'])
                            ratio=(luminance(240)+.05)/(luminance(worst)+.05)
                            assert ratio>=4.5,(glyph,ratio,backing)
                            ratios.append(ratio)
                    case.record.setdefault('overlay_contrast',[]).append({'layout':label,'enabled_icons_minimum_ratio_over_white':min(ratios)})
                case.click('restore','floatingRestore')
                case.close(True)
            finally:case.close()

def floating_queue():
    """Complete expanded-queue drag, original toolbar and real item workflow."""
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            if resume_hover and hover_eof_resume and engine=='vlc':continue
            primary='miniplayer-long.mkv'
            assert (fixtures/primary).is_file(),'Run prepare-miniplayer-fixture.py once for the retained synthetic input'
            case=Case('floating-queue-'+engine+'-'+scale+('-fixture-resumed' if resume_hover and hover_eof_resume else '-observation-resumed' if resume_hover else ''),engine=engine,scale=scale,
                extra=(str(fixtures/primary),str(fixtures/'embedded-text.mkv')))
            try:
                case.inspect('video-ready','snapshot','--await-core','state','--await-value','3')
                case.click('play','playButton','--await-core','state','--await-value','2')
                case.click('minimize','playerMinimize')
                case.inspect('floating-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                def hover_controls(label, playing):
                    case.inspect(label+'-leave','move','--target','floatingMediaName')
                    state=case.inspect(label+'-hidden','snapshot')
                    assert nodes(state,'floatingVideoControls')[0]['opacity']==0,('Hover controls stayed visible after pointer exit',label)
                    state=case.inspect(label+'-enter','move','--target','floatingVideoSurface','--fraction-x','.25','--fraction-y','.25')
                    state=case.inspect(label+'-visible','snapshot')
                    assert nodes(state,'floatingVideoControls')[0]['opacity']==1,('Hover controls stayed hidden over video',label)
                    assert state['core']['state']==playing,state['core']
                    assert nodes(state,'floatingClose') and nodes(state,'floatingRestore')
                hover_controls('compact-playing-hover',2)
                case.click('compact-pause','floatingPlay','--await-core','state','--await-value','3')
                hover_controls('compact-paused-hover',3)
                case.click('compact-resume','floatingPlay','--await-core','state','--await-value','2')
                compact=case.inspect('compact-drag-target','snapshot')
                title=nodes(compact,'floatingMediaName')[0]
                moved=case.inspect('drag-compact-metadata','drag','--target','floatingMediaName',
                    '--end-x',str(title['x']+title['width']*.8),'--end-y',str(title['y']+title['height']*.5))
                assert any(event.get('moving') for event in moved['pointer_trace']),'Compact metadata did not enter window drag'
                expanded=case.click('expand-queue','floatingQueueToggle','--capture')
                header=nodes(expanded,'floatingQueueHeader');assert len(header)==1
                assert nodes(expanded,'floatingQueueList') and nodes(expanded,'floatingQueueItem0')
                hover_controls('expanded-playing-hover',2)
                case.click('expanded-pause','floatingPlay','--await-core','state','--await-value','3')
                hover_controls('expanded-paused-hover',3)
                case.click('expanded-resume','floatingPlay','--await-core','state','--await-value','2')
                for glyph in ('sort','remove','add'):
                    image=nodes(expanded,'playerGlyph-'+glyph)
                    assert len(image)==1 and image[0]['width']==16 and image[0]['height']==16,(glyph,image)
                    assert image[0]['color']=='#6b6b6b',(glyph,image[0]['color'])
                dragged=case.inspect('drag-queue-header','drag','--target','floatingQueueHeader',
                    '--end-x',str(header[0]['x']+header[0]['width']*.8),'--end-y',str(header[0]['y']+header[0]['height']*.5))
                assert any(event.get('moving') for event in dragged['pointer_trace']),('Queue header did not enter its native drag handler',dragged['pointer_trace'])
                assert dragged['main_window']['visibility']==3 and dragged['core']['state']==2
                assert dragged['window']['width']<=dragged['window']['available_width'] and dragged['window']['height']<=dragged['window']['available_height']
                title=nodes(dragged,'floatingMediaName')[0]
                moved=case.inspect('drag-expanded-metadata','drag','--target','floatingMediaName',
                    '--end-x',str(title['x']+title['width']*.8),'--end-y',str(title['y']+title['height']*.5))
                assert any(event.get('moving') for event in moved['pointer_trace']),'Expanded metadata did not enter window drag'
                area=nodes(moved,'floatingQueueList')[0]
                moved=case.inspect('drag-empty-queue','drag','--target','floatingPlayer','--fraction-x','0.25',
                    '--fraction-y',str((area['y']+area['height']*.8)/nodes(moved,'floatingPlayer')[0]['height']),
                    '--end-x',str(area['x']+area['width']*.65),'--end-y',str(area['y']+area['height']*.8))
                assert any(event.get('moving') for event in moved['pointer_trace']),'Empty queue did not enter window drag'
                case.inspect('seek-press','press','--target','floatingSeek','--fraction-x','0.2')
                seeking=case.inspect('seek-move','move','--target','floatingSeek','--fraction-x','0.4')
                assert not nodes(seeking,'floatingPlayer')[0]['moving'],'Seekbar gesture moved the window'
                assert abs(nodes(seeking,'floatingSeek')[0]['value']-.4)<.04
                case.inspect('seek-release','release','--target','floatingSeek','--fraction-x','0.4')
                ordered=case.click('sort-queue','floatingQueueSort')
                first=nodes(ordered,'floatingQueueItem0')[0]['name']
                assert first in (primary,'embedded-text.mkv'),first
                case.click('play-queue-item','floatingQueueItem0','--await-core','url','--await-value',json.dumps((fixtures/first).as_uri()))
                case.inspect('selected-video-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                collapsed=case.click('collapse-queue','floatingQueueToggle')
                assert not nodes(collapsed,'floatingQueueHeader')
                case.click('restore-main','floatingRestore')
                def restored_geometry(label):
                    state=case.inspect(label,'move','--target','playerVideoSurface','--capture')
                    surface=nodes(state,'playerVideoSurface')[0]
                    dpr=state['window']['dpr']
                    actual=state['reported_video_surface']
                    expected={key:surface[key]*dpr for key in ('x','y','width','height')}
                    assert all(abs(actual[key]-value)<1.1 for key,value in expected.items()),(actual,expected)
                    assert not any(w['name']=='floatingPlayerWindow' and w['visible'] for w in state['windows'])
                    case.record.setdefault('restored_surface_geometry',[]).append({'actual':actual,'expected':expected})
                restored_geometry('restored-compact-video-geometry')
                case.click('minimize-again','playerMinimize')
                case.inspect('floating-again-ready','snapshot','--await-target','floatingPlayer','--await-property','ready','--await-value','true')
                case.click('expand-again','floatingQueueToggle')
                case.click('restore-expanded','floatingRestore')
                restored_geometry('restored-expanded-video-geometry')
                case.close(True)
            finally:case.close()

def floating_player():
    def current(case,label,capture=False):
        state=case.inspect(label,'snapshot','--await-target','floatingPlayer',
            '--await-property','ready','--await-value','true')
        if capture:
            case.inspect(label+'-hover','move','--target','floatingPlayer','--fraction-y','0.25')
            state=case.inspect(label+'-capture','snapshot','--capture')
        assert state['main_window']['visibility']==3, state['main_window']
        windows=[w for w in state['windows'] if w.get('name')=='floatingPlayerWindow' and w['visible']]
        assert len(windows)==1 and windows[0]['composition_ready'], windows
        assert windows[0]['native_id_hex']!=state['main_window']['native_id_hex']
        assert not state['engine_switching']
        assert state['window']['width']<=state['window']['available_width']
        assert state['window']['height']<=state['window']['available_height']
        assert not state['images']['failed']
        return state

    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            if any(c['name'].startswith('floating-'+engine+'-'+scale) and c['engine']==engine and c['scale']==scale and c['passed'] for c in records['cases']):continue
            case=Case('floating-'+engine+'-'+scale+('-seek-resumed' if resume_floating and floating_mpv_seek_repair and engine=='mpv' and scale=='1' else ''),engine=engine,scale=scale,
                extra=('--input-repeat=-1',str(fixtures/'control.mkv'),str(fixtures/'embedded-text.mkv')))
            try:
                initial=case.inspect('video-ready','snapshot','--await-core','state','--await-value','3')
                initial=case.inspect('seek-ready','snapshot','--await-core','seekable','--await-value','true')
                native=initial['main_window']['native_id_hex']
                geometry={k:initial['main_window'][k] for k in ('x','y','width','height')}
                case.click('play','playButton','--await-core','state','--await-value','2')
                before=case.inspect('before-minimize','snapshot')
                if engine=='vlc':
                    assert [v['value'] for v in before['visualization_choices'] if v['selected']]==['']
                case.click('minimize','playerMinimize')
                mini=current(case,'floating-ready',True)
                assert mini['playback_engine']==engine and mini['core']['url']==before['core']['url']
                assert mini['main_window']['native_id_hex']==native and mini['core']['state']==2
                case.click('pause-floating','floatingPlay','--await-core','state','--await-value','3')
                sought=case.inspect('seek-floating','click','--target','floatingSeek','--fraction-x','0.35')
                sought=case.inspect('seek-ui-observed','snapshot','--await-target','floatingSeek','--await-property','value','--await-value','0.35','--await-tolerance','0.03')
                assert abs(nodes(sought,'floatingSeek')[0]['value']-0.35)<0.03
                if engine=='vlc':assert sought['seek_requests'][-1]['status']=='submitted'
                # VLC's non-seeking timer point remains at its last paused
                # presentation. Confirm the selected seek point in the UI,
                # then observe the real resumed clock before pausing again.
                case.click('resume-after-seek','floatingPlay','--await-core','state','--await-value','2')
                advanced=case.inspect('seek-observed','snapshot','--await-core','position','--await-value','0.35','--await-comparison','at_least','--await-tolerance','0.03')
                assert advanced['core']['position']<0.55,advanced['core']
                paused=case.click('pause-after-seek','floatingPlay','--await-core','state','--await-value','3')
                queued=case.click('expand-queue','floatingQueueToggle','--capture')
                assert nodes(queued,'floatingQueueList') and nodes(queued,'floatingQueueItem0')
                assert queued['window']['height']>mini['window']['height']
                case.click('collapse-queue','floatingQueueToggle')
                case.inspect('monitor-bounded-resize','resize','--width','3840','--height','2160')
                bounded=current(case,'bounded-result',True)
                assert bounded['window']['width']<=640
                restored=case.click('restore-main','floatingRestore','--capture')
                assert restored['main_window']['visibility']!=3
                assert restored['main_window']['native_id_hex']==native
                assert all(restored['main_window'][k]==v for k,v in geometry.items()),(geometry,restored['main_window'])
                assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in restored['windows'])
                assert restored['core']['state']==3 and abs(restored['core']['position']-paused['core']['position'])<0.03
                case.click('play-again','playButton','--await-core','state','--await-value','2')
                case.click('minimize-again','playerMinimize')
                current(case,'same-mini-reopened')
                case.click('queue-reopened','floatingQueueToggle')
                case.click('next-item','floatingNext','--await-core','url','--await-value',json.dumps((fixtures/'embedded-text.mkv').as_uri()))
                next_video=case.inspect('next-video','snapshot','--await-core','mpv_video_ready' if engine=='mpv' else 'state','--await-value','true' if engine=='mpv' else '2')
                assert next_video['main_window']['visibility']==3 and next_video['core']['video_tracks']
                case.click('previous-item','floatingPrevious','--await-core','url','--await-value',json.dumps((fixtures/'control.mkv').as_uri()))
                previous_video=case.inspect('previous-video','snapshot','--await-core','mpv_video_ready' if engine=='mpv' else 'state','--await-value','true' if engine=='mpv' else '2')
                assert previous_video['main_window']['visibility']==3 and previous_video['core']['video_tracks']
                dismissed=case.click('dismiss','floatingClose')
                background=case.inspect('dismiss-keeps-playing','snapshot','--await-core','state','--await-value','2')
                assert background['main_window']['visibility']==3
                assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in background['windows'])
                case.close(True)
            finally:case.close()
        if not any(c['name'].startswith('floating-eof-'+engine) and c['passed'] for c in records['cases']):
            floating_eof(engine,current)
        for name,media in (('idle',None),('audio',fixtures/'audio-only.mka')):
            if any(c['name']=='floating-excludes-'+name+'-'+engine and c['passed'] for c in records['cases']):continue
            negative=Case('floating-excludes-'+name+'-'+engine,engine=engine,media=media)
            try:
                if media:
                    negative.inspect('paused','snapshot','--await-core','state','--await-value','3')
                    negative.click('play','playButton','--await-core','state','--await-value','2')
                state=negative.inspect('library-ready','snapshot')
                negative.click('minimize','playerMinimize')
                state=negative.inspect('no-floating','snapshot')
                assert state['main_window']['visibility']==3
                assert not any(w.get('name')=='floatingPlayerWindow' and w['visible'] for w in state['windows'])
                negative.close(True)
            finally:negative.close()


def floating_eof(engine,current):
        eof=Case('floating-eof-'+engine+('-notification-resumed' if resume_floating and floating_eof_notification_repair and engine=='mpv' else '-scope-resumed' if resume_floating and floating_eof_scope_repair and engine=='mpv' else '-replay-resumed' if resume_floating and floating_eof_repair and engine=='vlc' else ''),
            engine=engine,media=fixtures/'control.mkv',extra=('--no-start-paused',))
        try:
            eof.inspect('playing','snapshot','--await-core','state','--await-value','2')
            eof.click('minimize','playerMinimize')
            current(eof,'floating-ready')
            stopped=eof.inspect('natural-eof','snapshot','--await-target','floatingPlay','--await-property','description','--await-value',json.dumps('Replay'),'--capture')
            assert stopped['core']['state']==0,stopped['core']
            assert nodes(stopped,'floatingPlay') and nodes(stopped,'floatingRestore')
            replay=eof.click('replay','floatingPlay','--await-core','state','--await-value','2')
            assert replay['main_window']['visibility']==3
            current(eof,'replay-surface-ready',True)
            eof.close(True)
        finally:eof.close()


def visualizer_options():
    suffix='-eq-utf8-resumed' if options_utf8_repair else '-eq-resumed' if resume_visualizer_options else ''
    case=Case('original-visualizer-eq-options'+suffix,media=fixtures/'control.mkv')
    try:
        case.inspect('audio-ready','snapshot','--await-service','redesignAudioVisualizer','--await-property','available','--await-value','true')
        case.inspect('reference-viewport','resize','--width','1280','--height','800')
        case.click('playback-panel','toolsButton')
        if resume_visualizer_options:
            visualizer=json.loads((root/records['resumed_visualizer_options']['completed_visualizer_capture']).read_text(encoding='utf-8'))
        else:
            case.inspect('visualizer-focus','focus','--target','seekbarVisualizerChoice')
            visualizer=case.inspect('visualizer-options','key','--key','0x20','--text',' ','--capture')
        def originals(snapshot,prefix):
            rows=[n for n in snapshot['tree'] if n['visible'] and prefix in (n.get('source') or '')]
            assert rows and all(n.get('status')=='Ready' for n in rows),rows
            return [n['source'] for n in rows]
        visualizer_icons=originals(visualizer,'visualizer-')
        assert len(visualizer_icons)==4,visualizer_icons
        closed=case.inspect('current-panel','snapshot') if resume_visualizer_options else case.inspect('visualizer-cancel','key','--key','0x1000000')
        tab=next(n for n in closed['tree'] if n.get('name')=='Audio' and n.get('id')!='audioButton' and n['visible'] and n.get('actions'))
        case.inspect('audio-tab','click','--node',str(tab['node']))
        case.inspect('equalizer-expand','click','--name','Equalizer: Expand Settings')
        case.inspect('equalizer-focus','focus','--name','Equalizer Preset')
        first=case.inspect('equalizer-first-options','key','--key','0x20','--text',' ','--capture')
        first_icons=originals(first,'eq-')
        assert len(first_icons)>=4,first_icons
        last=case.inspect('equalizer-last-options','key','--key','0x1000011','--capture')
        last_icons=originals(last,'eq-')
        assert len(set(first_icons+last_icons))>=8,(first_icons,last_icons)
        case.inspect('equalizer-cancel','key','--key','0x1000000')
        case.record['original_dropdowns']={'visualizer_icons':visualizer_icons,'eq_first':first_icons,'eq_last':last_icons,
            'source_manifest':'modules/gui/qt/pixmaps/redesign/manifest.json'}
        case.close(True)
    finally:case.close()


def visualizer_handover(case):
    identity='redesignAudioVisualizer'
    case.click('handover-panel','toolsButton')
    case.inspect('handover-visualizer-focus','focus','--target','seekbarVisualizerChoice')
    case.inspect('handover-enable','key','--key','0x1000015',
        '--await-service',identity,'--await-property','mode','--await-value','"spectrometer"')
    case.inspect('handover-mpv-focus','focus','--name','MPV')
    mpv=case.inspect('handover-mpv','click','--name','MPV','--await-core','engine','--await-value','"mpv"')
    assert not service(mpv,identity)['active'] and not service(mpv,identity)['samples']
    case.inspect('handover-mpv-settled','snapshot','--await-core','engine_switching','--await-value','false')
    case.inspect('handover-vlc-focus','focus','--name','VLC')
    case.inspect('handover-vlc','click','--name','VLC','--await-core','engine','--await-value','"vlc"')
    case.inspect('handover-vlc-settled','snapshot','--await-core','engine_switching','--await-value','false')
    case.inspect('handover-audio-restored','snapshot','--await-service',identity,'--await-property','available','--await-value','true')
    case.inspect('handover-panel-dismiss','key','--key','0x1000000')
    case.click('handover-play','playButton','--await-core','state','--await-value','2')
    case.inspect('handover-new-pcm','snapshot','--await-service',identity,'--await-property','active','--await-value','true')
    case.click('handover-pause','playButton','--await-core','state','--await-value','3')
    drop_fixture(case,'input-without-audio','wide.mkv')
    no_audio=case.inspect('no-audio-observer-released','snapshot','--await-service',identity,'--await-property','available','--await-value','false')
    assert not service(no_audio,identity)['samples']


def audio_visualizer():
    """Real PCM effects stay inside the seek track and release on disable/handover."""
    if args.visualizer_options_only:return visualizer_options()
    if m7_final_path:return
    identity='redesignAudioVisualizer'
    for scale in ('1','1.5','2'):
        if resume_m7_lifecycle and scale=='1':
            case=Case('audio-visualizer-handover-1',media=fixtures/'control.mkv',extra=('--input-repeat=-1',))
            try:
                case.inspect('audio-ready','snapshot','--await-service',identity,'--await-property','available','--await-value','true')
                visualizer_handover(case)
                case.close(True)
            finally:case.close()
            continue
        suffix=('-observer-fixed' if m7_observer_repair else '-client-fixed') if resume_m7 and scale=='1' else ''
        case=Case('audio-visualizer-'+scale+suffix,scale=scale,media=fixtures/'control.mkv',extra=('--input-repeat=-1',))
        try:
            initial=case.inspect('audio-ready','snapshot','--await-service',identity,'--await-property','available','--await-value','true')
            baseline=nodes(initial,'progressSlider')[0]
            for index,mode in enumerate(('spectrometer','scope','spectrum','waveform'),1):
                case.click(mode+'-panel','toolsButton')
                case.inspect(mode+'-focus','focus','--target','seekbarVisualizerChoice')
                selected=case.inspect(mode+'-choose','key','--key','0x1000015',
                    '--await-service',identity,'--await-property','mode','--await-value',json.dumps(mode))
                assert service(selected,identity)['mode']==mode
                case.inspect(mode+'-dismiss-panel','key','--key','0x1000000')
                case.click(mode+'-play','playButton','--await-core','state','--await-value','2')
                active=case.inspect(mode+'-real-pcm','snapshot','--await-service',identity,
                    '--await-property','active','--await-value','true','--capture')
                values=service(active,identity)
                assert len(values['samples'])==(64 if mode in ('spectrometer','spectrum') else 512)
                assert any(abs(value)>0 for value in values['samples']), 'Audible synthetic tone produced no effect'
                assert active['native_vout_count']==1, 'Visualizer created another video output'
                strip=nodes(active,'liveAudioVisualizerStrip')[0]
                slider=nodes(active,'progressSlider')[0]
                for field in ('x','y','width','height'):
                    assert abs(strip[field]-slider[field])<.01,(mode,field,strip,slider)
                    assert abs(slider[field]-baseline[field])<.01,(mode,field,slider,baseline)
                moving=case.inspect(mode+'-new-audio-frame','snapshot','--await-service',identity,
                    '--await-property','frameRevision','--await-value',str(values['frameRevision']+2),'--await-comparison','at_least')
                case.inspect(mode+'-played-portion','snapshot','--await-core','position','--await-value','0.55','--await-comparison','at_least')
                paused=case.click(mode+'-pause','playButton','--await-core','state','--await-value','3')
                frozen=service(paused,identity)['frameRevision']
                observed=case.inspect(mode+'-paused-frame','snapshot','--capture')
                assert service(observed,identity)['frameRevision']==frozen
                strip=nodes(observed,'liveAudioVisualizerStrip')[0]
                with Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')) as picture:
                    sx=picture.width/observed['window']['width'];sy=picture.height/observed['window']['height']
                    played=picture.convert('RGB').crop((round((strip['x']+4)*sx),round((strip['y']+4)*sy),
                        round((strip['x']+strip['width']*.5)*sx),round((strip['y']+strip['height']-4)*sy)))
                accent=tuple(bytes.fromhex(observed['rendered_accent'].lstrip('#')))
                pixels=list(played.getdata())
                ink=sum(max(pixel)<12 for pixel in pixels)
                fill=sum(max(abs(pixel[i]-accent[i]) for i in range(3))<5 for pixel in pixels)
                assert ink>5 and fill>5,(mode,'Missing black effect on accent-filled progress',ink,fill)
                case.record.setdefault('visualizer_inversion',{})[mode]={'black_effect_pixels':ink,'accent_fill_pixels':fill}
                sought=case.click(mode+'-seek','progressSlider','--fraction-x','.3','--await-service',identity,'--await-property','active','--await-value','false')
                assert not service(sought,identity)['samples'], 'Paused seek retained stale audio samples'
                case.click(mode+'-resume-seek','playButton','--await-core','state','--await-value','2')
                case.inspect(mode+'-actual-seek','snapshot','--await-core','position','--await-value','0.3','--await-tolerance','0.06')
                case.inspect(mode+'-seek-new-pcm','snapshot','--await-service',identity,'--await-property','active','--await-value','true')
                case.click(mode+'-seek-pause','playButton','--await-core','state','--await-value','3')
            case.click('disable-panel','toolsButton')
            case.inspect('disable-focus','focus','--target','seekbarVisualizerChoice')
            disabled=case.inspect('disable','key','--key','0x1000010','--await-service',identity,'--await-property','mode','--await-value','""')
            assert not service(disabled,identity)['active'] and not service(disabled,identity)['samples']
            case.inspect('disable-dismiss-panel','key','--key','0x1000000')
            case.click('disabled-playback','playButton','--await-core','state','--await-value','2')
            advanced=case.inspect('disabled-audio-progress','snapshot','--await-core','position','--await-value','0.4','--await-comparison','at_least')
            assert service(advanced,identity)['frameRevision']==service(disabled,identity)['frameRevision']
            case.click('disabled-pause','playButton','--await-core','state','--await-value','3')
            if scale=='1':
                visualizer_handover(case)
            case.close(True)
        finally:case.close()
    unsupported=Case('audio-visualizer-mpv',engine='mpv',media=fixtures/'control.mkv')
    try:
        result=unsupported.click('unsupported-panel','toolsButton','--capture')
        assert not service(result,identity)['available']
        assert not nodes(result,'seekbarVisualizerChoice')[0]['enabled']
        assert 'VLC' in service(result,identity)['status']
        unsupported.close(True)
    finally:unsupported.close()


def no_library():
    """The disabled backend keeps the real redesign, menus and video workflow."""
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            if m7_final_path or (resume_m7_lifecycle and engine=='vlc'):continue
            reuse_navigation=resume_m7 and engine=='vlc' and scale=='1'
            if m7_observer_repair and reuse_navigation:
                profile_path=root/'no-library-vlc-1-client-fixed/profile'
            else:
                case=Case('no-library-'+engine+'-'+scale+('-client-fixed' if reuse_navigation else ''),engine=engine,scale=scale,extra=('--no-media-library',))
                try:
                    case.inspect('viewport','resize','--width','1280','--height','800')
                    if reuse_navigation:
                        case.inspect('resumed-library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
                    for section in (() if reuse_navigation else ('home','videos','music','network','playlists','recent')):
                        result=case.click('navigate-'+section,'libraryNav_'+section,
                            '--await-target','fullLibrary','--await-property','ready','--await-value','true',
                            *(['--capture'] if section=='home' else []))
                        assert nodes(result,'playerTopBar') and nodes(result,'libraryDisabledMessage')
                        assert result['media_library_available'] is False
                        case.inspect('no-indexing-'+section,'snapshot','--await-target','fullLibrary',
                            '--await-property','indexing','--await-value','false')
                    case.inspect('main-menu','click','--name','Main menu')
                    result=case.inspect('settings','click','--name','Settings')
                    assert any(row['id']=='redesignPreferences' for row in result['widgets'])
                    case.native('settings-close','preferencesClose')
                    case.close(True)
                    profile_path=case.path/'profile'
                    assert not any(path.name.endswith(('.db','.db-wal','.db-shm')) for path in profile_path.rglob('*'))
                finally:case.close()
            if scale=='1':
                restarted=Case('no-library-restart-'+engine+('-observer-fixed' if m7_observer_repair else ''),engine=engine,
                    reused_profile=profile_path,extra=('--no-media-library',))
                try:
                    result=restarted.inspect('restart-follows-no-library','snapshot',
                        '--await-target','fullLibrary','--await-property','ready','--await-value','true')
                    assert nodes(result,'libraryDisabledMessage') and not result['media_library_available']
                    direct=drop_fixture(restarted,'direct-file','control.mkv')
                    assert direct['core']['engine']==engine
                    restarted.inspect('direct-network-library','click','--name','Back to media')
                    restarted.inspect('direct-network-library-ready','snapshot','--await-target','fullLibrary','--await-property','ready','--await-value','true')
                    restarted.inspect('add-network-item','click','--name','Add item')
                    restarted.inspect('network-form','click','--name','Open network stream or playlist…')
                    url='http://127.0.0.1:'+str(server.server_port)+'/control.mkv'
                    restarted.inspect('network-url-focus','focus','--target','networkUrlsInput')
                    restarted.inspect('network-url-input','key','--key','0','--text',url)
                    network=restarted.click('direct-network-play','networkStreamSave',
                        '--await-core','url','--await-value',json.dumps(url))
                    assert not network['media_library_available']
                    folder=restarted.path/'direct-folder';folder.mkdir()
                    shutil.copyfile(fixtures/'control.mkv',folder/'only-video.mkv')
                    restarted.inspect('direct-folder','drop','--target','mainInterface','--url',folder.as_uri(),
                        '--await-core','url','--await-value',json.dumps((folder/'only-video.mkv').as_uri()))
                    restarted.close(True)
                    assert not any(path.name.endswith(('.db','.db-wal','.db-shm')) for path in (restarted.path/'profile').rglob('*'))
                finally:restarted.close()
        if m7_final_path and engine=='vlc':continue
        suffix='-ready-fixed' if m7_final_path else '-return-fixed' if resume_m7_lifecycle and engine=='vlc' else ''
        video=Case('no-library-video-'+engine+suffix,engine=engine,media=fixtures/'control.mkv',extra=('--no-media-library',))
        try:
            video.inspect('main-video','snapshot','--await-target','playerView','--await-property','visible','--await-value','true')
            video.inspect('paused-video-ready','snapshot','--await-core','state','--await-value','3')
            if engine=='mpv':
                video.inspect('mpv-video-ready','snapshot','--await-core','mpv_video_ready','--await-value','true')
            browsed=video.inspect('browse-during-video','click','--name','Back to media')
            library_target='compactLibrary' if nodes(browsed,'compactLibrary') else 'fullLibrary'
            result=video.inspect('browse-during-video-ready','snapshot','--await-target',library_target,'--await-property','ready','--await-value','true','--capture')
            assert nodes(result,'libraryMiniSeek') and nodes(result,'libraryDisabledMessage')
            video.click('return-to-video','libraryReturnToPlayer',
                '--await-target','viewLoader','--await-property','source','--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
            result=video.inspect('return-to-video-ready','snapshot','--await-target','viewLoader','--await-property','status','--await-value','1')
            assert nodes(result,'playerView')[0]['visible']
            assert result['core']['engine']==engine
            video.close(True)
        finally:video.close()


def engine_icon_pixels():
    """Verify changed PNG decode sizes; preserve unchanged handover evidence."""
    for scale in ('1','1.5','2'):
        case=Case('engine-icon-pixels-'+scale,scale=scale,engine='mpv',extra=('--no-file-logging','--logfile='))
        try:
            case.inspect('reference-viewport','resize','--width','1280','--height','800')
            case.inspect('idle-menu','click','--name','Main menu')
            case.inspect('idle-customize','click','--name','Customize Player')
            case.inspect('idle-player-mounted','snapshot','--await-target','viewLoader','--await-property','source',
                '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
            case.inspect('idle-editor-ready','snapshot','--await-target','playerLayoutEditor','--await-property','ready','--await-value','true')
            case.click('idle-editor-cancel','layoutCancel')
            case.inspect('idle-logo-ready','snapshot','--await-target','playerIdleCone','--await-property','status','--await-value','1')
            mounted=case.inspect('visible-header','snapshot')
            glyph=nodes(mounted,'playerGlyph-mpv');assert len(glyph)==1,glyph
            snapshot=case.inspect('native-dpr-icons','snapshot','--await-node',str(glyph[0]['node']),'--await-property','status','--await-value','1','--capture')
            verify_window_icon(case,snapshot)
            picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png'))
            ratio=picture.width/snapshot['window']['width']
            for identity in ('playerGlyph-mpv','playerIdleCone'):
                node=nodes(snapshot,identity);assert len(node)==1 and mpv_frame(node[0]['source'])
                node=node[0];crop=case.evidence/(identity+'.png')
                picture.crop(tuple(round(value*ratio) for value in
                    (node['x'],node['y'],node['x']+node['width'],node['y']+node['height']))).save(crop)
                case.record.setdefault('native_qml_icon_pixels',[]).append(dict(
                    qml_mpv_icon_pixels(crop,repo/'modules/gui/qt/pixmaps/redesign/mpv-display.ico',
                        tuple(math.floor(node[key]*ratio)-round(node[key]*ratio) for key in ('x','y'))),target=identity,source=node['source']))
            if scale=='1' and not args.skip_documentation_capture:
                # Current public UI documentation uses an empty owned profile.
                # No private movie, local path or user desktop is captured.
                case.click('readme-engine-panel','toolsButton')
                case.inspect('readme-vlc','click','--name','VLC')
                case.inspect('readme-vlc-ready','snapshot','--await-core','engine_switching','--await-value','false')
                case.inspect('readme-close-panel','key','--key','0x1000000')
                case.inspect('readme-player','snapshot','--capture')
                case.inspect('readme-main-menu','click','--name','Main menu','--capture')
                case.inspect('readme-global-settings','click','--name','Settings')
                case.native('readme-dark-theme','preferencesTheme2')
                case.native('readme-save-theme','preferencesSave')
                case.inspect('readme-reopen-settings','key','--key','0x50','--modifiers','0x4000000')
                case.inspect('readme-settings-size','widget_resize','--target','redesignPreferences','--width','1048','--height','865')
                settings=case.inspect('readme-settings','snapshot','--capture')
                assert any(row['id']=='preferencesHeading' and row.get('text')=='Global Settings' for row in settings['widgets'])
                case.native('readme-close-settings','preferencesClose')
            case.close(True)
        finally:case.close()


def engine_icons():
    """Complete mode identity handover, original artwork and persisted restart."""
    for scale in ('1','1.5','2'):
        case=Case('engine-icons-'+scale,scale=scale,media=fixtures/'control.mkv')
        def identity(label,engine):
            mounted=case.inspect(label+'-locate','snapshot')
            target=nodes(mounted,'playerGlyph-'+('mpv' if engine=='mpv' else 'vlc'));assert len(target)==1,target
            snapshot=case.inspect(label,'snapshot','--await-node',str(target[0]['node']),
                '--await-property','status','--await-value','1','--capture')
            glyph=nodes(snapshot,'playerGlyph-'+('mpv' if engine=='mpv' else 'vlc'))
            assert len(glyph)==1 and (mpv_frame(glyph[0]['source']) if engine=='mpv' else glyph[0]['source'].endswith('/vlc.svg')),glyph
            assert snapshot['window']['title'].endswith(('MPV' if engine=='mpv' else 'VLC')+' Media Player')
            verify_window_icon(case,snapshot)
            picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png'))
            ratio=picture.width/snapshot['window']['width'];node=glyph[0]
            picture.crop(tuple(round(value*ratio) for value in
                (node['x'],node['y'],node['x']+node['width'],node['y']+node['height']))).save(case.evidence/(label+'-header.png'))
            if engine=='mpv':
                pixels=qml_mpv_icon_pixels(case.evidence/(label+'-header.png'),repo/'modules/gui/qt/pixmaps/redesign/mpv-display.ico',
                    tuple(math.floor(node[key]*ratio)-round(node[key]*ratio) for key in ('x','y')))
                case.record.setdefault('native_qml_icon_pixels',[]).append(pixels)
            return snapshot
        try:
            case.inspect('reference-viewport','resize','--width','1280','--height','800')
            case.inspect('initial-paused','snapshot','--await-core','state','--await-value','3')
            identity('initial-vlc','vlc')
            for index,engine in enumerate(('mpv','vlc','mpv')):
                label='switch-'+str(index)+'-'+engine
                case.click(label+'-panel','toolsButton')
                case.inspect(label+'-select','click','--name','MPV' if engine=='mpv' else 'VLC')
                settled=case.inspect(label+'-settled','snapshot','--await-core','engine_switching','--await-value','false')
                assert settled['core']['engine']==engine and settled['core']['state']==3,settled['core']
                case.inspect(label+'-close','key','--key','0x1000000')
                identity(label,engine)
            case.close(True)
        finally:case.close()
        profile=case.path/'profile'
        case=Case('engine-icons-restart-'+scale,scale=scale,engine=None,media=fixtures/'control.mkv',reused_profile=profile)
        try:
            case.inspect('restart-paused','snapshot','--await-core','state','--await-value','3')
            identity('saved-mpv','mpv')
            case.close(True)
        finally:case.close()
        # Empty startup exercises the idle asset directly; stopping a loaded
        # input is a separate already-covered media transition, not an icon
        # observation predicate. The MPV native idle event does not wake the
        # legacy player-state observation used by the original checker.
        case=Case('engine-icons-idle-'+scale,scale=scale,engine=None,reused_profile=profile)
        try:
            case.inspect('idle-menu','click','--name','Main menu','--capture')
            case.inspect('idle-customize','click','--name','Customize Player')
            case.inspect('idle-player-mounted','snapshot','--await-target','viewLoader','--await-property','source',
                '--await-value',json.dumps('qrc:///qt/qml/VLC/Player/Player.qml'))
            case.inspect('idle-editor-ready','snapshot','--await-target','playerLayoutEditor','--await-property','ready','--await-value','true')
            case.click('idle-editor-cancel','layoutCancel')
            idle=case.inspect('idle-logo','snapshot','--await-target','playerIdleCone','--await-property','status','--await-value','1','--capture')
            assert idle['core']['engine']=='mpv' and mpv_frame(nodes(idle,'playerIdleCone')[0]['source'])
            verify_window_icon(case,idle)
            case.close(True)
        finally:case.close()


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

def player_panels():
    """Four complete native panels: original selected artwork, layout and bindings."""
    names=('Playback','Video','Audio','Subtitles')
    for engine in ('vlc','mpv'):
        for scale in ('1','1.5','2'):
            if resume_panels and engine=='vlc' and scale!='2':continue
            custom=scale=='1.5'
            color='#2f87b5' if custom else '#9859ad' if engine=='mpv' else '#d37918'
            extra=(('--qt-mpv-accent-color=' if engine=='mpv' else '--qt-accent-color=')+color,)
            case=Case('player-panels-'+engine+'-'+scale+('-window-observation' if resume_panels else ''),engine=engine,scale=scale,
                      media=fixtures/'embedded-text.mkv',extra=extra)
            try:
                case.inspect('reference-viewport','resize','--width','1280','--height','1100')
                case.inspect('paused','snapshot','--await-core','state','--await-value','3')
                case.click('open-panels','toolsButton')
                for page,label in enumerate(names):
                    selected=case.click('select-'+label,'playerSettingsTab_'+str(page))
                    identity='playerPlaybackTabIcon' if page==0 else 'playerTabIcon_'+str(page)
                    icon=nodes(selected,identity)
                    assert len(icon)==1,(label,icon)
                    snapshot=case.inspect('render-'+label,'snapshot','--await-node',icon[0]['node'],
                        '--await-property','status','--await-value','1','--capture')
                    assert snapshot.get('capture_saved') and snapshot.get('frame_observed_ms') is not None,(
                        'Panel capture did not reach a rendered frame',label,snapshot.get('window'),snapshot.get('observation_boundary'))
                    assert snapshot['rendered_accent']==color,(engine,scale,snapshot['rendered_accent'])
                    assert len(nodes(snapshot,identity))==1
                    assert not nodes(snapshot,'playerTabNeutral_'+str(page))
                    assert all(nodes(snapshot,'playerTabNeutral_'+str(other)) for other in range(4) if other!=page)
                    picture=Image.open((root/case.record['steps'][-1]['response']).with_suffix('.png')).convert('RGB')
                    ratio=picture.width/snapshot['window']['width']
                    icon=nodes(snapshot,identity)[0]
                    crop=picture.crop(tuple(round(v*ratio) for v in
                        (icon['x'],icon['y'],icon['x']+icon['width'],icon['y']+icon['height'])))
                    crop.save(case.evidence/('selected-'+label+'.png'))
                    pixels=list(crop.getdata())
                    expected=colorsys.rgb_to_hsv(*(int(color[i:i+2],16)/255 for i in (1,3,5)))[0]
                    colored=[p for p in pixels if max(p)-min(p)>25 and max(p)>80]
                    assert colored and any(abs(colorsys.rgb_to_hsv(*(v/255 for v in p))[0]-expected)<.035 for p in colored),(label,color,'selected accent absent')
                    assert any(max(p)-min(p)<4 and 60<=p[0]<=160 for p in pixels),(label,'neutral geometry lost')
                    body_node=nodes(snapshot,'mediaSettingsBody')[0]
                    if page:
                        footer=nodes(snapshot,'mediaSettingsFooter')[0]
                        assert body_node['y']+body_node['height']<=footer['y']+1,'Body overlaps fixed preset footer'
                        fields=[n for n in snapshot['tree'] if n['visible'] and n['id'].startswith('playerChoice_')]
                        assert fields
                        assert all(abs(n['width']-220)<1 for n in fields if n['id']!='playerChoice_Stereo Mode'),fields
                    if page==1:
                        assert any(n.get('name')=='Flip video: Horizontal' and n['visible'] and n['enabled']==(engine=='vlc') for n in snapshot['tree'])
                        assert not any(n.get('text')=='Defaults' and n['visible'] for n in snapshot['tree'])
                    if page in (2,3):
                        editor='audioDelayEditor' if page==2 else 'subtitleDelayEditor'
                        value='0.125 s' if page==2 else '-0.250 s'
                        core='audio_delay_ms' if page==2 else 'subtitle_delay_ms'
                        case.inspect('focus-delay-'+label,'focus','--target',editor)
                        case.inspect('select-delay-'+label,'key','--key','0x41','--modifiers','0x4000000','--text','a')
                        case.inspect('edit-delay-'+label,'key','--key','0','--text',value)
                        case.inspect('apply-delay-'+label,'key','--key','0x1000004',
                            '--await-core',core,'--await-value','125' if page==2 else '-250')
                    case.record.setdefault('panel_rendering',[]).append({'page':label,'accent':color,
                        'original_two_tone_selected':True,'neutral_inactive_tabs':True,'fixed_footer':page!=0})
                if engine=='vlc':
                    case.click('return-audio','playerSettingsTab_2')
                    case.inspect('focus-equalizer-preset','focus','--target','mediaChoice_equalizer-preset')
                    enabled=case.inspect('enable-equalizer-preset','key','--key','0x1000015')
                    assert enabled['media_tools']['filters']['equalizer'],'Choosing a preset did not enable equalization'
                    case.inspect('focus-equalizer-off','focus','--target','mediaChoice_equalizer-preset')
                    disabled=case.inspect('disable-equalizer','key','--key','0x1000010')
                    assert not disabled['media_tools']['filters']['equalizer'],'None did not disable equalization'
                    case.inspect('reveal-equalizer','focus','--name','Equalizer: Expand Settings')
                    expanded=case.inspect('expand-equalizer','click','--name','Equalizer: Expand Settings','--capture')
                    assert any(n['visible'] and n['id']=='mediaOption_equalizer-bands' for n in expanded['tree']) or any(n.get('text')=='60' and n['visible'] for n in expanded['tree'])
                case.close(True)
            finally:case.close()

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
            assert settled['rendered_accent']==('#9859ad' if engine=='mpv' else '#2f87b5')
            assert settled['presentation']==saved_presentation, 'Engine selection rewrote the saved appearance'
            glyph=nodes(settled,'playerGlyph-'+('mpv' if engine=='mpv' else 'vlc'))
            assert len(glyph)==1 and (mpv_frame(glyph[0]['source']) if engine=='mpv' else glyph[0]['source'].endswith('/vlc.svg')),glyph
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
            assert snapshot['core']['engine']=='mpv' and snapshot['rendered_accent']=='#9859ad'
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
    for name, operation in [('volume-dismiss',volume_accent_and_dismissal),('inline-subtitle-tracks',inline_subtitle_tracks),('inline-subtitles',inline_subtitles),('floating-contrast',floating_contrast),('floating-queue',floating_queue),('player-panels',player_panels),('floating-player',floating_player),('audio-visualizer',audio_visualizer),('no-library',no_library),('engine-accents',engine_accents),('engine-icon-pixels',engine_icon_pixels),('engine-icons',engine_icons),('media-previews',media_previews),('idle',idle),('settings-backdrop',settings_backdrop),('settings',settings),('menus',menus),('welcome',welcome),('shortcuts',interface_shortcuts),('playback',playback),('subtitles',subtitles),('preview',preview),('icons',icons),('sidebar',sidebar),('updates',updates),('seek-policy',seek_policy)]:
        if args.visualizer_options_only and name!='audio-visualizer':continue
        if args.case=='m7-regressions' and name not in ('audio-visualizer','no-library'):continue
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
        if args.case not in ('all','m7-regressions','onboarding-shortcuts','subtitles-mpv','playback-subtitles','integration-diagnostic','subtitle-tracks-diagnostic','preview-icons','correction','settings-survey',name): continue
        try:
            operation()
        except Exception as failure:
            detail=type(failure).__name__+': '+str(failure) if isinstance(failure,UnicodeDecodeError) else repr(failure)
            records.setdefault('failures',{})[name]=detail
            records.setdefault('failure_tracebacks',{})[name]=traceback.format_exc()
            save()
            print(json.dumps({'workflow':name,'failure':detail}),flush=True)
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
