use chrono::prelude::*;
use std::time::{SystemTime, UNIX_EPOCH};

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
