"""
Language management for ResourceChecker application.

Provides internationalization support for English and Turkish languages.
"""

import os
import json


# Global language dictionary
LANGUAGE_DICT = {
    'en': {
        # Main Window
        'main_title': 'Resource Checker - System Monitor',
        'settings_frame': 'Settings',
        'system_interval': 'System Monitoring Period (seconds):',
        'network_interval': 'Network Check Period (seconds):',
        'top_apps_count': 'Top consuming apps count:',
        'auto_log': 'Auto Log Save',
        'webhook_settings': '🔔 Webhook Settings',
        'start_monitoring': 'Start Monitoring',
        'stop_monitoring': 'Stop Monitoring',
        'network_health_check': 'Network Health Check',
        'auto_network_monitoring': 'Auto Network Monitoring',
        'stop_auto_network': 'Stop Auto Network Monitoring',
        'resource_temp_monitor': 'Resource & Temp Monitor',
        'cpu_stress_test': 'CPU Stress Test',
        'system_info_frame': 'System Information',
        'cpu_usage': 'CPU Usage: --',
        'ram_usage': 'RAM Usage: --',
        'network_status': 'Network Status: --',
        'top_cpu_apps': 'Top CPU Consuming Apps',
        'top_network_apps': 'Top Network Consuming Apps',
        'system_logs': 'System Log Records',
        'network_logs': 'Network Log Records',
        'clear_system_logs': 'Clear System Logs',
        'export_system_logs': 'Export System Logs',
        'clear_network_logs': 'Clear Network Logs',
        'export_network_logs': 'Export Network Logs',
        
        # Resource & Temperature Monitor
        'resource_temp_title': 'Resource & Temperature Monitor',
        'log_settings': 'Log Settings',
        'enable_logging': 'Enable Log Recording',
        'log_interval': 'Log Interval (sec):',
        'log_status_active': 'Log: Active',
        'log_status_inactive': 'Log: Inactive',
        'open_log_folder': '📁 Open Log Folder',
        'cpu_header': 'CPU',
        'gpu_header': 'GPU',
        'ram_header': 'RAM',
        'usage': 'Usage: - %',
        'temperature': 'Temperature: - °C',
        'min_temp': 'Min: - °C',
        'max_temp': 'Max: - °C',
        'usage_percent': 'Usage (%): - %',
        'usage_mb': 'Usage (MB): - / - MB',
        'gpu_util_not_available': 'GPUtil library not installed.',
        'gpu_install_hint': 'pip install gputil',
        
        # CPU Stress Test
        'stress_test_title': 'CPU Stress Test',
        'core_count': 'Number of Cores to Use:',
        'start_test': 'Start Test',
        'stop_test': 'Stop Test',
        'status_waiting': 'Status: Waiting',
        'status_running': 'Status: Running with {0} cores...',
        'status_stopped': 'Status: Stopped.',
        'performance_scores': 'Performance Scores',
        'current_score': 'Current Score: --',
        'average_score': 'Average Score: --',
        'max_score': 'Max Score: --',
        'test_duration': 'Test Duration: 00:00',
        
        # Standalone Stress Test
        'stress_standalone_title': 'CPU Stress Test',
        'core_count_label': 'Core Count:',
        'start_button': 'Start',
        'stop_button': 'Stop',
        'status_waiting_standalone': 'Status: Waiting',
        'status_running_standalone': 'Status: {0} processes running',
        'status_completed': 'Completed - Avg: {0:.0f}, Max: {1:.0f}',
        'status_stopped_standalone': 'Status: Stopped',
        'total_cpu': 'Total CPU: {0:.1f} %',
        'performance_frame': 'Performance',
        'current_label': 'Current: --',
        'average_label': 'Average: --',
        'max_label': 'Max: --',
        'duration_label': 'Duration: 00:00',
        'per_core_usage': 'Per-Core Usage (%):',
        
        # Log Messages
        'log_cleared': 'Log records cleared',
        'monitoring_started': 'Monitoring started - Update every {0} seconds',
        'monitoring_stopped': 'Monitoring stopped - Usage info reset',
        'network_monitoring_started': 'Auto network monitoring started - Every {0} seconds',
        'network_monitoring_stopped': 'Auto network monitoring stopped',
        'resource_monitor_opened': 'Resource & Temperature Monitor opened.',
        'stress_test_started': 'CPU Stress Test started with {0} cores.',
        'stress_test_stopped': 'CPU Stress Test stopped.',
        'stress_test_completed': 'CPU Stress Test completed. Duration: {0:02d}:{1:02d}, Avg Score: {2:.1f}, Max Score: {3:.1f}',
        'top_apps_updated': 'Top consuming apps count updated to {0}',
        'auto_logging_enabled': 'Auto log saving enabled: New file will be created when reaching 500KB(written every 1 minute)',
        'auto_logging_disabled': 'Auto log saving disabled - File writing stopped',
        'network_auto_logging_enabled': 'Auto network log saving enabled: New file will be created when reaching 500KB',
        'network_auto_logging_disabled': 'Auto network log saving disabled - File writing stopped',
        
        # Network Health
        'network_health_header': '=== Network Health Check ===',
        'health_check_completed': '=== Health Check Completed ===',
        'network_connection_error': 'NETWORK CONNECTION ERROR',
        'all_connections_ok': 'ALL NETWORK CONNECTIONS OK',
        'partial_connection': 'PARTIAL NETWORK CONNECTION ({0}/{1} OK)',
        'connection_ok': 'Network Connection OK',
        'connection_nok': 'NETWORK CONNECTION NOK ERROR',
        'partial_nok': 'NETWORK CONNECTION PARTIAL NOK ERROR',
        'host_status': 'HOST STATUS - {0}: {1}',
        'reachable': '✓ Reachable',
        'unreachable': '✗ Unreachable',
        
        # Dialogs and Messages
        'warning': 'Warning',
        'error': 'Error',
        'success': 'Success',
        'confirm': 'Confirm',
        'log_folder_not_found': 'Log Folder Not Found',
        'log_folder_message': 'Log folder does not exist.\n\nPlease start logging.',
        'log_folder_error': 'Error occurred while opening log folder: {0}',
        'export_success': 'Log file saved: {0}',
        'export_error': 'Error occurred while exporting log: {0}',
        
        # Language Toggle
        'language_english': 'English',
        'language_turkish': 'Türkçe',

        # --- Added: CPU Stress Test extra labels ---
        'per_core_score': 'Per-Core Score:',
        'sustainability': 'Sustainability:',
        'current_cpu_score': 'Current CPU Score: {0:.2f} MOp/s',
        'per_core_cpu_score': 'Per-Core Score: {0:.2f} MOp/s',
        'average_cpu_score': 'Average CPU Score: {0:.2f} MOp/s',
        'peak_cpu_score': 'Peak CPU Score: {0:.2f} MOp/s',
        'sustainability_value': 'Sustainability: {0:.1f}%',
        'test_duration_label': 'Test Duration: {0:02d}:{1:02d}',

        # --- Added: Webhook window labels/messages ---
        'webhook_window_title': 'Webhook Settings',
        'name_label': 'Name:',
        'url_label': 'URL:',
        'type_label': 'Type:',
        'active_label': 'Active',
        'threshold_label': 'Threshold (%):',
        'mode_add_new': 'Mode: Add New',
        'mode_editing': "Mode: Editing '{0}'",
        'add_new_btn': 'Add New',
        'save_changes_btn': 'Save Changes',
        'cancel_edit_btn': 'Cancel Edit',
        'send_test_btn': 'Send Test',
        'remove_selected_btn': 'Remove Selected',
        'close_btn': 'Close',
        'validation_title': 'Validation',
        'validation_name_url_required': 'Name and URL are required.',
        'duplicate_title': 'Duplicate',
        'duplicate_exists': "A webhook named '{0}' already exists. Select it to edit or use New for another.",
        'threshold_number_error': 'Threshold must be a number.',
        'duplicate_rename_error': "Another webhook named '{0}' already exists.",
        'test_title': 'Test',
        'test_select_warning': 'Select at least one webhook.',
        'test_results_title': 'Test Results',
        'test_results_message': 'Sent: {0}\nFailed: {1}',
        'test_message_title': '🔔 Test Webhook Message',
        'test_message_body': "This is a test message for webhook '{0}'.\n\nType: {1}\nActive: {2}\nTime: {3}",
        # --- Added: Network Settings Window ---
        'network_settings_title': 'Network Settings',
        'host_list_label': 'Test Hosts:',
        'host_name_label': 'Name:',
        'host_address_label': 'Address:',
        'add_host_btn': 'Add Host',
        'remove_host_btn': 'Remove Selected',
        'reset_hosts_btn': 'Reset Defaults',
        'close_window_btn': 'Close',
        'host_add_warning_title': 'Validation',
        'host_add_warning_msg': 'Name and address are required.',
        'host_remove_warning_title': 'Selection',
        'host_remove_warning_msg': 'Select at least one host to remove.',
        'hosts_reset_info_title': 'Reset',
        'hosts_reset_info_msg': 'Host list reset to defaults.',
    },
    'tr': {
        # Main Window
        'main_title': 'Resource Checker - System Monitor',
        'settings_frame': 'Ayarlar',
        'system_interval': 'Sistem İzleme Periyodu (saniye):',
        'network_interval': 'Network Kontrol Periyodu (saniye):',
        'top_apps_count': 'En çok kullanan uygulama sayısı:',
        'auto_log': 'Otomatik Log Kaydet',
        'webhook_settings': '🔔 Webhook Ayarları',
        'start_monitoring': 'İzlemeyi Başlat',
        'stop_monitoring': 'İzlemeyi Durdur',
        'network_health_check': 'Network Health Check',
        'auto_network_monitoring': 'Otomatik Network İzleme',
        'stop_auto_network': 'Otomatik Network İzlemeyi Durdur',
        'resource_temp_monitor': 'Resource & Temp Monitor',
        'cpu_stress_test': 'CPU Stress Test',
        'system_info_frame': 'Sistem Bilgileri',
        'cpu_usage': 'CPU Kullanımı: --',
        'ram_usage': 'RAM Kullanımı: --',
        'network_status': 'Network Durumu: --',
        'top_cpu_apps': 'En Çok CPU Kullanan Uygulamalar',
        'top_network_apps': 'En Çok Network Kullanan Uygulamalar',
        'system_logs': 'Sistem Log Kayıtları',
        'network_logs': 'Network Log Kayıtları',
        'clear_system_logs': 'Sistem Log Temizle',
        'export_system_logs': 'Sistem Log Export',
        'clear_network_logs': 'Network Log Temizle',
        'export_network_logs': 'Network Log Export',
        
        # Resource & Temperature Monitor
        'resource_temp_title': 'Kaynak & Sıcaklık Monitörü',
        'log_settings': 'Log Ayarları',
        'enable_logging': 'Log Kaydını Etkinleştir',
        'log_interval': 'Log Aralığı (sn):',
        'log_status_active': 'Log: Aktif',
        'log_status_inactive': 'Log: Pasif',
        'open_log_folder': '📁 Log Klasörünü Aç',
        'cpu_header': 'CPU',
        'gpu_header': 'GPU',
        'ram_header': 'RAM',
        'usage': 'Kullanım: - %',
        'temperature': 'Sıcaklık: - °C',
        'min_temp': 'Min: - °C',
        'max_temp': 'Max: - °C',
        'usage_percent': 'Kullanım (%): - %',
        'usage_mb': 'Kullanım (MB): - / - MB',
        'gpu_util_not_available': 'GPUtil kütüphanesi yüklü değil.',
        'gpu_install_hint': 'pip install gputil',
        
        # CPU Stress Test
        'stress_test_title': 'CPU Stres Testi',
        'core_count': 'Kullanılacak Çekirdek Sayısı:',
        'start_test': 'Testi Başlat',
        'stop_test': 'Testi Durdur',
        'status_waiting': 'Durum: Beklemede',
        'status_running': 'Durum: {0} çekirdek ile çalışıyor...',
        'status_stopped': 'Durum: Durduruldu.',
        'performance_scores': 'Performans Puanları',
        'current_score': 'Mevcut Puan: --',
        'average_score': 'Ortalama Puan: --',
        'max_score': 'En Yüksek Puan: --',
        'test_duration': 'Test Süresi: 00:00',
        
        # Standalone Stress Test
        'stress_standalone_title': 'CPU Stress Test',
        'core_count_label': 'Çekirdek Sayısı:',
        'start_button': 'Başlat',
        'stop_button': 'Durdur',
        'status_waiting_standalone': 'Durum: Beklemede',
        'status_running_standalone': 'Durum: {0} süreç çalışıyor',
        'status_completed': 'Tamamlandı - Ort: {0:.0f}, Max: {1:.0f}',
        'status_stopped_standalone': 'Durum: Durduruldu',
        'total_cpu': 'Toplam CPU: {0:.1f} %',
        'performance_frame': 'Performans',
        'current_label': 'Mevcut: --',
        'average_label': 'Ort: --',
        'max_label': 'Max: --',
        'duration_label': 'Süre: 00:00',
        'per_core_usage': 'Çekirdek Bazlı Kullanım (%):',
        
        # Log Messages
        'log_cleared': 'Log kayıtları temizlendi',
        'monitoring_started': 'İzleme başlatıldı - {0} saniye aralıklarla güncelleme',
        'monitoring_stopped': 'İzleme durduruldu - Kullanım bilgileri sıfırlandı',
        'network_monitoring_started': 'Otomatik network izleme başlatıldı - {0} saniye aralıklarla',
        'network_monitoring_stopped': 'Otomatik network izleme durduruldu',
        'resource_monitor_opened': 'Kaynak & Sıcaklık Monitörü açıldı.',
        'stress_test_started': 'CPU Stres Testi {0} çekirdek ile başlatıldı.',
        'stress_test_stopped': 'CPU Stres Testi durduruldu.',
        'stress_test_completed': 'CPU Stres Testi tamamlandı. Süre: {0:02d}:{1:02d}, Ort. Puan: {2:.1f}, Max Puan: {3:.1f}',
        'top_apps_updated': 'En çok kullanan uygulama sayısı {0} olarak güncellendi',
        'auto_logging_enabled': 'Otomatik log kaydetme etkin: 500KB\'a ulaşınca yeni dosya açılacak(1 dakikada bir yazılır)',
        'auto_logging_disabled': 'Otomatik log kaydetme devre dışı - dosya yazımı durdu',
        'network_auto_logging_enabled': 'Otomatik network log kaydetme etkin: 500KB\'a ulaşınca yeni dosya açılacak',
        'network_auto_logging_disabled': 'Otomatik network log kaydetme devre dışı - dosya yazımı durdu',
        
        # Network Health
        'network_health_header': '=== Network Health Check ===',
        'health_check_completed': '=== Health Check Tamamlandı ===',
        'network_connection_error': 'NETWORK CONNECTION ERROR',
        'all_connections_ok': 'ALL NETWORK CONNECTIONS OK',
        'partial_connection': 'PARTIAL NETWORK CONNECTION ({0}/{1} OK)',
        'connection_ok': 'Network Connection OK',
        'connection_nok': 'NETWORK CONNECTION NOK ERROR',
        'partial_nok': 'NETWORK CONNECTION PARTIAL NOK ERROR',
        'host_status': 'HOST STATUS - {0}: {1}',
        'reachable': '✓ Erişilebilir',
        'unreachable': '✗ Erişilemiyor',
        
        # Dialogs and Messages
        'warning': 'Uyarı',
        'error': 'Hata',
        'success': 'Başarılı',
        'confirm': 'Onay',
        'log_folder_not_found': 'Log Klasörü Bulunamadı',
        'log_folder_message': 'Log klasörü mevcut değil.\n\nLütfen loglamaç başlatınız.',
        'log_folder_error': 'Log klasörü açılırken hata oluştu: {0}',
        'export_success': 'Log dosyası kaydedildi: {0}',
        'export_error': 'Log export edilirken hata oluştu: {0}',
        
        # Language Toggle
        'language_english': 'English',
        'language_turkish': 'Türkçe',

        # --- Eklenen: CPU Stres Testi ek etiketler ---
        'per_core_score': 'Çekirdek Başına Puan:',
        'sustainability': 'Sürdürülebilirlik:',
        'current_cpu_score': 'Anlık CPU Puanı: {0:.2f} MOp/s',
        'per_core_cpu_score': 'Çekirdek Başına Puan: {0:.2f} MOp/s',
        'average_cpu_score': 'Ortalama CPU Puanı: {0:.2f} MOp/s',
        'peak_cpu_score': 'Zirve CPU Puanı: {0:.2f} MOp/s',
        'sustainability_value': 'Sürdürülebilirlik: {0:.1f}%',
        'test_duration_label': 'Test Süresi: {0:02d}:{1:02d}',

        # --- Eklenen: Webhook pencere etiketleri/mesajları ---
        'webhook_window_title': 'Webhook Ayarları',
        'name_label': 'Ad:',
        'url_label': 'URL:',
        'type_label': 'Tür:',
        'active_label': 'Aktif',
        'threshold_label': 'Eşik (%):',
        'mode_add_new': 'Mod: Yeni Ekle',
        'mode_editing': "Mod: Düzenleme '{0}'",
        'add_new_btn': 'Yeni Ekle',
        'save_changes_btn': 'Değişiklikleri Kaydet',
        'cancel_edit_btn': 'Düzenlemeyi İptal',
        'send_test_btn': 'Test Gönder',
        'remove_selected_btn': 'Seçileni Kaldır',
        'close_btn': 'Kapat',
        'validation_title': 'Doğrulama',
        'validation_name_url_required': 'Ad ve URL gereklidir.',
        'duplicate_title': 'Kopya',
        'duplicate_exists': "'{0}' adlı webhook zaten var. Düzenlemek için seçin veya yeni bir ad kullanın.",
        'threshold_number_error': 'Eşik bir sayı olmalıdır.',
        'duplicate_rename_error': "'{0}' adlı başka bir webhook mevcut.",
        'test_title': 'Test',
        'test_select_warning': 'En az bir webhook seçin.',
        'test_results_title': 'Test Sonuçları',
        'test_results_message': 'Gönderildi: {0}\nBaşarısız: {1}',
        'test_message_title': '🔔 Test Webhook Mesajı',
        'test_message_body': "Bu bir test mesajıdır ('{0}').\n\nTür: {1}\nAktif: {2}\nZaman: {3}",
        # --- Eklenen: Network Ayar Penceresi ---
        'network_settings_title': 'Network Ayarları',
        'host_list_label': 'Test Hostları:',
        'host_name_label': 'Ad:',
        'host_address_label': 'Adres:',
        'add_host_btn': 'Host Ekle',
        'remove_host_btn': 'Seçileni Kaldır',
        'reset_hosts_btn': 'Varsayılanlara Dön',
        'close_window_btn': 'Kapat',
        'host_add_warning_title': 'Doğrulama',
        'host_add_warning_msg': 'Ad ve adres gerekli.',
        'host_remove_warning_title': 'Seçim',
        'host_remove_warning_msg': 'Kaldırmak için en az bir host seçin.',
        'hosts_reset_info_title': 'Sıfırla',
        'hosts_reset_info_msg': 'Host listesi varsayılanlara döndürüldü.',
    }
}


class LanguageManager:
    """Language management class for internationalization support."""
    
    def __init__(self):
        self.current_language = 'en'  # Default to English
        self.config_file = 'language_config.json'
        self.load_language_preference()
        
    def get_text(self, key: str) -> str:
        """Get translated text for the specified key."""
        return LANGUAGE_DICT[self.current_language].get(key, key)
    
    def set_language(self, language: str):
        """Change language."""
        if language in LANGUAGE_DICT:
            self.current_language = language
            self.save_language_preference()
    
    def get_current_language(self) -> str:
        """Get current language."""
        return self.current_language
    
    def save_language_preference(self):
        """Save language preference to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'language': self.current_language}, f)
        except Exception:
            pass  # Silent fail
    
    def load_language_preference(self):
        """Load language preference from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.current_language = data.get('language', 'en')
        except Exception:
            self.current_language = 'en'  # Default to English


# Global language manager instance
language_manager = LanguageManager()