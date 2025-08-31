#!/usr/bin/env python3
"""
Test script to verify language functionality
"""

import sys
import os

# Add current directory to path to import main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.language  import LanguageManager, LANGUAGE_DICT

def test_language_manager():
    """Test the language manager functionality"""
    print("Testing Language Manager...")
    
    # Create language manager
    lm = LanguageManager()
    
    # Test default language (should be English)
    print(f"Default language: {lm.get_current_language()}")
    print(f"Default title: {lm.get_text('main_title')}")
    
    # Test switching to Turkish
    lm.set_language('tr')
    print(f"Switched to: {lm.get_current_language()}")
    print(f"Turkish title: {lm.get_text('main_title')}")
    
    # Test switching back to English
    lm.set_language('en')
    print(f"Switched to: {lm.get_current_language()}")
    print(f"English title: {lm.get_text('main_title')}")
    
    # Test various text keys
    test_keys = [
        'start_monitoring',
        'stop_monitoring',
        'cpu_usage',
        'ram_usage',
        'stress_test_title',
        'log_settings'
    ]
    
    print("\nTesting key translations:")
    for key in test_keys:
        en_text = LANGUAGE_DICT['en'].get(key, 'KEY_NOT_FOUND')
        tr_text = LANGUAGE_DICT['tr'].get(key, 'KEY_NOT_FOUND')
        print(f"{key}: EN='{en_text}' | TR='{tr_text}'")
    
    # Test unknown key
    unknown_text = lm.get_text('unknown_key')
    print(f"\nUnknown key test: '{unknown_text}'")
    
    print("\nLanguage system test completed successfully!")

if __name__ == "__main__":
    test_language_manager()