pub use common::{err, Error, Result};
mod qapi_sys;

fn main() {
    qapi_sys::cabi()
}
