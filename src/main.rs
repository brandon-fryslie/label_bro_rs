use actix_files as fs;
use actix_web::{web, App, HttpServer, HttpResponse, Result};
use tera::{Tera, Context};
mod routes;
mod python_bridge;
mod handlers;
mod models;
mod utils;

async fn index(tera: web::Data<Tera>) -> Result<HttpResponse> {
    let mut context = Context::new();
    context.insert("app_name", "Label Bro 😎");

    let rendered = tera.render("index.html", &context)
        .map_err(|_| actix_web::error::ErrorInternalServerError("Template error"))?;
    Ok(HttpResponse::Ok().content_type("text/html").body(rendered))
}
#[actix_rt::main]
async fn main() -> std::io::Result<()> {
    // Initialize the Python interpreter
    pyo3::prepare_freethreaded_python();

    let tera = Tera::new("templates/**/*").unwrap();

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(tera.clone()))
            .route("/", web::get().to(index))
            .service(fs::Files::new("/static", "./static").show_files_listing())
    })
    .bind("0.0.0.0:5099")?
    .run()
    .await
}

#[cfg(test)]
mod tests {
    use super::*;
    use actix_web::{test, App};

    #[actix_web::test]
    async fn test_index() {
        let app = test::init_service(App::new().configure(routes::init)).await;
        let req = test::TestRequest::get().uri("/").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }
}
