# ResourceChecker - Project Structure

1. **Create and Activate a Virtual Environment:**
    It's recommended to use a virtual environment to manage project dependencies.

    * On **Windows**:
        ```bash
        python -m venv .venv
        .\.venv\Scripts\activate
        ```
    * On **macOS/Linux**:
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

2.  **Install Dependencies:**
    Install all the required packages listed in the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```
    
## Directory Structure

```
ResourceChecker/
├── main.py                           # entry point
├── main_original.py                  # Backup of original monolithic file
├── test_structure.py                 # Validation test script
├── requirements.txt                  # Project dependencies
├── language_config.json             # Language preference storage
├── logs/                            # Generated log files
├── core/                            # Core business logic modules
│   ├── __init__.py                  # Core package initialization
│   ├── language.py                  # Internationalization & language management
│   ├── system_info.py              # System monitoring & process tracking
│   ├── hardware.py                 # CPU/GPU temperature & hardware monitoring
│   └── network.py                  # Network health checking & webhook notifications
├── gui/                            # User interface modules
│   ├── __init__.py                 # GUI package initialization
│   ├── main_window.py             # Main application window
│   ├── resource_monitor_window.py # Resource & temperature monitoring window
│   ├── network_settings_window.py # Network settings window
│   └── stress_test_window.py      # CPU stress testing window
└── utils/                          # Utility modules
    ├── __init__.py                # Utils package initialization
    └── logging.py                 # Logging, file management & auto-logging
```

### Running the Application
```bash
python main.py
```

### Running Tests
```bash
python test_structure.py
```
```bash
python test_language.py
```
```bash
python test_ui_elements.py
```

## Module Responsibilities

### Core Modules (`core/`)

#### `language.py`
- **LanguageManager**: Handles English/Turkish internationalization
- **LANGUAGE_DICT**: Complete translation dictionary
- **Global instance**: `language_manager` for application-wide use

#### `system_info.py`
- **SystemInfo**: CPU, memory, and network usage collection
- **ProcessMonitor**: Top CPU/network consuming process tracking

#### `hardware.py`
- **HardwareMonitor**: Advanced CPU temperature reading with multiple fallback strategies
- **GPU monitoring**: NVIDIA GPU usage and temperature via nvidia-smi (hidden console)
- **Cross-platform support**: Windows-focused with Linux/Mac compatibility

#### `network.py`
- **NetworkHealthChecker**: Multi-host network connectivity testing
- **WebhookConfig**: Webhook configuration management (JSON-based)
- **WebhookNotifier**: Microsoft Teams webhook notifications for alerts

### GUI Modules (`gui/`)

#### `main_window.py`
- **SystemMonitorGUI**: Main application interface
- **Features**: System monitoring, network health, process tracking, logging
- **Integration**: Launches resource monitor and stress test windows

#### `resource_monitor_window.py`
- **ResourceTempMonitorWindow**: Real-time hardware monitoring
- **Capabilities**: CPU/GPU/RAM monitoring with temperature tracking
- **Logging**: Configurable interval logging with file rotation

#### `stress_test_window.py`
- **CPUStressTestWindow**: CPU stress testing with performance scoring
- **Features**: Multi-core stress testing, performance metrics, duration tracking

### Utility Modules (`utils/`)

#### `logging.py`
- **Logger**: System log management with GUI integration
- **NetworkLogger**: Network-specific logging
- **FileManager**: File operations and export dialogs
- **AutoLogger**: Automatic periodic log saving

## Extra Info
- For executable file:
- pyinstaller --onefile -w ResourceChecker main.py 
- OUTPUT_PATH_FOR_EXE: dist\\ResourceChecker.exe