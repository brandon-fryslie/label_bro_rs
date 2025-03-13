use actix_web::{test, App};
use crate::routes::init;

#[actix_web::test]
async fn test_index() {
    let app = test::init_service(App::new().configure(init)).await;
    let req = test::TestRequest::get().uri("/").to_request();
    let resp = test::call_service(&app, req).await;
    assert!(resp.status().is_success());
}
