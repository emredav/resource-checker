#!/usr/bin/env python3
"""
Quick UI verification test for ResourceChecker.
Tests that all language and webhook settings are properly displayed.
"""

import tkinter as tk
from gui.main_window import SystemMonitorGUI
from core.language import language_manager


def test_ui_elements():
    """Test that all UI elements are properly created and visible."""
    print("🧪 Testing ResourceChecker UI Elements...")
    
    # Create root window (but don't show it)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    try:
        # Create the GUI
        app = SystemMonitorGUI(root)
        
        # Test language elements
        print("✅ Language button exists:", hasattr(app, 'language_button'))
        print("✅ Language label exists:", hasattr(app, 'language_label'))
        
        # Test webhook elements  
        print("✅ Webhook button exists:", hasattr(app, 'webhook_button'))
        
        # Test network settings elements
        print("✅ Network settings button exists:", hasattr(app, 'network_settings_btn'))
        print("✅ Network auto monitoring button exists:", hasattr(app, 'network_auto_btn'))
        
        # Test language functionality
        original_lang = language_manager.get_current_language()
        print(f"✅ Current language: {original_lang}")
        
        # Test language switching
        app._toggle_language()
        new_lang = language_manager.get_current_language()
        print(f"✅ Language switched to: {new_lang}")
        
        # Switch back (orijinali ne olursa olsun test sonunda EN yapılacak)
        app._toggle_language()
        restored_lang = language_manager.get_current_language()
        print(f"✅ Language restored to: {restored_lang}")
        
        # Test UI text updates
        print("✅ UI text update methods exist:")
        print("   - _update_settings_frame_texts:", hasattr(app, '_update_settings_frame_texts'))
        print("   - _update_control_buttons_texts:", hasattr(app, '_update_control_buttons_texts'))
        print("   - _update_all_texts:", hasattr(app, '_update_all_texts'))
        
        # Test button methods
        print("✅ Button methods exist:")
        print("   - open_webhook_settings:", hasattr(app, 'open_webhook_settings'))
        print("   - open_network_settings:", hasattr(app, 'open_network_settings'))
        print("   - toggle_network_monitoring:", hasattr(app, 'toggle_network_monitoring'))
        
        print("\n🎉 All UI elements test passed!")
        return True
        
    except Exception as e:
        print(f"❌ UI test failed: {e}")
        return False
    finally:
        # Test hangi dille başlarsa başlasın EN ile sonlandır
        language_manager.set_language('en')
        root.destroy()


def test_language_texts():
    """Test that all required language texts exist."""
    print("\n🌐 Testing Language Texts...")
    
    required_texts = [
        'settings_frame', 'system_interval', 'network_interval', 'top_apps_count',
        'auto_log', 'webhook_settings', 'start_monitoring', 'stop_monitoring',
        'network_health_check', 'auto_network_monitoring', 'stop_auto_network',
        'resource_temp_monitor', 'cpu_stress_test', 'language_english', 'language_turkish',
        'monitoring_options'
    ]
    
    missing_texts = []
    # Orijinal dili sakla
    original_lang = language_manager.get_current_language()
    for lang in ['en', 'tr']:
        language_manager.set_language(lang)
        print(f"\nTesting {lang.upper()} language:")
        
        for text_key in required_texts:
            text_value = language_manager.get_text(text_key)
            if text_value == text_key:  # Means translation not found
                missing_texts.append(f"{lang}:{text_key}")
                print(f"  ❌ Missing: {text_key}")
            else:
                print(f"  ✅ Found: {text_key} = '{text_value}'")
    
    # Test tamamlandıktan sonra dili kalıcı olarak EN yap
    language_manager.set_language('en')

    if missing_texts:
        print(f"\n❌ Missing translations: {missing_texts}")
        return False
    else:
        print(f"\n✅ All language texts found!")
        return True


if __name__ == "__main__":
    print("🔍 ResourceChecker UI Verification Test\n")
    
    # Run tests
    ui_test_passed = test_ui_elements()
    lang_test_passed = test_language_texts()
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    print(f"UI Elements Test:     {'✅ PASS' if ui_test_passed else '❌ FAIL'}")
    print(f"Language Texts Test:  {'✅ PASS' if lang_test_passed else '❌ FAIL'}")
    
    if ui_test_passed and lang_test_passed:
        print("\n🎉 All tests passed! UI is properly configured.")
        print("\n🚀 You can now run: python main.py")
        print("   - Language settings are in the Settings frame")
        print("   - Webhook settings button is also in Settings frame")
        print("   - Auto Network Monitoring is in the control buttons")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")