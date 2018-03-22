/*
 * QEMU monitor
 *
 * Copyright (c) 2003-2004 Fabrice Bellard
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "qemu/osdep.h"

#include "chardev/char-io.h"
#include "monitor-internal.h"
#include "qapi/error.h"
#include "qapi/qapi-commands-misc.h"
#include "qapi/qmp/qdict.h"
#include "qapi/qmp/qjson.h"
#include "qapi/qmp/qlist.h"
#include "qapi/qmp/qstring.h"
#include "trace.h"

struct QMPRequest {
    /* Owner of the request */
    MonitorQMP *mon;
    /*
     * Request object to be handled or Error to be reported
     * (exactly one of them is non-null)
     */
    QObject *req;
    Error *err;
};
typedef struct QMPRequest QMPRequest;

QmpCommandList qmp_commands, qmp_cap_negotiation_commands;

static bool qmp_oob_enabled(MonitorQMP *mon)
{
    return mon->capab[QMP_CAPABILITY_OOB];
}

static void monitor_qmp_caps_reset(MonitorQMP *mon)
{
    memset(mon->capab_offered, 0, sizeof(mon->capab_offered));
    memset(mon->capab, 0, sizeof(mon->capab));
    mon->capab_offered[QMP_CAPABILITY_OOB] = mon->common.use_io_thread;
}

static void qmp_request_free(QMPRequest *req)
{
    qobject_unref(req->req);
    error_free(req->err);
    g_free(req);
}

/* Caller must hold mon->qmp.qmp_queue_lock */
static void monitor_qmp_cleanup_req_queue_locked(MonitorQMP *mon)
{
    while (!g_queue_is_empty(mon->qmp_requests)) {
        qmp_request_free(g_queue_pop_head(mon->qmp_requests));
    }
}

static void monitor_qmp_cleanup_queues(MonitorQMP *mon)
{
    qemu_mutex_lock(&mon->qmp_queue_lock);
    monitor_qmp_cleanup_req_queue_locked(mon);
    qemu_mutex_unlock(&mon->qmp_queue_lock);
}

void qmp_send_response(MonitorQMP *mon, const QDict *rsp)
{
    const QObject *data = QOBJECT(rsp);
    QString *json;

    json = mon->pretty ? qobject_to_json_pretty(data) : qobject_to_json(data);
    assert(json != NULL);

    qstring_append_chr(json, '\n');
    monitor_puts(&mon->common, qstring_get_str(json));

    qobject_unref(json);
}

static void dispatch_return_cb(QmpSession *session, QDict *rsp)
{
    MonitorQMP *mon = container_of(session, MonitorQMP, session);

    if (mon->session.cmds == &qmp_cap_negotiation_commands) {
        QDict *error = qdict_get_qdict(rsp, "error");
        if (error
            && !g_strcmp0(qdict_get_try_str(error, "class"),
                          QapiErrorClass_str(ERROR_CLASS_COMMAND_NOT_FOUND))) {
            /* Provide a more useful error message */
            qdict_del(error, "desc");
            qdict_put_str(error, "desc", "Expecting capabilities negotiation"
                          " with 'qmp_capabilities'");
        }
    }

    qmp_send_response(mon, rsp);
}

static void monitor_qmp_dispatch(MonitorQMP *mon, QObject *req)
{
    Monitor *old_mon;

    old_mon = cur_mon;
    cur_mon = &mon->common;

    qmp_dispatch(&mon->session, req, qmp_oob_enabled(mon));

    cur_mon = old_mon;
}

/*
 * Pop a QMP request from a monitor request queue.
 * Return the request, or NULL all request queues are empty.
 * We are using round-robin fashion to pop the request, to avoid
 * processing commands only on a very busy monitor.  To achieve that,
 * when we process one request on a specific monitor, we put that
 * monitor to the end of mon_list queue.
 *
 * Note: if the function returned with non-NULL, then the caller will
 * be with qmp_mon->qmp_queue_lock held, and the caller is responsible
 * to release it.
 */
static QMPRequest *monitor_qmp_requests_pop_any_with_lock(void)
{
    QMPRequest *req_obj = NULL;
    Monitor *mon;
    MonitorQMP *qmp_mon;

    qemu_mutex_lock(&monitor_lock);

    QTAILQ_FOREACH(mon, &mon_list, entry) {
        if (!monitor_is_qmp(mon)) {
            continue;
        }

        qmp_mon = container_of(mon, MonitorQMP, common);
        qemu_mutex_lock(&qmp_mon->qmp_queue_lock);
        req_obj = g_queue_pop_head(qmp_mon->qmp_requests);
        if (req_obj) {
            /* With the lock of corresponding queue held */
            break;
        }
        qemu_mutex_unlock(&qmp_mon->qmp_queue_lock);
    }

    if (req_obj) {
        /*
         * We found one request on the monitor. Degrade this monitor's
         * priority to lowest by re-inserting it to end of queue.
         */
        QTAILQ_REMOVE(&mon_list, mon, entry);
        QTAILQ_INSERT_TAIL(&mon_list, mon, entry);
    }

    qemu_mutex_unlock(&monitor_lock);

    return req_obj;
}

void monitor_qmp_bh_dispatcher(void *data)
{
    QMPRequest *req_obj = monitor_qmp_requests_pop_any_with_lock();
    bool need_resume;
    MonitorQMP *mon;

    if (!req_obj) {
        return;
    }

    mon = req_obj->mon;
    /*  qmp_oob_enabled() might change after "qmp_capabilities" */
    need_resume = !qmp_oob_enabled(mon) ||
        mon->qmp_requests->length == QMP_REQ_QUEUE_LEN_MAX - 1;
    qemu_mutex_unlock(&mon->qmp_queue_lock);
    if (req_obj->req) {
        QDict *qdict = qobject_to(QDict, req_obj->req);
        QObject *id = qdict ? qdict_get(qdict, "id") : NULL;
        trace_monitor_qmp_cmd_in_band(qobject_get_try_str(id) ?: "");
        monitor_qmp_dispatch(mon, req_obj->req);
    } else {
        QmpSession *session = &req_obj->mon->session;
        assert(req_obj->err);
        qmp_return_error(qmp_return_new(session, req_obj->req), req_obj->err);
        req_obj->err = NULL;
    }

    if (need_resume) {
        /* Pairs with the monitor_suspend() in handle_qmp_command() */
        monitor_resume(&mon->common);
    }
    qmp_request_free(req_obj);

    /* Reschedule instead of looping so the main loop stays responsive */
    qemu_bh_schedule(qmp_dispatcher_bh);
}

static void handle_qmp_command(void *opaque, QObject *req, Error *err)
{
    MonitorQMP *mon = container_of(opaque, MonitorQMP, session);
    QObject *id = NULL;
    QDict *qdict;
    QMPRequest *req_obj;

    assert(!req != !err);

    qdict = qobject_to(QDict, req);
    if (qdict) {
        id = qdict_get(qdict, "id");
    } /* else will fail qmp_dispatch() */

    if (req && trace_event_get_state_backends(TRACE_HANDLE_QMP_COMMAND)) {
        QString *req_json = qobject_to_json(req);
        trace_handle_qmp_command(mon, qstring_get_str(req_json));
        qobject_unref(req_json);
    }

    if (qdict && qmp_is_oob(qdict)) {
        /* OOB commands are executed immediately */
        trace_monitor_qmp_cmd_out_of_band(qobject_get_try_str(id) ?: "");
        monitor_qmp_dispatch(mon, req);
        qobject_unref(req);
        return;
    }

    req_obj = g_new0(QMPRequest, 1);
    req_obj->mon = mon;
    req_obj->req = req;
    req_obj->err = err;

    /* Protect qmp_requests and fetching its length. */
    qemu_mutex_lock(&mon->qmp_queue_lock);

    /*
     * Suspend the monitor when we can't queue more requests after
     * this one.  Dequeuing in monitor_qmp_bh_dispatcher() will resume
     * it.  Note that when OOB is disabled, we queue at most one
     * command, for backward compatibility.
     */
    if (!qmp_oob_enabled(mon) ||
        mon->qmp_requests->length == QMP_REQ_QUEUE_LEN_MAX - 1) {
        monitor_suspend(&mon->common);
    }

    /*
     * Put the request to the end of queue so that requests will be
     * handled in time order.  Ownership for req_obj, req,
     * etc. will be delivered to the handler side.
     */
    assert(mon->qmp_requests->length < QMP_REQ_QUEUE_LEN_MAX);
    g_queue_push_tail(mon->qmp_requests, req_obj);
    qemu_mutex_unlock(&mon->qmp_queue_lock);

    /* Kick the dispatcher routine */
    qemu_bh_schedule(qmp_dispatcher_bh);
}

static void monitor_qmp_read(void *opaque, const uint8_t *buf, int size)
{
    MonitorQMP *mon = opaque;

    qmp_session_feed(&mon->session, (const char *) buf, size);
}

static QDict *qmp_greeting(MonitorQMP *mon)
{
    QList *cap_list = qlist_new();
    QObject *ver = NULL;
    QMPCapability cap;

    qmp_marshal_query_version(NULL, &ver, NULL);

    for (cap = 0; cap < QMP_CAPABILITY__MAX; cap++) {
        if (mon->capab_offered[cap]) {
            qlist_append_str(cap_list, QMPCapability_str(cap));
        }
    }

    return qdict_from_jsonf_nofail(
        "{'QMP': {'version': %p, 'capabilities': %p}}",
        ver, cap_list);
}

static void monitor_qmp_event(void *opaque, int event)
{
    QDict *data;
    MonitorQMP *mon = opaque;

    switch (event) {
    case CHR_EVENT_OPENED:
        qmp_session_init(&mon->session,
                         &qmp_cap_negotiation_commands,
                         handle_qmp_command,
                         dispatch_return_cb);
        monitor_qmp_caps_reset(mon);
        data = qmp_greeting(mon);
        qmp_send_response(mon, data);
        qobject_unref(data);
        mon_refcount++;
        break;
    case CHR_EVENT_CLOSED:
        /*
         * Note: this is only useful when the output of the chardev
         * backend is still open.  For example, when the backend is
         * stdio, it's possible that stdout is still open when stdin
         * is closed.
         */
        monitor_qmp_cleanup_queues(mon);
        qmp_session_destroy(&mon->session);
        mon_refcount--;
        monitor_fdsets_cleanup();
        break;
    }
}

void monitor_data_destroy_qmp(MonitorQMP *mon)
{
    qmp_session_destroy(&mon->session);
    qemu_mutex_destroy(&mon->qmp_queue_lock);
    monitor_qmp_cleanup_req_queue_locked(mon);
    g_queue_free(mon->qmp_requests);
}

static void monitor_qmp_setup_handlers_bh(void *opaque)
{
    MonitorQMP *mon = opaque;
    GMainContext *context;

    assert(mon->common.use_io_thread);
    context = iothread_get_g_main_context(mon_iothread);
    assert(context);
    qemu_chr_fe_set_handlers(&mon->common.chr, monitor_can_read,
                             monitor_qmp_read, monitor_qmp_event,
                             NULL, &mon->common, context, true);
    monitor_list_append(&mon->common);
}

void monitor_init_qmp(Chardev *chr, bool pretty)
{
    MonitorQMP *mon = g_new0(MonitorQMP, 1);

    /* Note: we run QMP monitor in I/O thread when @chr supports that */
    monitor_data_init(&mon->common, true, false,
                      qemu_chr_has_feature(chr, QEMU_CHAR_FEATURE_GCONTEXT));

    mon->pretty = pretty;

    qemu_mutex_init(&mon->qmp_queue_lock);
    mon->qmp_requests = g_queue_new();

    qemu_chr_fe_init(&mon->common.chr, chr, &error_abort);
    qemu_chr_fe_set_echo(&mon->common.chr, true);

    if (mon->common.use_io_thread) {
        /*
         * Make sure the old iowatch is gone.  It's possible when
         * e.g. the chardev is in client mode, with wait=on.
         */
        remove_fd_in_watch(chr);
        /*
         * We can't call qemu_chr_fe_set_handlers() directly here
         * since chardev might be running in the monitor I/O
         * thread.  Schedule a bottom half.
         */
        aio_bh_schedule_oneshot(iothread_get_aio_context(mon_iothread),
                                monitor_qmp_setup_handlers_bh, mon);
        /* The bottom half will add @mon to @mon_list */
    } else {
        qemu_chr_fe_set_handlers(&mon->common.chr, monitor_can_read,
                                 monitor_qmp_read, monitor_qmp_event,
                                 NULL, &mon->common, NULL, true);
        monitor_list_append(&mon->common);
    }
}
