# Native regression for the exact production release parser, geometry and
# embedded subtitle decoder. Use the retained configured compiler/CRT flags.
$(M2_CHECK_OUTPUT): $(top_srcdir)/tools/windows-player/first-run-policies-check.cpp $(srcdir)/dialogs/help/fork_release.hpp $(srcdir)/maininterface/window_geometry.hpp $(srcdir)/player/embedded_subtitles.hpp
	$(CXX) $(AM_CPPFLAGS) $(CPPFLAGS) $(AM_CXXFLAGS) $(CXXFLAGS) $(QT_CFLAGS) -std=c++17 -DVLC_QT_EMBEDDED_SUBTITLES -DQT_USE_QSTRINGBUILDER -DQT_NO_CAST_TO_ASCII -DQT_NO_CAST_FROM_BYTEARRAY -I$(srcdir) $(top_srcdir)/tools/windows-player/first-run-policies-check.cpp $(LDFLAGS) -static $(M2_CHECK_LIBS) -static-libgcc -static-libstdc++ -o $@
