#![forbid(unsafe_code)]

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn versi_mengikuti_workspace() {
        assert_eq!(VERSION, "0.0.1");
    }
}
