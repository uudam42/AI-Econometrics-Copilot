use std::io;
use std::net::TcpListener;
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::AppHandle;

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

    let resource_dir = app
        .path()
        .resource_dir()
        .unwrap_or_else(|_| PathBuf::from("."));
    let sidecar_path = resource_dir.join("binaries").join(sidecar_name);

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
