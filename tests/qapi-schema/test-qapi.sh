#!/bin/sh

PYTHON="$1"
SRC_PATH="$2"
SCHEMA="$3"

BASENAME=$(basename "$SCHEMA" .json)
TEST_OUT="$BASENAME.test.out"
TEST_ERR="$BASENAME.test.err"
TEST_EXIT="$BASENAME.test.exit"
OUT="$SRC_PATH/$BASENAME.out"
ERR="$SRC_PATH/$BASENAME.err"
EXIT="$SRC_PATH/$BASENAME.exit"


"$PYTHON" "$SRC_PATH"/test-qapi.py "$SCHEMA" > "$TEST_OUT" 2> "$TEST_ERR"
echo $? > "$TEST_EXIT"

# Sanitize error messages (make them independent of build directory)
perl -p -e "s|\\Q$SRC_PATH\\E/||g" "$TEST_ERR" | diff -u "$ERR" -
diff -u "$OUT" "$TEST_OUT"
diff -u "$EXIT" "$TEST_EXIT"
