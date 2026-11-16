# Add to the configured test/Makefile; do not reconfigure the retained cohort.
CHANNEL_MIXER_TEST_SOURCE ?= $(top_srcdir)/tools/desktop-player/check-channel-mixer.c
check_channel_mixer$(EXEEXT): $(CHANNEL_MIXER_TEST_SOURCE) $(top_srcdir)/modules/audio_filter/channel_mixer/simple.c
	$(LINK) $(DEFS) -I$(top_builddir) -I$(top_srcdir)/modules/audio_filter/channel_mixer $(AM_CPPFLAGS) $(CPPFLAGS) $< $(LIBVLCCORE) $(LIBM)
