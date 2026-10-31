// SPDX-License-Identifier: GPL-2.0-or-later
// Read-only Windows-reported active display/color capabilities. No mode change.
#include <windows.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <iomanip>
#include <iostream>
#include <vector>

int main()
{
    using Microsoft::WRL::ComPtr;
    ComPtr<IDXGIFactory1> factory;
    HRESULT hr = CreateDXGIFactory1(IID_PPV_ARGS(&factory));
    if (FAILED(hr)) return 2;
    std::cout << "{\"schema\":\"vlc_redesign.windows_display.v1\",\"scope\":\"Windows-reported capabilities; no physical luminance or Dolby Vision signaling claim\",\"outputs\":[";
    bool first = true;
    for (UINT adapterIndex = 0;; ++adapterIndex) {
        ComPtr<IDXGIAdapter1> adapter;
        hr = factory->EnumAdapters1(adapterIndex, &adapter);
        if (hr == DXGI_ERROR_NOT_FOUND) break;
        if (FAILED(hr)) return 3;
        for (UINT outputIndex = 0;; ++outputIndex) {
            ComPtr<IDXGIOutput> output;
            hr = adapter->EnumOutputs(outputIndex, &output);
            if (hr == DXGI_ERROR_NOT_FOUND) break;
            if (FAILED(hr)) return 4;
            ComPtr<IDXGIOutput6> advanced;
            DXGI_OUTPUT_DESC1 desc{};
            if (FAILED(output.As(&advanced)) || FAILED(advanced->GetDesc1(&desc))) return 5;
            if (!desc.AttachedToDesktop) continue;
            char name[128]{};
            if (!WideCharToMultiByte(CP_UTF8, 0, desc.DeviceName, -1, name, sizeof(name), nullptr, nullptr)) return 6;
            if (!first) std::cout << ',';
            first = false;
            std::cout << "{\"device\":" << std::quoted(name)
                << ",\"bits_per_color\":" << desc.BitsPerColor
                << ",\"dxgi_color_space\":" << int(desc.ColorSpace)
                << ",\"current_hdr_colorspace\":" << (desc.ColorSpace == DXGI_COLOR_SPACE_RGB_FULL_G2084_NONE_P2020 ? "true" : "false")
                << ",\"reported_min_luminance\":" << desc.MinLuminance
                << ",\"reported_max_luminance\":" << desc.MaxLuminance
                << ",\"reported_max_full_frame_luminance\":" << desc.MaxFullFrameLuminance << '}';
        }
    }
    std::cout << "],\"active_color_targets\":[";
    std::vector<DISPLAYCONFIG_PATH_INFO> paths;
    std::vector<DISPLAYCONFIG_MODE_INFO> modes;
    LONG code;
    do {
        UINT pathCount = 0, modeCount = 0;
        code = GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, &pathCount, &modeCount);
        if (code != ERROR_SUCCESS) return 7;
        paths.resize(pathCount); modes.resize(modeCount);
        code = QueryDisplayConfig(QDC_ONLY_ACTIVE_PATHS, &pathCount, paths.data(), &modeCount, modes.data(), nullptr);
        paths.resize(pathCount);
    } while (code == ERROR_INSUFFICIENT_BUFFER); // Documented display-change race at the API boundary.
    if (code != ERROR_SUCCESS) return 8;
    first = true;
    for (const auto &path : paths) {
        DISPLAYCONFIG_GET_ADVANCED_COLOR_INFO info{};
        info.header.type = DISPLAYCONFIG_DEVICE_INFO_GET_ADVANCED_COLOR_INFO;
        info.header.size = sizeof(info);
        info.header.adapterId = path.targetInfo.adapterId;
        info.header.id = path.targetInfo.id;
        const LONG status = DisplayConfigGetDeviceInfo(&info.header);
        if (!first) std::cout << ',';
        first = false;
        std::cout << "{\"target_id\":" << path.targetInfo.id << ",\"query_status\":" << status;
        if (status == ERROR_SUCCESS)
            std::cout << ",\"advanced_color_supported\":" << (info.advancedColorSupported ? "true" : "false")
                << ",\"advanced_color_enabled\":" << (info.advancedColorEnabled ? "true" : "false")
                << ",\"bits_per_channel\":" << info.bitsPerColorChannel;
        std::cout << '}';
    }
    std::cout << "]}\n";
    return 0;
}
