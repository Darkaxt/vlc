"""Release-build VLC teardown evidence from unconditional lifecycle messages."""
from pathlib import Path


def vlc_input_release_evidence(log: str, fixture: Path, exit_code: int) -> dict:
    """Require the actual local playback chain to close in lifecycle order.

    input.c's Destroy name message is inside #ifndef NDEBUG. It is not a
    release-build observer. These endpoints are emitted by normal decoder,
    demux/access teardown and the player STOPPED/UI shutdown paths instead.
    """
    markers=("Creating an input for playback'"+fixture.name+"'", 'EOF reached',
        'removing "video decoder" module', 'removing "demux" module',
        'removing "access" module', 'VLC_PLAYER_STATE_STOPPED', 'QApp exec() finished')
    cursor=0;events=[]
    for marker in markers:
        position=log.find(marker,cursor)
        if position<0:
            return {'passed':False,'missing_or_out_of_order':marker,'events':events,'exit_code':exit_code}
        line=log[position:log.find('\n',position) if '\n' in log[position:] else len(log)]
        events.append({'marker':marker,'offset':position,'observed':line})
        cursor=position+len(marker)
    return {'passed':exit_code==0,'events':events,'exit_code':exit_code,
        'scope':'Actual playback decoder/demux/access teardown, player STOPPED, Qt event-loop completion and native process exit0; debug-only object-destruction logging is not required.'}
