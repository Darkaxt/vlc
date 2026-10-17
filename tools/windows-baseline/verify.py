"""Native Windows acceptance for S1; all generated files stay in the E: task root."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(sys.argv[1]).resolve()
if root.drive.upper() != "E:" or root.name != "vlc-s1-20261017":
    raise SystemExit("Expected the registered E: S1 task root")
runtime, evidence = root / "runtime", root / "evidence"
portable = runtime / "portable"
portable.mkdir(exist_ok=True)
(root / "cache" / "qml").mkdir(parents=True, exist_ok=True)
env = dict(os.environ)
env.pop("QML_DISABLE_DISK_CACHE", None)
env.update(TEMP=str(root / "tmp"), TMP=str(root / "tmp"),
           VLC_PLUGIN_PATH=str(runtime / "plugins"), VLC_DATA_PATH=str(runtime),
           VLC_USERDATA_PATH=str(portable), QML_DISK_CACHE_PATH=str(root / "cache" / "qml"),
           QT_DISABLE_SHADER_DISK_CACHE="1", QSG_RHI_DISABLE_SHADER_DISK_CACHE="1",
           QT_FORCE_STDERR_LOGGING="1", QSG_INFO="1")


def run(name, args):
    started = time.monotonic()
    with (evidence / f"{name}.stdout").open("wb") as out, (evidence / f"{name}.stderr").open("wb") as err:
        completed = subprocess.run(args, cwd=runtime, env=env, stdout=out, stderr=err,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    result = {"exit_code": completed.returncode, "elapsed_seconds": time.monotonic() - started}
    print(name, json.dumps(result), flush=True)
    return result


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


exe = str(runtime / "vlc.exe")
results = {"plugin_cache": run("plugin-cache", [str(runtime / "vlc-cache-gen.exe"), str(runtime / "plugins")])}
results["engine"] = run("engine", [str(runtime / "playback-check.exe"), str(root / "fixture.mp4")])
results["engine"]["observation"] = json.loads((evidence / "engine.stdout").read_text())
results["missing_file"] = run("missing-file", [str(runtime / "playback-check.exe"), str(root / "missing-fixture.mp4")])
results["missing_file"]["observation"] = json.loads((evidence / "missing-file.stdout").read_text())
results["inventory"] = run("inventory", [str(runtime / "inventory.exe")])
inventory = json.loads((evidence / "inventory.stdout").read_text(encoding="utf8"))
results["inventory"]["module_count"] = len(inventory["modules"])
results["inventory"]["option_count"] = sum(len(m["options"]) for m in inventory["modules"])
results["inventory"]["version"] = inventory["version"]
option_names = {option["name"] for module in inventory["modules"] for option in module["options"]}
required_options = {"qt-updates-notif", "qt-start-minimized", "metadata-network-access",
                    "file-logging", "log-verbose", "logfile", "play-and-exit", "aout", "intf", "one-instance"}
if required_options - option_names:
    raise SystemExit(f"Native GUI command has unavailable options: {sorted(required_options - option_names)}")
results["qt_playback"] = run("qt-playback", [exe, "--intf=qt", "--ignore-config", "--no-one-instance",
    "--no-media-library", "--no-qt-privacy-ask", "--no-qt-updates-notif", "--no-metadata-network-access",
    "--qt-start-minimized", "--aout=dummy", "--play-and-exit", "--file-logging", "--log-verbose=2",
    f"--logfile={evidence / 'qt-playback.log'}", str(root / "fixture.mp4")])
log = (evidence / "qt-playback.log").read_text(encoding="utf8", errors="replace")
results["qt_playback"]["qt_event_loop_exited"] = "QApp exec() finished" in log
results["qt_playback"]["first_picture_received"] = "Received first picture" in log
results["qt_playback"]["input_released"] = "destroying input for 'fixture.mp4'" in log
before = json.loads((evidence / "existing-profile-before.json").read_text())
after = []
for item in before["items"]:
    p = Path(before["root"]) / item["name"]
    after.append({"name": item["name"], "exists": p.exists(),
                  **({"size": p.stat().st_size, "sha256": digest(p)} if p.is_file() else {})})
results["existing_profile_unchanged"] = before["items"] == after
loader_errors = []
for name in ["plugin-cache", "engine", "missing-file", "inventory", "qt-playback"]:
    path = evidence / f"{name}.stderr"
    loader_errors.extend(line for line in path.read_text(encoding="utf8", errors="replace").splitlines()
                         if "cannot load plug-in" in line)
loader_errors.extend(line for line in log.splitlines() if "cannot load plug-in" in line)
results["plugin_loader_errors"] = sorted(set(loader_errors))
results["fixture_sha256"] = digest(root / "fixture.mp4")
results["runtime_hashes"] = {p.name: digest(p) for p in runtime.iterdir()
                              if p.is_file() and p.suffix.lower() in {".exe", ".dll"}}
results["corrected_plugin_hashes"] = {str(path.relative_to(runtime)).replace("\\", "/"): digest(path)
    for path in [runtime / "plugins" / directory / filename for directory, filename in [
        ("access", "libaccess_srt_plugin.dll"), ("access_output", "libaccess_output_srt_plugin.dll"),
        ("codec", "libx265_plugin.dll"), ("demux", "libgme_plugin.dll"), ("gui", "libqt_plugin.dll")]]}
results["passed"] = (results["plugin_cache"]["exit_code"] == 0
    and results["engine"]["exit_code"] == 0 and results["engine"]["observation"]["passed"]
    and results["missing_file"]["exit_code"] == 1 and results["missing_file"]["observation"]["error"]
    and results["qt_playback"]["exit_code"] == 0 and results["qt_playback"]["qt_event_loop_exited"]
    and results["qt_playback"]["first_picture_received"] and results["qt_playback"]["input_released"]
    and results["existing_profile_unchanged"]
    and results["inventory"]["exit_code"] == 0 and results["inventory"]["option_count"] > 0
    and not results["plugin_loader_errors"])
(evidence / "native-verification.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf8")
print(json.dumps(results, indent=2), flush=True)
raise SystemExit(0 if results["passed"] else 1)
