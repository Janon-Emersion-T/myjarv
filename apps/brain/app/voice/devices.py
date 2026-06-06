from __future__ import annotations


class VoiceDeviceManager:
    def list_devices(self) -> dict[str, list[dict[str, object]]]:
        return {
            "inputs": [
                {"id": "default-mic", "kind": "microphone", "label": "Default Microphone", "is_default": True, "is_available": True},
                {"id": "usb-mic", "kind": "microphone", "label": "USB Studio Microphone", "is_default": False, "is_available": True},
            ],
            "outputs": [
                {"id": "default-speaker", "kind": "speaker", "label": "Default Speaker", "is_default": True, "is_available": True},
                {"id": "headphones", "kind": "speaker", "label": "Monitoring Headphones", "is_default": False, "is_available": True},
            ],
        }


voice_device_manager = VoiceDeviceManager()
