"""Regression for the normal release log contract, independent of NDEBUG logs."""
from pathlib import Path
import unittest

from runtime_teardown import vlc_input_release_evidence


class RuntimeTeardownTests(unittest.TestCase):
    fixture=Path('control.mkv')
    lines=(
        "main input debug: Creating an input for playback'control.mkv'",
        'main input debug: EOF reached',
        'main decoder debug: removing "video decoder" module "avcodec"',
        'main demux debug: removing "demux" module "mkv"',
        'main stream debug: removing "access" module "filesystem"',
        'qt interface debug: on_player_state_changed VLC_PLAYER_STATE_STOPPED',
        'qt interface debug: QApp exec() finished',
    )

    def test_release_without_debug_only_destruction_log(self):
        self.assertTrue(vlc_input_release_evidence('\n'.join(self.lines),self.fixture,0)['passed'])

    def test_incomplete_release_is_rejected_at_each_boundary(self):
        for index in range(len(self.lines)):
            with self.subTest(boundary=index):
                self.assertFalse(vlc_input_release_evidence('\n'.join(self.lines[:index]+self.lines[index+1:]),self.fixture,0)['passed'])

    def test_unrelated_or_out_of_order_teardown_is_rejected(self):
        self.assertFalse(vlc_input_release_evidence('\n'.join(reversed(self.lines)),self.fixture,0)['passed'])
        self.assertFalse(vlc_input_release_evidence('\n'.join(self.lines),Path('other.mkv'),0)['passed'])

    def test_crash_after_teardown_is_rejected(self):
        self.assertFalse(vlc_input_release_evidence('\n'.join(self.lines),self.fixture,1)['passed'])

    def test_debug_destroy_message_alone_does_not_prove_playback(self):
        self.assertFalse(vlc_input_release_evidence("destroying input for 'control.mkv'",self.fixture,0)['passed'])


if __name__=='__main__':
    unittest.main()
