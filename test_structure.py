#!/usr/bin/env python3
"""
Test script to validate the refactored structure of ResourceChecker.
"""

def test_imports():
    """Test all core module imports."""
    try:
        # Test core modules
        from core.language import LanguageManager, language_manager
        from core.system_info import SystemInfo, ProcessMonitor
        from core.network import NetworkHealthChecker, WebhookConfig, WebhookNotifier
        from core.hardware import HardwareMonitor
        
        # Test utilities
        from utils.logging import Logger, NetworkLogger, FileManager, AutoLogger
        
        # Test GUI modules
        from gui.main_window import SystemMonitorGUI
        from gui.resource_monitor_window import ResourceTempMonitorWindow
        from gui.stress_test_window import CPUStressTestWindow
        
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_language_manager():
    """Test language manager functionality."""
    try:
        from core.language import language_manager
        
        # Test getting text
        text = language_manager.get_text('main_title')
        print(f"✅ Language manager works! Main title: {text}")
        
        # Test language switching
        original_lang = language_manager.get_current_language()
        new_lang = 'tr' if original_lang == 'en' else 'en'
        language_manager.set_language(new_lang)
        new_text = language_manager.get_text('main_title')
        print(f"✅ Language switching works! New title: {new_text}")
        
        # Restore original language
        language_manager.set_language(original_lang)
        return True
    except Exception as e:
        print(f"❌ Language manager error: {e}")
        return False

def test_system_info():
    """Test system info functionality."""
    try:
        from core.system_info import SystemInfo
        
        cpu_usage = SystemInfo.get_cpu_usage(0.1)  # Quick test
        memory_info = SystemInfo.get_memory_info()
        
        print(f"✅ System Info works! CPU: {cpu_usage:.1f}%, RAM: {memory_info.percent:.1f}%")
        return True
    except Exception as e:
        print(f"❌ System info error: {e}")
        return False

def test_hardware_monitor():
    """Test hardware monitor functionality."""
    try:
        from core.hardware import HardwareMonitor
        
        cpu_temp = HardwareMonitor.get_cpu_temperature()
        gpu_info = HardwareMonitor.get_nvidia_gpu_info()
        
        print(f"✅ Hardware Monitor works! CPU temp: {cpu_temp}, GPU info: {gpu_info}")
        return True
    except Exception as e:
        print(f"❌ Hardware monitor error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing ResourceChecker refactored structure...\n")
    
    tests = [
        ("Import Tests", test_imports),
        ("Language Manager", test_language_manager),
        ("System Info", test_system_info),
        ("Hardware Monitor", test_hardware_monitor),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print()
    
    print("📊 Test Results Summary:")
    print("-" * 40)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring successful!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")