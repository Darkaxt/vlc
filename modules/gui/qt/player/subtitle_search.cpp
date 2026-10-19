// SPDX-License-Identifier: GPL-2.0-or-later
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "subtitle_search.hpp"
#include "player_controller.hpp"
#include "player_media_tools.hpp"
#include <vlc_configuration.h>
#include <vlc_iso_lang.h>
#include "subtitle_archive.hpp"
#include <QCryptographicHash>
#include <QDir>
#include <QFileInfo>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSaveFile>
#include <QUrlQuery>
#include <QUuid>
#include <QSet>
#include <QStringConverter>

namespace {
const char *const providerNames[] = {"OpenSubtitles", "SubDL", "SubSource"};
constexpr qsizetype responseLimit = 16 * 1024 * 1024;
constexpr qsizetype subtitleLimit = 8 * 1024 * 1024;
bool textSubtitle(const QString &name)
{
    return QStringList{QStringLiteral("srt"), QStringLiteral("vtt"), QStringLiteral("ass"), QStringLiteral("ssa")}.contains(QFileInfo(name).suffix().toLower());
}
QString textFormat(const QByteArray &bytes)
{
    const auto encoding = QStringConverter::encodingForData(bytes);
    if (bytes.contains('\0') && !encoding) return {};
    const QString text = encoding ? QStringDecoder(*encoding).decode(bytes) : QString::fromUtf8(bytes);
    if (text.trimmed().startsWith(QLatin1String("WEBVTT"))) return QStringLiteral("vtt");
    if (text.contains(QLatin1String("[Events]"), Qt::CaseInsensitive))
        return text.contains(QLatin1String("[V4 Styles]"), Qt::CaseInsensitive) ? QStringLiteral("ssa") : QStringLiteral("ass");
    static const QRegularExpression timed(QStringLiteral("(?m)^([\\d:]+[,.]\\d+)\\s+-->\\s+([\\d:]+[,.]\\d+)"));
    return timed.match(text).hasMatch() ? QStringLiteral("srt") : QString();
}
QString idString(const QJsonValue &value)
{
    return value.isString() ? value.toString() : value.isDouble() ? QString::number(value.toInteger()) : QString();
}
}
SubtitleSearch::SubtitleSearch(PlayerController *player, PlayerMediaTools *tools)
    : QObject(tools), m_player(player), m_tools(tools), m_network(this)
{
    // Optional process-local configuration supports supervised launches without
    // putting a secret in command arguments, settings files or diagnostic input.
    m_keys = {qgetenv("VLC_REDESIGN_OPENSUBTITLES_API_KEY"), qgetenv("VLC_REDESIGN_SUBDL_API_KEY"), qgetenv("VLC_REDESIGN_SUBSOURCE_API_KEY")};
    connect(player, &PlayerController::inputChanged, this, [this] { cancel(); m_items.clear(); m_archive.clear(); publish(); });
    connect(player->getSubtitleTracks(), &TrackListModel::selectionRequested, this, [this] { if (m_busy || m_waitingTrack) cancel(); });
    connect(tools, &PlayerMediaTools::cuesChanged, this, [this] {
        if (m_waitingTrack && m_tools->subtitleLoaded() && m_tools->isCurrentMedia(m_input)) {
            m_waitingTrack = false; m_status = tr("Downloaded subtitle loaded, selected and its association saved."); emit changed();
        }
    });
    m_status = tr("Choose a provider. Searches send your query and language only when you press Search. Credentials last for this VLC session.");
}
SubtitleSearch::~SubtitleSearch()
{
    ++m_generation;
    if (m_reply) { QObject::disconnect(m_reply.data(), nullptr, this, nullptr); m_reply->abort(); }
}
void SubtitleSearch::fail(const QString &message)
{
    m_busy = false; m_status = message; emit changed();
}
void SubtitleSearch::cancel()
{
    ++m_generation; m_waitingTrack = false;
    if (m_reply) { auto reply = m_reply; m_reply.clear(); reply->abort(); reply->deleteLater(); }
    m_busy = false; m_status = tr("Cancelled. No pending download will be associated."); emit changed();
}
void SubtitleSearch::setProvider(int value)
{
    if (value < 0 || value > 2 || value == m_provider) return;
    cancel(); m_provider = value; m_items.clear(); m_archive.clear(); publish();
    m_status = tr("Provider selected. Credentials stay local to this session; press Search to contact this provider."); emit changed();
}
void SubtitleSearch::setCredentials(const QString &key)
{
    cancel(); m_keys[m_provider] = key.trimmed().toUtf8();
    if (m_provider == 0) { m_token.clear(); m_openSubtitlesHost = QStringLiteral("api.opensubtitles.com"); }
    m_status = configured() ? tr("API key configured for this session.") : tr("API key cleared for this session."); emit changed();
}
QUrl SubtitleSearch::api(const QString &path) const
{
    const QString base = m_provider == 0 ? QStringLiteral("https://") + m_openSubtitlesHost + QStringLiteral("/api/v1")
        : m_provider == 1 ? QStringLiteral("https://api.subdl.com/api/v2") : QStringLiteral("https://api.subsource.net/api/v1");
    return QUrl(base + path);
}
bool SubtitleSearch::allowedDownload(const QUrl &url) const
{
    if (url.scheme() != QLatin1String("https") || !url.userInfo().isEmpty() || (url.port() != -1 && url.port() != 443)) return false;
    const QStringList hosts = m_provider == 0 ? QStringList{QStringLiteral("api.opensubtitles.com"), QStringLiteral("vip-api.opensubtitles.com"), QStringLiteral("dl.opensubtitles.com"), QStringLiteral("www.opensubtitles.com"), QStringLiteral("opensubtitles.com")}
        : m_provider == 1 ? QStringList{QStringLiteral("api.subdl.com"), QStringLiteral("dl.subdl.com")}
        : QStringList{QStringLiteral("api.subsource.net"), QStringLiteral("dl.subsource.net"), QStringLiteral("cdn.subsource.net")};
    return hosts.contains(url.host().toLower());
}
void SubtitleSearch::request(const QByteArray &method, const QUrl &url, const QJsonObject &body, bool authenticated, Completion completed, int redirects)
{
    if (!allowedDownload(url) || (authenticated && url.host() != api(QString()).host())) {
        fail(tr("The provider returned an unsupported download origin. No credentials were sent.")); return;
    }
    if (!configured() && authenticated) { fail(tr("Enter this provider's API key before searching.")); return; }
    const auto generation = m_generation;
    QNetworkRequest request(url);
    request.setAttribute(QNetworkRequest::RedirectPolicyAttribute, QNetworkRequest::ManualRedirectPolicy);
    request.setRawHeader("User-Agent", "DarkaxtVLCRedesign v0.1");
    request.setRawHeader("Accept", "application/json, application/zip, text/plain");
    if (authenticated) {
        if (m_provider == 0) { request.setRawHeader("Api-Key", m_keys[0]); if (!m_token.isEmpty()) request.setRawHeader("Authorization", QByteArray("Bearer ") + m_token); }
        else if (m_provider == 1) request.setRawHeader("Authorization", QByteArray("Bearer ") + m_keys[1]);
        else request.setRawHeader("X-API-Key", m_keys[2]);
    }
    QNetworkReply *reply;
    if (method == "POST") { request.setHeader(QNetworkRequest::ContentTypeHeader, QStringLiteral("application/json")); reply = m_network.post(request, QJsonDocument(body).toJson(QJsonDocument::Compact)); }
    else reply = m_network.get(request);
    m_reply = reply; m_busy = true; emit changed();
    reply->setReadBufferSize(256 * 1024);
    auto bytes = std::make_shared<QByteArray>();
    auto oversized = std::make_shared<bool>(false);
    connect(reply, &QIODevice::readyRead, this, [reply, bytes, oversized] {
        bytes->append(reply->readAll());
        if (bytes->size() > responseLimit) { *oversized = true; reply->abort(); }
    });
    connect(reply, &QNetworkReply::finished, this, [this, reply, bytes, oversized, generation, method, url, body, authenticated, completed, redirects] {
        reply->deleteLater();
        if (generation != m_generation) return;
        m_reply.clear(); bytes->append(reply->readAll());
        if (*oversized || bytes->size() > responseLimit) { fail(tr("Provider response exceeds the 16 MiB download limit.")); return; }
        const int status = reply->attribute(QNetworkRequest::HttpStatusCodeAttribute).toInt();
        const auto redirect = reply->attribute(QNetworkRequest::RedirectionTargetAttribute).toUrl();
        if (status >= 300 && status < 400 && !redirect.isEmpty()) {
            const auto next = url.resolved(redirect);
            if (redirects >= 8 || !allowedDownload(next)) { fail(tr("Unsupported or excessive provider redirects.")); return; }
            // A CDN never receives the provider's API key or account token.
            const bool sameOrigin = next.host() == url.host();
            if (!sameOrigin && method != "GET") { fail(tr("A provider attempted to redirect a request body to another origin. Nothing was forwarded.")); return; }
            this->request(status == 303 ? QByteArray("GET") : method, next, status == 303 ? QJsonObject() : body,
                authenticated && sameOrigin, completed, redirects + 1); return;
        }
        if (status == 401 || status == 403) { fail(tr("Provider refused authentication or permission (HTTP %1). Check this provider's API key and optional account login.").arg(status)); return; }
        if (status == 402) { fail(tr("This provider action requires a paid subscription. No payment or plan change was made.")); return; }
        if (status == 429 || status == 406) { fail(tr("Provider quota or rate limit reached (HTTP %1). No automatic retry was made.").arg(status)); return; }
        if (status < 200 || status >= 300 || reply->error() != QNetworkReply::NoError) { fail(status ? tr("Provider request failed (HTTP %1).").arg(status) : tr("Network or TLS connection failed. Check connectivity and try again explicitly.")); return; }
        m_busy = false;
        completed(*bytes, reply->rawHeader("Content-Disposition")); emit changed();
    });
}
void SubtitleSearch::login(const QString &username, const QString &password)
{
    if (m_provider != 0) { fail(tr("This provider uses its API key; an account password is not sent.")); return; }
    cancel(); m_status = tr("Signing in to OpenSubtitles…");
    request("POST", api(QStringLiteral("/login")), {{QStringLiteral("username"), username}, {QStringLiteral("password"), password}}, true,
        [this](const QByteArray &bytes, const QByteArray &) {
            QJsonObject data; if (!parseResponse(bytes, data)) return;
            const auto token = data.value(QStringLiteral("token")).toString().toUtf8();
            const auto host = data.value(QStringLiteral("base_url")).toString();
            if (token.isEmpty() || (host != QLatin1String("api.opensubtitles.com") && host != QLatin1String("vip-api.opensubtitles.com"))) { fail(tr("OpenSubtitles returned an unsupported login response.")); return; }
            m_token = token; m_openSubtitlesHost = host; m_status = tr("Signed in for this VLC session.");
        });
}
void SubtitleSearch::search(const QString &query, const QString &language)
{
    cancel(); m_items.clear(); m_archive.clear(); publish(); m_input = m_player->getUrl(); m_inputIdentity = m_tools->identity(m_input);
    const auto clean = query.trimmed();
    if (clean.size() < 2 || clean.size() > 256) { fail(tr("Enter a title between 2 and 256 characters.")); return; }
    m_language = language.trimmed().toLower(); m_title = clean;
    static const QRegularExpression code(QStringLiteral("^[a-z]{2,3}(?:-[a-z]{2})?$"));
    if (!code.match(m_language).hasMatch()) { fail(tr("Enter a language code such as en, de or pt-br.")); return; }
    QUrl url = api(m_provider == 0 ? QStringLiteral("/subtitles") : m_provider == 1 ? QStringLiteral("/subtitles/search") : QStringLiteral("/movies/search"));
    QUrlQuery params;
    if (m_provider == 0) { params.addQueryItem(QStringLiteral("languages"), m_language); params.addQueryItem(QStringLiteral("query"), clean.toLower()); }
    else if (m_provider == 1) { params.addQueryItem(QStringLiteral("film_name"), clean); params.addQueryItem(QStringLiteral("languages"), m_language); params.addQueryItem(QStringLiteral("unpack"), QStringLiteral("1")); }
    else { params.addQueryItem(QStringLiteral("q"), clean); params.addQueryItem(QStringLiteral("searchType"), QStringLiteral("text")); }
    url.setQuery(params); m_status = tr("Searching the selected provider…");
    request("GET", url, {}, true, [this](const QByteArray &bytes, const QByteArray &) {
        if (m_provider != 2) { subtitleResults(bytes); return; }
        QJsonObject doc; if (!parseResponse(bytes, doc)) return;
        for (const auto &v : doc.value(QStringLiteral("data")).toArray()) {
            const auto r = v.toObject();
            m_items.append({r.value(QStringLiteral("title")).toString(), {}, QString::number(r.value(QStringLiteral("releaseYear")).toInt()),
                idString(r.value(QStringLiteral("movieId"))), QStringLiteral("title"), {}});
            if (m_items.size() >= 100) break;
        }
        m_status = m_items.isEmpty() ? tr("No matching titles. Change the query or provider.") : tr("Select the intended title to list its subtitles."); publish();
    });
}
void SubtitleSearch::subtitleResults(const QByteArray &bytes)
{
    QJsonObject data; if (!parseResponse(bytes, data)) return; m_items.clear();
    const auto rows = m_provider == 0 ? data.value(QStringLiteral("data")).toArray() : m_provider == 1 ? data.value(QStringLiteral("subtitles")).toArray() : data.value(QStringLiteral("data")).toArray();
    for (const auto &v : rows) {
        const auto row = v.toObject();
        if (m_provider == 0) {
            const auto a = row.value(QStringLiteral("attributes")).toObject();
            for (const auto &fv : a.value(QStringLiteral("files")).toArray()) {
                const auto f = fv.toObject();
                m_items.append({f.value(QStringLiteral("file_name")).toString(), a.value(QStringLiteral("language")).toString(), a.value(QStringLiteral("release")).toString(), idString(f.value(QStringLiteral("file_id"))), QStringLiteral("subtitle"), {}});
            }
        } else if (m_provider == 1) {
            const auto unpacked = row.value(QStringLiteral("unpack_files")).toArray();
            if (!unpacked.isEmpty()) for (const auto &fv : unpacked) {
                const auto f = fv.toObject();
                m_items.append({f.value(QStringLiteral("name")).toString(), f.value(QStringLiteral("language")).toString(), f.value(QStringLiteral("release_name")).toString(), idString(f.value(QStringLiteral("file_n_id"))), QStringLiteral("subtitle"), QUrl(QStringLiteral("https://dl.subdl.com")).resolved(QUrl(f.value(QStringLiteral("url")).toString()))});
            } else m_items.append({row.value(QStringLiteral("name")).toString(), row.value(QStringLiteral("language")).toString(), row.value(QStringLiteral("release_name")).toString(), QRegularExpression(QStringLiteral("([0-9]+)\\.zip$"), QRegularExpression::CaseInsensitiveOption).match(row.value(QStringLiteral("name")).toString()).captured(1), QStringLiteral("subtitle"), QUrl(QStringLiteral("https://dl.subdl.com")).resolved(QUrl(row.value(QStringLiteral("url")).toString()))});
        } else {
            QStringList releases; for (const auto &release : row.value(QStringLiteral("releaseInfo")).toArray()) if (!release.toString().isEmpty()) releases.append(release.toString());
            m_items.append({m_title, row.value(QStringLiteral("language")).toString(), releases.join(QStringLiteral(" / ")), idString(row.value(QStringLiteral("subtitleId"))), QStringLiteral("subtitle"), {}});
        }
        if (m_items.size() >= 100) { m_items.resize(100); break; }
    }
    m_status = m_items.isEmpty() ? tr("No subtitles found for this query and language.") : tr("%1 results. Check title, release and language before downloading.").arg(m_items.size()); publish();
}
void SubtitleSearch::publish()
{
    m_results.clear();
    for (auto &r : m_items) {
        if (r.id.isEmpty() && r.kind == QLatin1String("subtitle"))
            r.id = QStringLiteral("file-") + QString::fromLatin1(QCryptographicHash::hash(r.url.toEncoded(), QCryptographicHash::Sha256).toHex().left(12));
        m_results.append(QVariantMap{{QStringLiteral("title"), r.title.left(512)}, {QStringLiteral("language"), r.language.left(64)},
            {QStringLiteral("release"), r.release.isEmpty() ? tr("Release not provided") : r.release.left(1024)}, {QStringLiteral("kind"), r.kind},
            {QStringLiteral("provider"), QString::fromLatin1(providerNames[m_provider])}, {QStringLiteral("reference"), r.id.left(128)}});
    }
    emit changed();
}
void SubtitleSearch::select(int row)
{
    if (m_busy || row < 0 || row >= m_items.size()) return;
    if (m_input != m_player->getUrl()) { fail(tr("The playing input changed. Search again for the intended media.")); return; }
    m_waitingTrack = false;
    const auto selected = m_items[row];
    m_archive.clear(); m_status = selected.kind == QLatin1String("title") ? tr("Loading this title's subtitles…") : tr("Downloading the selected subtitle…");
    if (selected.kind == QLatin1String("title")) {
        m_title = selected.title;
        auto url = api(QStringLiteral("/subtitles")); QUrlQuery params;
        params.addQueryItem(QStringLiteral("movieId"), selected.id);
        const auto *language = vlc_find_iso639(m_language.toUtf8().constData(), false);
        params.addQueryItem(QStringLiteral("language"), language ? QString::fromUtf8(language->psz_eng_name).toLower() : m_language); url.setQuery(params);
        request("GET", url, {}, true, [this](const QByteArray &bytes, const QByteArray &) { subtitleResults(bytes); }); return;
    }
    m_selected = selected;
    if (m_provider != 1 && (!QRegularExpression(QStringLiteral("^[0-9]+$")).match(selected.id).hasMatch() || selected.id.toULongLong() == 0)) {
        fail(tr("The provider returned an invalid subtitle identifier.")); return;
    }
    if (m_provider == 0) {
        request("POST", api(QStringLiteral("/download")), {{QStringLiteral("file_id"), selected.id.toLongLong()}, {QStringLiteral("sub_format"), QStringLiteral("srt")}}, true,
            [this, selected](const QByteArray &bytes, const QByteArray &) {
                QJsonObject data; if (!parseResponse(bytes, data)) return; const auto link = QUrl(data.value(QStringLiteral("link")).toString());
                m_status = tr("Download authorized; %1 downloads remain in the provider quota.").arg(data.value(QStringLiteral("remaining")).toInt());
                request("GET", link, {}, false, [this, selected](const QByteArray &bytes, const QByteArray &disposition) { decodeDownload(bytes, disposition, selected.title); });
            });
    } else {
        const auto url = m_provider == 1 ? selected.url : api(QStringLiteral("/subtitles/") + selected.id + QStringLiteral("/download"));
        request("GET", url, {}, m_provider == 2, [this, selected](const QByteArray &bytes, const QByteArray &disposition) { decodeDownload(bytes, disposition, selected.title); });
    }
}
QStringList SubtitleSearch::archiveFiles() const
{
    QStringList names; for (const auto &f : m_archive) names.append(f.name + QStringLiteral(" [") + textFormat(f.bytes).toUpper() + QLatin1Char(']')); return names;
}
bool SubtitleSearch::parseResponse(const QByteArray &bytes, QJsonObject &object)
{
    QJsonParseError error; const auto doc = QJsonDocument::fromJson(bytes, &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject()) { fail(tr("The provider returned an invalid JSON response.")); return false; }
    object = doc.object();
    if (object.contains(QStringLiteral("error"))
        || (object.value(QStringLiteral("status")).isBool() && !object.value(QStringLiteral("status")).toBool())
        || (object.value(QStringLiteral("success")).isBool() && !object.value(QStringLiteral("success")).toBool())) {
        fail(tr("The provider rejected the query. Check the title, language and account quota.")); return false;
    }
    return true;
}
void SubtitleSearch::decodeDownload(const QByteArray &bytes, const QByteArray &disposition, const QString &name)
{
    m_archive.clear();
    if (bytes.startsWith("PK\003\004") || bytes.startsWith("PK\005\006")) {
        QVector<SubtitleArchive::Member> files;
        const auto result = SubtitleArchive::decode(bytes, files);
        if (result != SubtitleArchive::Result::Ok) {
            switch (result) {
            case SubtitleArchive::Result::TooManyEntries: fail(tr("The subtitle archive exceeds the 256-entry limit.")); break;
            case SubtitleArchive::Result::TooLarge: fail(tr("The extracted subtitles exceed the size limit.")); break;
            case SubtitleArchive::Result::Duplicate: fail(tr("The archive repeats an identical member path; its files cannot be selected unambiguously.")); break;
            case SubtitleArchive::Result::NoSupportedFiles: fail(tr("The archive contains no supported SRT, WebVTT, ASS or SSA files.")); break;
            default: fail(tr("The subtitle archive is invalid or damaged.")); break;
            }
            return;
        }
        for (const auto &file : files)
            if (!textFormat(file.bytes).isEmpty()) m_archive.append({file.name, file.bytes});
        if (m_archive.isEmpty()) { fail(tr("The archive contains no supported SRT, WebVTT, ASS or SSA files.")); return; }
        if (m_archive.size() == 1) { associateArchiveFile(0); return; }
        m_status = tr("Choose the exact file from this archive; season packs are not assigned automatically."); emit changed(); return;
    }
    QString filename = name;
    static const QRegularExpression fileName(QStringLiteral("filename=\"?([^\";]+)"), QRegularExpression::CaseInsensitiveOption);
    const auto match = fileName.match(QString::fromUtf8(disposition)); if (match.hasMatch()) filename = QFileInfo(match.captured(1)).fileName();
    if (bytes.size() > subtitleLimit || textFormat(bytes).isEmpty()) { fail(tr("The provider response is not a supported text subtitle, or exceeds 8 MiB.")); return; }
    storeAndAssociate(filename, bytes);
}
void SubtitleSearch::associateArchiveFile(int index)
{
    if (index < 0 || index >= m_archive.size()) return;
    const auto chosen = m_archive[index]; storeAndAssociate(chosen.name, chosen.bytes);
}
void SubtitleSearch::storeAndAssociate(const QString &name, const QByteArray &bytes)
{
    if (!m_tools->isCurrentMedia(m_input) || (m_input.isLocalFile() && (m_inputIdentity.isEmpty() || m_inputIdentity != m_tools->identity(m_input)))) { fail(tr("The playing input or its file identity changed. Nothing was associated.")); return; }
    char *base = config_GetUserDir(VLC_USERDATA_DIR); const QString root = QDir(QString::fromUtf8(base ? base : "")).filePath(QStringLiteral("redesign-subtitles")); free(base);
    QDir dir(root);
    const QString format = textFormat(bytes);
    if (format.isEmpty()) { fail(tr("This archive member is not a supported text subtitle.")); return; }
    QString original = name; original.replace(QLatin1Char('\\'), QLatin1Char('/'));
    const QFileInfo member(original);
    original = (member.path() == QLatin1String(".") ? QString() : member.path() + QLatin1Char('/')) + member.completeBaseName() + QLatin1Char('.') + format;
    const QString context = m_selected.release.isEmpty() ? m_title : m_selected.release;
    const QString language = PlayerMediaTools::languageCode(m_selected.language.isEmpty() ? m_language : m_selected.language);
    const QString filename = SubtitleData::downloadFileName(context, original,
        language, QString::fromLatin1(providerNames[m_provider]), m_selected.id);
    const QString download = QUuid::createUuid().toString(QUuid::WithoutBraces);
    if (!dir.mkpath(QStringLiteral(".")) || !dir.mkdir(download)) { fail(tr("The download folder could not be created. Existing subtitles were not changed.")); return; }
    // A fresh exclusively-created directory keeps readable names and preserves
    // repeated downloads, without replacing an existing user's subtitle.
    const QString path = dir.filePath(download + QLatin1Char('/') + filename);
    bool saved = false;
    {
        QSaveFile file(path);
        saved = file.open(QIODevice::WriteOnly) && file.write(bytes) == bytes.size() && file.commit();
    }
    if (!saved) { dir.rmdir(download); fail(tr("The downloaded subtitle could not be saved. Existing subtitle files were not changed.")); return; }
    if (!m_tools->associateAndSave(QUrl::fromLocalFile(path))) { fail(tr("Subtitle saved locally. %1").arg(m_tools->status())); return; }
    m_waitingTrack = !m_tools->subtitleLoaded();
    m_status = m_waitingTrack ? tr("Subtitle downloaded and its association saved. VLC is loading the selected track.") : tr("Downloaded subtitle loaded, selected and its association saved.");
    m_archive.clear(); emit changed();
}
