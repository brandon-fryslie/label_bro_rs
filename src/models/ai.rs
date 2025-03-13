use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct AIRequest {
    pub prompt: String,
}
