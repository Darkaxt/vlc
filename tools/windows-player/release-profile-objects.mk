# A configure change changes compiler flags even for generated QML/cache units
# that do not include config.h. Depend on the existing configure identity, so
# objects already rebuilt after configuration retain their useful work, while
# older cached objects rebuild exactly once with the current release flags.
player_release_profile_inputs := $(sort $(filter %.$(OBJEXT) %.lo,$(foreach name,$(filter %_OBJECTS,$(.VARIABLES)),$($(name)))))
ifneq ($(strip $(player_release_profile_inputs)),)
$(player_release_profile_inputs): $(top_builddir)/config.status
endif
