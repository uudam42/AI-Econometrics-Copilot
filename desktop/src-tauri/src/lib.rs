use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;

use serde::Serialize;
use tauri::{AppHandle, Manager, State};

mod sidecar;

pub struct BackendState {
    process: Mutex<Option<Child>>,
    port: Mutex<u16>,
    data_dir: Mutex<PathBuf>,
}

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

#[tauri::command]
fn open_data_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let _ = opener::open(data_dir);
}

#[tauri::command]
fn open_exports_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let exports = data_dir.join("exports");
    let _ = opener::open(exports);
}

#[tauri::command]
fn open_logs_folder(state: State<BackendState>) {
    let data_dir = state.data_dir.lock().unwrap().clone();
    let logs = data_dir.join("logs");
    let _ = opener::open(logs);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let data_dir = sidecar::resolve_data_dir(app.handle());
            let port = sidecar::pick_port();

            log::info!("Data directory: {}", data_dir.display());
            log::info!("Selected port: {}", port);

            sidecar::ensure_directories(&data_dir);

            let child = match sidecar::start_backend(app.handle(), port, &data_dir) {
                Ok(child) => child,
                Err(e) => {
                    log::error!("Failed to start backend: {}", e);
                    return Err(e.into());
                }
            };

            if !sidecar::wait_for_health(port, Duration::from_secs(30)) {
                log::error!("Backend failed health check after 30 seconds");
            }

            app.manage(BackendState {
                process: Mutex::new(Some(child)),
                port: Mutex::new(port),
                data_dir: Mutex::new(data_dir),
            });

            Ok(())
        })
        .on_event(|app, event| {
            if let tauri::RunEvent::ExitRequested { .. } = event {
                if let Some(state) = app.try_state::<BackendState>() {
                    sidecar::stop_backend(&state.process);
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            get_backend_base_url,
            get_backend_info,
            get_app_info,
            open_data_folder,
            open_exports_folder,
            open_logs_folder,
        ])
        .run(tauri::generate_context!())
        .expect("error while running application");
}
