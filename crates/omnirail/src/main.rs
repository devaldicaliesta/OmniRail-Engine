#![forbid(unsafe_code)]

use std::process::ExitCode;

const BANTUAN: &str = "Pemakaian: omnirail [--version | --help]";

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let args: Vec<&str> = args.iter().map(String::as_str).collect();
    match args.as_slice() {
        ["--version" | "-V"] => {
            println!("omnirail {}", omnirail_core::VERSION);
            ExitCode::SUCCESS
        }
        ["--help" | "-h"] => {
            println!("{BANTUAN}");
            ExitCode::SUCCESS
        }
        _ => {
            eprintln!("{BANTUAN}");
            ExitCode::from(2)
        }
    }
}
