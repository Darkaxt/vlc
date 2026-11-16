# Add to the configured test/Makefile; do not reconfigure the retained cohort.
check_channel_mixer$(EXEEXT): $(top_srcdir)/tools/desktop-player/check-channel-mixer.c $(top_srcdir)/modules/audio_filter/channel_mixer/simple.c
	$(LINK) $(DEFS) -I$(top_builddir) $(AM_CPPFLAGS) $(CPPFLAGS) -UNDEBUG $< $(LIBVLCCORE) $(LIBM)
