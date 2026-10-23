/*****************************************************************************
 * Copyright (C) 2021 VLC authors and VideoLAN
 *
 * Authors: Benjamin Arnaud <bunjee@omega.gg>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * ( at your option ) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
 *****************************************************************************/

#if HAVE_CONFIG_H
# include "config.h"
#endif

#include "mlvideofoldersmodel.hpp"

// VLC includes
#include <vlc_media_library.h>

// Util includes
#include "util/covergenerator.hpp"
#include "util/vlctick.hpp"

// MediaLibrary includes
#include "mlcustomcover.hpp"
#include "mlfolder.hpp"
#include "mlhelper.hpp"
#include "medialib.hpp"
#include <QJSValue>
#include <QJSEngine>
#include <QQmlEngine>
#include <algorithm>

// Static variables

// NOTE: We multiply by 3 to cover most dpi settings.
static const int MLVIDEOFOLDERSMODEL_COVER_WIDTH  = 260 * 3; // 16 / 10 ratio
static const int MLVIDEOFOLDERSMODEL_COVER_HEIGHT = 162 * 3;

// Ctor / dtor

/* explicit */ MLVideoFoldersModel::MLVideoFoldersModel(QObject * parent) : MLBaseModel(parent) {}

void MLVideoFoldersModel::setHierarchical(bool value)
{
    if (m_hierarchical == value) return;
    m_hierarchical = value;
    emit hierarchicalChanged();
    resetCache();
}

void MLVideoFoldersModel::setFrequentOnly(bool value)
{
    if (m_frequentOnly == value) return;
    m_frequentOnly = value;
    emit frequentOnlyChanged();
    resetCache();
}

void MLVideoFoldersModel::resolveAddress(const QUrl& url, QJSValue callback)
{
    if (!m_mediaLib || !callback.isCallable()) return;
    struct Context { QString id; QString title; QUrl url; QVariantList path; };
    m_mediaLib->runOnMLThread<Context>(this,
        [url](vlc_medialibrary_t* ml, Context& result) {
            const auto normalized = url.adjusted(QUrl::StripTrailingSlash | QUrl::NormalizePathSegments).toString(QUrl::FullyEncoded);
#ifdef Q_OS_WIN
            const auto sensitivity = url.isLocalFile() ? Qt::CaseInsensitive : Qt::CaseSensitive;
#else
            const auto sensitivity = Qt::CaseSensitive;
#endif
            // The flat folders query contains media-bearing folders only.
            // Walk actual indexed roots/subfolders so empty folders and all
            // real breadcrumb ancestors remain addressable. These native list
            // operations return all members, irrespective of page parameters.
            ml_unique_ptr<vlc_ml_folder_list_t> list(vlc_ml_list_entry_points(ml, nullptr));
            qsizetype previousLength = 0;
            while (list) {
                const vlc_ml_folder_t* match = nullptr;
                QString matchedAddress;
                for (const auto& folder : ml_range_iterate<vlc_ml_folder_t>(list)) {
                    if (!folder.b_present || folder.b_banned || !folder.psz_mrl) continue;
                    const QUrl candidate = QUrl::fromEncoded(folder.psz_mrl);
                    const auto address = candidate.adjusted(QUrl::StripTrailingSlash | QUrl::NormalizePathSegments).toString(QUrl::FullyEncoded);
                    if (address.size() <= previousLength || address.size() <= matchedAddress.size()) continue;
                    if (normalized.compare(address,sensitivity) != 0 && !normalized.startsWith(address + QLatin1Char('/'),sensitivity)) continue;
                    match = &folder;
                    matchedAddress = address;
                }
                if (!match) break;
                const MLFolder item(match);
                const QUrl candidate = QUrl::fromEncoded(match->psz_mrl);
                result.path.append(QVariantMap{
                    {QStringLiteral("id"), item.getId().toString()},
                    {QStringLiteral("title"), item.getTitle()},
                    {QStringLiteral("address"), candidate.toString()},
                    {QStringLiteral("section"), QStringLiteral("folderMedia")}});
                if (normalized.compare(matchedAddress,sensitivity) == 0) {
                    result.id = item.getId().toString();
                    result.title = item.getTitle();
                    result.url = candidate;
                    return;
                }
                previousLength = matchedAddress.size();
                vlc_ml_folder_list_t* children = nullptr;
                if (vlc_ml_list(ml,VLC_ML_LIST_SUBFOLDERS,nullptr,match->i_id,&children) != VLC_SUCCESS) break;
                list.reset(children);
            }
            result.path.clear();
        },
        [this, callback](quint64, Context& result) mutable {
            auto engine = qjsEngine(this);
            if (!engine) return;
            callback.call({QJSValue(result.id),QJSValue(result.title),QJSValue(result.url.toString()),engine->toScriptValue(result.path)});
        });
}

// MLBaseModel reimplementation

QHash<int, QByteArray> MLVideoFoldersModel::roleNames() const /* override */
{
    return {
        { FOLDER_ID, QByteArrayLiteral("id") },
        { FOLDER_MRL, QByteArrayLiteral("mrl") },
        { FOLDER_TITLE, QByteArrayLiteral("title") },
        { FOLDER_TITLE_FIRST_SYMBOL, QByteArrayLiteral("title_first_symbol") },
        { FOLDER_THUMBNAIL, QByteArrayLiteral("thumbnail") },
        { FOLDER_DURATION, QByteArrayLiteral("duration") },
        { FOLDER_COUNT, QByteArrayLiteral("count") },
        { FOLDER_NB_VIDEOS, QByteArrayLiteral("nb_videos") },
    };
}

// Protected MLVideoModel implementation

QVariant MLVideoFoldersModel::itemRoleData(const MLItem * item, const int role) const /* override */
{
    if (item == nullptr)
        return QVariant();

    const MLFolder * folder = static_cast<const MLFolder *> (item);

    switch (role)
    {
        // NOTE: This is the condition for QWidget view(s).
        case Qt::DisplayRole:
            return QVariant::fromValue(folder->getTitle());
        // NOTE: These are the conditions for QML view(s).
        case FOLDER_ID:
            return QVariant::fromValue(folder->getId());
        case FOLDER_TITLE:
            return QVariant::fromValue(folder->getTitle());
        case FOLDER_TITLE_FIRST_SYMBOL:
            return QVariant::fromValue( getFirstSymbol(folder->getTitle()) );
        case FOLDER_THUMBNAIL:
        {
            return MLCustomCover::url(folder->getId()
                                    , QSize(MLVIDEOFOLDERSMODEL_COVER_WIDTH, MLVIDEOFOLDERSMODEL_COVER_HEIGHT)
                                    , QStringLiteral(":/placeholder/noart_videoCover.svg"));
        }
        case FOLDER_MRL:
            return QUrl(folder->getMRL());
        case FOLDER_DURATION:
            return QVariant::fromValue(folder->getDuration());
        case FOLDER_COUNT:
            return QVariant::fromValue(folder->getCount());
        case FOLDER_NB_VIDEOS:
            return QVariant::fromValue(folder->getVideoCount());
        default:
            return QVariant();
    }
}

vlc_ml_sorting_criteria_t MLVideoFoldersModel::nameToCriteria(QByteArray name) const /* override */
{
    return QHash<QByteArray, vlc_ml_sorting_criteria_t> {
        { QByteArrayLiteral("title"),    VLC_ML_SORTING_ALPHA    },
        { QByteArrayLiteral("duration"), VLC_ML_SORTING_DURATION },
    }.value(name, VLC_ML_SORTING_DEFAULT);
}

std::unique_ptr<MLListCacheLoader>
MLVideoFoldersModel::createMLLoader() const /* override */
{
    return std::make_unique<MLListCacheLoader>(m_mediaLib, std::make_shared<MLVideoFoldersModel::Loader>(*this));
}

// Protected MLBaseModel reimplementation

void MLVideoFoldersModel::onVlcMlEvent(const MLEvent & event) /* override */
{
    int type = event.i_type;

    if ((m_frequentOnly && (type == VLC_ML_EVENT_HISTORY_CHANGED
        || type == VLC_ML_EVENT_MEDIA_UPDATED || type == VLC_ML_EVENT_MEDIA_DELETED))
        || ((m_hierarchical || m_frequentOnly)
            && (type == VLC_ML_EVENT_FOLDER_UPDATED || type == VLC_ML_EVENT_FOLDER_DELETED))) {
        emit resetRequested();
        return;
    }

    switch (type)
    {
        case VLC_ML_EVENT_FOLDER_ADDED:
        {
            emit resetRequested();
            return;
        }
        case VLC_ML_EVENT_FOLDER_UPDATED:
        {
            MLItemId itemId(event.modification.i_entity_id, VLC_ML_PARENT_FOLDER);
            updateItemInCache(itemId);
            return;
        }
        case VLC_ML_EVENT_FOLDER_DELETED:
        {
            MLItemId itemId(event.deletion.i_entity_id, VLC_ML_PARENT_FOLDER);
            deleteItemInCache(itemId);
            return;
        }
        default:
            break;
    }

    MLBaseModel::onVlcMlEvent(event);
}

// Loader
std::vector<std::unique_ptr<MLItem>> MLVideoFoldersModel::Loader::hierarchicalFolders(
    vlc_medialibrary_t* ml, const vlc_ml_query_params_t* queryParams) const
{
    // Both operations return all members in the pinned native interface, even
    // when an offset/limit is supplied. Apply search, ordering and logical pages
    // here so the Qt cache cannot repeat the first page or miscount a search.
    ml_unique_ptr<vlc_ml_folder_list_t> list;
    if (m_parent.id <= 0) list.reset(vlc_ml_list_entry_points(ml,nullptr));
    else {
        vlc_ml_folder_list_t* children = nullptr;
        if (vlc_ml_list(ml,VLC_ML_LIST_SUBFOLDERS,nullptr,m_parent.id,&children) == VLC_SUCCESS)
            list.reset(children);
    }
    if (!list) return {};
    const auto pattern = QString::fromUtf8(queryParams->psz_pattern);
    std::vector<std::unique_ptr<MLItem>> result;
    for (const auto& folder : ml_range_iterate<vlc_ml_folder_t>(list)) {
        if (!folder.b_present || folder.b_banned) continue;
        if (!pattern.isEmpty() && !QString::fromUtf8(folder.psz_name).contains(pattern,Qt::CaseInsensitive)) continue;
        result.emplace_back(std::make_unique<MLFolder>(&folder));
    }
    std::sort(result.begin(),result.end(),[queryParams](const auto& a, const auto& b) {
        const auto left = static_cast<MLFolder*>(a.get());
        const auto right = static_cast<MLFolder*>(b.get());
        if (queryParams->i_sort == VLC_ML_SORTING_DURATION && left->getDuration().toVLCTick() != right->getDuration().toVLCTick())
            return queryParams->b_desc ? left->getDuration().toVLCTick() > right->getDuration().toVLCTick()
                                      : left->getDuration().toVLCTick() < right->getDuration().toVLCTick();
        const int order = QString::localeAwareCompare(left->getTitle(),right->getTitle());
        if (order) return queryParams->b_desc ? order > 0 : order < 0;
        return queryParams->b_desc ? left->getId().id > right->getId().id : left->getId().id < right->getId().id;
    });
    return result;
}

// Derive Home's folder ranking from the existing playback history. No second
// browsing-history database or preference is created; clearing native history
// also removes these results. Native pages run on the existing ML worker.
std::vector<std::unique_ptr<MLItem>> MLVideoFoldersModel::Loader::frequentFolders(vlc_medialibrary_t* ml) const
{
    struct Usage { quint64 plays = 0; time_t lastPlayed = 0; };
    QHash<QString, Usage> usage;
    const auto key = [](QUrl url) {
        auto result = url.adjusted(QUrl::StripTrailingSlash | QUrl::NormalizePathSegments).toString(QUrl::FullyEncoded);
#ifdef Q_OS_WIN
        if (url.isLocalFile()) result = result.toCaseFolded();
#endif
        return result;
    };
    auto query = vlc_ml_query_params_create();
    query.i_nbResults = 256;
    for (;;) {
        ml_unique_ptr<vlc_ml_media_list_t> page(vlc_ml_list_history(ml, &query, VLC_ML_HISTORY_TYPE_GLOBAL));
        if (!page) break;
        for (const auto& media : ml_range_iterate<vlc_ml_media_t>(page)) {
            if (!media.p_files) continue;
            for (const auto& file : ml_range_iterate<vlc_ml_file_t>(media.p_files)) {
                if (file.i_type != VLC_ML_FILE_TYPE_MAIN || !file.psz_mrl || !file.b_present) continue;
                const auto url = QUrl::fromEncoded(file.psz_mrl);
                if (!url.isLocalFile()) continue;
                auto& item = usage[key(url.adjusted(QUrl::RemoveFilename))];
                item.plays += std::max(1u, media.i_playcount);
                item.lastPlayed = std::max(item.lastPlayed, media.i_last_played_date);
                break;
            }
        }
        if (page->i_nb_items < query.i_nbResults) break;
        query.i_offset += query.i_nbResults;
    }
    struct RankedFolder { std::unique_ptr<MLFolder> item; Usage usage; };
    std::vector<RankedFolder> folders;
    query.i_offset = 0;
    for (;;) {
        ml_unique_ptr<vlc_ml_folder_list_t> page(vlc_ml_list_folders(ml, &query));
        if (!page) break;
        for (const auto& folder : ml_range_iterate<vlc_ml_folder_t>(page)) {
            if (!folder.b_present || folder.b_banned || !folder.psz_mrl) continue;
            const auto found = usage.constFind(key(QUrl::fromEncoded(folder.psz_mrl)));
            if (found != usage.cend()) folders.push_back({std::make_unique<MLFolder>(&folder), *found});
        }
        if (page->i_nb_items < query.i_nbResults) break;
        query.i_offset += query.i_nbResults;
    }
    std::sort(folders.begin(), folders.end(), [](const auto& a, const auto& b) {
        if (a.usage.plays != b.usage.plays) return a.usage.plays > b.usage.plays;
        if (a.usage.lastPlayed != b.usage.lastPlayed) return a.usage.lastPlayed > b.usage.lastPlayed;
        return a.item->getId().id < b.item->getId().id;
    });
    std::vector<std::unique_ptr<MLItem>> result;
    for (auto& folder : folders) result.emplace_back(std::move(folder.item));
    return result;
}

size_t MLVideoFoldersModel::Loader::count(vlc_medialibrary_t * ml, const vlc_ml_query_params_t* queryParams) const /* override */
{
    if (m_frequentOnly) return frequentFolders(ml).size();
    if (m_hierarchical) return hierarchicalFolders(ml,queryParams).size();
    return vlc_ml_count_folders_by_type(ml, queryParams, VLC_ML_MEDIA_TYPE_VIDEO);
}

std::vector<std::unique_ptr<MLItem>>
MLVideoFoldersModel::Loader::load(vlc_medialibrary_t * ml,
                                  const vlc_ml_query_params_t* queryParams) const /* override */
{
    if (m_frequentOnly) {
        auto folders = frequentFolders(ml);
        const size_t begin = std::min(size_t(queryParams->i_offset), folders.size());
        const size_t end = queryParams->i_nbResults ? std::min(folders.size(), begin + queryParams->i_nbResults) : folders.size();
        std::vector<std::unique_ptr<MLItem>> result;
        for (size_t i = begin; i < end; ++i) result.emplace_back(std::move(folders[i]));
        return result;
    }
    if (m_hierarchical) {
        auto folders = hierarchicalFolders(ml,queryParams);
        const size_t begin = std::min(size_t(queryParams->i_offset),folders.size());
        const size_t end = queryParams->i_nbResults ? std::min(folders.size(),begin+queryParams->i_nbResults) : folders.size();
        std::vector<std::unique_ptr<MLItem>> result;
        for (size_t i = begin; i < end; ++i) result.emplace_back(std::move(folders[i]));
        return result;
    }
    ml_unique_ptr<vlc_ml_folder_list_t> list(vlc_ml_list_folders_by_type(ml,queryParams,VLC_ML_MEDIA_TYPE_VIDEO));
    if (list == nullptr)
        return {};

    std::vector<std::unique_ptr<MLItem>> result;

    for (const vlc_ml_folder_t & folder : ml_range_iterate<vlc_ml_folder_t>(list))
    {
        result.emplace_back(std::make_unique<MLFolder>(&folder));
    }

    return result;
}

std::unique_ptr<MLItem>
MLVideoFoldersModel::Loader::loadItemById(vlc_medialibrary_t* ml, MLItemId itemId) const
{
    assert(itemId.type == VLC_ML_PARENT_FOLDER);
    ml_unique_ptr<vlc_ml_folder_t> folder(vlc_ml_get_folder(ml, itemId.id));
    if (!folder)
        return nullptr;
    return std::make_unique<MLFolder>(folder.get());
}
