[app]

title = Stemoproep
package.name = stemoproep
package.domain = org.voorbeeld
source.dir = .
source.include_exts = py,ttf,png,jpg,kv
version = 0.3
requirements = python3,kivy==2.3.1,pyjnius,arabic-reshaper,python-bidi
orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO, READ_CONTACTS
android.minapi = 23
android.api = 35
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
