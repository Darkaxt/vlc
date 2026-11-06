// SPDX-License-Identifier: GPL-2.0-or-later
// One recipe for QML, QIcon and the Windows Shell's persistent icon resource.
#pragma once
#include <QBuffer>
#include <QColor>
#include <QCoreApplication>
#include <QDataStream>
#include <QDir>
#include <QFile>
#include <QIcon>
#include <QImage>
#include <QPixmap>
#include <QSaveFile>

namespace EngineIcon {
inline QColor defaultAccent(bool mpv)
{
    // Logo highlight purple, rather than mpv.io's nearly-black header fill.
    return QColor(mpv ? "#9859ad" : "#d37918");
}
inline QImage tint(QImage image, const QColor &accent, bool mpv)
{
    image=image.convertToFormat(QImage::Format_ARGB32);
    for(int y=0;y<image.height();++y) {
        auto *line=reinterpret_cast<QRgb *>(image.scanLine(y));
        for(int x=0;x<image.width();++x) {
            const QColor original=QColor::fromRgba(line[x]);
            // Keep the neutral bevel, play triangle, highlights and alpha.
            if(!original.alpha() || original.hslSaturationF()<0.12)continue;
            QColor color=accent;
            if(mpv)
                color=QColor::fromHslF(accent.hslHueF()<0 ? 0 : accent.hslHueF(),
                    original.hslSaturationF()*accent.hslSaturationF(),original.lightnessF());
            color.setAlpha(original.alpha());line[x]=color.rgba();
        }
    }
    return image;
}
struct Assets { QIcon icon; QString root; QString ico; bool valid=false; };
inline bool save(const QString &path,const QByteArray &bytes)
{
    QFile old(path);
    if(old.open(QIODevice::ReadOnly) && old.readAll()==bytes)return true;
    old.close();QSaveFile output(path);
    return output.open(QIODevice::WriteOnly) && output.write(bytes)==bytes.size() && output.commit();
}
inline Assets create(bool mpv,const QColor &accent,const QString &cache)
{
    Assets result;
    const bool original=accent==defaultAccent(mpv);
    result.root=original ? QStringLiteral(":/redesign/icons") :
        QDir(cache).filePath(QStringLiteral("engine-icons-v1/%1-%2").arg(mpv?"mpv":"vlc",accent.name().mid(1)));
    if(!original && !QDir().mkpath(result.root))return result;
    QList<QByteArray> frames;QList<int> sizes;
    for(int size : {16,24,32,48,64,256}) {
        QImage image(mpv ? QStringLiteral(":/redesign/icons/mpv-%1.png").arg(size) : QStringLiteral(":/redesign/icons/app.png"));
        if(image.isNull())return result;
        if(!original)image=tint(image,accent,mpv);
        if(image.size()!=QSize(size,size))image=image.scaled(size,size,Qt::KeepAspectRatio,Qt::SmoothTransformation);
        result.icon.addPixmap(QPixmap::fromImage(image));
        QByteArray png;QBuffer buffer(&png);buffer.open(QIODevice::WriteOnly);
        if(!image.save(&buffer,"PNG"))return result;
        frames.push_back(png);sizes.push_back(size);
        if(!original && !save(QDir(result.root).filePath(QStringLiteral("%1-%2.png").arg(mpv?"mpv":"vlc").arg(size)),png))return result;
    }
    if(original) {
        result.ico=QDir(QCoreApplication::applicationDirPath()).filePath(mpv?"mpv.ico":"vlc.exe");
    } else {
        QByteArray ico;QDataStream stream(&ico,QIODevice::WriteOnly);stream.setByteOrder(QDataStream::LittleEndian);
        stream<<quint16(0)<<quint16(1)<<quint16(frames.size());
        quint32 offset=6+16*frames.size();
        for(int i=0;i<frames.size();++i) {
            stream<<quint8(sizes[i]==256?0:sizes[i])<<quint8(sizes[i]==256?0:sizes[i])
                  <<quint8(0)<<quint8(0)<<quint16(1)<<quint16(32)<<quint32(frames[i].size())<<offset;
            offset+=frames[i].size();
        }
        for(const auto &frame:frames)stream.writeRawData(frame.constData(),frame.size());
        result.ico=QDir(result.root).filePath(mpv?"mpv.ico":"vlc.ico");
        if(stream.status()!=QDataStream::Ok || !save(result.ico,ico))return result;
    }
    result.valid=true;return result;
}
}
