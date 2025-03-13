use actix_web::{HttpResponse, Responder};

pub async fn generate() -> impl Responder {
    HttpResponse::Ok().body("AI Generate")
}
