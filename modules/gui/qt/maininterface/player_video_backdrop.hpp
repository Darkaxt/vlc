// SPDX-License-Identifier: GPL-2.0-or-later
#ifndef VLC_PLAYER_VIDEO_BACKDROP_HPP
#define VLC_PLAYER_VIDEO_BACKDROP_HPP

#include <dcomp.h>
#include <wrl.h>
#include <QQuickItem>
#include <QPointer>
#include <QMutex>
#include <QVariantList>
#include <array>
#include <atomic>

namespace vlc {

// The vout's existing SetContent call supplies the same decoded swapchain to
// three clipped video copies. Only system-created visuals enter the DComp tree;
// this forwarding interface is exclusively the vout window's content handle.
// No second decoder, screen capture, desktop backdrop or CPU readback is used.
class PlayerVideoBackdrop final : public IDCompositionVisual
{
    std::atomic<ULONG> m_references{1};
    template<class T> using ComPtr = Microsoft::WRL::ComPtr<T>;
    struct Region {
        ComPtr<IDCompositionVisual> clipVisual, video;
        ComPtr<IDCompositionRectangleClip> clip;
        ComPtr<IDCompositionGaussianBlurEffect> blur;
        QRectF rect;
        float radius = -1, sigma = -1;
        bool visible = false;
    };
    ComPtr<IDCompositionDevice> m_device;
    ComPtr<IDCompositionVisual> m_source, m_root;
    std::array<Region, 3> m_regions;
    QMutex m_lock;
    QPointF m_videoPosition;
    bool m_content = false, m_enabled = false;
    HRESULT m_error = S_OK;

    HRESULT check(HRESULT result) { if (FAILED(result)) m_error = result; return result; }

public:
    IDCompositionVisual *bottomVisual() const { return m_regions.front().clipVisual.Get(); }

    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **object) override
    {
        if (!object) return E_POINTER;
        *object = nullptr;
        // The pinned MinGW header declares this interface but omits uuidof.
        static constexpr GUID visualId{0x4d93059d, 0x097b, 0x4651,
            {0x9a, 0x60, 0xf0, 0xf2, 0x51, 0x16, 0xe2, 0xf3}};
        if (IsEqualIID(iid, IID_IUnknown) || IsEqualIID(iid, visualId)) {
            *object = static_cast<IDCompositionVisual *>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }
    ULONG STDMETHODCALLTYPE AddRef() override { return ++m_references; }
    ULONG STDMETHODCALLTYPE Release() override
    {
        const auto remaining = --m_references;
        if (!remaining) delete this;
        return remaining;
    }

    HRESULT initialize(IDCompositionDevice *device, IDCompositionVisual *source,
                       IDCompositionVisual *root, IDCompositionVisual *ui)
    {
        m_device = device; m_source = source; m_root = root;
        ComPtr<IDCompositionDevice3> effects;
        HRESULT hr = device->QueryInterface(IID_PPV_ARGS(&effects));
        if (FAILED(hr)) return hr;
        for (auto &region : m_regions) {
            if (FAILED(hr = device->CreateVisual(&region.clipVisual)) ||
                FAILED(hr = device->CreateVisual(&region.video)) ||
                FAILED(hr = device->CreateRectangleClip(&region.clip)) ||
                // DComp defaults to +/-2^21, not a zero-origin empty clip.
                FAILED(hr = region.clip->SetLeft(0.f)) ||
                FAILED(hr = region.clip->SetTop(0.f)) ||
                FAILED(hr = region.clip->SetRight(0.f)) ||
                FAILED(hr = region.clip->SetBottom(0.f)) ||
                FAILED(hr = effects->CreateGaussianBlurEffect(&region.blur)) ||
                FAILED(hr = region.video->SetEffect(region.blur.Get())) ||
                FAILED(hr = region.blur->SetBorderMode(D2D1_BORDER_MODE_HARD)) ||
                FAILED(hr = region.clipVisual->SetClip(region.clip.Get())) ||
                FAILED(hr = region.clipVisual->AddVisual(region.video.Get(), FALSE, nullptr)) ||
                FAILED(hr = root->AddVisual(region.clipVisual.Get(), FALSE, ui)))
                return hr;
        }
        return S_OK;
    }

    ~PlayerVideoBackdrop()
    {
        for (auto &region : m_regions)
            if (region.clipVisual) m_root->RemoveVisual(region.clipVisual.Get());
    }

    void setEnabled(bool enabled)
    {
        QMutexLocker lock(&m_lock);
        m_enabled = enabled;
        if (!enabled) for (auto &region : m_regions) {
            check(region.clip->SetRight(0.f));
            check(region.clip->SetBottom(0.f));
            region.visible = false;
        }
    }

    void setVideoPosition(const QPointF &position)
    {
        QMutexLocker lock(&m_lock);
        m_videoPosition = position;
        for (auto &region : m_regions) {
            check(region.video->SetOffsetX(float(position.x() - region.rect.x())));
            check(region.video->SetOffsetY(float(position.y() - region.rect.y())));
        }
    }

    // Called at beforeSynchronizing, while Qt blocks its GUI thread. QML owns
    // these background rectangles and supplies their real transformed geometry.
    QVariantMap synchronize(QQuickItem *root, qreal dpr)
    {
        const auto items = root->findChildren<QQuickItem *>(QStringLiteral("playerVideoBackdrop"));
        QMutexLocker lock(&m_lock);
#ifdef VLC_PLAYER_DIAGNOSTICS
        QVariantList regions;
#endif
        bool changed = false;
        for (size_t i = 0; i < m_regions.size(); ++i) {
            auto &region = m_regions[i];
            auto item = i < size_t(items.size()) ? items[qsizetype(i)] : nullptr;
            QRectF rect;
            float radius = 0, sigma = 0;
            const bool visible = m_enabled && m_content && item && item->isVisible()
                                 && item->opacity() > 0 && item->width() > 0 && item->height() > 0;
            if (visible) {
                const auto logical = item->mapRectToScene(item->boundingRect());
                rect = QRectF(logical.topLeft() * dpr, logical.size() * dpr);
                radius = item->property("radius").toFloat() * dpr;
                // Figma/Dev Mode's radius maps to CSS blur (Gaussian sigma) / 2.
                sigma = item->property("backgroundBlurRadius").toFloat() * dpr / 2.f;
            }
            if (rect != region.rect || visible != region.visible || radius != region.radius || sigma != region.sigma) {
                check(region.clipVisual->SetOffsetX(float(rect.x())));
                check(region.clipVisual->SetOffsetY(float(rect.y())));
                check(region.clip->SetRight(float(rect.width())));
                check(region.clip->SetBottom(float(rect.height())));
                check(region.clip->SetTopLeftRadiusX(radius)); check(region.clip->SetTopLeftRadiusY(radius));
                check(region.clip->SetTopRightRadiusX(radius)); check(region.clip->SetTopRightRadiusY(radius));
                check(region.clip->SetBottomLeftRadiusX(radius)); check(region.clip->SetBottomLeftRadiusY(radius));
                check(region.clip->SetBottomRightRadiusX(radius)); check(region.clip->SetBottomRightRadiusY(radius));
                check(region.blur->SetStandardDeviation(sigma));
                check(region.video->SetOffsetX(float(m_videoPosition.x() - rect.x())));
                check(region.video->SetOffsetY(float(m_videoPosition.y() - rect.y())));
                region.rect = rect; region.radius = radius; region.sigma = sigma; region.visible = visible;
                changed = true;
            }
#ifdef VLC_PLAYER_DIAGNOSTICS
            regions.append(QVariantMap{{QStringLiteral("visible"), visible},
                {QStringLiteral("rect_px"), QVariantMap{{QStringLiteral("x"), rect.x()}, {QStringLiteral("y"), rect.y()},
                    {QStringLiteral("width"), rect.width()}, {QStringLiteral("height"), rect.height()}}},
                {QStringLiteral("sigma_px"), sigma}, {QStringLiteral("corner_radius_px"), radius}});
#endif
        }
        if (changed) check(m_device->Commit());
#ifdef VLC_PLAYER_DIAGNOSTICS
        return {{QStringLiteral("video_content"), m_content}, {QStringLiteral("enabled"), m_enabled},
                {QStringLiteral("hresult"), quint32(m_error)}, {QStringLiteral("regions"), regions}};
#else
        return {};
#endif
    }

    HRESULT STDMETHODCALLTYPE SetContent(IUnknown *content) override
    {
        QMutexLocker lock(&m_lock);
        HRESULT result = m_source->SetContent(content);
        if (FAILED(result)) return result;
        for (auto &region : m_regions) check(region.video->SetContent(content));
        m_content = content != nullptr;
        return result;
    }

    HRESULT STDMETHODCALLTYPE SetOffsetX(float v) override { return m_source->SetOffsetX(v); }
    HRESULT STDMETHODCALLTYPE SetOffsetX(IDCompositionAnimation *v) override { return m_source->SetOffsetX(v); }
    HRESULT STDMETHODCALLTYPE SetOffsetY(float v) override { return m_source->SetOffsetY(v); }
    HRESULT STDMETHODCALLTYPE SetOffsetY(IDCompositionAnimation *v) override { return m_source->SetOffsetY(v); }
    HRESULT STDMETHODCALLTYPE SetTransform(const D2D_MATRIX_3X2_F &v) override { return m_source->SetTransform(v); }
    HRESULT STDMETHODCALLTYPE SetTransform(IDCompositionTransform *v) override { return m_source->SetTransform(v); }
    HRESULT STDMETHODCALLTYPE SetTransformParent(IDCompositionVisual *v) override { return m_source->SetTransformParent(v); }
    HRESULT STDMETHODCALLTYPE SetEffect(IDCompositionEffect *v) override { return m_source->SetEffect(v); }
    HRESULT STDMETHODCALLTYPE SetBitmapInterpolationMode(DCOMPOSITION_BITMAP_INTERPOLATION_MODE v) override { return m_source->SetBitmapInterpolationMode(v); }
    HRESULT STDMETHODCALLTYPE SetBorderMode(DCOMPOSITION_BORDER_MODE v) override { return m_source->SetBorderMode(v); }
    HRESULT STDMETHODCALLTYPE SetClip(const D2D_RECT_F &v) override { return m_source->SetClip(v); }
    HRESULT STDMETHODCALLTYPE SetClip(IDCompositionClip *v) override { return m_source->SetClip(v); }
    HRESULT STDMETHODCALLTYPE AddVisual(IDCompositionVisual *v, BOOL above, IDCompositionVisual *reference) override { return m_source->AddVisual(v, above, reference); }
    HRESULT STDMETHODCALLTYPE RemoveVisual(IDCompositionVisual *v) override { return m_source->RemoveVisual(v); }
    HRESULT STDMETHODCALLTYPE RemoveAllVisuals() override { return m_source->RemoveAllVisuals(); }
    HRESULT STDMETHODCALLTYPE SetCompositeMode(DCOMPOSITION_COMPOSITE_MODE v) override { return m_source->SetCompositeMode(v); }
};
}
#endif
