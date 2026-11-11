use std::process::Command;

fn omnirail(args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_omnirail"))
        .args(args)
        .output()
        .expect("binary omnirail bisa dijalankan")
}

#[test]
fn versi() {
    let out = omnirail(&["--version"]);
    assert!(out.status.success());
    assert_eq!(
        String::from_utf8_lossy(&out.stdout).trim(),
        "omnirail 0.0.1"
    );
}

#[test]
fn argumen_tidak_dikenal_keluar_dengan_kode_2() {
    let out = omnirail(&["serve"]);
    assert_eq!(out.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&out.stderr).contains("Pemakaian"));
}
