# file: app/util.py
from __future__ import annotations
import os
import re
import socket
import sys
from datetime import datetime, timezone, timedelta

try:
    import pytz  # packaged for reliable IST tz
    IST = pytz.timezone('Asia/Kolkata')
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    try:
        return datetime.now(IST)
    except Exception:
        return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def is_ist_now(hour: int, minute: int = 0) -> bool:
    now = get_ist_now()
    return now.hour == hour and now.minute == minute


def in_android() -> bool:
    return 'ANDROID_ARGUMENT' in os.environ


def ensure_runtime_permissions():
    # Request POST_NOTIFICATIONS (API 33+) and ignore-battery-optimizations
    if not in_android():
        return
    try:
        from jnius import autoclass, cast
        from android import mActivity  # type: ignore
        Build = autoclass('android.os.Build')
        if Build.VERSION.SDK_INT >= 33:
            ActivityCompat = autoclass('androidx.core.app.ActivityCompat')
            Manifest = autoclass('android.Manifest')
            perms = [Manifest.permission.POST_NOTIFICATIONS]
            ActivityCompat.requestPermissions(mActivity, perms, 1001)
        # Ask user to whitelist from battery optimizations
        PowerManager = autoclass('android.os.PowerManager')
        Context = autoclass('android.content.Context')
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        Uri = autoclass('android.net.Uri')
        pkg = mActivity.getPackageName()
        pm = cast('android.os.PowerManager', mActivity.getSystemService(Context.POWER_SERVICE))
        if not pm.isIgnoringBatteryOptimizations(pkg):
            intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS)
            intent.setData(Uri.parse(f"package:{pkg}"))
            mActivity.startActivity(intent)
    except Exception as e:
        print("[perm] warn:", e)


def app_storage_dir() -> str:
    # Kivy App.user_data_dir when available; fallback to private dir
    path = None
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app:
            path = app.user_data_dir
    except Exception:
        pass
    if not path:
        path = os.path.join(os.getcwd(), ".appdata")
    os.makedirs(path, exist_ok=True)
    return path
