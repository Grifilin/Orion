[app]
title = Orion
package.name = orion
package.domain = ru.grifilin
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy==2.3.0,requests,urllib3,certifi,chardet,idna,pyjnius,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.build_tools = 33.0.2
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
