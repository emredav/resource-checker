"""
Wi-Fi Analyzer Module for ResourceChecker.
Uses native Windows 'netsh' commands to gather detailed Wi-Fi information.
"""

import subprocess
import re
from typing import List, Dict, Optional

class WifiAnalyzer:
    @staticmethod
    def _run_command(command: List[str]) -> str:
        """Run a command and return its output as string."""
        try:
            # Hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore',
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout
        except Exception as e:
            return ""

    @staticmethod
    def get_current_interface_info() -> Dict[str, str]:
        """
        Get details of the currently active Wi-Fi interface.
        Parses 'netsh wlan show interfaces'.
        """
        output = WifiAnalyzer._run_command(['netsh', 'wlan', 'show', 'interfaces'])
        info = {}
        
        # Regex mappings for English and typical output
        # Windows output keys might be localized, so we parse by line structure mostly or known keys
        # But 'netsh' output IS localized on non-English systems.
        # We need a robust parser. "Key : Value" structure is consistent.
        
        lines = output.splitlines()
        current_data = {}
        
        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                
                # Normalize keys to a standard internal set
                # English / Turkish key mapping heuristics
                if "SSID" == key: current_data['ssid'] = val
                elif "BSSID" in key: current_data['bssid'] = val
                elif "State" in key or "Durum" in key: current_data['state'] = val
                elif "Channel" in key or "Kanal" in key: current_data['channel'] = val
                elif "Signal" in key or "Sinyal" in key: current_data['signal'] = val.replace('%', '')
                elif "Receive rate" in key or "Alma hızı" in key: current_data['rx_rate'] = val
                elif "Transmit rate" in key or "İletim hızı" in key: current_data['tx_rate'] = val
                elif "Radio type" in key or "Radyo türü" in key: current_data['radio'] = val
                elif "Description" in key or "Açıklama" in key: current_data['description'] = val
        
        return current_data

    @staticmethod
    def scan_networks() -> List[Dict[str, str]]:
        """
        Scan for nearby networks.
        Parses 'netsh wlan show networks mode=bssid'.
        """
        output = WifiAnalyzer._run_command(['netsh', 'wlan', 'show', 'networks', 'mode=bssid'])
        networks = []
        current_net = None
        current_bssid = None
        
        lines = output.splitlines()
        
        count = 0
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Start of a new network block (e.g. "SSID 1 : MyWifi")
            if line.startswith("SSID") and ":" in line:
                # Save previous if exists
                if current_net:
                     # If bssids were collected
                     networks.append(current_net)
                
                parts = line.split(":", 1)
                ssid_name = parts[1].strip()
                current_net = {
                    'ssid': ssid_name if ssid_name else "[Hidden]",
                    'bssids': []
                }
            
            elif line.startswith("Network type") or line.startswith("Ağ türü"):
                 if current_net: current_net['type'] = line.split(":")[1].strip()
            elif line.startswith("Authentication") or line.startswith("Kimlik doğrulama"):
                 if current_net: current_net['auth'] = line.split(":")[1].strip()
            # BSSID Parser
            elif line.startswith("BSSID"):
                 # Start of a BSSID block within the SSID
                 parts = line.split(":", 1)
                 b_mac = parts[1].strip()
                 current_bssid = {'mac': b_mac}
                 if current_net:
                     current_net['bssids'].append(current_bssid)
            
            # BSSID details (Signal, Channel, Band)
            elif current_bssid is not None:
                if ":" in line:
                    parts = line.split(":", 1)
                    k = parts[0].strip()
                    v = parts[1].strip()
                    
                    if "Signal" in k or "Sinyal" in k:
                        current_bssid['signal'] = v.replace('%', '')
                    elif "Channel" in k or "Kanal" in k:
                        current_bssid['channel'] = v
                    elif "Radio" in k or "Radyo" in k:
                        current_bssid['radio'] = v
        
        # Add last one
        if current_net:
            networks.append(current_net)
            
        # Flatten the list: Return one entry per BSSID (Access Point) for detailed analysis
        # Or keep grouped. For Analyzer, usually we want to see individual APs (BSSIDs) to detect overlap.
        flat_list = []
        for net in networks:
            ssid = net.get('ssid', 'Unknown')
            auth = net.get('auth', 'Unknown')
            bssids = net.get('bssids', [])
            
            if not bssids:
                 # Logic for case where no BSSID info is showing (rare with mode=bssid but possible)
                 flat_list.append({
                     'ssid': ssid,
                     'mac': 'N/A',
                     'signal': '0',
                     'channel': 'N/A',
                     'radio': 'N/A',
                     'auth': auth
                 })
            else:
                for b in bssids:
                    flat_list.append({
                        'ssid': ssid,
                        'auth': auth,
                        'mac': b.get('mac', 'Unknown'),
                        'signal': b.get('signal', '0'),
                        'channel': b.get('channel', 'Unknown'),
                        'radio': b.get('radio', 'Unknown')
                    })
        
        # Sort by signal strength desc
        def sig_sort(x):
            try: return int(x['signal'])
            except: return 0
        
        flat_list.sort(key=sig_sort, reverse=True)
        return flat_list

    @staticmethod
    def get_saved_profiles() -> List[str]:
        """
        Get list of saved Wi-Fi profile names.
        """
        profiles = []
        try:
            output = WifiAnalyzer._run_command(['netsh', 'wlan', 'show', 'profiles'])
            # Output format:
            # User profiles
            # -------------
            #     All User Profile     : SSID_Name
            
            for line in output.splitlines():
                if " : " in line:
                    parts = line.split(" : ", 1)
                    if len(parts) == 2:
                        profiles.append(parts[1].strip())
        except Exception as e:
            print(f"Error getting profiles: {e}")
        return profiles

    @staticmethod
    def get_profile_details(profile_name: str) -> Dict[str, Optional[str]]:
        """
        Get details for a specific profile (including password if manageable).
        """
        details = {
            'ssid': profile_name,
            'auth': 'Unknown',
            'cipher': 'Unknown',
            'password': None,
            'connection_mode': 'Unknown'
        }
        
        try:
            # key=clear is required to see the password
            output = WifiAnalyzer._run_command(['netsh', 'wlan', 'show', 'profile', f'name={profile_name}', 'key=clear'])
            
            # Helper to parse key-value lines roughly
            for line in output.splitlines():
                line = line.strip()
                if not line: continue
                
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    
                    # Keywords (EN / TR mixed heuristics)
                    if "Authentication" in key or "Kimlik doğrulama" in key:
                        details['auth'] = val
                    elif "Cipher" in key or "Şifre" in key:
                        # "Şifre" in TR netsh usually means Cipher, "Anahtar İçeriği" is Key Content
                        details['cipher'] = val
                    elif "Key Content" in key or "Anahtar İçeriği" in key:
                        details['password'] = val
                    elif "Connection mode" in key or "Bağlantı modu" in key:
                        details['connection_mode'] = val

        except Exception as e:
            print(f"Error getting details for {profile_name}: {e}")
            
        return details

    @staticmethod
    def delete_profile(profile_name: str) -> bool:
        """Delete a saved Wi-Fi profile."""
        try:
            cmd = ['netsh', 'wlan', 'delete', 'profile', f'name={profile_name}']
            subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            print(f"Error deleting profile {profile_name}: {e}")
            return False
