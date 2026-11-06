// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once
#include <algorithm>
#include <array>
#include <climits>
#include <cmath>
#include <cstdint>
#include <memory>
extern "C" {
#include "../../../visualization/visual/fft.h"
}

namespace AudioVisualization {
constexpr size_t SampleCount=FFT_BUFFER_SIZE;
using Frame=std::array<float,SampleCount>;
using Spectrum=std::array<float,SampleCount/2+1>;

// A bounded observer of the existing PCM stream. Audio buffers remain const.
class Capture {
public:
    void reset() { m_samples.fill(0); m_cursor=0; m_count=0; }
    bool ready() const { return m_count==SampleCount; }
    void append(const float *pcm,size_t frames,unsigned channels) {
        if(!pcm || !frames || !channels || channels>64)return;
        // Only the newest display frame is needed, even for a large PCM block.
        if(frames>SampleCount) { pcm+=(frames-SampleCount)*channels;frames=SampleCount; }
        // Keep a real audible channel, rather than phase-cancelling stereo or
        // dropping center/right-only content in multichannel sources.
        unsigned selected=0;
        double strongest=-1;
        for(unsigned c=0;c<channels;++c) {
            double energy=0;
            for(size_t i=0;i<frames;++i) { const float f=sample(pcm[i*channels+c]); energy+=double(f)*f; }
            if(energy>strongest) { strongest=energy; selected=c; }
        }
        for(size_t i=0;i<frames;++i) {
            m_samples[m_cursor]=sample(pcm[i*channels+selected]);
            m_cursor=(m_cursor+1)%SampleCount;
            m_count=std::min(SampleCount,m_count+1);
        }
    }
    Frame frame() const {
        Frame result{};
        if(ready())for(size_t i=0;i<SampleCount;++i)result[i]=m_samples[(m_cursor+i)%SampleCount];
        return result;
    }
private:
    static float sample(float f) { return std::isfinite(f)?std::clamp(f,-1.f,1.f):0; }
    Frame m_samples{};
    size_t m_cursor=0,m_count=0;
};

class Transform {
public:
    Transform():m_fft(visual_fft_init(),fft_close) {}
    bool valid() const { return bool(m_fft); }
    Spectrum spectrum(const Frame &frame) {
        Spectrum result{};
        if(!valid())return result;
        std::array<sound_sample,SampleCount> input{};
        for(size_t i=0;i<SampleCount;++i) {
            const double window=0.5-0.5*std::cos(2*3.14159265358979323846*i/(SampleCount-1));
            input[i]=sound_sample(std::lround(std::clamp(frame[i],-1.f,1.f)*INT16_MAX*window));
        }
        fft_perform(input.data(),result.data(),m_fft.get());
        // Correct the Hann window's coherent gain, retaining silence as zero.
        for(float &f:result)f=std::clamp(float(std::sqrt(std::max(0.f,f))*2/double(FFT_MAX_VALUE_OUTPUT)),0.f,1.f);
        return result;
    }
private:
    std::unique_ptr<fft_state,void(*)(fft_state*)> m_fft;
};
}
