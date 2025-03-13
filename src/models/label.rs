use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct LabelRequest {
    pub text: String,
    pub should_print_full_label: bool,
    pub should_print_small_label: bool,
}
