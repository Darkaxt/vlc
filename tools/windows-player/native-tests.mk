# Expand the configured suite without executing Windows binaries inside WSL.
.PHONY: native-test-programs
native-test-programs:
	@$(foreach program,$(check_PROGRAMS),printf '%s\n' '$(program)';) true
