#[cfg(test)]
mod tests {
    use label_bro_rs::routes;
    use actix_web::{test, App};

    #[actix_web::test]
    async fn test_label_handler() {
        let app = test::init_service(App::new().configure(routes::init)).await;
        let req = test::TestRequest::post().uri("/label").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }

    #[actix_web::test]
    async fn test_ai_handler() {
        let app = test::init_service(App::new().configure(routes::init)).await;
        let req = test::TestRequest::post().uri("/ai").to_request();
        let resp = test::call_service(&app, req).await;
        assert!(resp.status().is_success());
    }
}
