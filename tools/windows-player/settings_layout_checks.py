"""Original Figma field geometry checked against the instantiated native UI."""


def check_settings_layout(snapshot, category, *, compact):
    widgets = {row['node']: row for row in snapshot['widgets']}
    area = next(row for row in widgets.values() if row['id'] == 'preferencesScroll' + str(category))

    def belongs(row):
        while row['parent'] >= 0:
            row = widgets[row['parent']]
            if row['node'] == area['node']:
                return True
        return False

    checked = []
    for editor in widgets.values():
        if not editor['center_visible'] or not belongs(editor) or editor['parent'] < 0:
            continue
        owner = widgets[editor['parent']]
        if not owner['id'].startswith('preference-') or owner['id'].startswith('preference-native-'):
            continue
        identity = editor['id']
        full_action = identity in ('preferencesAction-shortcuts', 'preferencesAction-reset-shortcuts',
                                   'preferencesAction-rescan-plugins')
        if not (identity.startswith(('value-', 'editor-')) or full_action):
            continue
        if editor['type'] == 'QCheckBox':
            continue
        expected = owner['width'] if compact else 320
        assert abs(editor['width'] - expected) <= 1, ('Reference field width', owner['id'], identity, editor['width'], expected)
        if identity in ('editor-mouse-hide-timeout','editor-qt-notification-duration'):
            # Original Interface rows use a22px slider,8px gap and17px labels.
            # Their QWidget wrapper is sized by that child layout. Acceptance
            # concerns its rendered47px height, not QWidget's min/max mechanism.
            assert editor['height']==47,('Reference Interface slider group height',identity,editor['height'],47)
        else:
            assert editor['minimum_height']==editor['height']==editor['maximum_height'], (
                'Stylesheet changed the fixed reference field height',identity,
                editor['minimum_height'],editor['height'],editor['maximum_height'])
        if editor['type'] in ('QSpinBox','QDoubleSpinBox'):
            assert editor['maximum_width']>90,('Legacy numeric width cap remains',identity,editor['maximum_width'])
            assert editor['input_alignment'] & 1,('Reference numeric input must align left',identity)
            assert editor['spin_buttons']==2,('Reference text input must not expose spin arrows',identity)
        if full_action:
            assert editor['font_weight']==600,('Reference action typography must be semibold',identity,editor['font_weight'])
        checked.append(identity)
        if identity.startswith('editor-freetype-') and identity.endswith('color'):
            assert editor['height'] == 32, ('Color field height', editor)
            value = next(row for row in widgets.values() if row['parent'] == editor['node'] and row['id'].startswith('value-'))
            swatch = next(row for row in widgets.values() if row['parent'] == editor['node'] and row['id'].startswith('color-'))
            assert value['type'] == 'QLineEdit' and len(value['text']) == 7 and value['text'].startswith('#')
            assert swatch['width'] == swatch['height'] == 24
    if category == 12:
        for identity, expected in (('preferencesExtensionSearch',210), ('preferencesFindExtensions',186),
                                   ('preferencesAddExtension',100), ('preferencesRemoveExtension',100)):
            editor=next(row for row in widgets.values() if row['id']==identity)
            if not editor['center_visible']:
                continue
            if not compact:
                assert editor['width']==expected,('Reference extension toolbar width',identity,editor['width'],expected)
            toolbar=widgets[editor['parent']]
            assert editor['x']>=0 and editor['x']+editor['width']<=toolbar['width']
            checked.append(identity)
    if category == 4:
        for identity in ('value-audio-track','value-sub-track'):
            editor=next(row for row in widgets.values() if row['id']==identity)
            assert editor['type']=='QLineEdit',('Reference track index must be a text input',identity,editor['type'])
            assert editor['input_alignment'] & 1,('Track input must align left',identity)
        disc=next(row for row in widgets.values() if row['id']=='value-dvd')
        assert disc['type']=='QComboBox' and disc['editable'],('Optical drive must allow detected choices and a custom device path',disc['type'])
    if category == 7:
        for identity in ('value-freetype-font','value-freetype-monofont'):
            editor=next((row for row in widgets.values() if row['id']==identity),None)
            if editor and editor['center_visible']:
                assert editor['type']=='QLineEdit',('Reference font family is a free text input',identity,editor['type'])
        size=next((row for row in widgets.values() if row['id']=='value-sub-text-scale-size'),None)
        if size and size['center_visible']:
            assert size['type']=='QComboBox',('Reference font size has real presets and custom numeric entry',size['type'])
    if category == 0 and not compact and area['scroll_value'] == 0:
        # These original positions are independent of native option values.
        # The log path is a grouped editor, not a shrunken Browse button.
        def dialog_y(row):
            value = row['y']
            while row['parent'] >= 0:
                row = widgets[row['parent']]
                if row['id'] == 'redesignPreferences':
                    return value
                value += row['y']
            raise AssertionError('Settings control has no dialog parent')
        for identity, expected in (('preferencesLanguage', 114), ('editor-logfile', 538),
                                   ('value-log-verbose', 584), ('preferencesAdvanced0', 645)):
            editor = next(row for row in widgets.values() if row['id'] == identity)
            assert abs(dialog_y(editor) - expected) <= 2, ('Reference vertical rhythm', identity, dialog_y(editor), expected)
    return checked
