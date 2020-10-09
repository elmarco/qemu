use chrono::prelude::*;
#[cfg(unix)]
use nix::sys::time::{TimeVal, TimeValLike};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};
#[cfg(windows)]
use winapi::um::{sysinfoapi, wininet, winnt};

use crate::*;

pub(crate) fn get_timezone() -> Result<qapi::GuestTimezone> {
    let local = Local.timestamp(0, 0);
    let zone = Some(local.format("%Z").to_string());
    let offset = local.offset().fix().local_minus_utc() as i64;

    Ok(qapi::GuestTimezone { zone, offset })
}

pub(crate) fn get_time() -> Result<i64> {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(n) => Ok(n.as_secs() as i64),
        Err(_) => err!("SystemTime before UNIX EPOCH!"),
    }
}

#[cfg(unix)]
pub(crate) fn set_time(time_ns: Option<i64>) -> Result<()> {
    const NANOS_PER_SEC: i64 = 1_000_000_000;

    if nix::unistd::access("/sbin/hwclock", nix::unistd::AccessFlags::X_OK).is_err() {
        return err!("Can't execute hwclock");
    }

    let mut hwclock = Command::new("/sbin/hwclock");
    hwclock.stdin(Stdio::null());
    hwclock.stdout(Stdio::null());
    hwclock.stderr(Stdio::null());

    // if user has passed a time to set and the system time is set, we just need
    // to synchronize the hardware clock. However, if no time was passed, user
    // is requesting the opposite: set the system time from the hardware clock
    // (RTC). */
    if let Some(time_ns) = time_ns {
        // year-2038 will overflow in case time_t is 32bit
        if time_ns / 1000000000 != time_ns as libc::time_t / NANOS_PER_SEC {
            return err!(format!("Time {} is too large", time_ns));
        }
        // a bit unsure about the need of such check
        let dt = chrono::Utc.timestamp(time_ns / NANOS_PER_SEC, (time_ns % NANOS_PER_SEC) as u32);
        if dt.year() < 1970 || dt.year() >= 2070 {
            return err!("Invalid time");
        }
        let ret =
            unsafe { libc::settimeofday(TimeVal::nanoseconds(time_ns).as_ref(), std::ptr::null()) };
        if ret == -1 {
            return Err(std::io::Error::last_os_error().into());
        }
        hwclock.arg("-w");
    } else {
        hwclock.arg("-s");
    }

    let status = hwclock.status()?;
    if !status.success() {
        return err!("hwclock failed to set hardware clock to system time");
    }
    Ok(())
}

#[cfg(windows)]
pub(crate) fn set_time(time_ns: Option<i64>) -> Result<()> {
    match time_ns {
        Some(time_ns) => {
            let st = win32::unix_time_to_system_time(time_ns as u64)?;
            win32::acquire_privilege(winnt::SE_SYSTEMTIME_NAME)?;

            if unsafe { sysinfoapi::SetSystemTime(&st) } == 0 {
                return err!("Failed to set system time");
            }
        }
        None => {
            // Unfortunately, Windows libraries don't provide an easy way to access
            // RTC yet: https://msdn.microsoft.com/en-us/library/aa908981.aspx
            //
            // Instead, a workaround is to use the Windows win32tm command to
            // resync the time using the Windows Time service.
            let status = Command::new("w32tm /resync /nowait").status()?;
            if !status.success() {
                return err!("w32tm failed");
            }
            if let Some(code) = status.code() {
                let mut flags = 0;
                if unsafe { wininet::InternetGetConnectedState(&mut flags, 0) } == 0 {
                    return err!("No internet connection on guest, sync not accurate");
                }
            }
        }
    }

    Ok(())
}
