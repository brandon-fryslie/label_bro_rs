use actix_web::{HttpResponse, Responder};

pub async fn index() -> impl Responder {
    HttpResponse::Ok().body("Label Bro 😎")
}

pub async fn print_labels() -> impl Responder {
    HttpResponse::Ok().body("Print Labels")
}

pub async fn preview_labels() -> impl Responder {
    HttpResponse::Ok().body("Preview Labels")
}

pub async fn print_image() -> impl Responder {
    HttpResponse::Ok().body("Print Image")
}

pub async fn discover_printers() -> impl Responder {
    HttpResponse::Ok().body("Discover Printers")
}
