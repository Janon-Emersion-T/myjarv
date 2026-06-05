use std::env;

fn main() {
    let input = env::args().skip(1).collect::<Vec<String>>().join(" ");
    let normalized = input.trim().to_lowercase();
    println!("jarvis_text_utils normalized={}", normalized);
}

