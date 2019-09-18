#!/bin/sh

WHAT="$1"
SRC_PATH="$2"

case "$WHAT" in
    etags)
        rm -f TAGS
        find "$SRC_PATH" -name '*.[ch]' -exec etags --append {} +
        ;;
    ctags)
        rm -f tags
        find "$SRC_PATH" -name '*.[ch]' -exec ctags --append {} +
        ;;
    cscope)
        find "$SRC_PATH" -name "*.[chsS]" -printf '"%p"\n' | sed 's,^\./,,' > cscope.files
        cscope -b -i cscope.files
        ;;
esac
