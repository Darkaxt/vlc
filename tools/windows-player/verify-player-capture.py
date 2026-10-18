"""Verify native player geometry and the SDR color-pattern blur regression.

Input is a diagnostic JSON snapshot and the recorded HWND's composed PNG.
The pattern check uses a 1920x1080 testsrc2 frame at approximately 1920x1080
physical client pixels; it checks both the blurred chrome and unaffected video.
"""
import argparse
import json
from pathlib import Path

from PIL import Image


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pattern_edges(capture, window):
    with Image.open(capture) as original:
        image = original.convert("RGB")
    scale = window["dpr"]
    width, height = window["width"], window["height"]
    require(abs(width * scale - 1920) <= 3, "Pattern client width must be approximately 1920 physical pixels")
    require(abs(height * scale - 1080) <= 3, "Pattern client height must be approximately 1080 physical pixels")
    # Magenta/cyan boundary, away from the title, folder and window buttons.
    x = int(1600 + (image.width - width * scale) / 2)
    inset_y = (image.height - height * scale) / 2
    chrome_y, video_y = int(20 * scale + inset_y), int(150 + inset_y)
    chrome = [image.getpixel((q, chrome_y))[0] for q in range(x - 20, x + 21)]
    video = [image.getpixel((q, video_y))[0] for q in range(x - 20, x + 21)]
    return {"chrome_red": chrome, "video_red": video,
            "chrome_levels": len(set(chrome)), "video_levels": len(set(video))}


def verify_capture(snapshot, capture, pattern=False):
    require(not snapshot["qml_errors"], "QML errors were reported")
    require(snapshot["images"]["failed"] == 0 and snapshot["images"]["pending"] == 0,
            "Mounted player images are not resolved")
    window = snapshot["window"]
    width = window["width"]

    def item(identifier):
        matches = [n for n in snapshot["tree"] if n["id"] == identifier and n["visible"]]
        require(len(matches) == 1, "Expected one visible " + identifier)
        return matches[0]

    for identifier in ("previousButton", "playButton", "nextButton", "progressSlider",
                       "muteButton", "volumeSlider", "toolsButton", "subtitleButton",
                       "audioButton", "playqueueToggle"):
        node = item(identifier)
        require(node["x"] >= 0 and node["x"] + node["width"] <= width + 0.01,
                identifier + " exceeds the player width")
        require(bool(node.get("name")), identifier + " has no accessible name")
    require(item("playerTopBar")["height"] == 40, "Title bar differs from Figma's logical height")
    require(item("playerControlBar")["height"] == 54, "Controls differ from Figma's logical height")
    require(item("progressSlider")["width"] >= 60, "Seek target is too small")
    require(bool(item("playerMediaTitle").get("text")), "Media title/filename is missing")
    backdrop = snapshot["video_backdrop"]
    require(backdrop.get("hresult") == 0 and backdrop.get("video_content") and backdrop.get("enabled"),
            "Native video backdrop is not attached successfully")
    result = {"status": "passed", "window": window,
              "media_title": item("playerMediaTitle")["text"]}
    if pattern:
        edges = pattern_edges(capture, window)
        require(edges["chrome_levels"] >= 8, "Video beneath the translucent chrome is unblurred")
        require(edges["video_levels"] <= 6, "Blur leaks outside the chrome into the video")
        result["pattern_edges"] = edges
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--pattern", action="store_true", help="Light theme, reference-aspect testsrc2 capture")
    args = parser.parse_args()
    result = verify_capture(json.loads(args.snapshot.read_text(encoding="utf8")), args.capture, args.pattern)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
