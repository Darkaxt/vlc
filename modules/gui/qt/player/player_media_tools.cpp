// SPDX-License-Identifier: GPL-2.0-or-later
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "player_media_tools.hpp"
#include "mpv_playback.hpp"
#include "playlist/playlist_controller.hpp"
#include <vlc_aout.h>
#include <vlc_configuration.h>
#include <vlc_iso_lang.h>
#include <vlc_modules.h>
#include <vlc_variables.h>
#include <vlc_vout.h>
#include "../../../audio_filter/equalizer_presets.h"
#include <QDateTime>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSaveFile>
#include <QSet>
#include <QStringConverter>
#include <cmath>

namespace {
struct Option { const char *section, *key, *module, *label; };
const Option optionsList[] = {
    {"subtitleTiming", "subsdelay-mode", "subsdelay", QT_TRANSLATE_NOOP("PlayerMediaTools", "Duration Calculation")},
    {"subtitleTiming", "subsdelay-factor", "subsdelay", QT_TRANSLATE_NOOP("PlayerMediaTools", "Subtitle Duration Factor")},
    {"subtitle", "freetype-font", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Subtitle Font")},
    {"subtitle", "freetype-color", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Text Color")},
    {"subtitle", "freetype-outline-color", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Outline Color")},
    {"subtitle", "sub-margin", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Subtitle Offset")},
    {"subtitle", "sub-text-scale", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Relative Font Size")},
    {"subtitle", "freetype-absolute-fontsize", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Font Size in Pixels (0 = Auto)")},
    {"subtitle", "freetype-outline-thickness", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Outline Thickness")},
    {"subtitle", "freetype-background-opacity", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Background Opacity")},
    {"equalizer", "equalizer-preamp", "equalizer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Preamp")},
    {"equalizer", "equalizer-2pass", "equalizer", QT_TRANSLATE_NOOP("PlayerMediaTools", "2 Pass")},
    {"equalizer", "equalizer-preset", "equalizer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Equalizer Preset")},
    {"equalizer", "equalizer-bands", "equalizer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Bands")},
    {"compressor", "compressor-rms-peak", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "RMS / Peak")},
    {"compressor", "compressor-attack", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Attack (ms)")},
    {"compressor", "compressor-release", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Release (ms)")},
    {"compressor", "compressor-threshold", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Threshold (dB)")},
    {"compressor", "compressor-ratio", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Ratio")},
    {"compressor", "compressor-knee", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Knee Radius (dB)")},
    {"compressor", "compressor-makeup-gain", "compressor", QT_TRANSLATE_NOOP("PlayerMediaTools", "Makeup Gain (dB)")},
    {"spatializer", "spatializer-roomsize", "spatializer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Size")},
    {"spatializer", "spatializer-width", "spatializer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Width")},
    {"spatializer", "spatializer-wet", "spatializer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Wet")},
    {"spatializer", "spatializer-dry", "spatializer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Dry")},
    {"spatializer", "spatializer-damp", "spatializer", QT_TRANSLATE_NOOP("PlayerMediaTools", "Damp")},
    {"stereo_widen", "stereowiden-delay", "stereo_widen", QT_TRANSLATE_NOOP("PlayerMediaTools", "Delay Time (ms)")},
    {"stereo_widen", "stereowiden-feedback", "stereo_widen", QT_TRANSLATE_NOOP("PlayerMediaTools", "Feedback Gain")},
    {"stereo_widen", "stereowiden-crossfeed", "stereo_widen", QT_TRANSLATE_NOOP("PlayerMediaTools", "Crossfeed")},
    {"stereo_widen", "stereowiden-dry-mix", "stereo_widen", QT_TRANSLATE_NOOP("PlayerMediaTools", "Dry Mix")},
    {"pitch", "pitch-shift", "scaletempo_pitch", QT_TRANSLATE_NOOP("PlayerMediaTools", "Adjust Pitch (semitones)")},
    {"essential", "hue", "adjust", QT_TRANSLATE_NOOP("PlayerMediaTools", "Hue")},
    {"essential", "brightness", "adjust", QT_TRANSLATE_NOOP("PlayerMediaTools", "Brightness")},
    {"essential", "contrast", "adjust", QT_TRANSLATE_NOOP("PlayerMediaTools", "Contrast")},
    {"essential", "saturation", "adjust", QT_TRANSLATE_NOOP("PlayerMediaTools", "Saturation")},
    {"essential", "gamma", "adjust", QT_TRANSLATE_NOOP("PlayerMediaTools", "Gamma")},
    {"essential", "sharpen-sigma", "sharpen", QT_TRANSLATE_NOOP("PlayerMediaTools", "Sharpen Sigma")},
    {"essential", "gradfun-radius", "gradfun", QT_TRANSLATE_NOOP("PlayerMediaTools", "Banding Removal Radius")},
    {"essential", "grain-variance", "grain", QT_TRANSLATE_NOOP("PlayerMediaTools", "Film Grain Variance")},
    {"crop", "crop-top", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Top (px)")},
    {"crop", "crop-bottom", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Bottom (px)")},
    {"crop", "crop-left", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Left (px)")},
    {"crop", "crop-right", "", QT_TRANSLATE_NOOP("PlayerMediaTools", "Right (px)")},
    {"colors", "extract-component", "extract", QT_TRANSLATE_NOOP("PlayerMediaTools", "Color Extraction")},
    {"colors", "colorthres-color", "colorthres", QT_TRANSLATE_NOOP("PlayerMediaTools", "Color Threshold")},
    {"colors", "colorthres-saturationthres", "colorthres", QT_TRANSLATE_NOOP("PlayerMediaTools", "Saturation")},
    {"colors", "colorthres-similaritythres", "colorthres", QT_TRANSLATE_NOOP("PlayerMediaTools", "Similarity")},
    {"colors", "posterize-level", "posterize", QT_TRANSLATE_NOOP("PlayerMediaTools", "Posterize")},
    {"colors", "gradient-mode", "gradient", QT_TRANSLATE_NOOP("PlayerMediaTools", "Gradient")},
    {"colors", "gradient-type", "gradient", QT_TRANSLATE_NOOP("PlayerMediaTools", "Color")},
    {"colors", "gradient-cartoon", "gradient", QT_TRANSLATE_NOOP("PlayerMediaTools", "Cartoon")},
    {"colors", "sepia-intensity", "sepia", QT_TRANSLATE_NOOP("PlayerMediaTools", "Sepia Intensity")},
    {"geometry", "transform-type", "transform", QT_TRANSLATE_NOOP("PlayerMediaTools", "Rotate / Flip")},
    {"geometry", "rotate-angle", "rotate", QT_TRANSLATE_NOOP("PlayerMediaTools", "Rotate (degrees)")},
};
const Option *findOption(const QString &key)
{
    for (const auto &o : optionsList) if (key == QLatin1String(o.key)) return &o;
    return nullptr;
}
bool audioOption(const Option &o)
{
    return QByteArray(o.section) == "equalizer" || QByteArray(o.section) == "compressor"
        || QByteArray(o.section) == "spatializer" || QByteArray(o.section) == "stereo_widen"
        || QByteArray(o.section) == "pitch";
}
QVariant readVariable(vlc_object_t *object, const char *key, int type)
{
    if (type == VLC_VAR_STRING) {
        char *text = var_InheritString(object, key);
        const QString result = QString::fromUtf8(text ? text : ""); free(text); return result;
    }
    if (type == VLC_VAR_FLOAT) return var_InheritFloat(object, key);
    if (type == VLC_VAR_BOOL) return var_InheritBool(object, key);
    return qlonglong(var_InheritInteger(object, key));
}
void writeVariable(vlc_object_t *object, const char *key, int type, const QVariant &value)
{
    if (!var_Type(object, key)) var_Create(object, key, type | VLC_VAR_DOINHERIT);
    if (type == VLC_VAR_STRING) var_SetString(object, key, value.toString().toUtf8().constData());
    else if (type == VLC_VAR_FLOAT) var_SetFloat(object, key, value.toFloat());
    else if (type == VLC_VAR_BOOL) var_SetBool(object, key, value.toBool());
    else var_SetInteger(object, key, value.toLongLong());
}
QStringList subtitleFiles(const QDir &dir)
{
    QStringList result;
    for (const auto &f : dir.entryInfoList(QDir::Files | QDir::Readable, QDir::Name))
        if (QStringList{QStringLiteral("srt"), QStringLiteral("vtt"), QStringLiteral("ass"), QStringLiteral("ssa"), QStringLiteral("sub"), QStringLiteral("idx")}.contains(f.suffix().toLower()))
            result.append(f.absoluteFilePath());
    return result;
}
}

PlayerMediaTools::PlayerMediaTools(qt_intf_t *intf, PlayerController *player)
    : QObject(player), m_intf(intf), m_player(player)
{
    char *dir = config_GetUserDir(VLC_CONFIG_DIR);
    m_statePath = QDir(QString::fromUtf8(dir ? dir : "")).filePath(QStringLiteral("redesign-media-tools.json")); free(dir);
    readState();
    m_globalSubtitleDelay = player->getSubtitleDelayMS();
    connect(player->getVideoTracks(), &TrackListModel::countChanged, this, &PlayerMediaTools::changed);
    connect(player->getVideoTracks(), &QAbstractItemModel::dataChanged, this, &PlayerMediaTools::changed);
    connect(player, &PlayerController::inputChanged, this, &PlayerMediaTools::inputChanged);
    connect(player, &PlayerController::playbackEngineChanged, this, [this] { loadTimeline(); emit changed(); });
    connect(player, &PlayerController::subtitleFPSChanged, this, &PlayerMediaTools::loadTimeline);
    connect(player, &PlayerController::statisticsUpdated, this, &PlayerMediaTools::updateStatistics);
    for (auto *tracks : {player->getAudioTracks(), player->getSubtitleTracks()}) {
        connect(tracks, &QAbstractItemModel::dataChanged, this, &PlayerMediaTools::changed);
        connect(tracks, &TrackListModel::countChanged, this, &PlayerMediaTools::changed);
    }
    connect(player, &PlayerController::hasVideoOutputChanged, this, [this] {
        if (!m_player->hasVideoOutput() || m_player->usesMpv()) return;
        const auto values = m_sessionValues;
        for (auto it = values.begin(); it != values.end(); ++it) setValue(it.key(), it.value().toVariant());
        const auto filters = m_sessionFilters;
        for (auto it = filters.begin(); it != filters.end(); ++it) enableFilter(it.key(), it.value());
    });
    connect(player->getAudioTracks(), &TrackListModel::countChanged, this, &PlayerMediaTools::restoreTracks);
    connect(player->getSubtitleTracks(), &TrackListModel::countChanged, this, &PlayerMediaTools::restoreTracks);
    connect(player->getSubtitleTracks(), &QAbstractItemModel::dataChanged, this, &PlayerMediaTools::loadTimeline);
    connect(player->getSubtitleTracks(), &TrackListModel::countChanged, this, &PlayerMediaTools::loadTimeline);
    connect(player->getAudioTracks(), &TrackListModel::selectionRequested, this, [this] { m_manualAudioChoice = true; });
    connect(player->getSubtitleTracks(), &TrackListModel::selectionRequested, this, [this] { m_manualSubtitleChoice = true; });
    m_sleep.setSingleShot(true);
    cancelSleep();
    connect(&m_sleep, &QTimer::timeout, this, [this] {
        m_sleepMinutes = 0;
        m_intf->p_mainPlaylistController->stop();
        m_sleepStatus = tr("Sleep timer expired; playback stopped."); emit changed();
    });
    inputChanged();
}
void PlayerMediaTools::report(const QString &text) { m_status = text; emit changed(); }
QString PlayerMediaTools::languageCode(const QString &language)
{
    const auto value = language.trimmed().toLower();
    const auto *record = vlc_find_iso639(value.toUtf8().constData(), true);
    return record ? QString::fromUtf8(*record->psz_iso639_1 ? record->psz_iso639_1 : record->psz_iso639_2T) : value;
}
void PlayerMediaTools::readState()
{
    QFile f(m_statePath);
    if (!f.exists()) { m_state = {{QStringLiteral("version"), 1}}; return; }
    if (!f.open(QIODevice::ReadOnly) || f.size() > 8 * 1024 * 1024) {
        m_writable = false; report(tr("Saved media settings could not be read; the original file is preserved.")); return;
    }
    QJsonParseError error;
    const auto doc = QJsonDocument::fromJson(f.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject() || doc.object().value(QStringLiteral("version")).toInt() != 1) {
        m_writable = false; report(tr("Saved media settings have an unsupported format; the original file is preserved.")); return;
    }
    m_state = doc.object();
    m_timelineVisible = m_state.value(QStringLiteral("timelineVisible")).toBool();
    m_waveformVisible = m_state.value(QStringLiteral("waveformVisible")).toBool();
    m_statisticsVisible = m_state.value(QStringLiteral("statisticsVisible")).toBool();
}
bool PlayerMediaTools::writeState(const QJsonObject &state)
{
    if (!m_writable) { report(tr("Saved media settings are read-only; preserve or repair the original file first.")); return false; }
    const auto bytes = QJsonDocument(state).toJson(QJsonDocument::Indented);
    if (bytes.size() > 8 * 1024 * 1024) { report(tr("Saved media settings reached their size limit.")); return false; }
    QSaveFile f(m_statePath);
    if (!QDir().mkpath(QFileInfo(m_statePath).absolutePath()) || !f.open(QIODevice::WriteOnly)
        || f.write(bytes) != bytes.size() || !f.commit()) {
        report(tr("Media settings could not be saved; the previous file is preserved.")); return false;
    }
    m_state = state; emit changed(); return true;
}
QString PlayerMediaTools::mediaKey(const QUrl &url) const
{
    if (!url.isLocalFile()) return {};
    const auto f = QFileInfo(url.toLocalFile());
    if (!f.exists() || !f.isFile()) return {};
    QString path = f.canonicalFilePath();
#ifdef _WIN32
    path = path.toCaseFolded();
#endif
    return QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);
}
QJsonObject PlayerMediaTools::identity(const QUrl &url) const
{
    const QFileInfo f(url.toLocalFile());
    QFile file(f.absoluteFilePath());
    if (!file.open(QIODevice::ReadOnly)) return {};
    QCryptographicHash hash(QCryptographicHash::Sha256);
    const bool full = f.size() <= 8 * 1024 * 1024;
    if (full) {
        if (!hash.addData(&file)) return {};
    } else {
        hash.addData(file.read(65536));
        if (!file.seek(std::max<qint64>(0, f.size() - 65536))) return {};
        hash.addData(file.read(65536));
    }
    return {{QStringLiteral("size"), QString::number(f.size())},
            {QStringLiteral("modified"), QString::number(f.lastModified().toMSecsSinceEpoch())},
            {QStringLiteral("fingerprint"), QString::fromLatin1(hash.result().toHex())},
            {QStringLiteral("fingerprintScope"), full ? QStringLiteral("full") : QStringLiteral("first-last-64KiB")}};
}
bool PlayerMediaTools::validAssociation(const QUrl &media, const QJsonObject &a) const
{
    const auto current = identity(media);
    return !mediaKey(media).isEmpty() && !current.isEmpty() && current == a.value(QStringLiteral("mediaIdentity")).toObject()
        && !mediaKey(QUrl(a.value(QStringLiteral("subtitle")).toString())).isEmpty()
        && identity(QUrl(a.value(QStringLiteral("subtitle")).toString())) == a.value(QStringLiteral("subtitleIdentity")).toObject();
}
void PlayerMediaTools::prepareMatches(const QVariantList &media, const QVariantList &subtitles)
{
    m_matches.clear(); QStringList paths;
    for (const auto &v : subtitles) { const QUrl u(v.toString()); if (u.isLocalFile()) paths.append(u.toLocalFile()); }
    for (const auto &v : media) {
        const QUrl url(v.toString());
        if (mediaKey(url).isEmpty()) continue;
        const auto candidates = SubtitleData::match(url.toLocalFile(), paths);
        QVariantList choices;
        for (const auto &p : candidates) choices.append(QUrl::fromLocalFile(p));
        const auto saved = m_state.value(QStringLiteral("associations")).toObject().value(mediaKey(url)).toObject();
        QUrl chosen = candidates.size() == 1 ? QUrl::fromLocalFile(candidates.first()) : QUrl();
        QString state = candidates.isEmpty() ? tr("Unmatched") : candidates.size() > 1 ? tr("Ambiguous — choose a subtitle") : tr("Matched");
        if (!saved.isEmpty()) {
            if (validAssociation(url, saved)) { chosen = QUrl(saved.value(QStringLiteral("subtitle")).toString()); state = tr("Saved association"); }
            else { chosen = QUrl(); state = tr("Saved media or subtitle changed/missing — choose again"); }
        }
        m_matches.append(QVariantMap{{QStringLiteral("media"), url}, {QStringLiteral("title"), QFileInfo(url.toLocalFile()).fileName()},
            {QStringLiteral("choices"), choices}, {QStringLiteral("subtitle"), chosen}, {QStringLiteral("state"), state}});
        if (m_matches.size() >= 2048) { report(tr("Only the first 2048 media files are shown.")); break; }
    }
    emit matchesChanged();
}
void PlayerMediaTools::matchFolder(const QUrl &folder)
{
    if (!folder.isLocalFile()) { report(tr("Choose a local folder.")); return; }
    QDir dir(folder.toLocalFile()); QVariantList media, subs;
    const QStringList extensions{QStringLiteral("mkv"), QStringLiteral("mp4"), QStringLiteral("avi"), QStringLiteral("mov"), QStringLiteral("webm"), QStringLiteral("m4v"), QStringLiteral("ts"), QStringLiteral("m2ts"), QStringLiteral("mpg"), QStringLiteral("mpeg"), QStringLiteral("ogv"), QStringLiteral("wmv")};
    for (const auto &f : dir.entryInfoList(QDir::Files | QDir::Readable, QDir::Name))
        if (extensions.contains(f.suffix().toLower())) media.append(QUrl::fromLocalFile(f.absoluteFilePath()));
    for (const auto &f : subtitleFiles(dir)) subs.append(QUrl::fromLocalFile(f));
    prepareMatches(media, subs);
}
void PlayerMediaTools::matchQueue(const QVariantList &subtitles)
{
    QVariantList media;
    auto *playlist = m_intf->p_playlist;
    vlc_playlist_Lock(playlist);
    for (size_t i = 0, n = vlc_playlist_Count(playlist); i < n && i < 2048; ++i) {
        char *uri = input_item_GetURI(vlc_playlist_item_GetMedia(vlc_playlist_Get(playlist, i)));
        if (uri) media.append(QUrl(QString::fromUtf8(uri)));
        free(uri);
    }
    vlc_playlist_Unlock(playlist);
    prepareMatches(media, subtitles);
}
void PlayerMediaTools::chooseMatch(int row, const QUrl &subtitle)
{
    if (row < 0 || row >= m_matches.size()) return;
    auto item = m_matches[row].toMap();
    item[QStringLiteral("subtitle")] = subtitle;
    item[QStringLiteral("state")] = subtitle.isEmpty() ? tr("Unmatched") : tr("Chosen manually");
    m_matches[row] = item; emit matchesChanged();
}
bool PlayerMediaTools::saveMatches()
{
    auto associations = m_state.value(QStringLiteral("associations")).toObject();
    for (const auto &v : m_matches) {
        const auto row = v.toMap(); const auto media = row.value(QStringLiteral("media")).toUrl();
        const auto subtitle = row.value(QStringLiteral("subtitle")).toUrl();
        if (subtitle.isEmpty()) continue;
        const auto key = mediaKey(media);
        if (key.isEmpty() || mediaKey(subtitle).isEmpty()) { report(tr("A selected file is missing; no associations were saved.")); return false; }
        associations.insert(key, QJsonObject{{QStringLiteral("mediaIdentity"), identity(media)},
            {QStringLiteral("subtitle"), subtitle.toString(QUrl::FullyEncoded)}, {QStringLiteral("subtitleIdentity"), identity(subtitle)}});
    }
    if (associations.size() > 2048) { report(tr("Saved associations reached the 2048-file limit; remove old associations first.")); return false; }
    auto state = m_state; state[QStringLiteral("associations")] = associations;
    if (!writeState(state)) return false;
    const auto current = associations.value(mediaKey(m_player->getUrl())).toObject();
    if (validAssociation(m_player->getUrl(), current) && !addSubtitle(QUrl(current.value(QStringLiteral("subtitle")).toString()))) {
        report(tr("Associations were saved. %1").arg(m_status)); return false;
    }
    report(tr("Subtitle associations saved.")); return true;
}
bool PlayerMediaTools::isCurrentMedia(const QUrl &media) const
{
    if (media != m_player->getUrl()) return false;
    if (m_player->usesMpv()) return m_player->getInput() && !media.isEmpty() && m_player->mpvPlayback()->isMediaLoaded();
    vlc_player_locker lock(m_player->getPlayer());
    const auto input = vlc_player_GetCurrentMedia(m_player->getPlayer());
    char *raw = input ? input_item_GetURI(input) : nullptr;
    const QUrl actual(QString::fromUtf8(raw ? raw : "")); free(raw);
    return !actual.isEmpty() && actual == media;
}
bool PlayerMediaTools::addSubtitle(const QUrl &subtitle)
{
    if (!isCurrentMedia(m_player->getUrl())) { report(tr("The playing input changed; choose the subtitle again for the intended media.")); return false; }
    if (!subtitle.isLocalFile() || mediaKey(subtitle).isEmpty()) { report(tr("The subtitle file is missing or unavailable.")); return false; }
    if (!m_player->associateSubtitleFile(subtitle.toString(QUrl::FullyEncoded))) { report(tr("VLC could not add this subtitle to the current input.")); return false; }
    m_subtitle = subtitle; m_preferAssociation = true; m_manualSubtitleChoice = false;
    // Pinned input.c InputSourceNew hashes the exact associated URL; es_out.c
    // prefixes its stable SPU ids with that source hash. Match that identity,
    // never an arbitrary newly selected track or an embedded track's ordinal.
    m_expectedSubtitlePrefix = TrackListModel::associatedSourcePrefix(subtitle.toString(QUrl::FullyEncoded).toUtf8());
    m_awaitingSubtitleTrack = true;
    loadTimeline();
    if (!m_subtitleLoaded) report(tr("Subtitle requested. VLC has not selected this file's track yet."));
    return true;
}
void PlayerMediaTools::forgetAssociation(const QUrl &media)
{
    auto state = m_state, a = state.value(QStringLiteral("associations")).toObject();
    QString key = mediaKey(media);
    if (key.isEmpty() && media.isLocalFile()) {
        QString path = QDir::cleanPath(QFileInfo(media.toLocalFile()).absoluteFilePath());
#ifdef _WIN32
        path = path.toCaseFolded();
#endif
        key = QUrl::fromLocalFile(path).toString(QUrl::FullyEncoded);
    }
    a.remove(key); state[QStringLiteral("associations")] = a;
    if (writeState(state)) report(tr("Saved association removed. The currently selected subtitle is unchanged."));
}
QVariantList PlayerMediaTools::associations() const
{
    QVariantList rows; const auto saved = m_state.value(QStringLiteral("associations")).toObject();
    for (auto it = saved.begin(); it != saved.end(); ++it)
        rows.append(QVariantMap{{QStringLiteral("media"), QUrl(it.key())},
            {QStringLiteral("subtitle"), QUrl(it.value().toObject().value(QStringLiteral("subtitle")).toString())}});
    return rows;
}
bool PlayerMediaTools::associateAndSave(const QUrl &subtitle)
{
    const auto media = m_player->getUrl();
    if (!isCurrentMedia(media)) { report(tr("The playing input changed; no association was saved.")); return false; }
    if (mediaKey(media).isEmpty()) { addSubtitle(subtitle); return false; }
    prepareMatches({media}, {subtitle}); chooseMatch(0, subtitle); return saveMatches();
}
void PlayerMediaTools::browseSubtitle(int row)
{
    const auto media = m_player->getUrl();
    const auto file = QFileDialog::getOpenFileName(nullptr, tr("Add subtitle file"),
        media.isLocalFile() ? QFileInfo(media.toLocalFile()).absolutePath() : QString(),
        tr("Subtitles (*.srt *.vtt *.ass *.ssa *.sub *.idx);;All files (*)"), nullptr, QFileDialog::DontUseNativeDialog);
    if (file.isEmpty()) return;
    if (row >= 0) chooseMatch(row, QUrl::fromLocalFile(file));
    else if (media == m_player->getUrl()) associateAndSave(QUrl::fromLocalFile(file));
    else report(tr("The playing input changed while choosing the subtitle. Choose again for the intended media."));
}
void PlayerMediaTools::browseSubtitleFolder()
{
    const auto folder = QFileDialog::getExistingDirectory(nullptr, tr("Add subtitles to folder"),
        m_player->getUrl().isLocalFile() ? QFileInfo(m_player->getUrl().toLocalFile()).absolutePath() : QString(),
        QFileDialog::ShowDirsOnly | QFileDialog::DontUseNativeDialog);
    if (!folder.isEmpty()) matchFolder(QUrl::fromLocalFile(folder));
}
void PlayerMediaTools::browseQueueSubtitles()
{
    const auto files = QFileDialog::getOpenFileNames(nullptr, tr("Add subtitles to current queue"), QString(),
        tr("Subtitles (*.srt *.vtt *.ass *.ssa *.sub *.idx);;All files (*)"), nullptr, QFileDialog::DontUseNativeDialog);
    if (files.isEmpty()) return;
    QVariantList urls; for (const auto &file : files) urls.append(QUrl::fromLocalFile(file));
    matchQueue(urls);
}
QUrl PlayerMediaTools::browsePresetFolder()
{
    const auto folder = QFileDialog::getExistingDirectory(nullptr, tr("Show folder for this preset"), QString(),
        QFileDialog::ShowDirsOnly | QFileDialog::DontUseNativeDialog);
    return folder.isEmpty() ? QUrl() : QUrl::fromLocalFile(folder);
}
void PlayerMediaTools::loadTimeline()
{
    m_cues.clear();
    bool selected = false, external = false;
    if (m_player->usesMpv()) {
        for (const auto &value : m_player->mpvPlayback()->value(QStringLiteral("track-list")).toList()) {
            const auto track = value.toMap();
            if (track.value(QStringLiteral("type")).toString() != QStringLiteral("sub") || !track.value(QStringLiteral("selected")).toBool()) continue;
            selected = true;
            const auto file = track.value(QStringLiteral("external-filename")).toString();
            const QUrl url = QUrl::fromLocalFile(file);
            external |= !m_subtitle.isEmpty() && (url == m_subtitle || QUrl(file) == m_subtitle);
        }
    } else {
        vlc_player_locker lock(m_player->getPlayer());
        const auto *track = vlc_player_GetSelectedTrack(m_player->getPlayer(), SPU_ES);
        selected = track != nullptr;
        external = track && !m_expectedSubtitlePrefix.isEmpty() && QByteArray(vlc_es_id_GetStrId(track->es_id)).startsWith(m_expectedSubtitlePrefix);
    }
    m_subtitleLoaded = external;
    if (external && m_awaitingSubtitleTrack) { m_awaitingSubtitleTrack = false; report(tr("Subtitle track loaded and selected.")); }
    if (!selected) m_timelineStatus = tr("No subtitle track selected.");
    else if (!external) m_timelineStatus = tr("Cue timeline is available for added SRT, WebVTT, ASS and SSA files. Embedded and image subtitles keep playing normally.");
    else {
        QFile file(m_subtitle.toLocalFile()); const auto ext = QFileInfo(file).suffix().toLower();
        if (!QStringList{QStringLiteral("srt"), QStringLiteral("vtt"), QStringLiteral("ass"), QStringLiteral("ssa")}.contains(ext))
            m_timelineStatus = tr("This subtitle type has no text cue timeline; playback is unchanged.");
        else if (!file.open(QIODevice::ReadOnly) || file.size() > 8 * 1024 * 1024)
            m_timelineStatus = tr("Cue file is missing, unreadable or exceeds 8 MiB; subtitle playback is unchanged.");
        else {
            const auto bytes = file.readAll();
            const auto encoding = QStringConverter::encodingForData(bytes).value_or(QStringConverter::Utf8);
            QStringDecoder decoder(encoding); const QString text = decoder.decode(bytes);
            for (const auto &cue : decoder.hasError() ? QVector<SubtitleData::Cue>() : SubtitleData::cues(text, ext))
                m_cues.append(QVariantMap{{QStringLiteral("start"), cue.start}, {QStringLiteral("end"), cue.end}, {QStringLiteral("text"), cue.text}});
            m_timelineStatus = m_cues.isEmpty() ? tr("No supported text cues found; subtitle playback is unchanged.") : (m_cues.size() >= 100000 ? tr("First 100000 source cues; the cue timeline is capped. Subtitle playback is unchanged.") : tr("%1 source cues; positions follow subtitle FPS and track delay. Duration filters can extend the displayed cue ends.").arg(m_cues.size()));
        }
    }
    emit cuesChanged();
}
QVariant PlayerMediaTools::value(const QString &key) const
{
    const auto *o = findOption(key); if (!o) return {};
    const bool crop = QByteArray(o->section) == "crop";
    const int type = crop ? VLC_VAR_INTEGER : config_GetType(o->key); if (!type) return {};
    if (crop) { auto out = m_player->getVout(); return out && var_Type(out.get(), o->key) ? QVariant(qlonglong(var_GetInteger(out.get(), o->key))) : QVariant(); }
    if (audioOption(*o)) { auto aout = m_player->getAout(); if (aout) return readVariable(VLC_OBJECT(aout.get()), o->key, type); }
    else { auto vout = m_player->getVout(); if (vout) return readVariable(VLC_OBJECT(vout.get()), o->key, type); }
    return readVariable(VLC_OBJECT(m_intf), o->key, type);
}
QVariantList PlayerMediaTools::options(const QString &section) const
{
    QVariantList result;
    for (const auto &o : optionsList) {
        if (section != QLatin1String(o.section)) continue;
        const QString key = QString::fromUtf8(o.key);
        const bool crop = QByteArray(o.section) == "crop";
        const auto *c = config_FindConfig(o.key); const int type = crop ? VLC_VAR_INTEGER : config_GetType(o.key);
        QVariantMap row{{QStringLiteral("key"), QString::fromUtf8(o.key)}, {QStringLiteral("module"), QString::fromUtf8(o.module)},
            {QStringLiteral("label"), tr(o.label)}, {QStringLiteral("available"), !m_player->usesMpv() && c != nullptr && type != 0}, {QStringLiteral("value"), value(QString::fromUtf8(o.key))},
            {QStringLiteral("choices"), QVariantList{}}, {QStringLiteral("color"), false}, {QStringLiteral("step"), 1}};
        row[QStringLiteral("kind")] = type == VLC_VAR_BOOL ? QStringLiteral("bool") : type == VLC_VAR_STRING ? QStringLiteral("string") : QStringLiteral("number");
        if (crop) {
            auto out = m_player->getVout();
            const auto dimensions = videoInfo();
            const bool vertical = key == QLatin1String("crop-top") || key == QLatin1String("crop-bottom");
            const int size = dimensions.value(vertical ? QStringLiteral("height") : QStringLiteral("width")).toInt();
            const char *opposite = key == QLatin1String("crop-top") ? "crop-bottom" : key == QLatin1String("crop-bottom") ? "crop-top" : key == QLatin1String("crop-left") ? "crop-right" : "crop-left";
            const qlonglong border = out ? var_GetInteger(out.get(), opposite) : 0;
            row[QStringLiteral("available")] = out && size > 0 && var_Type(out.get(), o.key);
            row[QStringLiteral("minimum")] = 0;
            row[QStringLiteral("maximum")] = std::max<qlonglong>(0, qlonglong(size) - 1 - border);
            row[QStringLiteral("step")] = 1;
        }
        if (c) {
            if (type == VLC_VAR_FLOAT || type == VLC_VAR_INTEGER) {
                row[QStringLiteral("minimum")] = type == VLC_VAR_FLOAT ? c->min.f : double(c->min.i);
                row[QStringLiteral("maximum")] = type == VLC_VAR_FLOAT ? c->max.f : double(c->max.i);
            }
            row[QStringLiteral("color")] = QByteArray(o.key).endsWith("-color") || QByteArray(o.key) == "extract-component";
            row[QStringLiteral("step")] = type == VLC_VAR_FLOAT ? 0.01 : 1;
            QVariantList choices;
            for (int i = 0; i < c->list_count; ++i) {
                const QVariant v = type == VLC_VAR_STRING ? QVariant(QString::fromUtf8(c->list.psz[i])) : QVariant(c->list.i[i]);
                choices.append(QVariantMap{{QStringLiteral("text"), QString::fromUtf8(c->list_text && c->list_text[i] ? c->list_text[i] : "")}, {QStringLiteral("value"), v}});
            }
            row[QStringLiteral("choices")] = choices;
        }
        result.append(row);
    }
    return result;
}
bool PlayerMediaTools::setValue(const QString &key, const QVariant &v)
{
    if (m_player->usesMpv()) { report(tr("VLC appearance and filter tools require VLC playback. Switch engines in Playback settings.")); return false; }
    const auto *o = findOption(key); if (!o) return false;
    if (QByteArray(o->section) == "crop") {
        QVariantMap metadata;
        for (const auto &row : options(QStringLiteral("crop")))
            if (row.toMap().value(QStringLiteral("key")).toString() == key) { metadata = row.toMap(); break; }
        auto out = m_player->getVout();
        if (!out || !metadata.value(QStringLiteral("available")).toBool()) { report(tr("No active video output for pixel cropping.")); return false; }
        bool ok; const qlonglong border = v.toLongLong(&ok);
        if (!ok || border < 0 || border > metadata.value(QStringLiteral("maximum")).toLongLong()) { report(tr("Crop borders must leave at least one source pixel.")); return false; }
        if (var_SetInteger(out.get(), o->key, border) != VLC_SUCCESS) { report(tr("VLC could not apply this crop border.")); return false; }
        m_sessionValues[key] = border; emit changed(); return true;
    }
    const auto *c = config_FindConfig(o->key); const int type = config_GetType(o->key);
    if (!c || !type) { report(tr("This option is unavailable in this VLC build.")); return false; }
    if (type == VLC_VAR_FLOAT || type == VLC_VAR_INTEGER) {
        bool ok; const double number = v.toDouble(&ok);
        const double low = type == VLC_VAR_FLOAT ? c->min.f : double(c->min.i), high = type == VLC_VAR_FLOAT ? c->max.f : double(c->max.i);
        if (!ok || !std::isfinite(number) || (high > low && (number < low || number > high))) { report(tr("The value is outside VLC's supported range.")); return false; }
    }
    if (type == VLC_VAR_INTEGER && (key.endsWith(QLatin1String("-color")) || key == QLatin1String("extract-component"))
        && (v.toLongLong() < 0 || v.toLongLong() > 0xffffff)) { report(tr("Enter an RGB color between #000000 and #FFFFFF.")); return false; }
    if (key == QLatin1String("equalizer-bands")) {
        const auto bands = v.toString().split(QRegularExpression(QStringLiteral("\\s+")), Qt::SkipEmptyParts);
        bool valid = bands.size() == 10 || v.toString().trimmed().isEmpty();
        for (const auto &band : bands) { bool ok; const double gain = band.toDouble(&ok); valid &= ok && std::isfinite(gain) && gain >= -20 && gain <= 20; }
        if (!valid) { report(tr("Equalizer requires ten finite gains between -20 and +20 dB.")); return false; }
    }
    m_sessionValues[key] = QJsonValue::fromVariant(v);
    if (audioOption(*o)) {
        auto aout = m_player->getAout();
        if (!aout) { report(tr("No active audio output.")); return false; }
        if (key == QLatin1String("equalizer-preset")) {
            const eqz_preset_t *preset = nullptr;
            for (const auto &candidate : eqz_preset_10b)
                if (v.toString() == QString::fromUtf8(candidate.psz_name)) { preset = &candidate; break; }
            if (!preset) { report(tr("This equalizer preset is unavailable.")); return false; }
            // Use the same preset data as VLC's existing equalizer dialog.
            // Apply bands/preamp even while disabled, before a queued restart.
            QStringList bands;
            for (int i = 0; i < preset->i_band; ++i) bands.append(QString::number(preset->f_amp[i], 'f', 7));
            writeVariable(VLC_OBJECT(aout.get()), o->key, type, v);
            writeVariable(VLC_OBJECT(aout.get()), "equalizer-bands", VLC_VAR_STRING, bands.join(QLatin1Char(' ')));
            writeVariable(VLC_OBJECT(aout.get()), "equalizer-preamp", VLC_VAR_FLOAT, preset->f_preamp);
            m_sessionValues[QStringLiteral("equalizer-bands")] = bands.join(QLatin1Char(' '));
            m_sessionValues[QStringLiteral("equalizer-preamp")] = preset->f_preamp;
        } else writeVariable(VLC_OBJECT(aout.get()), o->key, type, v);
    } else {
        auto vout = m_player->getVout();
        if (!vout) { emit changed(); return true; }
        writeVariable(VLC_OBJECT(vout.get()), o->key, type, v);
    }
    emit changed(); return true;
}
bool PlayerMediaTools::filterEnabled(const QString &module) const
{
    if (m_player->usesMpv()) return false;
    const QByteArray bytes = module.toUtf8(); module_t *mod = module_find(bytes.constData());
    if (!mod) return false;
    const char *chain = module_provides(mod, "audio filter") ? "audio-filter" : module_provides(mod, "sub filter") ? "sub-filter" : "video-filter";
    char *raw = nullptr;
    if (QByteArray(chain) == "audio-filter") { auto out = m_player->getAout(); if (out) raw = var_GetString(out.get(), chain); }
    else { auto out = m_player->getVout(); if (out) raw = var_GetString(out.get(), chain); }
    const QString text = QString::fromUtf8(raw ? raw : ""); free(raw);
    return text.split(QLatin1Char(':'), Qt::SkipEmptyParts).contains(module);
}
void PlayerMediaTools::enableFilter(const QString &module, bool enabled)
{
    if (m_player->usesMpv()) { report(tr("This filter requires VLC playback. Switch engines in Playback settings.")); return; }
    const QByteArray bytes = module.toUtf8(); module_t *mod = module_find(bytes.constData());
    if (!mod) { report(tr("This filter is unavailable in this VLC build.")); return; }
    m_sessionFilters[module] = enabled;
    if (module_provides(mod, "audio filter")) vlc_player_aout_EnableFilter(m_player->getPlayer(), bytes.constData(), enabled);
    else {
        const char *chain = module_provides(mod, "sub filter") ? "sub-filter" : "video-filter";
        auto out = m_player->getVout(); if (!out) { report(tr("No active video output.")); return; }
        char *raw = var_GetString(out.get(), chain); QStringList list = QString::fromUtf8(raw ? raw : "").split(QLatin1Char(':'), Qt::SkipEmptyParts); free(raw);
        if (enabled && !list.contains(module)) list.append(module);
        else if (!enabled) list.removeAll(module);
        var_SetString(out.get(), chain, list.join(QLatin1Char(':')).toUtf8().constData());
    }
    emit changed();
}
void PlayerMediaTools::resetSection(const QString &section)
{
    if (m_player->usesMpv()) { report(tr("Resetting VLC filters and appearance requires VLC playback.")); return; }
    if (section == QLatin1String("crop")) {
        if (!m_player->getVout()) { report(tr("No active video output for pixel cropping.")); return; }
        for (const auto &o : optionsList) if (section == QLatin1String(o.section)) setValue(QString::fromUtf8(o.key), 0);
        report(tr("Crop borders reset.")); return;
    }
    QSet<QString> modules;
    for (const auto &o : optionsList) if (section == QLatin1String(o.section)) {
        const auto *c = config_FindConfig(o.key); if (!c) continue;
        const int type = config_GetType(o.key);
        const QVariant original = type == VLC_VAR_STRING ? QVariant(QString::fromUtf8(c->orig.psz ? c->orig.psz : ""))
            : type == VLC_VAR_FLOAT ? QVariant(c->orig.f) : QVariant(qlonglong(c->orig.i));
        setValue(QString::fromUtf8(o.key), original);
        if (*o.module) modules.insert(QString::fromUtf8(o.module));
    }
    for (const auto &module : modules) enableFilter(module, false);
    if (section == QLatin1String("subtitle")) { resetSection(QStringLiteral("subtitleTiming")); m_player->setSubtitleDelayMS(0); m_player->setSubtitleFPS(0); }
    report(tr("Section reset to VLC defaults."));
}
QStringList PlayerMediaTools::presets() const { return m_state.value(QStringLiteral("presets")).toObject().keys(); }
void PlayerMediaTools::savePreset(const QString &name, const QUrl &folder)
{
    const auto clean = name.trimmed(); const auto dir = QFileInfo(folder.toLocalFile());
    if (clean.isEmpty() || clean.size() > 80 || !folder.isLocalFile() || !dir.isDir()) { report(tr("Enter a preset name and choose its existing show folder.")); return; }
    auto presets = m_state.value(QStringLiteral("presets")).toObject();
    if (!presets.contains(clean) && presets.size() >= 64) { report(tr("Remove an old preset before adding another; the limit is 64.")); return; }
    // Capture the real current selection, including language and ordinal. When
    // the next episode orders tracks differently, the language wins; an ordinal
    // is used only within that language (or when no language was supplied).
    if (m_player->usesMpv()) {
        const auto tracks = m_player->mpvPlayback()->value(QStringLiteral("track-list")).toList();
        for (const bool sub : {false, true}) {
            QString language; int index = sub ? -2 : -1, ordinal = 0;
            for (const auto &entry : tracks) {
                const auto track = entry.toMap();
                if (track.value(QStringLiteral("type")).toString() != (sub ? QStringLiteral("sub") : QStringLiteral("audio"))) continue;
                if (track.value(QStringLiteral("selected")).toBool()) {
                    index = ordinal; language = languageCode(track.value(QStringLiteral("lang")).toString()); break;
                }
                ++ordinal;
            }
            (sub ? m_preferredSubtitle : m_preferredAudio) = language;
            (sub ? m_preferredSubtitleIndex : m_preferredAudioIndex) = index;
        }
    } else {
        vlc_player_locker lock(m_player->getPlayer());
        for (const auto cat : {AUDIO_ES, SPU_ES}) {
            const auto *selected = vlc_player_GetSelectedTrack(m_player->getPlayer(), cat);
            QString language; int index = -1;
            if (selected) {
                language = languageCode(QString::fromUtf8(selected->fmt.psz_language ? selected->fmt.psz_language : ""));
                for (size_t i = 0; i < vlc_player_GetTrackCount(m_player->getPlayer(), cat); ++i)
                    if (vlc_player_GetTrackAt(m_player->getPlayer(), cat, i)->es_id == selected->es_id) { index = int(i); break; }
            } else if (cat == SPU_ES) index = -2; // Explicitly disabled subtitles.
            (cat == SPU_ES ? m_preferredSubtitle : m_preferredAudio) = language;
            (cat == SPU_ES ? m_preferredSubtitleIndex : m_preferredAudioIndex) = index;
        }
    }
    QJsonObject values;
    for (const auto &o : optionsList) if (QByteArray(o.section) == "subtitle" || QByteArray(o.section) == "subtitleTiming") values[QString::fromUtf8(o.key)] = QJsonValue::fromVariant(value(QString::fromUtf8(o.key)));
    presets[clean] = QJsonObject{{QStringLiteral("folder"), QUrl::fromLocalFile(dir.canonicalFilePath()).toString(QUrl::FullyEncoded)},
        {QStringLiteral("values"), values}, {QStringLiteral("delay"), m_player->getSubtitleDelayMS()},
        {QStringLiteral("fps"), m_player->getSubtitleFPS()}, {QStringLiteral("durationEnabled"), filterEnabled(QStringLiteral("subsdelay"))},
        {QStringLiteral("audioLanguage"), m_preferredAudio}, {QStringLiteral("subtitleLanguage"), m_preferredSubtitle},
        {QStringLiteral("audioIndex"), m_preferredAudioIndex}, {QStringLiteral("subtitleIndex"), m_preferredSubtitleIndex}};
    auto state = m_state; state[QStringLiteral("presets")] = presets;
    if (writeState(state)) { m_activePreset = clean; report(tr("Preset saved. The most specific show folder applies to subsequent inputs; manual changes apply to this input only.")); }
}
void PlayerMediaTools::applyPreset(const QString &name)
{
    const auto preset = m_state.value(QStringLiteral("presets")).toObject().value(name).toObject();
    if (preset.isEmpty()) return;
    m_manualAudioChoice = m_manualSubtitleChoice = false;
    const auto values = preset.value(QStringLiteral("values")).toObject();
    if (!m_player->usesMpv())
        for (auto it = values.begin(); it != values.end(); ++it) setValue(it.key(), it.value().toVariant());
    m_player->setSubtitleDelayMS(preset.value(QStringLiteral("delay")).toInt());
    if (!m_player->usesMpv()) {
        m_player->setSubtitleFPS(float(preset.value(QStringLiteral("fps")).toDouble()));
        enableFilter(QStringLiteral("subsdelay"), preset.value(QStringLiteral("durationEnabled")).toBool());
    }
    m_preferredAudio = languageCode(preset.value(QStringLiteral("audioLanguage")).toString()); m_preferredSubtitle = languageCode(preset.value(QStringLiteral("subtitleLanguage")).toString());
    m_preferredAudioIndex = preset.value(QStringLiteral("audioIndex")).toInt(-1); m_preferredSubtitleIndex = preset.value(QStringLiteral("subtitleIndex")).toInt(-1);
    m_activePreset = name; restoreTracks(); emit changed();
    if (m_player->usesMpv()) report(tr("Track and delay preferences applied. This preset's VLC appearance and filters require VLC playback."));
}
void PlayerMediaTools::removePreset(const QString &name)
{
    auto state = m_state, p = state.value(QStringLiteral("presets")).toObject(); p.remove(name); state[QStringLiteral("presets")] = p;
    if (writeState(state) && m_activePreset == name) m_activePreset.clear();
    emit changed();
}
void PlayerMediaTools::setPreferredTrack(bool sub, const QString &language, int index)
{
    (sub ? m_manualSubtitleChoice : m_manualAudioChoice) = false;
    if (sub) m_preferAssociation = false;
    (sub ? m_preferredSubtitle : m_preferredAudio) = languageCode(language);
    (sub ? m_preferredSubtitleIndex : m_preferredAudioIndex) = index;
    restoreTracks(); emit changed();
}
QVariantMap PlayerMediaTools::preferredTrack(bool sub) const
{
    return {{QStringLiteral("language"), sub ? m_preferredSubtitle : m_preferredAudio}, {QStringLiteral("index"), sub ? m_preferredSubtitleIndex : m_preferredAudioIndex}};
}
void PlayerMediaTools::restoreTracks()
{
    // Old Qt track-list notifications can run after the core changed inputs.
    // Never apply the previous input's preset to that newer core media.
    if (m_restoringTracks || !isCurrentMedia(m_player->getUrl())) return;
    m_restoringTracks = true;
    if (m_player->usesMpv()) {
        auto *mpv = m_player->mpvPlayback();
        const auto tracks = mpv->value(QStringLiteral("track-list")).toList();
        for (const bool sub : {false, true}) {
            if (sub ? m_manualSubtitleChoice : m_manualAudioChoice) continue;
            if (sub && m_preferAssociation) continue; // sub-add already selects the exact requested file.
            const auto language = sub ? m_preferredSubtitle : m_preferredAudio;
            const int preferred = sub ? m_preferredSubtitleIndex : m_preferredAudioIndex;
            const QString property = sub ? QStringLiteral("sid") : QStringLiteral("aid");
            if (sub && preferred == -2) { mpv->set(property, QStringLiteral("no")); continue; }
            int ordinal = 0; QVariantMap chosen;
            for (const auto &entry : tracks) {
                const auto track = entry.toMap();
                if (track.value(QStringLiteral("type")).toString() != (sub ? QStringLiteral("sub") : QStringLiteral("audio"))) continue;
                const bool matches = language.isEmpty() || languageCode(track.value(QStringLiteral("lang")).toString()) == language;
                if (matches && ((!language.isEmpty() && chosen.isEmpty()) || ordinal == preferred)) chosen = track;
                if (matches && ordinal == preferred) break;
                ++ordinal;
            }
            if (!chosen.isEmpty() && !chosen.value(QStringLiteral("selected")).toBool()) mpv->set(property, chosen.value(QStringLiteral("id")).toString());
        }
        m_restoringTracks = false;
        return;
    }
    vlc_player_locker lock(m_player->getPlayer());
    for (const auto cat : {AUDIO_ES, SPU_ES}) {
        if (cat == SPU_ES ? m_manualSubtitleChoice : m_manualAudioChoice) continue;
        if (cat == SPU_ES && m_preferAssociation && !m_expectedSubtitlePrefix.isEmpty()) {
            for (size_t i = 0; i < vlc_player_GetTrackCount(m_player->getPlayer(), cat); ++i) {
                const auto *track = vlc_player_GetTrackAt(m_player->getPlayer(), cat, i);
                if (QByteArray(vlc_es_id_GetStrId(track->es_id)).startsWith(m_expectedSubtitlePrefix)) {
                    if (!track->selected) vlc_player_SelectEsId(m_player->getPlayer(), track->es_id, VLC_PLAYER_SELECT_EXCLUSIVE);
                    break;
                }
            }
            continue;
        }
        const auto language = cat == SPU_ES ? m_preferredSubtitle : m_preferredAudio;
        const int index = cat == SPU_ES ? m_preferredSubtitleIndex : m_preferredAudioIndex;
        const size_t count = vlc_player_GetTrackCount(m_player->getPlayer(), cat);
        if (index == -2 && cat == SPU_ES) { vlc_player_UnselectTrackCategory(m_player->getPlayer(), cat); continue; }
        const vlc_player_track *chosen = nullptr;
        for (size_t i = 0; i < count; ++i) {
            const auto *track = vlc_player_GetTrackAt(m_player->getPlayer(), cat, i);
            if (!language.isEmpty() && languageCode(QString::fromUtf8(track->fmt.psz_language ? track->fmt.psz_language : "")) == language) {
                if (!chosen || int(i) == index) chosen = track;
                if (int(i) == index) break;
            }
            if (language.isEmpty() && int(i) == index) chosen = track;
        }
        if (chosen && !chosen->selected) vlc_player_SelectEsId(m_player->getPlayer(), chosen->es_id, VLC_PLAYER_SELECT_EXCLUSIVE);
    }
    m_restoringTracks = false;
}
void PlayerMediaTools::inputChanged()
{
    if (m_writable) m_status.clear(); // Transient results belong to the old input; preserve store-recovery errors.
    m_statisticsText = m_player->usesMpv() ? tr("VLC playback statistics require the VLC engine.") : tr("Waiting for playback statistics…"); emit statisticsChanged();
    m_subtitle = QUrl(); m_expectedSubtitlePrefix.clear(); m_awaitingSubtitleTrack = false; m_subtitleLoaded = false;
    m_activePreset.clear(); m_cues.clear(); m_sessionValues = {}; m_sessionFilters.clear();
    m_manualAudioChoice = m_manualSubtitleChoice = m_preferAssociation = false;
    // The configured filter chains are the baseline for each new input. In-flight
    // preset restoration is replayed only on the actual output-ready transition.
    for (const auto &o : optionsList) {
        if (!*o.module || audioOption(o)) continue;
        auto *module = module_find(o.module); if (!module) continue;
        const char *key = module_provides(module, "sub filter") ? "sub-filter" : "video-filter";
        char *raw = config_GetPsz(key);
        m_sessionFilters[QString::fromUtf8(o.module)] = QString::fromUtf8(raw ? raw : "").split(QLatin1Char(':'), Qt::SkipEmptyParts).contains(QString::fromUtf8(o.module));
        free(raw);
    }
    char *videoFilters = config_GetPsz("video-filter");
    m_sessionFilters[QStringLiteral("invert")] = QString::fromUtf8(videoFilters ? videoFilters : "").split(QLatin1Char(':'), Qt::SkipEmptyParts).contains(QStringLiteral("invert"));
    free(videoFilters);
    m_preferredAudio.clear(); m_preferredSubtitle.clear(); m_preferredAudioIndex = m_preferredSubtitleIndex = -1;
    // Restore inherited global appearance before applying this show's preset.
    // Session edits never write vlcrc and cannot leak into an unrelated show.
    for (const auto &o : optionsList) if ((QByteArray(o.section) == "subtitle" || QByteArray(o.section) == "subtitleTiming") && config_FindConfig(o.key)) {
        const int type = config_GetType(o.key); QVariant global;
        if (type == VLC_VAR_STRING) { char *s = config_GetPsz(o.key); global = QString::fromUtf8(s ? s : ""); free(s); }
        else if (type == VLC_VAR_FLOAT) global = config_GetFloat(o.key);
        else global = qlonglong(config_GetInt(o.key));
        m_sessionValues[QString::fromUtf8(o.key)] = QJsonValue::fromVariant(global);
    }
    m_player->setSubtitleDelayMS(m_globalSubtitleDelay);
    if (!m_player->usesMpv()) m_player->setSubtitleFPS(float(config_GetFloat("sub-fps")));
    const auto media = m_player->getUrl();
    if (media.isLocalFile()) {
        const auto path = QFileInfo(media.toLocalFile()).canonicalFilePath();
        QString name; qsizetype longest = -1; const auto presets = m_state.value(QStringLiteral("presets")).toObject();
        for (auto it = presets.begin(); it != presets.end(); ++it) {
            auto folder = QUrl(it.value().toObject().value(QStringLiteral("folder")).toString()).toLocalFile();
            if (!QFileInfo(folder).isDir()) continue;
            folder = QDir::cleanPath(folder) + QLatin1Char('/');
            if (path.startsWith(folder,
#ifdef _WIN32
                Qt::CaseInsensitive
#else
                Qt::CaseSensitive
#endif
                ) && folder.size() > longest) { name = it.key(); longest = folder.size(); }
        }
        if (!name.isEmpty()) applyPreset(name);
        const auto a = m_state.value(QStringLiteral("associations")).toObject().value(mediaKey(media)).toObject();
        if (!a.isEmpty()) {
            if (validAssociation(media, a)) addSubtitle(QUrl(a.value(QStringLiteral("subtitle")).toString()));
            else report(tr("The saved media or subtitle changed/missing; select it again to confirm the association."));
        }
    }
    loadTimeline(); emit changed();
}
void PlayerMediaTools::setTimelineVisible(bool enabled)
{
    auto state = m_state; state[QStringLiteral("timelineVisible")] = enabled;
    if (writeState(state)) { m_timelineVisible = enabled; emit changed(); emit analysisTogglesChanged(); }
}
void PlayerMediaTools::setWaveformVisible(bool enabled)
{
    auto state = m_state; state[QStringLiteral("waveformVisible")] = enabled;
    if (writeState(state)) { m_waveformVisible = enabled; emit changed(); emit analysisTogglesChanged(); }
}
void PlayerMediaTools::updateStatistics(const input_stats_t &stats)
{
    if (!m_statisticsVisible) return;
    m_statisticsText = tr("Read: %1 MiB\nDecoded video: %2 frames\nDisplayed: %3 · Lost: %4\nDecoded audio: %5 blocks\nPlayed audio: %6 · Lost: %7")
        .arg(double(stats.i_read_bytes) / (1024 * 1024), 0, 'f', 1)
        .arg(stats.i_decoded_video).arg(stats.i_displayed_pictures).arg(stats.i_lost_pictures)
        .arg(stats.i_decoded_audio).arg(stats.i_played_abuffers).arg(stats.i_lost_abuffers);
    emit statisticsChanged();
}
void PlayerMediaTools::setStatisticsVisible(bool enabled)
{
    auto state = m_state; state[QStringLiteral("statisticsVisible")] = enabled;
    if (!writeState(state)) return;
    m_statisticsVisible = enabled;
    if (enabled) { vlc_player_locker lock(m_player->getPlayer()); if (const auto stats = vlc_player_GetStatistics(m_player->getPlayer())) updateStatistics(*stats); }
    emit changed();
}
void PlayerMediaTools::armSleep(int minutes)
{
    if (minutes <= 0 || minutes > 1440) { cancelSleep(); return; }
    m_sleepMinutes = minutes; m_sleep.start(minutes * 60000);
    m_sleepStatus = tr("Timer set for %1 minutes for this VLC session. Playback stops on expiry. Cancel to keep playing; restarting VLC clears the timer.").arg(minutes); emit changed();
}
void PlayerMediaTools::cancelSleep()
{
    m_sleep.stop(); m_sleepMinutes = 0; m_sleepStatus = tr("Sleep timer off. It is not restored after restarting VLC."); emit changed();
}
bool PlayerMediaTools::subtitleFPSSupported() const
{
    if (m_player->usesMpv()) return false;
    if (!m_subtitleLoaded) return false;
    vlc_player_locker lock(m_player->getPlayer());
    const auto *track = vlc_player_GetSelectedTrack(m_player->getPlayer(), SPU_ES);
    // input.c applies its FPS rate only to subtitle.c's rate-controllable
    // associated demux. Native WebVTT and embedded/image tracks keep PTS.
    return track && (track->fmt.i_codec == VLC_CODEC_SUBT || track->fmt.i_codec == VLC_CODEC_SSA);
}
double PlayerMediaTools::subtitleTimeScale() const
{
    if (!subtitleFPSSupported()) return 1.;
    vlc_player_locker lock(m_player->getPlayer());
    const auto *track = vlc_player_GetSelectedTrack(m_player->getPlayer(), VIDEO_ES);
    const double fps = m_player->getSubtitleFPS();
    if (!track || fps <= 1 || track->fmt.video.i_frame_rate_base == 0) return 1.;
    const double original = double(track->fmt.video.i_frame_rate) / track->fmt.video.i_frame_rate_base;
    // Match input.c RequestSubRate and subtitle.c's timestamp multiplier.
    return original > 1 ? original / fps : 1.;
}
QVariantList PlayerMediaTools::trackLanguages(bool subtitle) const
{
    QVariantList result; QSet<QString> seen;
    if (m_player->usesMpv()) {
        for (const auto &entry : m_player->mpvPlayback()->value(QStringLiteral("track-list")).toList()) {
            const auto track = entry.toMap();
            if (track.value(QStringLiteral("type")).toString() != (subtitle ? QStringLiteral("sub") : QStringLiteral("audio"))) continue;
            const auto code = languageCode(track.value(QStringLiteral("lang")).toString());
            if (code.isEmpty() || seen.contains(code)) continue;
            const auto *language = vlc_find_iso639(code.toUtf8().constData(), false);
            seen.insert(code); result.append(QVariantMap{{QStringLiteral("text"), language ? QString::fromUtf8(language->psz_eng_name) : code}, {QStringLiteral("value"), code}});
        }
        return result;
    }
    vlc_player_locker lock(m_player->getPlayer()); const auto cat = subtitle ? SPU_ES : AUDIO_ES;
    for (size_t i = 0; i < vlc_player_GetTrackCount(m_player->getPlayer(), cat); ++i) {
        const auto *track = vlc_player_GetTrackAt(m_player->getPlayer(), cat, i);
        const auto code = languageCode(QString::fromUtf8(track->fmt.psz_language ? track->fmt.psz_language : ""));
        if (code.isEmpty() || seen.contains(code)) continue;
        const auto *language = vlc_find_iso639(code.toUtf8().constData(), false);
        const QString label = language ? QString::fromUtf8(language->psz_eng_name) : code;
        seen.insert(code); result.append(QVariantMap{{QStringLiteral("text"), label}, {QStringLiteral("value"), code}});
    }
    return result;
}
QString PlayerMediaTools::selectedLanguage(bool subtitle) const
{
    if (m_player->usesMpv()) {
        for (const auto &entry : m_player->mpvPlayback()->value(QStringLiteral("track-list")).toList()) {
            const auto track = entry.toMap();
            if (track.value(QStringLiteral("type")).toString() == (subtitle ? QStringLiteral("sub") : QStringLiteral("audio")) && track.value(QStringLiteral("selected")).toBool())
                return languageCode(track.value(QStringLiteral("lang")).toString());
        }
        return {};
    }
    vlc_player_locker lock(m_player->getPlayer());
    const auto *track = vlc_player_GetSelectedTrack(m_player->getPlayer(), subtitle ? SPU_ES : AUDIO_ES);
    return track ? languageCode(QString::fromUtf8(track->fmt.psz_language ? track->fmt.psz_language : "")) : QString();
}
QVariantMap PlayerMediaTools::videoInfo() const
{
    if (m_player->usesMpv()) {
        const auto params = m_player->mpvPlayback()->value(QStringLiteral("video-params")).toMap();
        if (params.isEmpty())
            return {{QStringLiteral("resolution"), tr("No video track")}, {QStringLiteral("hdr"), tr("Unavailable")}};
        return {{QStringLiteral("width"), params.value(QStringLiteral("w"))}, {QStringLiteral("height"), params.value(QStringLiteral("h"))},
            {QStringLiteral("resolution"), QStringLiteral("%1 × %2").arg(params.value(QStringLiteral("w")).toInt()).arg(params.value(QStringLiteral("h")).toInt())},
            {QStringLiteral("hdr"), tr("%1 source → SDR display output").arg(params.value(QStringLiteral("gamma")).toString())}};
    }
    vlc_player_locker lock(m_player->getPlayer());
    const auto *track = vlc_player_GetSelectedTrack(m_player->getPlayer(), VIDEO_ES);
    if (!track) return {{QStringLiteral("resolution"), tr("No video track")}, {QStringLiteral("hdr"), tr("Unavailable")}};
    const auto &v = track->fmt.video;
    const QString hdr = v.transfer == TRANSFER_FUNC_SMPTE_ST2084 ? tr("PQ / HDR source")
        : v.transfer == TRANSFER_FUNC_HLG ? tr("HLG source")
        : v.transfer == TRANSFER_FUNC_UNDEF ? tr("Transfer not specified") : tr("SDR source");
    return {{QStringLiteral("width"), v.i_visible_width}, {QStringLiteral("height"), v.i_visible_height},
        {QStringLiteral("resolution"), QStringLiteral("%1 × %2").arg(v.i_visible_width).arg(v.i_visible_height)},
        {QStringLiteral("hdr"), hdr}};
}
QVariantMap PlayerMediaTools::metadata() const
{
    return {{QStringLiteral("title"), m_player->getTitle()}, {QStringLiteral("artist"), m_player->getArtist()},
        {QStringLiteral("album"), m_player->getAlbum()}, {QStringLiteral("location"), m_player->getUrl()},
        {QStringLiteral("durationSeconds"), m_player->getLength().toSeconds()}, {QStringLiteral("seekable"), m_player->isSeekable()},
        {QStringLiteral("reverseSupported"), m_player->isRewindable()}};
}
