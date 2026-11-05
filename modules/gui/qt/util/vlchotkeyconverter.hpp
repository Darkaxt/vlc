#ifndef VLC_HOTKEY_CONVERTER_HPP
#define VLC_HOTKEY_CONVERTER_HPP

#include <QObject>
#include <QPoint>
#include <QStringList>
#include <QList>
#include <QKeySequence>
#include <QtQml/qqmlregistration.h>

/* VLC Key/Wheel hotkeys interactions */

Q_MOC_INCLUDE("QKeyEvent")
Q_MOC_INCLUDE("QWheelEvent")

class QKeyEvent;
class QWheelEvent;
class QInputEvent;

int qtKeyModifiersToVLC( const QInputEvent& e );
int qtEventToVLCKey( QKeyEvent *e );
int qtWheelEventToVLCKey( const QWheelEvent& e );
QString VLCKeyToString( unsigned val, bool );

// These are native configuration keys, shared by registration, dispatch and the
// shortcut editor. The labels/defaults describe the existing interface commands.
#define VLC_INTERFACE_SHORTCUTS(X) \
    X("open-file", "Open File(s)", "Ctrl+o") \
    X("open-advanced", "Open Multiple Files", "Ctrl+Shift+o") \
    X("open-folder", "Open Folder", "Ctrl+f") \
    X("open-disc", "Open Disc", "Ctrl+d") \
    X("open-network", "Open Network Stream", "Ctrl+n") \
    X("open-capture", "Open Capture Device", "Ctrl+c") \
    X("paste", "Open Location from Clipboard", "Ctrl+v\tShift+Insert") \
    X("save-playlist", "Save Play Queue to File", "Ctrl+y") \
    X("convert", "Convert / Save", "Ctrl+r") \
    X("stream", "Stream", "Ctrl+s") \
    X("quit", "Quit", "Ctrl+q") \
    X("effects", "Effects and Filters", "Ctrl+e") \
    X("media-info", "Media Information", "Ctrl+i") \
    X("codec-info", "Codec Information", "Ctrl+j") \
    X("messages", "Messages", "Ctrl+m") \
    X("preferences", "Settings", "Ctrl+p") \
    X("goto-time", "Jump to Time", "Ctrl+t") \
    X("vlm", "VLM Configuration", "Ctrl+Shift+w") \
    X("help", "Help", "F1") \
    X("about", "About VLC", "Shift+F1") \
    X("toolbar-menu", "Show Menu Bar", "F10") \
    X("interface-fullscreen", "Fullscreen Interface", "F11") \
    X("minimal-view", "Minimal View", "Ctrl+h") \
    X("hide-ui", "Hide Player Interface", "Ctrl+Shift+h") \
    X("zoom-in", "Increase Interface Scale", "Ctrl++\tCtrl+=") \
    X("zoom-out", "Decrease Interface Scale", "Ctrl+-\tCtrl+Shift+-") \
    X("bookmarks", "Manage Bookmarks", "Ctrl+b") \
    X("folder-address", "Go to Folder Address", "Alt+d") \
    X("recent-1", "Open Recent Media 1", "Ctrl+1") \
    X("recent-2", "Open Recent Media 2", "Ctrl+2") \
    X("recent-3", "Open Recent Media 3", "Ctrl+3") \
    X("recent-4", "Open Recent Media 4", "Ctrl+4") \
    X("recent-5", "Open Recent Media 5", "Ctrl+5") \
    X("recent-6", "Open Recent Media 6", "Ctrl+6") \
    X("recent-7", "Open Recent Media 7", "Ctrl+7") \
    X("recent-8", "Open Recent Media 8", "Ctrl+8") \
    X("recent-9", "Open Recent Media 9", "Ctrl+9") \
    X("recent-0", "Open Recent Media 10", "Ctrl+0")

struct ConfiguredShortcut
{
    QString option, action, keys, defaults;
};
QList<ConfiguredShortcut> configuredShortcuts();
QStringList configuredShortcutSequences(const QString &option);
QStringList interfaceShortcutSequences(const QString &originalSequence);
QList<QKeySequence> interfaceMenuShortcuts(const QString &originalSequence);
bool shortcutKeysEqual(const QString &first, const QString &second);

/**
 * @brief The WheelToVLCConverter class aggregates wheel events and
 * emit a signal once it gathers a full scroll step, as VLC doesn't handle
 * fractionnal scroll events
 */
class WheelToVLCConverter : public QObject
{
    Q_OBJECT
    QML_ELEMENT

public:
    using QObject::QObject;

public:
    Q_INVOKABLE Qt::Orientations getWheelOrientation(int x, int y);

signals:
    /**
     * @param vlcKey the VLC hotkey representation
     */
    void vlcWheelKey(int vlcKey);
    /**
     * @param steps: positive value indicated UP wheel events, negative DOWN wheel event
     * @param modifiers are keyboard pressed modifiers
     */
    void wheelUpDown(int steps, Qt::KeyboardModifiers modifiers);
    /**
     * @param steps: positive value indicated UP wheel events, negative DOWN wheel event
     * @param modifiers are keyboard pressed modifiers
     */
    void wheelLeftRight(int steps, Qt::KeyboardModifiers modifiers);

public slots:
    /**
     * @brief qmlWheelEvent handles wheel events as emitted by QWidget
     * @param e the wheel event
     */
    void wheelEvent(const QWheelEvent* e);

    /**
     * @brief qmlWheelEvent handles wheel events as emitted by QML
     * @param wheelEvent qml wheel event
     */
    void qmlWheelEvent(const QObject* wheelEvent);

    void customWheelEvent(const QPoint& pixelDelta,
                          const QPoint& angleDelta,
                          const Qt::MouseButtons buttons = {},
                          const Qt::KeyboardModifiers modifiers = {},
                          const bool inverted = false);

private:
    QPoint m_scrollAmount = {};
    bool m_reversed = false;
    Qt::KeyboardModifiers m_modifiers = {};
    Qt::MouseButtons m_buttons = {};
};

#endif // VLC_HOTKEY_CONVERTER_HPP
