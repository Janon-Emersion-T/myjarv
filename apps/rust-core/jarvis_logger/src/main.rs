use std::env;

fn main() {
    let event = env::args().nth(1).unwrap_or_else(|| "jarvis.logger".to_string());
    println!("jarvis_logger event={}", event);
}

