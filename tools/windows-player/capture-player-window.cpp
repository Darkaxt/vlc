// SPDX-License-Identifier: GPL-2.0-or-later
// One SDR frame from the recorded VLC HWND/PID/executable, without a picker,
// desktop capture, window activation or OS input. Build with the Windows SDK.
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <wincodec.h>
#include <windows.graphics.capture.interop.h>
#include <windows.graphics.directx.direct3d11.interop.h>
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.Graphics.Capture.h>
#include <winrt/Windows.Graphics.DirectX.Direct3D11.h>
#include <winrt/Windows.Graphics.DirectX.h>
#include <iostream>
#include <memory>
#include <mutex>

using namespace winrt;
using namespace winrt::Windows::Graphics::Capture;

struct FrameState
{
    std::mutex mutex;
    Direct3D11CaptureFrame frame{nullptr};
    handle ready{CreateEventW(nullptr, TRUE, FALSE, nullptr)};
    bool received = false;
};

int wmain(int argc, wchar_t **argv)
{
    if (argc != 5)
    {
        std::wcerr << L"Usage: capture-player-window PID HWND_HEX EXPECTED_EXE OUTPUT_PNG\n";
        return 2;
    }
    try
    {
        init_apartment(apartment_type::multi_threaded);
        const DWORD expected = wcstoul(argv[1], nullptr, 10);
        const HWND window = reinterpret_cast<HWND>(wcstoull(argv[2], nullptr, 16));
        DWORD actual = 0;
        GetWindowThreadProcessId(window, &actual);
        if (!expected || actual != expected)
            throw hresult_error(E_INVALIDARG, L"Owned window/PID mismatch");

        handle process{OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, FALSE, expected)};
        if (!process) throw_last_error();
        wchar_t executable[32768];
        DWORD executableLength = 32768;
        check_bool(QueryFullProcessImageNameW(process.get(), 0, executable, &executableLength));
        if (_wcsicmp(executable, argv[3]) != 0)
            throw hresult_error(E_INVALIDARG, L"Owned executable identity mismatch");

        auto factory = get_activation_factory<GraphicsCaptureItem, IGraphicsCaptureItemInterop>();
        GraphicsCaptureItem item{nullptr};
        check_hresult(factory->CreateForWindow(window, guid_of<GraphicsCaptureItem>(), put_abi(item)));
        com_ptr<ID3D11Device> device;
        com_ptr<ID3D11DeviceContext> context;
        check_hresult(D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr,
            D3D11_CREATE_DEVICE_BGRA_SUPPORT, nullptr, 0, D3D11_SDK_VERSION,
            device.put(), nullptr, context.put()));
        auto dxgi = device.as<IDXGIDevice>();
        com_ptr<IInspectable> inspectable;
        check_hresult(CreateDirect3D11DeviceFromDXGIDevice(dxgi.get(), inspectable.put()));
        auto pool = Direct3D11CaptureFramePool::CreateFreeThreaded(
            inspectable.as<winrt::Windows::Graphics::DirectX::Direct3D11::IDirect3DDevice>(),
            winrt::Windows::Graphics::DirectX::DirectXPixelFormat::B8G8R8A8UIntNormalized,
            2, item.Size());
        auto capture = pool.CreateCaptureSession(item);
        capture.IsCursorCaptureEnabled(false);
        auto state = std::make_shared<FrameState>();
        if (!state->ready) throw_last_error();
        // Shared callback state survives any in-flight handler during revocation.
        auto revoker = pool.FrameArrived(auto_revoke, [state](auto const &sender, auto const &) {
            std::lock_guard<std::mutex> guard(state->mutex);
            if (state->received) return;
            state->frame = sender.TryGetNextFrame();
            if (!state->frame) return;
            state->received = true;
            SetEvent(state->ready.get());
        });
        capture.StartCapture();
        HANDLE handles[]{state->ready.get(), process.get()};
        const DWORD outcome = WaitForMultipleObjects(2, handles, FALSE, INFINITE);
        revoker.revoke();
        capture.Close();
        if (outcome == WAIT_FAILED) throw_last_error();
        if (outcome != WAIT_OBJECT_0)
            throw hresult_error(E_ABORT, L"Owned process ended before a capture frame");

        std::lock_guard<std::mutex> guard(state->mutex);
        auto access = state->frame.Surface().as<
            ::Windows::Graphics::DirectX::Direct3D11::IDirect3DDxgiInterfaceAccess>();
        com_ptr<ID3D11Texture2D> texture;
        check_hresult(access->GetInterface(__uuidof(ID3D11Texture2D), texture.put_void()));
        D3D11_TEXTURE2D_DESC desc;
        texture->GetDesc(&desc);
        const auto size = state->frame.ContentSize();
        if (size.Width <= 0 || size.Height <= 0
            || unsigned(size.Width) > desc.Width || unsigned(size.Height) > desc.Height)
            throw hresult_error(E_INVALIDARG, L"Capture resized outside the original frame");
        desc.Usage = D3D11_USAGE_STAGING;
        desc.BindFlags = 0;
        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        desc.MiscFlags = 0;
        com_ptr<ID3D11Texture2D> staging;
        check_hresult(device->CreateTexture2D(&desc, nullptr, staging.put()));
        context->CopyResource(staging.get(), texture.get());
        D3D11_MAPPED_SUBRESOURCE mapped;
        check_hresult(context->Map(staging.get(), 0, D3D11_MAP_READ, 0, &mapped));

        com_ptr<IWICImagingFactory> wic;
        check_hresult(CoCreateInstance(CLSID_WICImagingFactory, nullptr, CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(wic.put())));
        com_ptr<IWICStream> stream;
        check_hresult(wic->CreateStream(stream.put()));
        check_hresult(stream->InitializeFromFilename(argv[4], GENERIC_WRITE));
        com_ptr<IWICBitmapEncoder> encoder;
        check_hresult(wic->CreateEncoder(GUID_ContainerFormatPng, nullptr, encoder.put()));
        check_hresult(encoder->Initialize(stream.get(), WICBitmapEncoderNoCache));
        com_ptr<IWICBitmapFrameEncode> output;
        check_hresult(encoder->CreateNewFrame(output.put(), nullptr));
        check_hresult(output->Initialize(nullptr));
        check_hresult(output->SetSize(size.Width, size.Height));
        WICPixelFormatGUID format = GUID_WICPixelFormat32bppBGRA;
        check_hresult(output->SetPixelFormat(&format));
        check_hresult(output->WritePixels(size.Height, mapped.RowPitch,
            mapped.RowPitch * size.Height, static_cast<BYTE *>(mapped.pData)));
        check_hresult(output->Commit());
        check_hresult(encoder->Commit());
        context->Unmap(staging.get(), 0);
        state->frame.Close();
        pool.Close();
        std::wcout << L"Owned window capture " << size.Width << L" x " << size.Height << L"\n";
        return 0;
    }
    catch (hresult_error const &error)
    {
        std::wcerr << L"Capture HRESULT " << std::hex << error.code().value
                   << L": " << error.message().c_str() << L"\n";
        return 1;
    }
}
