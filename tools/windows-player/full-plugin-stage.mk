# Ask the configured Automake graph for every installed plugin and category.
# EXTRA/noinst/check libraries are deliberately outside the installable product.
player_plugin_categories := $(filter-out EXTRA noinst check,$(patsubst %_LTLIBRARIES,%,$(filter %_LTLIBRARIES,$(.VARIABLES))))
.PHONY: player-plugin-map
player-plugin-map:
	@$(foreach category,$(sort $(player_plugin_categories)),$(foreach library,$($(category)_LTLIBRARIES),$(if $(filter %_plugin.la,$(library)),printf '%s\t%s\n' '$(library)' '$($(category)dir)/$(notdir $(library))';))) true
