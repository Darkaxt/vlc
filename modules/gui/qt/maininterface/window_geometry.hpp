// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_QT_WINDOW_GEOMETRY_HPP
#define VLC_QT_WINDOW_GEOMETRY_HPP
#include <QMargins>
#include <QRect>
#include <QSizeF>
#include <algorithm>
#include <cmath>

class QWindow;
QMargins windowFrameMargins(QWindow *window);

// Both the video and non-video interface area must fit before native frames
// are added. Input/output coordinates are Qt logical pixels, on one screen.
inline QRect fitVideoWindow(const QSizeF &video, const QSize &chrome, const QRect &screen,
    const QMargins &frame, const QSize &minimum, const QSize &maximum, const QPoint &position)
{
    const QRect area = screen.marginsRemoved(frame);
    const QSize limit = area.size().boundedTo(maximum).expandedTo(QSize(1, 1));
    const QSize overhead(std::max(0, chrome.width()), std::max(0, chrome.height()));
    const QSize room = (limit - overhead).expandedTo(QSize(1, 1));
    const double scale = std::min({1., room.width() / std::max(1., video.width()),
        room.height() / std::max(1., video.height())});
    QSize size(int(std::floor(std::max(1., video.width()) * scale)),
               int(std::floor(std::max(1., video.height()) * scale)));
    size = (size + overhead).expandedTo(minimum.boundedTo(limit)).boundedTo(limit);
    return QRect(QPoint(std::clamp(position.x(), area.left(), area.left() + area.width() - size.width()),
                        std::clamp(position.y(), area.top(), area.top() + area.height() - size.height())), size);
}
#endif
