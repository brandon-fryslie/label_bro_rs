use actix_web::web;
use crate::handlers::{label, ai};

pub fn init(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/")
            .route("", web::get().to(label::index))
            .route("printLabels", web::post().to(label::print_labels))
            .route("previewLabels", web::post().to(label::preview_labels))
            .route("aiGenerate", web::post().to(ai::generate))
            .route("printImage", web::post().to(label::print_image))
            .route("discoverPrinters", web::get().to(label::discover_printers))
    );
}
