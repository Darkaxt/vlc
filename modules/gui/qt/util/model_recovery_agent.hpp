/*****************************************************************************
 * Copyright (C) 2024 VLC authors and VideoLAN
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

#ifndef MODEL_RECOVERY_AGENT_HPP
#define MODEL_RECOVERY_AGENT_HPP

#include <QFile>
#include <QTimer>
#include <QSettings>
#include <QPointer>
#include <QFileInfo>
#include <QMessageBox>
#include <QTemporaryFile>
#include <QAbstractItemModel>
#include <QLockFile>
#include <QUrl>

#include <cstdio>

#include "qt.hpp"

#include "widgets/native/qvlcframe.hpp"
#include "widgets/native/redesign_style.hpp"

class ModelRecoveryAgent
{
    const QPointer<QSettings> m_settings;
    const QString m_key;
    QString m_recoveryFileName;
    QTimer m_timer;
    bool m_conditionDismissInitialDirtiness = false;
    std::unique_ptr<QLockFile> m_lockFile;
    std::unique_ptr<QMessageBox> m_recoveryQuestion;
    bool m_recoveryPending = false;

public:
    // NOTE: settings and model must outlive the instance of this class.
    template<class T>
    ModelRecoveryAgent(class QSettings *settings, const QString& modelIdentifier, T* model, qt_intf_t *intf)
        : m_settings(settings), m_key(modelIdentifier + QStringLiteral("/RecoveryFilePath"))
    {
        assert(settings);
        assert(model);
        QString recoveryPrompt;
        settings->sync();
        if (settings->contains(m_key))
        {
            assert(settings->value(m_key).typeId() == QMetaType::QString);
            QString recoveryFileName = settings->value(m_key).toString();
            if (!recoveryFileName.isEmpty())
            {
                m_recoveryFileName = std::move(recoveryFileName);
                {
                    m_lockFile = std::make_unique<QLockFile>(m_recoveryFileName + QStringLiteral(".lock"));
                    m_lockFile->setStaleLockTime(0); // if the process crashed, QLockFile considers the lock stale regardless of the lock time
                    if (!m_lockFile->tryLock()) // if the older instance is still alive, it would have the lock
                        throw std::exception(); // Older instance is managing the recovery, don't take over. We don't support recovering multiple models at the moment.
                }
                const QFileInfo fileInfo(m_recoveryFileName);
                if (fileInfo.size() > 0)
                {
                    recoveryPrompt = qtr("Do you want to restore the %1 model from %2?")
                        .arg(modelIdentifier.toLower(), fileInfo.lastModified().toString());
                    m_recoveryPending = true;
                }
            }
        }

        if (m_recoveryFileName.isEmpty())
        {
            QTemporaryFile temporaryFile;
            temporaryFile.setAutoRemove(false);
            if (!temporaryFile.open())
                throw std::exception();
            m_recoveryFileName = temporaryFile.fileName();
            {
                assert(!m_lockFile);
                m_lockFile = std::make_unique<QLockFile>(m_recoveryFileName + QStringLiteral(".lock"));
                m_lockFile->setStaleLockTime(0); // if the process crashed, QLockFile considers the lock stale regardless of the lock time
                assert(!m_lockFile->isLocked()); // the file name is new here, it can not be locked before
                if (!m_lockFile->tryLock())
                    throw std::exception();
            }
            settings->setValue(m_key, m_recoveryFileName);
            settings->sync();
        }

        m_timer.setInterval(10000); // 10 seconds
        m_timer.setSingleShot(true);

        QObject::connect(&m_timer, &QTimer::timeout, model, [this, model]() {
            // Do not overwrite a crashed queue before its owner decides.
            if (m_recoveryPending) return;
            if (m_conditionDismissInitialDirtiness)
            {
                m_conditionDismissInitialDirtiness = false;
                return;
            }

            assert(!m_recoveryFileName.isEmpty());

            const QByteArray tmpFileName = (m_recoveryFileName + QStringLiteral(".part")).toLatin1();
            const QByteArray recoveryFileName = m_recoveryFileName.toLatin1();

            if (model->isEmpty())
            {
                remove(recoveryFileName.constData());
                return;
            }

            if (model->serialize(tmpFileName.constData()) != VLC_SUCCESS)
                return;

            remove(recoveryFileName.constData());
            if (!rename(tmpFileName.constData(), recoveryFileName.constData()))
            {
                assert(m_settings);
                m_settings->sync();
                if (!m_settings->contains(m_key))
                {
                    m_settings->setValue(m_key, m_recoveryFileName);
                    m_settings->sync();
                }
                else if (m_settings->value(m_key) != m_recoveryFileName)
                {
                    QObject::disconnect(model, nullptr, &m_timer, nullptr);
                    m_timer.stop();
                }
            }
        });

        QObject::connect(model, &T::itemsReset, &m_timer, QOverload<>::of(&QTimer::start));
        QObject::connect(model, &T::itemsAdded, &m_timer, QOverload<>::of(&QTimer::start));
        QObject::connect(model, &T::itemsMoved, &m_timer, QOverload<>::of(&QTimer::start));
        QObject::connect(model, &T::itemsRemoved, &m_timer, QOverload<>::of(&QTimer::start));
        QObject::connect(model, &T::itemsUpdated, &m_timer, QOverload<>::of(&QTimer::start));
        if (m_recoveryPending)
        {
            m_recoveryQuestion = std::make_unique<QMessageBox>(QMessageBox::Question,
                qtr("The application closed abruptly."), recoveryPrompt,
                QMessageBox::Yes | QMessageBox::No);
            m_recoveryQuestion->setObjectName(QStringLiteral("modelRecoveryQuestion"));
            m_recoveryQuestion->setDefaultButton(QMessageBox::Yes);
            applyRedesignDialogStyle(m_recoveryQuestion.get(), intf);
            QVLCDialog::setWindowTransientParent(m_recoveryQuestion.get(), nullptr, intf);
            QObject::connect(m_recoveryQuestion.get(), &QDialog::finished, &m_timer,
                [this, guardedModel = QPointer<T>(model)](int result) {
                    if (!guardedModel || (result != QMessageBox::Yes && result != QMessageBox::No))
                        return;
                    m_recoveryPending = false;
                    if (result == QMessageBox::Yes)
                    {
                        m_conditionDismissInitialDirtiness = true;
                        guardedModel->append(QVariant::fromValue(QUrl::fromLocalFile(m_recoveryFileName)));
                    }
                });
            // Construct the agent completely before returning to the event
            // loop. A modal exec() here can resume after its model is gone.
            m_recoveryQuestion->setModal(true);
            m_recoveryQuestion->show();
        }

    }

    ~ModelRecoveryAgent()
    {
        if (m_recoveryQuestion)
        {
            QObject::disconnect(m_recoveryQuestion.get(), nullptr, &m_timer, nullptr);
            m_recoveryQuestion.reset();
        }
        // Closing VLC without answering is not consent to discard recovery.
        if (m_recoveryPending) return;
        if (!m_recoveryFileName.isEmpty())
        {
            QFile::remove(m_recoveryFileName);
        }

        assert(m_settings);

        m_settings->sync();

        if (m_settings->value(m_key) == m_recoveryFileName)
        {
            m_settings->remove(m_key);
            m_settings->sync();
        }
    }
};

#endif // MODEL_RECOVERY_AGENT_HPP
