use std::env;

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let joined = if args.is_empty() { "<none>".to_string() } else { args.join(" ") };
    let risk = if joined.contains("rm ") || joined.contains("delete") {
        "CRITICAL"
    } else if joined.contains("deploy") || joined.contains("push") {
        "HIGH"
    } else {
        "LOW"
    };
    println!("jarvis_command_guard risk={} command={}", risk, joined);
}

