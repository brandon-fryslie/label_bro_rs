use actix_web::web;
use crate::handlers::label;

pub fn init(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/")
            .route("", web::get().to(label::index))
            .route("printLabels", web::post().to(label::print_labels)) // Corrected function name
            .route("previewLabels", web::post().to(label::preview_labels))
            .route("printImage", web::post().to(label::print_image))
    );
}
