# Effective flags/config.h changes affect generated QML/cache objects too.
# An unchanged configure rerun must not invalidate the entire retained graph.
player_release_profile_inputs := $(sort $(filter %.$(OBJEXT) %.lo,$(foreach name,$(filter %_OBJECTS,$(.VARIABLES)),$($(name)))))
ifneq ($(strip $(player_release_profile_inputs)),)
$(player_release_profile_inputs): $(top_builddir)/player-object-profile.json
endif
