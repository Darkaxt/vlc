# Expand the configured suite without executing Windows binaries inside WSL.
.PHONY: native-test-programs
native-test-programs:
	@$(foreach program,$(check_PROGRAMS),printf 'NATIVE-TEST\t%s\n' '$(program)';) true

# The selected upstream C units compile internal sources and call POSIX APIs
# from the shared test harness. Use VLC's existing configured Windows fixups.
native_test_recipe := $(lastword $(MAKEFILE_LIST))
test_src_audio_output_dec_LDADD += $(top_builddir)/compat/libcompat.la
test_modules_video_filter_blend_LDADD += $(top_builddir)/compat/libcompat.la
test_src_audio_output_dec.exe test_modules_video_filter_blend.exe: $(top_builddir)/compat/libcompat.la $(native_test_recipe)

ifdef NATIVE_TEST_INPUT_STATE
$(test_src_audio_output_dec_OBJECTS) $(test_modules_video_filter_blend_OBJECTS) $(test_qt_csd_button_model_OBJECTS) $(test_player_chrome_OBJECTS) $(test_src_misc_history_OBJECTS) $(test_src_misc_saved_options_OBJECTS): $(NATIVE_TEST_INPUT_STATE)
endif

ifneq ($(strip $(QT_QTEST_COMMON_ldadd)),)
native_qt_platform_object = tests/native-test-qt-platform.o
$(native_qt_platform_object): $(NATIVE_QT_PLATFORM_SOURCE) $(NATIVE_TEST_INPUT_STATE)
	@$(MKDIR_P) tests
	$(AM_V_CXX)$(CXX) $(DEFS) $(DEFAULT_INCLUDES) $(INCLUDES) $(test_qt_csd_button_model_CPPFLAGS) $(CPPFLAGS) $(test_qt_csd_button_model_CXXFLAGS) $(CXXFLAGS) -c -o $@ $<
test_qt_csd_button_model_LDADD = $(native_qt_platform_object) $(NATIVE_QT_OFFSCREEN_ARCHIVE) $(QT_QTEST_COMMON_ldadd)
test_qt_csd_button_model.exe: $(native_qt_platform_object) $(NATIVE_QT_OFFSCREEN_ARCHIVE) $(native_test_recipe)
endif
