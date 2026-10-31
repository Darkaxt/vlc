# Extend the generated Automake graph without changing its prerequisite rules.
# Compile all frontend objects/resources first; the driver then releases its
# bounded header cache before asking Automake to link the complete Qt plugin.
.PHONY: qt-player-objects
qt-player-objects: $(BUILT_SOURCES) $(libqt_plugin_la_OBJECTS) $(libqt_plugin_la_DEPENDENCIES) $(EXTRA_libqt_plugin_la_DEPENDENCIES)

# Called only when the driver's recorded preprocessor flags change. Use the
# existing native generator/flags; keep unchanged source-header mtimes intact.
.PHONY: qt-regenerate-player-moc
qt-regenerate-player-moc:
	$(moc_verbose)$(MOC) $(MOC_CPPFLAGS) -o player/player_controller.moc.cpp $(srcdir)/player/player_controller.hpp
