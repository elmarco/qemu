use std::os::windows::ffi::OsStrExt;
use winapi::um::handleapi::CloseHandle;
use winapi::um::processthreadsapi::{GetCurrentProcess, OpenProcessToken};
use winapi::um::securitybaseapi::AdjustTokenPrivileges;
use winapi::um::winbase::LookupPrivilegeValueW;
use winapi::um::winnt;

use crate::*;

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
