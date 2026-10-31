/*****************************************************************************
 * Copyright (C) 2019 VLC authors and VideoLAN
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
#include "input_models.hpp"
#include "player/subtitle_data.hpp"
#include <QCryptographicHash>
#include <QUrl>
#include <algorithm>

#include "player/player_controller.hpp"

//***************************
//  track list model
//***************************

TrackListModel::TrackListModel(vlc_player_t *player, QObject *parent)
    : QAbstractListModel(parent)
    , m_player(player)
{
}

QByteArray TrackListModel::associatedSourcePrefix(const QByteArray &uri)
{
    // Pinned input.c InputSourceNew / es_out.c stable associated-source IDs.
    return QCryptographicHash::hash(uri, QCryptographicHash::Md5).toHex() + "/spu/";
}
void TrackListModel::setAssociatedSourceLabel(const QString &uri, const QString &label)
{
    m_sourceLabels[associatedSourcePrefix(uri.toUtf8())] = SubtitleData::trackSourceName(label);
    if (!m_data.isEmpty()) emit dataChanged(index(0), index(m_data.size() - 1), {Qt::DisplayRole});
}
Qt::ItemFlags TrackListModel::flags(const QModelIndex &) const
{
    return Qt::ItemIsUserCheckable;
}

int TrackListModel::rowCount(const QModelIndex &) const
{
    return m_data.size();
}

QVariant TrackListModel::data(const QModelIndex &index, int role) const
{
    int row = index.row();
    if (row >= m_data.size())
        return QVariant{};
    if (role == Qt::DisplayRole) {
        if (m_externalSelection) return m_data[row].m_title;
        const QByteArray id = vlc_es_id_GetStrId(m_data[row].m_id.get());
        for (auto it = m_sourceLabels.begin(); it != m_sourceLabels.end(); ++it)
            if (id.startsWith(it.key())) return m_data[row].m_title.contains(it.value(), Qt::CaseInsensitive)
                ? m_data[row].m_title : it.value() + QStringLiteral(" — ") + m_data[row].m_title;
        return m_data[row].m_title;
    }
    else if (role == Qt::CheckStateRole)
        return QVariant::fromValue<bool>(m_data[row].m_selected);
    return QVariant{};
}

bool TrackListModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    int row = index.row();
    if (row >= m_data.size())
        return false;
    if ( role != Qt::CheckStateRole )
        return false;
    if (!value.canConvert<bool>())
        return false;
    bool select = value.toBool();
    emit selectionRequested();
    if (m_externalSelection) {
        m_externalSelection(m_data[row].m_externalId, select);
        return true;
    }
    vlc_player_locker lock{ m_player };

    if (select)
    {
        vlc_es_id_t *es_id = m_data[row].m_id.get();
        const enum es_format_category_e cat = vlc_es_id_GetCat(es_id);
        enum vlc_player_select_policy policy =
            ( cat ==  VIDEO_ES ) || m_multiSelect ? VLC_PLAYER_SELECT_SIMULTANEOUS
                                                  : VLC_PLAYER_SELECT_EXCLUSIVE;
        vlc_player_SelectEsId(m_player, es_id, policy);
    }
    else
        vlc_player_UnselectEsId(m_player, m_data[row].m_id.get());
    return true;
}

void TrackListModel::updateTracks(vlc_player_list_action action, const vlc_player_track *track_info)
{
    switch (action) {
    case VLC_PLAYER_LIST_ADDED:
    {
        beginInsertRows({}, m_data.size(), m_data.size());
        m_data.append(Data{ track_info });
        endInsertRows();
        emit countChanged();
        break;
    }
    case VLC_PLAYER_LIST_REMOVED:
    {
        auto it = std::find_if(m_data.begin(), m_data.end(), [&](const Data& t) {
            return t.m_id.get() == track_info->es_id;
        });
        if (it == m_data.end())
            return;

        int pos = std::distance(m_data.begin(), it);
        beginRemoveRows({}, pos, pos);
        m_data.erase(it);
        endRemoveRows();
        emit countChanged();
        break;
    }
    case VLC_PLAYER_LIST_UPDATED:
    {
        int pos = 0;
        bool found = false;
        for (Data& d : m_data)
        {
            if (d.m_id.get() == track_info->es_id)
            {
                d.update(track_info);
                found = true;
                break;
            }
            pos++;
        }
        if (!found)
            return;
        QModelIndex dataIndex = index(pos);
        emit dataChanged(dataIndex, dataIndex, { Qt::DisplayRole, Qt::CheckStateRole });
        break;
    }
    }
}

void TrackListModel::setExternalSelection(std::function<void(const QString &, bool)> selection)
{
    clear();
    m_externalSelection = std::move(selection);
}

void TrackListModel::updateExternalTracks(const QVariantList &tracks, const QString &type)
{
    assert(m_externalSelection);
    QList<Data> incoming;
    for (const auto &value : tracks) {
        const auto track = value.toMap();
        if (track.value(QStringLiteral("type")).toString() != type) continue;
        QStringList labels;
        const QString title = track.value(QStringLiteral("title")).toString();
        const QString external = track.value(QStringLiteral("external-filename")).toString();
        if (!title.isEmpty()) labels.append(title);
        else if (!external.isEmpty()) labels.append(QUrl::fromUserInput(external).fileName());
        const QString language = track.value(QStringLiteral("lang")).toString();
        if (!language.isEmpty()) labels.append(language);
        const QString codec = track.value(QStringLiteral("codec")).toString();
        if (!codec.isEmpty()) labels.append(codec);
        if (labels.isEmpty()) labels.append(tr("Track %1").arg(track.value(QStringLiteral("id")).toLongLong()));
        incoming.append(Data(labels.join(QStringLiteral(" — ")), track.value(QStringLiteral("id")).toString(),
            track.value(QStringLiteral("selected")).toBool()));
    }
    const bool sameTracks = incoming.size() == m_data.size() &&
        std::equal(incoming.cbegin(), incoming.cend(), m_data.cbegin(),
            [](const Data &a, const Data &b) { return a.m_externalId == b.m_externalId; });
    if (!sameTracks) {
        const bool countDiffers = incoming.size() != m_data.size();
        beginResetModel();
        m_data = std::move(incoming);
        endResetModel();
        if (countDiffers) emit countChanged();
        return;
    }
    // MPV reports the whole track list on a selection change. Keep the real
    // delegates/focus alive and notify their changed roles, like VLC's path.
    for (int row = 0; row < incoming.size(); ++row) {
        QList<int> roles;
        if (incoming[row].m_title != m_data[row].m_title) roles.append(Qt::DisplayRole);
        if (incoming[row].m_selected != m_data[row].m_selected) roles.append(Qt::CheckStateRole);
        if (roles.isEmpty()) continue;
        m_data[row] = incoming[row];
        emit dataChanged(index(row), index(row), roles);
    }
}

void TrackListModel::updateTrackSelection(vlc_es_id_t *trackid, bool selected)
{
    if (trackid == NULL)
        return;
    QList<Data>::iterator it = std::find_if(m_data.begin(), m_data.end(), [&](const Data& track) {
        return trackid == track.m_id.get();
    });
    if (it == m_data.end())
        return;
    size_t pos = std::distance(m_data.begin(), it);
    it->m_selected = selected;
    QModelIndex dataIndex = index(pos);
    emit dataChanged(dataIndex, dataIndex, {  Qt::CheckStateRole });
}

void TrackListModel::clear()
{
    m_sourceLabels.clear();
    if (m_data.isEmpty()) return;
    beginRemoveRows({}, 0, m_data.size() - 1);
    m_data.clear();
    endRemoveRows();
    emit countChanged();
}

QHash<int, QByteArray> TrackListModel::roleNames() const
{
    QHash<int, QByteArray> roleNames = this->QAbstractListModel::roleNames();
    roleNames[Qt::CheckStateRole] = QByteArrayLiteral("checked");
    return roleNames;
}

void TrackListModel::setMultiSelect(bool multiSelect)
{
    if (m_multiSelect == multiSelect)
        return;

    m_multiSelect = multiSelect;
    if ( !m_multiSelect && getCount() > 1 )
    {
        int firstSelectedIndex = -1;
        for ( int i = 0; i < getCount(); i++ )
        {
            if ( data( index( i ), Qt::CheckStateRole ).toBool() )
            {
                if (firstSelectedIndex != -1)
                    setData( index(i), false, Qt::CheckStateRole );
                else
                    firstSelectedIndex = i;
            }
        }

        if ( firstSelectedIndex != -1 )
            setData( index(firstSelectedIndex), true, Qt::CheckStateRole );
    }
    emit multiSelectChanged(m_multiSelect);
}

TrackListModel::Data::Data(const vlc_player_track *track_info)
    : m_title( qfu(track_info->name) )
    , m_id( track_info->es_id, true )
    , m_selected( track_info->selected )
{
}

void TrackListModel::Data::update(const vlc_player_track *track_info)
{
    m_id.reset(track_info->es_id, true);
    m_title = qfu(track_info->name);
    m_selected = track_info->selected;
}


//***************************
//  TitleListModel
//***************************


TitleListModel::TitleListModel(vlc_player_t *player, QObject *parent)
    : QAbstractListModel(parent)
    , m_player(player)
{
}

Qt::ItemFlags TitleListModel::flags(const QModelIndex &) const
{
    return Qt::ItemIsUserCheckable;
}

int TitleListModel::rowCount(const QModelIndex &) const
{
    return m_count;
}

QVariant TitleListModel::data(const QModelIndex &index, int role) const
{
    int row = index.row();
    if (row >= m_count)
        return QVariant{};
    const vlc_player_title* title = getTitleAt(row);

    if (role == Qt::DisplayRole)
        return qfu(title->name);
    else if (role == Qt::CheckStateRole)
        return QVariant::fromValue<bool>(row == m_current);
    return QVariant{};
}

bool TitleListModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    int row = index.row();
    if (row < 0 || row >= m_count)
        return false;
    if ( role != Qt::CheckStateRole )
        return false;
    if (!value.canConvert<bool>())
        return false;
    bool select = value.toBool();
    if (select)
    {
        vlc_player_locker lock{ m_player };
        const vlc_player_title* title = getTitleAt(row);
        if (!title)
            return false;
        vlc_player_SelectTitle(m_player, title);
    }
    return true;
}

void TitleListModel::setCurrent(int current)
{
    if (m_count == 0 || m_current == current)
        return;
    int oldCurrent = m_current;
    m_current = current;

    QModelIndex oldIndex = index(oldCurrent);
    QModelIndex currentIndex = index(current);

    if (oldCurrent >= 0)
        emit dataChanged(oldIndex, oldIndex, { Qt::CheckStateRole });
    if ( current >= 0 )
        emit dataChanged(currentIndex, currentIndex, { Qt::CheckStateRole });
}

const vlc_player_title *TitleListModel::getTitleAt(size_t index) const
{
    return vlc_player_title_list_GetAt(m_titleList.get(), index);
}

void TitleListModel::resetTitles(vlc_player_title_list *newTitleList)
{
    beginResetModel();
    m_titleList.reset(newTitleList, true);
    m_current = -1;
    if (m_titleList)
        m_count = vlc_player_title_list_GetCount(m_titleList.get());
    else
        m_count = 0;
    endResetModel();
    emit countChanged();
}

QHash<int, QByteArray> TitleListModel::roleNames() const
{
    QHash<int, QByteArray> roleNames = this->QAbstractListModel::roleNames();
    roleNames[Qt::CheckStateRole] = QByteArrayLiteral("checked");
    return roleNames;
}

//***************************
//  ChapterListModel
//***************************

ChapterListModel::ChapterListModel(vlc_player_t *player, QObject *parent)
    : QAbstractListModel(parent)
    , m_player(player)
{
}

Qt::ItemFlags ChapterListModel::flags(const QModelIndex &) const
{
    return Qt::ItemIsUserCheckable;
}

int ChapterListModel::rowCount(const QModelIndex &) const
{
    return m_title ? m_title->chapter_count : 0;
}

QVariant ChapterListModel::data(const QModelIndex &index, int role) const
{
    int row = index.row();
    if (m_title == nullptr || row < 0 || (size_t)row >= m_title->chapter_count)
        return QVariant{};
    const vlc_player_chapter& chapter = m_title->chapters[row];

    if (role == Qt::DisplayRole)
        return qfu(chapter.name);
    else if (role == Qt::CheckStateRole)
        return QVariant::fromValue<bool>(row == m_current);
    else if (role == ChapterListRoles::TimeRole )
        // Chapters store offsets from the beginning, not absolute VLC clock
        // values. Zero is a valid first chapter and must not lose VLC_TICK_0.
        return QVariant::fromValue<VLCDuration>(chapter.time);
    else if (role == ChapterListRoles::StartPositionRole && (m_title->length != 0))
        return QVariant::fromValue<float>(chapter.time / (float) m_title->length);
    else if (role == ChapterListRoles::EndPositionRole && (m_title->length != 0))
        return (size_t)row + 1 == m_title->chapter_count
                ? QVariant::fromValue<float> (1)
                : QVariant::fromValue<float> (m_title->chapters[row+1].time / (float) m_title->length);

    return QVariant{};
}

bool ChapterListModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    int row = index.row();
    if (m_title == nullptr || (size_t)row >= m_title->chapter_count)
        return false;
    if ( role != Qt::CheckStateRole )
        return false;
    if (!value.canConvert<bool>())
        return false;
    bool select = value.toBool();
    if (select)
    {
        if (m_externalChapterSelect) { m_externalChapterSelect(row); return true; }
        vlc_player_locker lock{ m_player };
        vlc_player_SelectChapter(m_player, m_title, row);
    }
    return true;
}

QHash<int, QByteArray> ChapterListModel::roleNames() const
{
    return QHash<int, QByteArray>{
        {Qt::DisplayRole, QByteArrayLiteral("display")},
        {Qt::CheckStateRole, QByteArrayLiteral("checked")},
        {ChapterListRoles::TimeRole, QByteArrayLiteral("time")},
        {ChapterListRoles::StartPositionRole, QByteArrayLiteral("startPosition")},
        {ChapterListRoles::EndPositionRole, QByteArrayLiteral("endPosition")}
    };
}

void ChapterListModel::setCurrent(int current)
{
    if (m_title == nullptr || m_title->chapter_count == 0 || m_current == current)
        return;
    int oldCurrent = m_current;
    m_current = current;

    QModelIndex oldIndex = index(oldCurrent);
    QModelIndex currentIndex = index(current);

    if (oldCurrent >= 0)
        emit dataChanged(oldIndex, oldIndex, { Qt::CheckStateRole });
    if ( current >= 0 )
        emit dataChanged(currentIndex, currentIndex, { Qt::CheckStateRole });
}

void ChapterListModel::resetTitle(const vlc_player_title *newTitle)
{
    beginResetModel();
    m_externalChapterSelect = {};
    m_title =newTitle;
    m_current = -1;
    endResetModel();
    emit countChanged();
}

void ChapterListModel::updateExternalChapters(const QVariantList &chapters, vlc_tick_t duration,
                                             std::function<void(int)> select)
{
    beginResetModel();
    m_externalChapters.clear(); m_externalChapterNames.clear();
    m_externalChapterSelect = std::move(select);
    for (const auto &entry : chapters) {
        const auto chapter = entry.toMap();
        m_externalChapterNames.append(chapter.value(QStringLiteral("title"),
            tr("Chapter %1").arg(m_externalChapters.size() + 1)).toString().toUtf8());
        m_externalChapters.append({m_externalChapterNames.last().constData(),
            vlc_tick_t(chapter.value(QStringLiteral("time")).toDouble() * CLOCK_FREQ)});
    }
    m_externalTitle = {"", duration, 0, size_t(m_externalChapters.size()), m_externalChapters.constData()};
    m_title = &m_externalTitle;
    m_current = -1;
    endResetModel();
    emit countChanged();
}

void ChapterListModel::selectChapter(int index)
{
    if (!m_title || index < 0 || static_cast<size_t>(index) >= m_title->chapter_count)
        return;
    if (m_externalChapterSelect) { m_externalChapterSelect(index); return; }
    {
        vlc_player_locker lock{ m_player };
        vlc_player_SelectChapter(m_player, m_title, index);
    }
}

QString ChapterListModel::getNameAtPosition(float pos) const
{
    if(m_title != nullptr){

        vlc_tick_t posTime = pos * m_title->length;
        int prevChapterIndex = 0;

        for(unsigned int i=0;i<m_title->chapter_count;i++){

            vlc_tick_t currentChapterTime = m_title->chapters[i].time;

            if(currentChapterTime > posTime)
                return qfu(m_title->chapters[prevChapterIndex].name);

            else if(i == (m_title->chapter_count - 1))
                return qfu(m_title->chapters[i].name);

            prevChapterIndex = i;
        }
    }
    return QString();
}

int ChapterListModel::getClosestChapterFromPos(float pos, float threshold) const
{
    if(m_title == nullptr)
        return -1;

    vlc_tick_t posTime = pos * m_title->length;
    vlc_tick_t closestTime = VLC_TICK_INVALID;
    int chapterIndex = -1;

    for(size_t i=0; i<m_title->chapter_count; i++){

        vlc_tick_t currentChapterTime = m_title->chapters[i].time;
        if (currentChapterTime == VLC_TICK_INVALID)
            continue;
        if (closestTime == VLC_TICK_INVALID
            || qAbs(currentChapterTime - posTime) < qAbs(closestTime - posTime))
        {
            closestTime = currentChapterTime;
            chapterIndex = i;
        }
        else
            break;
    }

    if (closestTime == VLC_TICK_INVALID)
        return -1;
    else
    {
        float chapterPos = closestTime / (float)m_title->length;

        if (qAbs(chapterPos - pos) < threshold)
            return chapterIndex;
        return -1;
    }

}


//***************************
//  ProgramListModel
//***************************


ProgramListModel::ProgramListModel(vlc_player_t *player, QObject *parent)
    : QAbstractListModel(parent)
    , m_player(player)
{
}

Qt::ItemFlags ProgramListModel::flags(const QModelIndex &) const
{
    return Qt::ItemIsUserCheckable;
}

int ProgramListModel::rowCount(const QModelIndex &) const
{
    return m_data.size();
}

QVariant ProgramListModel::data(const QModelIndex &index, int role) const
{
    int row = index.row();
    if (row >= m_data.size())
        return QVariant{};
    if (role == Qt::DisplayRole)
        return m_data[row].m_title;
    else if (role == Qt::CheckStateRole)
        return QVariant::fromValue<bool>(m_data[row].m_selected);
    return QVariant{};
}

bool ProgramListModel::setData(const QModelIndex &index, const QVariant &value, int role)
{
    int row = index.row();
    if (row >= m_data.size())
        return false;
    if ( role != Qt::CheckStateRole )
        return false;
    if (!value.canConvert<bool>())
        return false;
    bool select = value.toBool();
    vlc_player_locker lock{ m_player };

    if (select)
        vlc_player_SelectProgram(m_player, m_data[row].m_id);
    return true;
}

void ProgramListModel::updatePrograms(vlc_player_list_action action, const vlc_player_program *program)
{
    assert(program);
    switch (action) {
    case VLC_PLAYER_LIST_ADDED:
        beginInsertRows({}, m_data.size(), m_data.size());
        m_data.append(Data{ program });
        endInsertRows();
        emit countChanged();
        break;

    case VLC_PLAYER_LIST_REMOVED:
    {
        auto it = std::find_if(m_data.begin(), m_data.end(), [&](const Data& t) {
            return t.m_id == program->group_id;
        });
        if (it == m_data.end())
            return;
        int pos = std::distance(m_data.begin(), it);
        beginRemoveRows({}, pos, pos);
        m_data.erase(it);
        endRemoveRows();
        emit countChanged();
        break;
    }
    case VLC_PLAYER_LIST_UPDATED:
    {
        int pos = 0;
        bool found = false;
        for (Data& d : m_data)
        {
            if (d.m_id == program->group_id)
            {
                d.update(program);
                found = true;
                break;
            }
            pos++;
        }
        if (!found)
            return;
        QModelIndex dataIndex = index(pos);
        emit dataChanged(dataIndex, dataIndex, { Qt::DisplayRole, Qt::CheckStateRole });
        break;
    }
    }
}

void ProgramListModel::updateProgramSelection(int programid, bool selected)
{
    QList<Data>::iterator it = std::find_if(m_data.begin(), m_data.end(), [&](const Data& program) {
        return programid == program.m_id;
    });
    if (it == m_data.end())
        return;
    size_t pos = std::distance(m_data.begin(), it);
    it->m_selected = selected;
    QModelIndex dataIndex = index(pos);
    emit dataChanged(dataIndex, dataIndex, {  Qt::CheckStateRole });
}

void ProgramListModel::clear()
{
    beginRemoveRows({}, 0, m_data.size() - 1);
    m_data.clear();
    endRemoveRows();
}

QHash<int, QByteArray> ProgramListModel::roleNames() const
{
    QHash<int, QByteArray> roleNames = this->QAbstractListModel::roleNames();
    roleNames[Qt::CheckStateRole] = QByteArrayLiteral("checked");
    return roleNames;
}

ProgramListModel::Data::Data(const vlc_player_program *program)
    : m_title(qfu(program->name))
    , m_id( program->group_id )
    , m_selected( program->selected )
    , m_scrambled( program->scrambled )
{
    assert(program);
}

void ProgramListModel::Data::update(const vlc_player_program *program)
{
    assert(program);
    m_title = qfu(program->name);
    m_id = program->group_id;
    m_selected = program->selected;
    m_scrambled = program->scrambled;
}

