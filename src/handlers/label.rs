
use actix_web::{HttpResponse, Responder};
use pyo3::prelude::*;
use pyo3::types::PyTuple;

pub async fn print_labels() -> impl Responder {
    println!("print_labels handler called");

    let result = Python::with_gil(|py| {
        // Define the tuple with the correct types
        let r_tuple: (&str, i32, &str) = ("label_text", 696, "full");
        
        // Convert the tuple to a PyObject using PyTuple
        let args = PyTuple::new(py, &[r_tuple.0, r_tuple.1.to_string().as_str(), r_tuple.2]);

        // Debugging statement to check the conversion
        println!("Python function called with args: {:?}", args);

        Ok::<_, PyErr>(())
    });

    match result {
        Ok(_) => HttpResponse::Ok().body("Labels printed successfully"),
        Err(e) => {
            eprintln!("Error constructing Python object: {:?}", e);
            HttpResponse::InternalServerError().body("Failed to print labels")
        }
    }
}

pub async fn index() -> impl Responder {
    HttpResponse::Ok().body("Welcome to Label Bro!")
}

pub async fn preview_labels() -> impl Responder {
    HttpResponse::Ok().body("Preview Labels")
}

pub async fn print_image() -> impl Responder {
    HttpResponse::Ok().body("Print Image")
}

