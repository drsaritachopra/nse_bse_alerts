# file: main.py
from __future__ import annotations
import os
import sys
import threading
import time
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from app.runner import check_and_alert, ensure_app_dirs
from app.util import in_android, ensure_runtime_permissions, is_ist_now

KV = None

class Root(BoxLayout):
    status = StringProperty("Idle")
    last_checked = StringProperty("—")

    def trigger_check(self):
        # Why thread: avoid blocking UI with network/IO
        self.status = "Checking…"
        threading.Thread(target=self._do_check, daemon=True).start()

    def _do_check(self):
        try:
            new_count = check_and_alert(manual=True)
            self.status = f"Done. New alerts: {new_count}"
        except Exception as e:  # surface unexpected errors into UI
            self.status = f"Error: {e}"
        finally:
            self.last_checked = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class AlertsApp(App):
    def build(self):
        global KV
        if KV is None:
            KV = Builder.load_file("ui.kv")
        ensure_app_dirs()
        Clock.schedule_once(lambda *_: self._bootstrap_service(), 0)
        return Root()

    def _bootstrap_service(self):
        # Start foreground service + request permissions on Android
        if in_android():
            try:
                ensure_runtime_permissions()
                from android import AndroidService  # type: ignore
                service = AndroidService(
                    "NSE+BSE Corporate Alerts",
                    "Monitoring corporate actions…",
                )
                service.start("service-start")
            except Exception as e:
                print("[WARN] Could not start service:", e)

if __name__ == "__main__":
    AlertsApp().run()
