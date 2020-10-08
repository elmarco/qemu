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

pub(crate) fn set_response_delimited() {
    unsafe { sys::ga_set_response_delimited(sys::ga_state) }
}

mod sys {
    #[repr(C)]
    pub struct GAState(libc::c_void);

    extern "C" {
        pub static ga_state: *mut GAState;

        pub fn ga_set_response_delimited(s: *mut GAState);

        pub fn slog(format: *const libc::c_char, ...);
    }
}
