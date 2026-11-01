# Windres reads the icon, so a changed maintained icon must rebuild the resource.
# Extends the existing generated Make graph without reconfiguring the SDK.
vlc_win32_rc.$(OBJEXT): $(top_srcdir)/share/icons/vlc.ico
