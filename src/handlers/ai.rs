use actix_web::{HttpResponse, Responder};

pub async fn generate() -> impl Responder {
    println!("generate handler called");
    HttpResponse::Ok().body("AI generated")
}
