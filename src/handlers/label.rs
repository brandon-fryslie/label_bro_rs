use actix_web::{HttpResponse, Responder, Error};
use pyo3::types::PyTuple;

use pyo3::prelude::*;


// pub async fn print_labels() -> impl Responder {
pub async fn print_labels() -> impl Responder {
    println!("print_labels handler called");

    let result = Python::with_gil(|py| {
        let r_tuple = ("label_text", 696, "full");
        let args = r_tuple.into_pyobject(py);

        Ok::<_, PyErr>(args)
    });

    match result {
        Ok(_) => HttpResponse::Ok().body("Labels printed successfully"),
        Err(e) => {
            eprintln!("Error constructing Python object: {:?}", e);
            HttpResponse::InternalServerError().body("Failed to print labels")
        }
    })
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

