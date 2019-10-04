# These are used when we want to do substitutions without confusing Make
NULL  :=
SPACE := $(NULL) #
COMMA := ,

# Don't use implicit rules or variables
# we have explicit rules for everything
MAKEFLAGS += -rR

# Flags for dependency generation
QEMU_DGFLAGS += -MMD -MP -MT $@ -MF $(@D)/$(*F).d

# Compiler searches the source file dir first, but in vpath builds
# we need to make it search the build dir too, before any other
# explicit search paths. There are two search locations in the build
# dir, one absolute and the other relative to the compiler working
# directory. These are the same for target-independent files, but
# different for target-dependent ones.
QEMU_LOCAL_INCLUDES = -iquote $(BUILD_DIR)/$(@D) -iquote $(@D)

%.o: %.c
	@mkdir -p $(dir $@)
	$(call quiet-command,$(CC) $(QEMU_LOCAL_INCLUDES) $(QEMU_INCLUDES) \
	       $(QEMU_CFLAGS) $(QEMU_DGFLAGS) $(CFLAGS) $($@-cflags) \
	       -c -o $@ $<,"CC","$(TARGET_DIR)$@")

# Usage: $(call quiet-command,command and args,"NAME","args to print")
# This will run "command and args", and either:
#  if V=1 just print the whole command and args
#  otherwise print the 'quiet' output in the format "  NAME     args to print"
# NAME should be a short name of the command, 7 letters or fewer.
# If called with only a single argument, will print nothing in quiet mode.
quiet-command-run = $(if $(V),,$(if $2,printf "  %-7s %s\n" $2 $3 && ))$1
quiet-@ = $(if $(V),,@)
quiet-command = $(quiet-@)$(call quiet-command-run,$1,$2,$3)

# cc-option
# Usage: CFLAGS+=$(call cc-option, -falign-functions=0, -malign-functions=0)

cc-option = $(if $(shell $(CC) $1 $2 -S -o /dev/null -xc /dev/null \
              >/dev/null 2>&1 && echo OK), $2, $3)
cc-c-option = $(if $(shell $(CC) $1 $2 -c -o /dev/null -xc /dev/null \
                >/dev/null 2>&1 && echo OK), $2, $3)

VPATH_SUFFIXES = %.c %.h %.S %.cc %.cpp %.m %.mak %.texi %.sh %.rc Kconfig% %.json.in
set-vpath = $(if $1,$(foreach PATTERN,$(VPATH_SUFFIXES),$(eval vpath $(PATTERN) $1)))

# will delete the target of a rule if commands exit with a nonzero exit status
.DELETE_ON_ERROR:
