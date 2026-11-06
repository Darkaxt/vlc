// SPDX-License-Identifier: GPL-2.0-or-later
#include "../player/audio_visualization_data.hpp"
#include <cassert>
#include <cmath>
#include <limits>
#include <vector>

int main()
{
    using namespace AudioVisualization;
    Capture capture;
    std::array<float, SampleCount> zero{};
    assert(!capture.ready());
    capture.append(zero.data(),SampleCount,1);
    assert(capture.ready());
    auto frame=capture.frame();
    assert(std::all_of(frame.begin(),frame.end(),[](float f){return f==0;}));
    Transform transform;
    assert(transform.valid());
    auto power=transform.spectrum(frame);
    assert(std::all_of(power.begin(),power.end(),[](float f){return f==0;}));

    // An integral-bin tone has a measurable frequency peak. Capture the audible
    // channel even when only the right/center channel carries audio, or stereo
    // channels have opposite phase. Do not touch the actual audio block.
    for(unsigned channels : {1u,2u,6u}) {
        capture.reset();
        std::vector<float> pcm(SampleCount*channels,0);
        for(size_t i=0;i<SampleCount;++i)
            pcm[i*channels+channels-1]=0.75f*std::sin(2*3.14159265358979323846*32*i/SampleCount);
        if(channels==2)for(size_t i=0;i<SampleCount;++i)pcm[i*2]=-pcm[i*2+1];
        const auto original=pcm;
        capture.append(pcm.data(),SampleCount/2,channels);
        assert(!capture.ready());
        capture.append(pcm.data()+SampleCount/2*channels,SampleCount/2,channels);
        assert(capture.ready() && pcm==original);
        frame=capture.frame();
        power=transform.spectrum(frame);
        const auto peak=std::max_element(power.begin()+1,power.end())-power.begin();
        assert(peak==32 && power[32]>0.7f && power[32]<0.8f);
    }
    // Seek/flush must erase old content, including partially accumulated frames.
    capture.reset();
    assert(!capture.ready());
    capture.append(zero.data(),SampleCount-1,1);
    assert(!capture.ready());
    capture.append(zero.data(),1,1);
    assert(capture.ready());
    power=transform.spectrum(capture.frame());
    assert(std::all_of(power.begin(),power.end(),[](float f){return f==0;}));
    auto invalid=zero;
    invalid[3]=std::numeric_limits<float>::quiet_NaN();
    invalid[8]=std::numeric_limits<float>::infinity();
    capture.append(invalid.data(),SampleCount,1);
    frame=capture.frame();
    assert(std::all_of(frame.begin(),frame.end(),[](float f){return std::isfinite(f);}));
    // A large block contributes exactly its newest frame, with bounded work.
    std::vector<float> large(SampleCount*3,-0.25f);
    std::fill(large.end()-SampleCount,large.end(),0.5f);
    capture.append(large.data(),large.size(),1);
    frame=capture.frame();
    assert(std::all_of(frame.begin(),frame.end(),[](float f){return f==0.5f;}));
    return 0;
}
