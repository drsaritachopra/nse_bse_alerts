---


## Buildozer & Packaging


### `buildozer.spec`
```ini
# file: buildozer.spec
[app]
title = NSE+BSE Corporate Alerts
package.name = nsebsealerts
package.domain = com.yourdomain
source.dir = .
version = 0.1.0
orientation = portrait
fullscreen = 0


# Icons/splash (optional)
icon.filename = %(source.dir)s/.buildozer/android/platform/build-armeabi-v7a/dists/nsebsealerts/src/main/res/mipmap/ic_launcher.png


requirements = python3,kivy==2.2.1,requests,beautifulsoup4,lxml,plyer,pytz
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a


# Service entry point (foreground)
services = foreground:service/main.py


# Permissions
android.permissions = INTERNET,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,POST_NOTIFICATIONS


# Use androidx for NotificationCompat
android.gradle_dependencies = androidx.core:core:1.12.0


# Keep network working with NSE site
android.add_default_config = android:usesCleartextTraffic="true"


[buildozer]
log_level = 2
warn_on_root = 0