use std::os::windows::ffi::OsStrExt;
use winapi::shared::minwindef::*;
use winapi::um::handleapi::CloseHandle;
use winapi::um::minwinbase::*;
use winapi::um::processthreadsapi::{GetCurrentProcess, OpenProcessToken};
use winapi::um::securitybaseapi::AdjustTokenPrivileges;
use winapi::um::winbase::LookupPrivilegeValueW;
use winapi::um::winnt;

use crate::*;

const NANOS_PER_SEC: u64 = 1_000_000_000;
const INTERVALS_PER_SEC: u64 = NANOS_PER_SEC / 100;
const INTERVALS_TO_UNIX_EPOCH: u64 = 11_644_473_600 * INTERVALS_PER_SEC;

pub(crate) fn acquire_privilege(name: &str) -> Result<()> {
    let mut token = std::ptr::null_mut();
    let status = unsafe {
        OpenProcessToken(
            GetCurrentProcess(),
            winnt::TOKEN_ADJUST_PRIVILEGES | winnt::TOKEN_QUERY,
            &mut token,
        )
    };
    if status == 0 {
        return err!("failed to open privilege token");
    }

    let mut tp: winnt::TOKEN_PRIVILEGES = unsafe { std::mem::zeroed() };
    let name = std::ffi::OsStr::new(name);
    let name = name.encode_wide().chain(Some(0)).collect::<Vec<_>>();

    let status = unsafe {
        LookupPrivilegeValueW(
            std::ptr::null_mut(),
            name.as_ptr(),
            &mut tp.Privileges[0].Luid,
        )
    };
    if status == 0 {
        unsafe { CloseHandle(token) };
        return err!("no luid for requested privilege");
    }

    tp.PrivilegeCount = 1;
    tp.Privileges[0].Attributes = winnt::SE_PRIVILEGE_ENABLED;
    let size = std::mem::size_of::<winnt::TOKEN_PRIVILEGES>() as u32;
    let status = unsafe {
        AdjustTokenPrivileges(
            token,
            0,
            &mut tp,
            size,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
        )
    };
    unsafe { CloseHandle(token) };
    if status == 0 {
        return err!("unable to acquire requested privilege");
    }

    Ok(())
}

pub(crate) fn unix_time_to_file_time(time_ns: u64) -> Result<FILETIME> {
    if let Some(inter) = INTERVALS_TO_UNIX_EPOCH.checked_add(time_ns / 100) {
        Ok(FILETIME {
            dwLowDateTime: inter as u32,
            dwHighDateTime: (inter >> 32) as u32,
        })
    } else {
        err!("Failed to convert UNIX time to FILETIME")
    }
}

pub(crate) fn unix_time_to_system_time(time_ns: u64) -> Result<SYSTEMTIME> {
    let ft = unix_time_to_file_time(time_ns)?;

    let mut st: SYSTEMTIME = unsafe { std::mem::zeroed() };
    if unsafe { winapi::um::timezoneapi::FileTimeToSystemTime(&ft, &mut st) } == 0 {
        return err!("Failed to convert UNIX time to SYSTEMTIME");
    };

    Ok(st)
}
