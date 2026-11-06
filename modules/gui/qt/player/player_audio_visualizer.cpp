// SPDX-License-Identifier: GPL-2.0-or-later
#ifdef HAVE_CONFIG_H
# include "config.h"
#endif
#include "player_audio_visualizer.hpp"
#include <vlc_filter.h>
#include <vlc_block.h>
#include <mutex>
#include <unordered_map>
#include <new>

struct PlayerVisualizationState {
    std::mutex mutex;
    AudioVisualization::Capture capture;
    quint64 revision=0;
    bool enabled=true,loaded=false;
};

namespace {
// Bind the pass-through observer to the exact held player aout. A filter keeps
// its shared state through asynchronous removal; no raw QObject crosses threads.
std::mutex registryMutex;
std::unordered_map<vlc_object_t *,std::weak_ptr<PlayerVisualizationState>> registry;
using FilterState=std::shared_ptr<PlayerVisualizationState>;

block_t *observe(filter_t *filter,block_t *block)
{
    const auto &state=*static_cast<FilterState *>(filter->p_sys);
    const unsigned channels=aout_FormatNbChannels(&filter->fmt_in.audio);
    if(channels && block->i_nb_samples<=block->i_buffer/(sizeof(float)*channels)) {
        std::lock_guard lock(state->mutex);
        if(state->enabled) {
            state->capture.append(reinterpret_cast<const float *>(block->p_buffer),block->i_nb_samples,channels);
            ++state->revision;
        }
    }
    return block; // Never alter, replace or release the audible PCM buffer.
}
void flush(filter_t *filter)
{
    const auto &state=*static_cast<FilterState *>(filter->p_sys);
    std::lock_guard lock(state->mutex);
    state->capture.reset();++state->revision;
}
void close(filter_t *filter)
{
    const auto &state=*static_cast<FilterState *>(filter->p_sys);
    { std::lock_guard lock(state->mutex);state->loaded=false;state->capture.reset();++state->revision; }
    delete static_cast<FilterState *>(filter->p_sys);
}
const vlc_filter_operations operations=[] {
    vlc_filter_operations ops{};
    ops.filter_audio=observe;ops.flush=flush;ops.close=close;
    return ops;
}();
}

int QtAudioVisualizerOpen(filter_t *filter)
{
    FilterState state;
    {
        std::lock_guard lock(registryMutex);
        for(auto *parent=vlc_object_parent(filter);parent;parent=vlc_object_parent(parent)) {
            const auto found=registry.find(parent);
            if(found!=registry.end()) { state=found->second.lock();break; }
        }
    }
    if(!state)return VLC_EGENERIC;
    auto *held=new(std::nothrow) FilterState(state);
    if(!held)return VLC_ENOMEM;
    filter->fmt_in.audio.i_format=VLC_CODEC_FL32;
    aout_FormatPrepare(&filter->fmt_in.audio);
    filter->fmt_out.audio=filter->fmt_in.audio;
    filter->p_sys=held;filter->ops=&operations;
    { std::lock_guard lock(state->mutex);state->loaded=true;++state->revision; }
    return VLC_SUCCESS;
}

PlayerAudioVisualizer::PlayerAudioVisualizer(PlayerController *player,QObject *parent)
    :QObject(parent),m_player(player)
{
    setObjectName(QStringLiteral("redesignAudioVisualizer"));
    // This is a rendering cadence, not a completion/retry timeout. It reads only
    // the latest bounded PCM frame, never queues work on the real-time thread.
    m_renderClock.setInterval(33);
    m_renderClock.setTimerType(Qt::PreciseTimer);
    connect(&m_renderClock,&QTimer::timeout,this,&PlayerAudioVisualizer::refresh);
    connect(player,&PlayerController::playingStateChanged,this,&PlayerAudioVisualizer::updateOutput);
    connect(player,&PlayerController::inputChanged,this,&PlayerAudioVisualizer::resetOutput);
    connect(player,&PlayerController::playbackEngineChanged,this,&PlayerAudioVisualizer::resetOutput);
    connect(player,&PlayerController::seekRequested,this,&PlayerAudioVisualizer::resetSamples);
    connect(player->getAudioTracks(),&TrackListModel::countChanged,this,&PlayerAudioVisualizer::updateOutput);
    connect(player->getAudioTracks(),&QAbstractItemModel::dataChanged,this,
        [this](const QModelIndex &,const QModelIndex &,const QList<int> &roles) {
            if(!roles.isEmpty() && !roles.contains(Qt::CheckStateRole))return;
            resetSamples();updateOutput();
        });
    updateOutput();
}
PlayerAudioVisualizer::~PlayerAudioVisualizer() { detach(); }

void PlayerAudioVisualizer::detach()
{
    m_renderClock.stop();
    if(m_output) {
        { std::lock_guard lock(registryMutex);registry.erase(VLC_OBJECT(m_output.get())); }
        if(m_state) { std::lock_guard lock(m_state->mutex);m_state->enabled=false;m_state->capture.reset(); }
        aout_EnableFilter(m_output.get(),"qt-seek-visualizer",false);
    }
    m_state.reset();m_output.reset();m_samples.clear();m_seenRevision=0;m_loaded=false;
}
void PlayerAudioVisualizer::resetOutput() { detach();updateOutput(); }
void PlayerAudioVisualizer::resetSamples()
{
    if(m_state) { std::lock_guard lock(m_state->mutex);m_state->capture.reset();++m_state->revision; }
    m_samples.clear();++m_frameRevision;emit changed();
}
void PlayerAudioVisualizer::updateOutput()
{
    auto *tracks=m_player->getAudioTracks();
    bool selected=false;
    for(int row=0;row<tracks->rowCount();++row)
        selected|=tracks->data(tracks->index(row,0),Qt::CheckStateRole).toBool();
    const auto output=!m_player->usesMpv() && m_player->isStarted()
        && selected ? m_player->getAout() : SharedAOut();
    m_available=bool(output) && m_transform.valid();
    if(m_output && (m_output.get()!=output.get() || m_mode.isEmpty()))detach();
    if(m_available && !m_mode.isEmpty() && !m_output) {
        m_output=output;m_state=std::make_shared<PlayerVisualizationState>();
        { std::lock_guard lock(registryMutex);registry[VLC_OBJECT(m_output.get())]=m_state; }
        if(aout_EnableFilter(m_output.get(),"qt-seek-visualizer",true)!=VLC_SUCCESS) {
            detach();m_error=tr("The audio output could not enable the visualizer.");
        }
    }
    if(m_output && m_player->getPlayingState()==PlayerController::PLAYING_STATE_PLAYING)m_renderClock.start();
    else m_renderClock.stop();
    emit changed();
}
void PlayerAudioVisualizer::setMode(const QString &mode)
{
    if(!QStringList{"","spectrometer","scope","spectrum","waveform"}.contains(mode))return;
    if(m_mode==mode)return;
    if(!mode.isEmpty() && !available())return;
    m_mode=mode;m_error.clear();m_seenRevision=0;m_samples.clear();
    updateOutput();
    refresh();
}
QString PlayerAudioVisualizer::status() const
{
    if(m_player->usesMpv())return tr("Audio visualization requires VLC playback.");
    if(!m_available)return tr("Start playback of an audio track to enable visualization.");
    if(!m_error.isEmpty())return m_error;
    if(!m_mode.isEmpty() && !m_loaded)return tr("Waiting for audio samples…");
    return {};
}
void PlayerAudioVisualizer::refresh()
{
    if(!m_state)return;
    AudioVisualization::Frame frame;
    bool ready;
    {
        std::lock_guard lock(m_state->mutex);
        if(m_seenRevision==m_state->revision)return;
        m_seenRevision=m_state->revision;m_loaded=m_state->loaded;
        ready=m_state->capture.ready();frame=m_state->capture.frame();
    }
    m_samples.clear();
    if(ready) {
        if(m_mode==QStringLiteral("spectrum") || m_mode==QStringLiteral("spectrometer")) {
            const auto spectrum=m_transform.spectrum(frame);
            for(int band=0;band<64;++band) {
                const int first=std::max(1,int(std::pow(256.,double(band)/64)));
                const int last=std::min(257,std::max(first+1,int(std::ceil(std::pow(256.,double(band+1)/64)))));
                float peak=0;for(int bin=first;bin<last;++bin)peak=std::max(peak,spectrum[bin]);
                m_samples.append(peak>0?std::clamp((20*std::log10(double(peak))+60)/60,0.,1.):0.);
            }
        } else for(float sample:frame)m_samples.append(sample);
    }
    ++m_frameRevision;emit changed();
}
