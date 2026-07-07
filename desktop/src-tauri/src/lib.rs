use std::path::PathBuf;
use std::process::Child;
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;
use tauri::{Emitter, Manager, State};

mod sidecar;

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

pub struct BackendState {
    process: Mutex<Option<Child>>,
    port: Mutex<u16>,
    data_dir: Mutex<PathBuf>,
}

/// Tracks the overall startup sequence so the frontend can show progress.
pub struct StartupState {
    status: Mutex<StartupStatusKind>,
    message: Mutex<String>,
}

#[derive(Serialize, Clone, PartialEq, Debug)]
#[serde(rename_all = "snake_case")]
pub enum StartupStatusKind {
    Starting,
    PreparingWorkspace,
    StartingEngine,
    LoadingTools,
    Ready,
    Failed,
}

// ---------------------------------------------------------------------------
// Serialisable response structs
// ---------------------------------------------------------------------------

#[derive(Serialize)]
pub struct BackendInfo {
    pub base_url: String,
    pub port: u16,
    pub data_dir: String,
    pub healthy: bool,
}

#[derive(Serialize)]
pub struct AppInfo {
    pub app_version: String,
    pub backend_version: String,
    pub database_path: String,
    pub exports_dir: String,
    pub uploads_dir: String,
}

#[derive(Serialize, Clone)]
pub struct StartupStatus {
    pub status: StartupStatusKind,
    pub message: String,
}

#[derive(Serialize)]
pub struct StorageUsage {
    pub database_bytes: u64,
    pub uploads_bytes: u64,
    pub artifacts_bytes: u64,
    pub exports_bytes: u64,
    pub logs_bytes: u64,
    pub total_bytes: u64,
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

fn emit_startup(app: &tauri::AppHandle, kind: StartupStatusKind, msg: &str) {
    if let Some(state) = app.try_state::<StartupState>() {
        *state.status.lock().unwrap() = kind.clone();
        *state.message.lock().unwrap() = msg.to_string();
    }
    let payload = StartupStatus { status: kind, message: msg.to_string() };
    let _ = app.emit("startup_status", payload);
}

fn dir_size_bytes(path: &PathBuf) -> u64 {
    walkdir::WalkDir::new(path)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .filter_map(|e| e.metadata().ok())
        .map(|m| m.len())
        .sum()
}

// ---------------------------------------------------------------------------
// Tauri commands — backend / info
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_backend_base_url(state: State<BackendState>) -> String {
    let port = state.port.lock().unwrap();
    format!("http://127.0.0.1:{}/api", *port)
}

#[tauri::command]
fn get_backend_info(state: State<BackendState>) -> BackendInfo {
    let port = *state.port.lock().unwrap();
    let data_dir = state.data_dir.lock().unwrap().clone();
    BackendInfo {
        base_url: format!("http://127.0.0.1:{}/api", port),
        port,
        data_dir: data_dir.display().to_string(),
        healthy: sidecar::check_health(port),
    }
}

#[tauri::command]
fn get_app_info(state: State<BackendState>) -> AppInfo {
    let data_dir = state.data_dir.lock().unwrap().clone();
    AppInfo {
        app_version: env!("CARGO_PKG_VERSION").to_string(),
        backend_version: "0.2.0".to_string(),
        database_path: data_dir.join("database").join("ai_econometrics.db").display().to_string(),
        exports_dir: data_dir.join("exports").display().to_string(),
        uploads_dir: data_dir.join("uploads").display().to_string(),
    }
}

// ---------------------------------------------------------------------------
// Tauri commands — startup status
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_startup_status(state: State<StartupState>) -> StartupStatus {
    StartupStatus {
        status: state.status.lock().unwrap().clone(),
        message: state.message.lock().unwrap().clone(),
    }
}

// ---------------------------------------------------------------------------
// Tauri commands — storage
// ---------------------------------------------------------------------------

#[tauri::command]
fn get_storage_usage(state: State<BackendState>) -> StorageUsage {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let db_bytes = dir_size_bytes(&data_dir.join("database"));
    let up_bytes = dir_size_bytes(&data_dir.join("uploads"));
    let ar_bytes = dir_size_bytes(&data_dir.join("artifacts"));
    let ex_bytes = dir_size_bytes(&data_dir.join("exports"));
    let lg_bytes = dir_size_bytes(&data_dir.join("logs"));
    StorageUsage {
        database_bytes: db_bytes,
        uploads_bytes: up_bytes,
        artifacts_bytes: ar_bytes,
        exports_bytes: ex_bytes,
        logs_bytes: lg_bytes,
        total_bytes: db_bytes + up_bytes + ar_bytes + ex_bytes + lg_bytes,
    }
}

#[tauri::command]
fn reset_local_data(state: State<BackendState>) -> Result<(), String> {
    let data_dir = state.data_dir.lock().unwrap().clone();
    for sub in &["uploads", "artifacts", "exports"] {
        let dir = data_dir.join(sub);
        if dir.exists() {
            std::fs::remove_dir_all(&dir).map_err(|e| e.to_string())?;
            std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
        }
    }
    let db = data_dir.join("database").join("ai_econometrics.db");
    if db.exists() {
        std::fs::remove_file(&db).map_err(|e| e.to_string())?;
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Tauri commands — filesystem shortcuts
// ---------------------------------------------------------------------------

#[tauri::command]
fn open_data_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let _ = opener::open(data_dir);
}

#[tauri::command]
fn open_exports_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let _ = opener::open(data_dir.join("exports"));
}

#[tauri::command]
fn open_logs_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let _ = opener::open(data_dir.join("logs"));
}

// ---------------------------------------------------------------------------
// Application entrypoint
// ---------------------------------------------------------------------------

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            // Register both states up front so commands can always access them
            // without panicking, even before the backend is healthy.
            app.manage(StartupState {
                status: Mutex::new(StartupStatusKind::Starting),
                message: Mutex::new(String::new()),
            });
            app.manage(BackendState {
                process: Mutex::new(None),
                port: Mutex::new(0),
                data_dir: Mutex::new(PathBuf::new()),
            });

            let handle = app.handle().clone();

            std::thread::spawn(move || {
                emit_startup(&handle, StartupStatusKind::PreparingWorkspace,
                    "Preparing local workspace…");

                let data_dir = sidecar::resolve_data_dir(&handle);
                let port = sidecar::pick_port();

                log::info!("Data directory: {}", data_dir.display());
                log::info!("Selected port: {}", port);

                sidecar::ensure_directories(&data_dir);

                // Store data_dir and port early so commands are useful even
                // if the health check times out.
                if let Some(state) = handle.try_state::<BackendState>() {
                    *state.data_dir.lock().unwrap() = data_dir.clone();
                    *state.port.lock().unwrap() = port;
                }

                emit_startup(&handle, StartupStatusKind::StartingEngine,
                    "Starting analysis engine…");

                let child = match sidecar::start_backend(&handle, port, &data_dir) {
                    Ok(c) => c,
                    Err(e) => {
                        log::error!("Failed to start backend: {}", e);
                        emit_startup(&handle, StartupStatusKind::Failed,
                            "Could not start the analysis engine. Check the logs for details.");
                        return;
                    }
                };

                // Store the process handle for clean shutdown.
                if let Some(state) = handle.try_state::<BackendState>() {
                    *state.process.lock().unwrap() = Some(child);
                }

                emit_startup(&handle, StartupStatusKind::LoadingTools,
                    "Loading research tools…");

                if !sidecar::wait_for_health(port, Duration::from_secs(30)) {
                    log::error!("Backend failed health check after 30 seconds");
                    emit_startup(&handle, StartupStatusKind::Failed,
                        "The analysis engine did not respond in time. Check the logs for details.");
                } else {
                    emit_startup(&handle, StartupStatusKind::Ready, "Ready");
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_base_url,
            get_backend_info,
            get_app_info,
            get_startup_status,
            get_storage_usage,
            reset_local_data,
            open_data_folder,
            open_exports_folder,
            open_logs_folder,
        ])
        .build(tauri::generate_context!())
        .expect("error while building application")
        .run(|app, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
                if let Some(state) = app.try_state::<BackendState>() {
                    sidecar::stop_backend(&state.process);
                }
            }
        });
}
