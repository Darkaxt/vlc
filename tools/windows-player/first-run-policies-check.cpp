// SPDX-License-Identifier: GPL-2.0-or-later
#include "dialogs/help/fork_release.hpp"
#include "maininterface/window_geometry.hpp"
#include "player/embedded_subtitles.hpp"
#include <QCoreApplication>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <iostream>
#include <cstdlib>

static void require(bool value, const char *message)
{
    if (!value) { std::cerr << message << std::endl; std::exit(1); }
}

static QJsonObject release(const QString &version)
{
    const auto tag=QStringLiteral("redesign-v")+version;
    const auto base=QStringLiteral("Modern-VLC-Fork-")+version;
    QJsonArray assets;
    for(const auto &name:QStringList{base+QStringLiteral("-win64-portable.zip"),base+QStringLiteral("-corresponding-source.tar.gz"),
        base+QStringLiteral("-win64-symbols.zip"),QStringLiteral("SHA256SUMS.txt")})
        assets.append(QJsonObject{{QStringLiteral("name"),name},{QStringLiteral("state"),QStringLiteral("uploaded")},
            {QStringLiteral("size"),1024},{QStringLiteral("browser_download_url"),QStringLiteral("https://github.com/Darkaxt/vlc/releases/download/")+tag+QLatin1Char('/')+name}});
    return {{QStringLiteral("tag_name"),tag},{QStringLiteral("html_url"),QStringLiteral("https://github.com/Darkaxt/vlc/releases/tag/")+tag},
        {QStringLiteral("draft"),false},{QStringLiteral("prerelease"),false},{QStringLiteral("assets"),assets},{QStringLiteral("body"),QStringLiteral("Test release")}};
}

int main(int argc,char **argv)
{
    QCoreApplication app(argc,argv);
    require(argc==2,"Pass the exact generated fixture directory");
    auto json=release(QString::fromLatin1(ForkRelease::currentVersion));
    const auto parse=[](const QJsonObject &value){return ForkRelease::parse(QJsonDocument(value).toJson());};
    require(parse(json).valid,"Current complete normal release rejected");
    require(parse(release(QStringLiteral("1.2.0"))).version>QVersionNumber(1,1,2),"Newer fork version comparison failed");
    auto invalid=json;invalid[QStringLiteral("draft")]=true;require(!parse(invalid).valid,"Draft release accepted");
    invalid=json;invalid[QStringLiteral("prerelease")]=true;require(!parse(invalid).valid,"Prerelease accepted");
    invalid=json;invalid[QStringLiteral("tag_name")]=QStringLiteral("4.0.0-dev");require(!parse(invalid).valid,"Upstream development version accepted");
    invalid=json;invalid[QStringLiteral("html_url")]=QStringLiteral("https://example.com/update");require(!parse(invalid).valid,"Foreign release page accepted");
    invalid=json;auto assets=invalid[QStringLiteral("assets")].toArray();assets.removeLast();invalid[QStringLiteral("assets")]=assets;require(!parse(invalid).valid,"Incomplete publication accepted");
    require(!ForkRelease::parse(QByteArray("{broken")).valid,"Malformed JSON accepted");
    require(!ForkRelease::parse(QByteArray(1024*1024+1,'x')).valid,"Oversized metadata accepted");
    QFile actual(QString::fromLocal8Bit(argv[1])+QStringLiteral("/github-latest.json"));
    require(actual.open(QIODevice::ReadOnly),"Real HTTPS metadata fixture missing");
    require(ForkRelease::parse(actual.readAll()).valid,"Actual GitHub HTTPS metadata rejected");
    int geometryCases=0;
    for(const auto &screen:{QRect(0,0,1920,1040),QRect(-1280,0,1280,680),QRect(20,40,854,440)})
        for(const auto &source:{QSizeF(3840,2160),QSizeF(5760,1080),QSizeF(800,2400)})
            for(const double scale:{1.,1.5,2.}) {
                const QMargins frame(8,31,8,8);
                const auto fit=fitVideoWindow(source/scale,QSize(40,94),screen,frame,QSize(472,360),QSize(16777215,16777215),QPoint(1500,900));
                require(screen.contains(fit.marginsAdded(frame)),"Video/chrome/frame overflowed the current screen");
                ++geometryCases;
            }
    const auto directory=QString::fromLocal8Bit(argv[1])+QLatin1Char('/');
    const std::atomic_bool running{false};
    QJsonArray decoded;
    for(const auto &name:{QStringLiteral("embedded-text.mkv"),QStringLiteral("embedded-ass.mkv"),QStringLiteral("embedded-text.mp4")}) {
        const auto result=readEmbeddedSubtitles(directory+name,0,-1,running);
        require(result.error.isEmpty()&&!result.cancelled,"Embedded text extraction failed");
        require(result.cues.size()==3,"Unexpected subtitle cue count");
        require(std::abs(result.cues.front().toMap()[QStringLiteral("start")].toLongLong()-1000)<=5,"Embedded cue start is not media-relative");
        require(std::abs(result.cues.front().toMap()[QStringLiteral("end")].toLongLong()-2500)<=5,"Embedded cue end is incorrect");
        decoded.append(QJsonObject{{QStringLiteral("file"),name},{QStringLiteral("cues"),QJsonArray::fromVariantList(result.cues)}});
    }
    const auto other=readEmbeddedSubtitles(directory+QStringLiteral("embedded-text.mkv"),1,-1,running);
    require(other.error.isEmpty()&&other.cues.size()==2,"Second selected subtitle stream missing");
    require(std::abs(other.cues.front().toMap()[QStringLiteral("start")].toLongLong()-2000)<=5,"Selected stream identity mixed with first track");
    const auto image=readEmbeddedSubtitles(directory+QStringLiteral("embedded-image.mkv"),0,-1,running);
    require(image.cues.isEmpty()&&image.error.contains(QStringLiteral("Image subtitles")),"Image subtitle was advertised as text cues");
    const std::atomic_bool cancelled{true};
    const auto stopped=readEmbeddedSubtitles(directory+QStringLiteral("embedded-text.mkv"),0,-1,cancelled);
    require(stopped.cancelled&&stopped.cues.isEmpty(),"Cancelled extraction published cues");
    std::cout<<QJsonDocument(QJsonObject{{QStringLiteral("passed"),true},{QStringLiteral("geometry_cases"),geometryCases},
        {QStringLiteral("decoded"),decoded},{QStringLiteral("real_https_metadata"),true},{QStringLiteral("selected_track_identity"),true},
        {QStringLiteral("image_limit"),true},{QStringLiteral("cancellation"),true}}).toJson().constData();
    return 0;
}
