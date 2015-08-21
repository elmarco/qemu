/*
 * Core Definitions for QAPI/QMP Dispatch
 *
 * Copyright IBM, Corp. 2011
 *
 * Authors:
 *  Anthony Liguori   <aliguori@us.ibm.com>
 *  Michael Roth      <mdroth@us.ibm.com>
 *
 * This work is licensed under the terms of the GNU LGPL, version 2.1 or later.
 * See the COPYING.LIB file in the top-level directory.
 *
 */

#include "qemu/osdep.h"
#include "qapi/qmp/dispatch.h"


static QmpCommand *qmp_command_new(QmpCommandList *cmds, const char *name,
                                   QmpCommandOptions options)
{
    QmpCommand *cmd = g_malloc0(sizeof(*cmd));

    cmd->name = name;
    cmd->enabled = true;
    cmd->options = options;
    QTAILQ_INSERT_TAIL(cmds, cmd, node);

    return cmd;
}


void qmp_register_command(QmpCommandList *cmds, const char *name,
                          QmpCommandFunc *fn, QmpCommandOptions options)
{
    QmpCommand *cmd = qmp_command_new(cmds, name, options);

    assert(!(options & QCO_ASYNC));
    cmd->fn = fn;
}

void qmp_register_async_command(QmpCommandList *cmds, const char *name,
                            QmpCommandAsyncFunc *fn, QmpCommandOptions options)
{
    QmpCommand *cmd = qmp_command_new(cmds, name, options);

    assert(options & QCO_ASYNC);
    cmd->async_fn = fn;
}

const QmpCommand *qmp_find_command(const QmpCommandList *cmds, const char *name)
{
    QmpCommand *cmd;

    QTAILQ_FOREACH(cmd, cmds, node) {
        if (strcmp(cmd->name, name) == 0) {
            return cmd;
        }
    }
    return NULL;
}

static void qmp_toggle_command(QmpCommandList *cmds, const char *name,
                               bool enabled)
{
    QmpCommand *cmd;

    QTAILQ_FOREACH(cmd, cmds, node) {
        if (strcmp(cmd->name, name) == 0) {
            cmd->enabled = enabled;
            return;
        }
    }
}

void qmp_disable_command(QmpCommandList *cmds, const char *name)
{
    qmp_toggle_command(cmds, name, false);
}

void qmp_enable_command(QmpCommandList *cmds, const char *name)
{
    qmp_toggle_command(cmds, name, true);
}

bool qmp_command_is_enabled(const QmpCommand *cmd)
{
    return cmd->enabled;
}

const char *qmp_command_name(const QmpCommand *cmd)
{
    return cmd->name;
}

bool qmp_has_success_response(const QmpCommand *cmd)
{
    return !(cmd->options & QCO_NO_SUCCESS_RESP);
}

void qmp_for_each_command(const QmpCommandList *cmds, qmp_cmd_callback_fn fn,
                          void *opaque)
{
    const QmpCommand *cmd;

    QTAILQ_FOREACH(cmd, cmds, node) {
        fn(cmd, opaque);
    }
}
