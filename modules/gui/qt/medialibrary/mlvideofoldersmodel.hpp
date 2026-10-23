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

#ifndef MLVIDEOFOLDERSMODEL_HPP
#define MLVIDEOFOLDERSMODEL_HPP

// MediaLibrary includes
#include "mlvideomodel.hpp"

// Forward declarations
class MLFolder;

class MLVideoFoldersModel : public MLBaseModel
{
    Q_OBJECT
    Q_PROPERTY(bool hierarchical READ hierarchical WRITE setHierarchical NOTIFY hierarchicalChanged FINAL)
    Q_PROPERTY(bool frequentOnly READ frequentOnly WRITE setFrequentOnly NOTIFY frequentOnlyChanged FINAL)

public:
    enum Roles
    {
        FOLDER_ID = Qt::UserRole + 1,
        FOLDER_TITLE,
        FOLDER_TITLE_FIRST_SYMBOL,
        FOLDER_THUMBNAIL,
        FOLDER_DURATION,
        FOLDER_COUNT,
        FOLDER_MRL,
        FOLDER_NB_VIDEOS
    };

public:
    explicit MLVideoFoldersModel(QObject * parent = nullptr);

    bool hierarchical() const { return m_hierarchical; }
    void setHierarchical(bool value);
    bool frequentOnly() const { return m_frequentOnly; }
    void setFrequentOnly(bool value);
signals:
    void hierarchicalChanged();
    void frequentOnlyChanged();
public:
    Q_INVOKABLE void resolveAddress(const QUrl& url, QJSValue callback);

public: // MLBaseModel reimplementation
    QHash<int, QByteArray> roleNames() const override;

protected:
    QVariant itemRoleData(const MLItem *item, int role = Qt::DisplayRole) const override;

    vlc_ml_sorting_criteria_t nameToCriteria(QByteArray name) const override;

    std::unique_ptr<MLListCacheLoader> createMLLoader() const override;

protected: // MLBaseModel reimplementation
    void onVlcMlEvent(const MLEvent & event) override;

private:
    bool m_hierarchical = false;
    bool m_frequentOnly = false;
    struct Loader : public MLListCacheLoader::MLOp
    {
        explicit Loader(const MLVideoFoldersModel& model) : MLOp(model), m_hierarchical(model.hierarchical()), m_frequentOnly(model.frequentOnly()) {}
        const bool m_hierarchical;
        const bool m_frequentOnly;
        std::vector<std::unique_ptr<MLItem>> frequentFolders(vlc_medialibrary_t* ml) const;
        std::vector<std::unique_ptr<MLItem>> hierarchicalFolders(vlc_medialibrary_t* ml, const vlc_ml_query_params_t* queryParams) const;
        size_t count(vlc_medialibrary_t * ml, const vlc_ml_query_params_t* queryParams) const override;

        std::vector<std::unique_ptr<MLItem>> load(vlc_medialibrary_t * ml,
                                                  const vlc_ml_query_params_t* queryParams) const override;

        std::unique_ptr<MLItem> loadItemById(vlc_medialibrary_t* ml, MLItemId itemId) const override;
    };
};

#endif // MLVIDEOFOLDERSMODEL_HPP
