// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

#include <QApplication>
#include <QIcon>
#include <QIconEngine>
#include <QPainter>
#include <QPixmap>
#include <QStyle>
#include <QStyleOption>
#include <QSvgRenderer>

// Keep the original SVG geometry until Qt requests the actual icon size/DPR.
// A pre-rendered 24px QIcon otherwise filters its antialiased edges again when
// an 18px help button or the search action requests a smaller pixmap.
class SettingsSvgIconEngine final : public QIconEngine
{
public:
    SettingsSvgIconEngine(const QString &path, const QColor &color,
                          const QString &selectedPath = {}, const QColor &selectedColor = {})
        : path(path), color(color), selectedPath(selectedPath), selectedColor(selectedColor) {}

    QIconEngine *clone() const override
    {
        return new SettingsSvgIconEngine(path, color, selectedPath, selectedColor);
    }

    QString key() const override { return QStringLiteral("ModernVLCSettingsSvg"); }
    bool isNull() override { return path.isEmpty(); }

    QPixmap pixmap(const QSize &size, QIcon::Mode mode, QIcon::State state) override
    {
        return scaledPixmap(size, mode, state, 1);
    }

    QPixmap scaledPixmap(const QSize &size, QIcon::Mode mode, QIcon::State, qreal scale) override
    {
        if (size.isEmpty()) return {};
        QPixmap result(size * scale);
        result.setDevicePixelRatio(scale);
        result.fill(Qt::transparent);
        {
            QPainter painter(&result);
            const bool selected = mode == QIcon::Selected && !selectedPath.isEmpty();
            QSvgRenderer svg(selected ? selectedPath : path);
            const QRectF bounds{QPointF(), QSizeF(size)};
            svg.render(&painter, bounds);
            painter.setCompositionMode(QPainter::CompositionMode_SourceIn);
            painter.fillRect(bounds, selected ? selectedColor : color);
        }
        if (mode == QIcon::Disabled)
        {
            QStyleOption option;
            option.palette = QApplication::palette();
            return QApplication::style()->generatedIconPixmap(mode, result, &option);
        }
        return result;
    }

    void paint(QPainter *painter, const QRect &rect, QIcon::Mode mode, QIcon::State state) override
    {
        const auto image = scaledPixmap(rect.size(), mode, state, painter->device()->devicePixelRatioF());
        painter->save();
        painter->setRenderHint(QPainter::SmoothPixmapTransform, false);
        painter->drawPixmap(rect.topLeft(), image);
        painter->restore();
    }

private:
    const QString path;
    const QColor color;
    const QString selectedPath;
    const QColor selectedColor;
};

inline QIcon settingsSvgIcon(const QString &path, const QColor &color,
                             const QString &selectedPath = {}, const QColor &selectedColor = {})
{
    return QIcon(new SettingsSvgIconEngine(path, color, selectedPath, selectedColor));
}
