# file: service/main.py
from __future__ import annotations
import os
import sys
import time
import traceback
from datetime import datetime, timedelta, time as dtime

# Ensure we can import app/*
SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SERVICE_DIR, os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.runner import check_and_alert, ensure_app_dirs
from app.util import get_ist_now, in_android

# --- Android notification plumbing via pyjnius ---
try:
    from jnius import autoclass, cast
except Exception:  # running off-device
    autoclass = cast = None

NOTIF_CHANNEL_ID = "nsebse_alerts_channel"
NOTIF_ID = 101


def _android_context():
    if not in_android():
        return None
    PythonService = autoclass('org.kivy.android.PythonService')
    return PythonService.mService


def _create_channel_if_needed(ctx):
    # For Android O+; safe to call repeatedly
    try:
        Build = autoclass('android.os.Build')
        if Build.VERSION.SDK_INT < 26:
            return
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotificationManager = autoclass('android.app.NotificationManager')
        Importance = NotificationManager.IMPORTANCE_LOW
        channel = NotificationChannel(NOTIF_CHANNEL_ID, 'Corporate Alerts', Importance)
        manager = cast('android.app.NotificationManager', ctx.getSystemService(ctx.NOTIFICATION_SERVICE))
        manager.createNotificationChannel(channel)
    except Exception:
        traceback.print_exc()


def _small_icon_id(ctx):
    try:
        # Use app mipmap/icon
        res = ctx.getResources()
        pkg = ctx.getPackageName()
        icon_id = res.getIdentifier('icon', 'mipmap', pkg)
        if icon_id == 0:
            icon_id = android.R.drawable.stat_notify_sync_noanim  # type: ignore
        return icon_id
    except Exception:
        return 0


def _build_notification(ctx, text):
    try:
        _create_channel_if_needed(ctx)
        Builder = autoclass('androidx.core.app.NotificationCompat$Builder')
        PendingIntent = autoclass('android.app.PendingIntent')
        Intent = autoclass('android.content.Intent')
        # Open app when tapping the notification
        intent = Intent(ctx, autoclass('org.kivy.android.PythonActivity'))
        flags = PendingIntent.FLAG_UPDATE_CURRENT
        pending = PendingIntent.getActivity(ctx, 0, intent, flags)

        builder = Builder(ctx, NOTIF_CHANNEL_ID)
        builder.setContentTitle('NSE+BSE Corporate Alerts')
        builder.setContentText(text)
        builder.setSmallIcon(_small_icon_id(ctx))
        builder.setOngoing(True)
        builder.setContentIntent(pending)
        return builder.build()
    except Exception:
        traceback.print_exc()
        return None


def _start_foreground(text="Monitoring…"):
    ctx = _android_context()
    if not ctx:
        return
    notif = _build_notification(ctx, text)
    if notif is not None:
        ctx.startForeground(NOTIF_ID, notif)


def _update_notification(text: str):
    ctx = _android_context()
    if not ctx:
        return
    notif = _build_notification(ctx, text)
    if notif is None:
        return
    NotificationManagerCompat = autoclass('androidx.core.app.NotificationManagerCompat')
    nm = NotificationManagerCompat.from(ctx)
    nm.notify(NOTIF_ID, notif)


# --- Scheduling policy ---
MARKET_START = dtime(9, 15)
MARKET_END = dtime(15, 30)


def _within_market_hours(now):
    if now.weekday() >= 5:  # Sat/Sun
        return False
    t = now.time()
    return (t >= MARKET_START) and (t <= MARKET_END)


def service_main():
    ensure_app_dirs()
    _start_foreground("Starting…")
    last_daily = None  # last date (IST) when 07:00 run executed

    while True:
        try:
            now = get_ist_now()
            # 07:00 daily run
            seven = dtime(7, 0)
            if (last_daily != now.date()) and (now.time() >= seven):
                n = check_and_alert(trigger="07:00 daily")
                last_daily = now.date()
                _update_notification(f"Daily run: {n} new at {now.strftime('%H:%M')}")

            # Market-hours every 10 minutes
            if _within_market_hours(now) and (now.minute % 10 == 0):
                n = check_and_alert(trigger="10m market window")
                _update_notification(f"Last: {n} new at {now.strftime('%H:%M')}")

        except Exception:
            traceback.print_exc()
        finally:
            time.sleep(60)  # tick once per minute


if __name__ == '__main__':
    service_main()
