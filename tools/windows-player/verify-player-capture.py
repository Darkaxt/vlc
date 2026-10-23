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
    # Magenta/cyan boundary. Sample below title glyphs so long metadata
    # cannot masquerade as blur detail in the source 40px title bar.
    x = int(1600 + (image.width - width * scale) / 2)
    inset_y = (image.height - height * scale) / 2
    chrome_y, video_y = int(35 * scale + inset_y), int(150 + inset_y)
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


def verify_library_capture(snapshot, capture):
    """Check the measured native library against the archived Figma geometry.

    Full Home: 6261:15078; compact header/list: 848:1997; video grid:
    970:4028. Content-dependent empty shelves are allowed to collapse.
    """
    require(not snapshot['qml_errors'], 'QML errors were reported')
    require(snapshot['library'] and snapshot['library']['ready'], 'Library is not ready')
    require(snapshot['images']['failed'] == 0 and snapshot['images']['pending'] == 0,
            'Mounted library assets are unresolved')
    window = snapshot['window']
    with Image.open(capture) as image:
        require(abs(image.width-window['width']*window['dpr']) <= 1
                and abs(image.height-window['height']*window['dpr']) <= 1,
                'Capture does not match the recorded native window')
    visible = [n for n in snapshot['tree'] if n['visible']]
    def item(identifier):
        matches = [n for n in visible if n['id'] == identifier]
        require(len(matches) == 1, 'Expected one visible '+identifier)
        return matches[0]
    library = item(snapshot['library']['id'])
    compact = library['id'] == 'compactLibrary'
    back = item('libraryBack')
    require(back['width'] == 24 and back['height'] == 24, 'Library header icon is not 24 square')
    require(abs(back['x']-library['x']-(70 if compact else 237)) <= 1,
            'Library header horizontal inset differs from Figma')
    require(abs(back['y']-library['y']-(20 if compact else 25)) <= 1,
            'Library header vertical inset differs from Figma')
    for key in ('home','videos','music','network','playlists','recent'):
        node = item('libraryNav_'+key)
        require(bool(node.get('name')), 'Library navigation lacks an accessible name')
        require(node['x'] >= library['x'] and node['x']+node['width'] <= library['x']+library['width']+1,
                'Library navigation exceeds its pane')
    home_cards = [n for n in visible if n['id'].startswith('libraryHomeItem_')]
    if not compact:
        for card in home_cards:
            require(card['width'] in (200,316), 'Home card width differs from Figma')
            require(card['height'] in (217,268), 'Home card height differs from Figma rounding')
        headings = {n.get('text'):n for n in visible if n.get('text') in
                    ('Continue Watching','Listen Again','Frequently Visited Folders')}
        if any(n['width'] == 316 for n in home_cards) and any(n['width'] == 200 for n in home_cards):
            y = library['y']+108
            for title,card_height in (('Continue Watching',217),('Listen Again',268),('Frequently Visited Folders',239)):
                node = headings[title]
                # Fractional DPR may round Inter's line box up by one logical
                # pixel per heading. Check the source gaps without accumulating
                # that native font rounding into a false spacing regression.
                require(abs(node['height']-24) <= 1, title+' line box differs from Figma')
                require(abs(node['x']-library['x']-237) <= 1 and abs(node['y']-y) <= 1,
                        title+' differs from Figma shelf spacing')
                y = node['y']+node['height']+20+card_height+77
    mini = [n for n in visible if n['id'] == 'mini']
    if mini:
        node = mini[0]
        require(node['x'] >= 0 and node['y'] >= 40 and node['x']+node['width'] <= window['width']+1
                and node['y']+node['height'] <= window['height']+1, 'Miniplayer exceeds the native window')
    return {'status':'passed','scope':'native library chrome; separately composed video is excluded',
            'window':window,'library':snapshot['library'],'source_frames':['6261:15078','848:1997','970:4028']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--pattern", action="store_true", help="Light theme, reference-aspect testsrc2 capture")
    parser.add_argument("--library", action="store_true", help="Verify native library chrome against Figma")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf8"))
    result = verify_library_capture(snapshot,args.capture) if args.library else verify_capture(snapshot,args.capture,args.pattern)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
