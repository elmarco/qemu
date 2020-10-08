use crate::*;
use chrono::prelude::*;

pub(crate) fn get_timezone() -> Result<qapi::GuestTimezone> {
    let local = Local.timestamp(0, 0);
    let zone = Some(local.format("%Z").to_string());
    let offset = local.offset().fix().local_minus_utc() as i64;

    Ok(qapi::GuestTimezone { zone, offset })
}
