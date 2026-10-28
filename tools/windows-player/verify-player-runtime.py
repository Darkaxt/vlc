
from pathlib import Path
import os,sys,json,subprocess,hashlib,datetime,re
sys.dont_write_bytecode = True
import argparse
parser=argparse.ArgumentParser(description='Verify a normal portable player on an inactive desktop, without OS input.')
parser.add_argument('--runtime',type=Path,required=True)
parser.add_argument('--fixture',type=Path,required=True)
parser.add_argument('--scratch',type=Path,required=True)
parser.add_argument('--evidence',type=Path,required=True)
parser.add_argument('--with-media-library',action='store_true',help='Exercise normal native media-library startup as well as playback')
options=parser.parse_args()
s=options.scratch.resolve();r=options.runtime.resolve();e=options.evidence.resolve()
repo=Path(__file__).resolve().parents[2]
if s.drive.upper() not in ('D:','E:') or r.drive.upper() not in ('D:','E:') or not e.is_relative_to(s):
 parser.error('Use an explicit D:/E: scratch root, evidence below it, and an isolated D:/E: runtime')
if not options.fixture.is_file():parser.error('The playback fixture must exist')
if not (r/'portable').is_dir() or any((r/'portable').iterdir()):
 parser.error('The isolated runtime must have an existing empty portable directory; preserve prior settings separately')
(s/'tmp').mkdir(parents=True,exist_ok=True);(s/'cache/qml-normal').mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(repo/'tools/windows-player'))
from isolated_desktop import IsolatedProcess
assert r.is_dir() and (r/'portable').is_dir()
e.mkdir(parents=True,exist_ok=True)
qt=r/'plugins/gui/libqt_plugin.dll';blob=qt.read_bytes()
markers=['VLC_PLAYER_DIAGNOSTICS_DIR','VLC_PLAYER_DIAGNOSTICS_TOKEN','VLC_PLAYER_DIAGNOSTICS_OFFSCREEN','VLC_PLAYER_DIAGNOSTICS_PROXY_PORT','redesignSeekRequests','offscreen_session_is_capture_only','core_observation_listener_failed_action_not_undone','palette_highlight','PlayerDiagnostics']
for marker in markers:
 for encoding in ['ascii','utf-16le']:assert marker.encode(encoding) not in blob,(marker,encoding)
print('Normal plugin contains no diagnostic transport, authentication or offscreen mode',flush=True)
env=dict(os.environ)
for k in list(env):
 if k.startswith('VLC_PLAYER_DIAGNOSTICS'):del env[k]
env.update(TEMP=str(s/'tmp'),TMP=str(s/'tmp'),VLC_DATA_PATH=str(r),VLC_USERDATA_PATH=str(r/'portable'),QML_DISK_CACHE_PATH=str(s/'cache/qml-normal'),QT_DISABLE_SHADER_DISK_CACHE='1',QSG_RHI_DISABLE_SHADER_DISK_CACHE='1',QT_FORCE_STDERR_LOGGING='1',QSG_INFO='1',QT_SCREEN_SCALE_FACTORS='1;1;1;1;1;1;1;1',QT_SCALE_FACTOR='1')
# VLC already scans the plugins directory beside this exact executable.
# VLC_PLUGIN_PATH adds another scan, rather than replacing that directory;
# repeating it creates duplicate module/configuration owners in the audit.
env.pop('VLC_PLUGIN_PATH',None)
env.pop('QML_DISABLE_DISK_CACHE',None)
records={}
with (e/'plugin-cache.stdout').open('wb') as out,(e/'plugin-cache.stderr').open('wb') as err:
 p=subprocess.run([str(r/'vlc-cache-gen.exe'),str(r/'plugins')],cwd=r,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 assert p.returncode==0,p.returncode
records['plugin_cache_exit']=p.returncode
cache_log=(e/'plugin-cache.stderr').read_text(encoding='utf8',errors='replace')
assert 'cannot load plug-in' not in cache_log,cache_log
print('Packaged plugin inventory exits normally',flush=True)
args=[str(r/'vlc.exe'),'--intf=qt','--no-one-instance',*([] if options.with_media_library else ['--no-media-library']),'--restore-playback-pos=0','--no-save-recentplay','--no-qt-privacy-ask','--no-qt-updates-notif','--no-metadata-network-access','--no-qt-video-autoresize','--no-video-title-show','--no-volume-save','--mmdevice-volume=0.0','--play-and-exit','--file-logging','--log-verbose=2','--logfile='+str(e/'native-ui.log'),str(options.fixture.resolve())]
with (e/'native-ui.stdout').open('wb') as out,(e/'native-ui.stderr').open('wb') as err:
 p=IsolatedProcess(args,cwd=r,env=env,stdout=out,stderr=err)
 records['pid']=p.pid;records['desktop']=p.desktop_name;records['exit_code']=p.wait()
# Preserve the exact native result even when acceptance below fails.
log=(e/'native-ui.log').read_text(encoding='utf8',errors='replace');stderr=(e/'native-ui.stderr').read_text(encoding='utf8',errors='replace')
qml_failure_pattern=r'(TypeError:|ReferenceError:|is not installed|is not a type|is not available in|Type [^\n]+ unavailable|failed to load component|Binding loop detected|source item.s window:|Cannot assign to non-existent property|Unable to assign \[undefined\] to)'
requirements={
 'actual_picture': 'Received first picture' in log,
 'natural_eof': 'EOF reached' in log,
 'input_released': ("destroying input for '"+options.fixture.name+"'") in log,
 'qt_event_loop_finished': 'QApp exec() finished' in log,
 'no_plugin_load_errors':not any(x in log for x in ['cannot load module','could not load module','cannot load plug-in']),
 'no_qml_runtime_errors':not re.search(qml_failure_pattern,log+'\n'+stderr)
}
if options.with_media_library:
 requirements['native_media_library_started']='using medialibrary module "medialibrary"' in log
warnings=[line for line in (log+'\n'+stderr).splitlines() if re.search(qml_failure_pattern,line)]
records['qml_runtime_errors']=warnings
records['media_library_enabled']=options.with_media_library
records.update(checks=requirements,qt_plugin_sha256=hashlib.sha256(blob).hexdigest(),upnp_plugin_sha256=hashlib.sha256((r/'plugins/services_discovery/libupnp_plugin.dll').read_bytes()).hexdigest(),debug_markers_absent=markers,profile_isolation='Existing empty portable directory beside executable',capture_scope='Inactive desktop, no OS input or desktop switching',verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
records['passed']=records['exit_code']==0 and all(requirements.values())
(e/'result.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
print(json.dumps(records,indent=2),flush=True)
raise SystemExit(0 if records['passed'] else 1)
