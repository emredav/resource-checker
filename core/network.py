"""
Network monitoring and webhook notification functionality.

Provides network health checking capabilities and webhook notifications
for system alerts and status updates.
"""

import os
import json
import time
import socket
import requests
from datetime import datetime
from typing import List, Tuple, Dict


class NetworkHealthChecker:
    """Network health checking class."""

    def __init__(self):
        self.default_hosts = [
            ("Google DNS", "8.8.8.8"),
            ("Google", "google.com"),
            ("Github", "github.com")
        ]
        self.test_hosts = self.default_hosts.copy()

    def add_host(self, name: str, address: str):
        """Add new host to test."""
        self.test_hosts.append((name, address))

    def remove_host(self, index: int):
        """Remove host by index."""
        if 0 <= index < len(self.test_hosts):
            return self.test_hosts.pop(index)
        return None

    def reset_to_defaults(self):
        """Reset to default host list."""
        self.test_hosts = self.default_hosts.copy()

    def check_health(self) -> Tuple[List[str], int]:
        """Perform network health check."""
        results = []
        successful_count = 0

        for name, host in self.test_hosts:
            try:
                # Simple IP check
                is_ip = False
                parts = host.split('.')
                if len(parts) == 4:
                    try:
                        is_ip = all(0 <= int(p) <= 255 for p in parts)
                    except ValueError:
                        is_ip = False

                if is_ip:
                    # IP test using TCP connection (DNS servers usually have port 53 open)
                    # Avoid ICMP to prevent extra cmd window + some environments block ICMP
                    target_ports = [53, 443, 80]  # Priority order for testing
                    reachable = False
                    for port in target_ports:
                        try:
                            with socket.create_connection((host, port), timeout=3):
                                reachable = True
                                break
                        except Exception:
                            continue
                    if reachable:
                        status = "✓ Reachable"
                        successful_count += 1
                    else:
                        status = "✗ Unreachable"
                else:
                    # Domain test: first resolve DNS, then try TCP connection to 443 -> 80
                    resolved_ip = socket.gethostbyname(host)  # DNS resolution, fails on exception
                    target_ports = [443, 80]
                    reachable = False
                    for port in target_ports:
                        try:
                            with socket.create_connection((resolved_ip, port), timeout=3):
                                reachable = True
                                break
                        except Exception:
                            continue
                    if reachable:
                        status = "✓ Reachable"
                        successful_count += 1
                    else:
                        status = "✗ Unreachable"
            except Exception:
                status = "✗ Unreachable"

            results.append(f"{name} ({host}): {status}")

        return results, successful_count


class WebhookConfig:
    """Webhook configuration management class."""

    def __init__(self):
        self.config_file = "webhook_config.json"
        self.webhooks = {}
        self.load_config()

    def load_config(self):
        """Load webhook settings from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.webhooks = data.get('webhooks', {})
        except Exception as e:
            print(f"Webhook config loading error: {str(e)}")
            self.webhooks = {}

    def save_config(self):
        """Save webhook settings to file."""
        try:
            config_data = {
                'webhooks': self.webhooks
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Webhook config save error: {str(e)}")

    def add_webhook(self, name: str, url: str, webhook_type: str, active: bool = True, threshold: float = None):
        """Add new webhook."""
        self.webhooks[name] = {
            'url': url,
            'type': webhook_type,  # 'network' or 'cpu'
            'active': active,
            'threshold': threshold  # Will be used for CPU
        }
        self.save_config()

    def remove_webhook(self, name: str):
        """Remove webhook."""
        if name in self.webhooks:
            del self.webhooks[name]
            self.save_config()
            return True
        return False

    def update_webhook_status(self, name: str, active: bool):
        """Update webhook active/inactive status."""
        if name in self.webhooks:
            self.webhooks[name]['active'] = active
            self.save_config()
            return True
        return False

    def get_active_webhooks(self, webhook_type: str = None):
        """Get active webhooks."""
        active_webhooks = {}
        for name, config in self.webhooks.items():
            if config['active'] and (webhook_type is None or config['type'] == webhook_type):
                active_webhooks[name] = config
        return active_webhooks


class WebhookNotifier:
    """Webhook notification sender class."""

    def __init__(self, webhook_config: WebhookConfig):
        self.webhook_config = webhook_config
        self.last_network_status = True
        self.cpu_alert_sent = {}  # Last CPU alert sending times

    def send_teams_message(self, webhook_url: str, title: str, message: str, color: str = "FF0000"):
        """Send message to Teams."""
        try:
            payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": color,
                "summary": title,
                "sections": [{
                    "activityTitle": title,
                    "activitySubtitle": f"System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "text": message,
                    "markdown": True
                }]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            print(f"Teams webhook send error: {str(e)}")
            return False

    def check_and_notify_network(self, network_ok: bool):
        """Check network status and notify if needed."""
        # Check if status changed
        if network_ok != self.last_network_status:
            self.last_network_status = network_ok

            if not network_ok:
                # Network connection lost
                active_webhooks = self.webhook_config.get_active_webhooks('network')

                for name, config in active_webhooks.items():
                    title = "🚨 NETWORK CONNECTION ERROR"
                    message = f"**Warning:** Network connection could not be detected!\n\n" \
                              f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                              f"**Status:** All tested hosts failed to connect\n" \
                              f"**Webhook:** {name}"

                    success = self.send_teams_message(config['url'], title, message, "FF0000")
                    if success:
                        print(f"Network alert sent: {name}")
                    else:
                        print(f"Network alert failed to send: {name}")
            else:
                # Network connection restored
                active_webhooks = self.webhook_config.get_active_webhooks('network')

                for name, config in active_webhooks.items():
                    title = "✅ NETWORK CONNECTION RESTORED"
                    message = f"**Info:** Network connection has been re-established!\n\n" \
                              f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                              f"**Status:** Network connection returned to normal\n" \
                              f"**Webhook:** {name}"

                    success = self.send_teams_message(config['url'], title, message, "00FF00")
                    if success:
                        print(f"Network restoration notification sent: {name}")

    def check_and_notify_cpu(self, cpu_percent: float):
        """Check CPU usage and notify if needed."""
        active_webhooks = self.webhook_config.get_active_webhooks('cpu')
        current_time = time.time()

        for name, config in active_webhooks.items():
            threshold = config.get('threshold', 80.0)

            if cpu_percent >= threshold:
                # Check if at least 5 minutes passed since last alert (spam prevention)
                last_alert_time = self.cpu_alert_sent.get(name, 0)

                if current_time - last_alert_time >= 300:  # 5 minutes
                    title = f"⚠️ HIGH CPU USAGE"
                    message = f"**Warning:** CPU usage exceeded set threshold!\n\n" \
                              f"**Current CPU:** {cpu_percent:.1f}%\n" \
                              f"**Threshold:** {threshold}%\n" \
                              f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" \
                              f"**Webhook:** {name}"

                    success = self.send_teams_message(config['url'], title, message, "FFA500")
                    if success:
                        self.cpu_alert_sent[name] = current_time
                        print(f"CPU alert sent: {name} (CPU: {cpu_percent:.1f}%, Threshold: {threshold}%)")
                    else:
                        print(f"CPU alert failed to send: {name}")