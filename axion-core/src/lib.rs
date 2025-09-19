pub mod meta_core;
pub mod integrity;
pub mod audit_ledger;
pub mod state;
pub mod security;

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct AxionCore {
    pub version: String,
    pub timestamp: String,
}

impl AxionCore {
    pub fn new() -> Self {
        Self {
            version: "0.1.0".to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
        }
    }
}
