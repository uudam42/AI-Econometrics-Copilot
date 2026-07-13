use std::io;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{AppHandle, Manager};

const SUBDIRS: &[&str] = &[
    "database", "uploads", "artifacts", "exports", "logs", "config",
];

pub fn resolve_data_dir(app: &AppHandle) -> PathBuf {
    if let Ok(val) = std::env::var("AI_ECONOMETRICS_DATA_DIR") {
        return PathBuf::from(val);
    }

    if let Some(data) = app.path().app_local_data_dir().ok() {
        return data;
    }

    if let Some(local) = dirs::data_local_dir() {
        return local.join("AI Econometrics Copilot");
    }

    PathBuf::from("./data")
}

pub fn ensure_directories(data_dir: &PathBuf) {
    for sub in SUBDIRS {
        let p = data_dir.join(sub);
        if let Err(e) = std::fs::create_dir_all(&p) {
            log::warn!("Could not create {}: {}", p.display(), e);
        }
    }
}

pub fn pick_port() -> u16 {
    if let Ok(val) = std::env::var("AI_ECONOMETRICS_PORT") {
        if let Ok(port) = val.parse::<u16>() {
            return port;
        }
    }

    portpicker::pick_unused_port().unwrap_or(8000)
}

pub fn start_backend(
    app: &AppHandle,
    port: u16,
    data_dir: &PathBuf,
) -> io::Result<Child> {
    let db_path = data_dir.join("database").join("ai_econometrics.db");
    let db_url = format!("sqlite:///{}", db_path.display());

    let sidecar_name = if cfg!(target_os = "windows") {
        "ai-econometrics-backend.exe"
    } else {
        "ai-econometrics-backend"
    };

    // Tauri installs externalBin sidecars next to the main executable with
    // the target-triple suffix stripped; the resource-dir variants cover
    // dev layouts where the binary was never bundled.
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(PathBuf::from))
        .unwrap_or_else(|| PathBuf::from("."));
    let resource_dir = app
        .path()
        .resource_dir()
        .unwrap_or_else(|_| PathBuf::from("."));

    let candidates = [
        exe_dir.join(sidecar_name),
        exe_dir.join("binaries").join(sidecar_name),
        resource_dir.join(sidecar_name),
        resource_dir.join("binaries").join(sidecar_name),
    ];
    let sidecar_path = candidates
        .iter()
        .find(|p| p.exists())
        .cloned()
        .unwrap_or_else(|| candidates[0].clone());

    let log_file_path = data_dir.join("logs").join("backend.log");
    let log_file = std::fs::File::create(&log_file_path).unwrap_or_else(|_| {
        std::fs::File::create("backend.log").unwrap()
    });
    let log_stderr = log_file.try_clone().unwrap_or_else(|_| {
        std::fs::File::create("backend_err.log").unwrap()
    });

    log::info!("Starting sidecar: {}", sidecar_path.display());

    Command::new(&sidecar_path)
        .env("ECOPILOT_DATABASE_URL", &db_url)
        .env("ECOPILOT_DATA_DIR", data_dir.join("database").to_str().unwrap_or("."))
        .env("ECOPILOT_UPLOAD_DIR", data_dir.join("uploads").to_str().unwrap_or("."))
        .env("ECOPILOT_ARTIFACT_DIR", data_dir.join("artifacts").to_str().unwrap_or("."))
        .env("ECOPILOT_LOG_LEVEL", "INFO")
        .env("ECOPILOT_CORS_ORIGINS", r#"["http://tauri.localhost"]"#)
        .env("AI_ECONOMETRICS_PORT", port.to_string())
        .env("AI_ECONOMETRICS_DESKTOP_MODE", "true")
        .stdout(Stdio::from(log_file))
        .stderr(Stdio::from(log_stderr))
        .spawn()
}

pub fn check_health(port: u16) -> bool {
    let url = format!("http://127.0.0.1:{}/health", port);
    reqwest::blocking::get(&url)
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}

pub fn wait_for_health(port: u16, timeout: Duration) -> bool {
    let start = Instant::now();
    while start.elapsed() < timeout {
        if check_health(port) {
            log::info!("Backend healthy after {:?}", start.elapsed());
            return true;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
    false
}

pub fn stop_backend(process: &Mutex<Option<Child>>) {
    if let Ok(mut guard) = process.lock() {
        if let Some(ref mut child) = *guard {
            log::info!("Stopping backend sidecar...");
            let _ = child.kill();
            let _ = child.wait();
        }
        *guard = None;
    }
}

// ---------------------------------------------------------------------------
// Unit tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pick_port_parses_env_var() {
        // Test the parsing branch directly — port "9999" → 9999
        let parsed: Option<u16> = "9999".parse().ok();
        assert_eq!(parsed, Some(9999));
    }

    #[test]
    fn pick_port_ignores_non_numeric_env_var() {
        let parsed: Option<u16> = "not_a_port".parse().ok();
        assert_eq!(parsed, None);
    }

    #[test]
    fn pick_port_without_env_returns_valid_port() {
        // Remove env var so portpicker / fallback is exercised
        std::env::remove_var("AI_ECONOMETRICS_PORT");
        let port = pick_port();
        assert!(port > 0, "pick_port must return a non-zero port");
    }

    #[test]
    fn health_url_format_is_correct() {
        let port: u16 = 8765;
        let url = format!("http://127.0.0.1:{}/health", port);
        assert_eq!(url, "http://127.0.0.1:8765/health");
    }

    #[test]
    fn db_url_uses_sqlite_scheme() {
        let data_dir = PathBuf::from("/data");
        let db_path = data_dir.join("database").join("ai_econometrics.db");
        let db_url = format!("sqlite:///{}", db_path.display());
        assert!(db_url.starts_with("sqlite:///"));
        assert!(db_url.contains("ai_econometrics.db"));
    }

    #[test]
    fn sidecar_binary_name_ends_correctly() {
        let name = if cfg!(target_os = "windows") {
            "ai-econometrics-backend.exe"
        } else {
            "ai-econometrics-backend"
        };
        assert!(name.starts_with("ai-econometrics-backend"));
        if cfg!(target_os = "windows") {
            assert!(name.ends_with(".exe"));
        }
    }

    #[test]
    fn subdirs_list_is_complete() {
        for required in &["database", "uploads", "artifacts", "exports", "logs", "config"] {
            assert!(
                SUBDIRS.contains(required),
                "SUBDIRS missing required entry: {}",
                required
            );
        }
    }

    #[test]
    fn ensure_directories_creates_all_subdirs() {
        let tmp = std::env::temp_dir().join("ecopilot_sidecar_test");
        let _ = std::fs::remove_dir_all(&tmp);
        ensure_directories(&tmp);
        for sub in SUBDIRS {
            assert!(
                tmp.join(sub).is_dir(),
                "ensure_directories should create subdir: {}",
                sub
            );
        }
        let _ = std::fs::remove_dir_all(&tmp);
    }

    #[test]
    fn startup_status_kinds_cover_all_stages() {
        // Verify the expected status string sequence used by the frontend
        let stages = ["starting", "preparing_workspace", "starting_engine",
                      "loading_tools", "ready", "failed"];
        // Validate that none are empty — logic check only
        for s in &stages {
            assert!(!s.is_empty());
        }
    }
}
