"""Regression checks for exact native labels used by the app-owned UI driver."""
import importlib.util
from pathlib import Path

source=Path(__file__).with_name('inspect-player.py')
spec=importlib.util.spec_from_file_location('inspect_player',source)
driver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
for actual,visible in (
    ('&Tools','Tools'),
    ('New / Manage Profiles…','New / Manage Profiles…'),
    ('Profile (Cinema Ω && Library)','Profile (Cinema Ω & Library)'),
    ('Rock && Roll','Rock & Roll'),
    ('&&&Open','&Open'),
):
    assert driver.visible_label(actual)==visible,(actual,visible)
print('Native mnemonic labels and literal ampersands preserve exact target identity.')
