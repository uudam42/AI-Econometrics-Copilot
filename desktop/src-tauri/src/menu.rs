use tauri::menu::{MenuBuilder, MenuItemBuilder, SubmenuBuilder};

pub fn build_app_menu(
    app: &tauri::AppHandle,
) -> tauri::Result<tauri::menu::Menu<tauri::Wry>> {
    // File submenu
    let new_project = MenuItemBuilder::with_id("nav_home", "New Project")
        .accelerator("CmdOrCtrl+N")
        .build(app)?;
    let analyze = MenuItemBuilder::with_id("nav_quick_analyze", "Analyse My Excel\u{2026}")
        .accelerator("CmdOrCtrl+O")
        .build(app)?;
    let open_data = MenuItemBuilder::with_id("open_data_folder", "Open Data Folder")
        .build(app)?;
    let open_exports =
        MenuItemBuilder::with_id("open_exports_folder", "Open Exports Folder").build(app)?;
    let open_logs =
        MenuItemBuilder::with_id("open_logs_folder", "Open Logs Folder").build(app)?;
    let exit = MenuItemBuilder::with_id("app_exit", "Exit")
        .accelerator("Alt+F4")
        .build(app)?;

    let file_menu = SubmenuBuilder::new(app, "File")
        .item(&new_project)
        .item(&analyze)
        .separator()
        .item(&open_data)
        .item(&open_exports)
        .item(&open_logs)
        .separator()
        .item(&exit)
        .build()?;

    // Help submenu
    let quick_start =
        MenuItemBuilder::with_id("nav_quick_start", "Quick Start Guide").build(app)?;
    let troubleshoot =
        MenuItemBuilder::with_id("open_logs_folder_help", "Troubleshooting (Open Logs)")
            .build(app)?;
    let about = MenuItemBuilder::with_id("show_about", "About AI Econometrics Copilot")
        .build(app)?;

    let help_menu = SubmenuBuilder::new(app, "Help")
        .item(&quick_start)
        .item(&troubleshoot)
        .separator()
        .item(&about)
        .build()?;

    MenuBuilder::new(app)
        .item(&file_menu)
        .item(&help_menu)
        .build()
}
