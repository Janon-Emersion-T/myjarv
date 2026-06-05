use std::env;
use std::path::Path;

fn main() {
    let args: Vec<String> = env::args().collect();
    let path = args.get(1).cloned().unwrap_or_else(|| ".".to_string());
    let exists = Path::new(&path).exists();
    println!("jarvis_file_guard path={} exists={}", path, exists);
}

