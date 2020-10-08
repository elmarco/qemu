use common::{sys, *};

use crate::*;

macro_rules! qmp {
    // the basic return value variant
    ($e:expr, $errp:ident, $errval:expr) => {{
        assert!(!$errp.is_null());
        unsafe {
            *$errp = std::ptr::null_mut();
        }

        match $e {
            Ok(val) => val,
            Err(err) => unsafe {
                *$errp = err.to_qemu_full();
                $errval
            },
        }
    }};
    // the ptr return value variant
    ($e:expr, $errp:ident) => {{
        assert!(!$errp.is_null());
        unsafe {
            *$errp = std::ptr::null_mut();
        }

        match $e {
            Ok(val) => val.to_qemu_full().into(),
            Err(err) => unsafe {
                *$errp = err.to_qemu_full();
                std::ptr::null_mut()
            },
        }
    }};
}

#[no_mangle]
extern "C" fn qmp_guest_sync_delimited(id: i64, _errp: *mut *mut sys::Error) -> i64 {
    set_response_delimited();
    id
}

#[no_mangle]
extern "C" fn qmp_guest_sync(id: i64, _errp: *mut *mut sys::Error) -> i64 {
    id
}

#[no_mangle]
extern "C" fn qmp_guest_ping(_errp: *mut *mut sys::Error) {
    slog("guest-ping called");
}

mod hostname;

#[no_mangle]
extern "C" fn qmp_guest_get_host_name(errp: *mut *mut sys::Error) -> *mut qapi_sys::GuestHostName {
    qmp!(hostname::get(), errp)
}

mod vcpus;

#[no_mangle]
extern "C" fn qmp_guest_get_vcpus(
    errp: *mut *mut sys::Error,
) -> *mut qapi_sys::GuestLogicalProcessorList {
    qmp!(vcpus::get(), errp)
}

#[no_mangle]
extern "C" fn qmp_guest_set_vcpus(
    vcpus: *const qapi_sys::GuestLogicalProcessorList,
    errp: *mut *mut sys::Error,
) -> libc::c_longlong {
    let vcpus = unsafe { from_qemu_none(qapi::NewPtr(vcpus)) };
    qmp!(vcpus::set(vcpus), errp, -1)
}

mod datetime;

#[no_mangle]
extern "C" fn qmp_guest_get_timezone(errp: *mut *mut sys::Error) -> *mut qapi_sys::GuestTimezone {
    qmp!(datetime::get_timezone(), errp)
}
