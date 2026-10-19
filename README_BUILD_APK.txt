VoiceCall APK build instructions
================================

This archive contains the VoiceCall Kivy project. The APK has NOT been compiled yet.

Requirements:
- Linux or Windows with WSL2 Ubuntu
- Java 17 and Android build dependencies
- Buildozer installed in a Python virtual environment

From the Ubuntu/WSL terminal, copy the project to Linux home (recommended):
  mkdir -p ~/VoiceCall
  cp -r /mnt/c/Users/<YOUR_WINDOWS_USER>/Downloads/VoiceCall_stage2_contacts/. ~/VoiceCall/
  cd ~/VoiceCall

Create and activate a virtual environment (adjust Python version if needed):
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip setuptools
  pip install buildozer cython==0.29.34

Then build:
  buildozer -v android debug

On first build, Buildozer downloads Android SDK/NDK and other components; this may take a long time and needs internet and disk space. If successful, the APK will be in the bin/ directory.

The app requests microphone access for speech recognition and contacts access for searching saved contacts. The call button opens Android's dialer; it does not place a call automatically.
