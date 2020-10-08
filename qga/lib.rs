use std::ffi::CString;

mod qapi;
mod qapi_sys;
mod qmp;

pub(crate) fn slog(msg: &str) {
    if let Ok(cs) = CString::new(msg) {
        unsafe {
            sys::slog(CString::new("%s").unwrap().as_ptr(), cs.as_ptr());
        }
    }
}

mod sys {
    extern "C" {
        pub fn slog(format: *const libc::c_char, ...);
    }
}
