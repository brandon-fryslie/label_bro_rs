# Actix Actor System Example

This program demonstrates a simple Actix actor system that sends and receives messages.

## Basic Actix Actor Example

1. **Create a Rust file (e.g., `main.rs`)**: Implement a basic Actix actor system.

```rust
use actix::prelude::*;

// Define a message
struct Ping;

// Implement the Message trait for Ping
impl Message for Ping {
    type Result = &'static str;
}

// Define an actor
struct MyActor;

// Implement the Actor trait for MyActor
impl Actor for MyActor {
    type Context = Context<Self>;
}

// Implement the Handler trait for MyActor to handle Ping messages
impl Handler<Ping> for MyActor {
    type Result = &'static str;

    fn handle(&mut self, _msg: Ping, _ctx: &mut Context<Self>) -> Self::Result {
        "Pong"
    }
}

#[actix::main]
async fn main() {
    // Start the system
    let system = System::new();

    // Start MyActor
    let addr = MyActor.start();

    // Send a Ping message and wait for the response
    let res = addr.send(Ping).await;

    match res {
        Ok(response) => println!("Received: {}", response),
        Err(err) => println!("Error: {:?}", err),
    }

    // Stop the system
    system.stop();
}
```

2. **Add dependencies**: Ensure your `Cargo.toml` includes the Actix dependency.

```toml
[dependencies]
actix = "0.12"
```

3. **Run the program**: Use `cargo run` to execute the program.
````

## Running Tests

To run the tests for your Rust project, you can use the following command:

```bash
cargo test
```

This command will compile your project and run all the tests defined in your `tests` directory and any test modules within your source files.

If you want to run a specific test or a subset of tests, you can use the `--test` flag followed by the test name. For example:

```bash
cargo test test_index
```

This will run only the test named `test_index`.

If you encounter any issues or need further customization, feel free to ask!
