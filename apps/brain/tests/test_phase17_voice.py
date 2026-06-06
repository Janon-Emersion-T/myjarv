import sys
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "apps" / "brain"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.main import app  # noqa: E402


class VoicePhase17Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_voice_session_lifecycle_and_command_modes(self):
        create = self.client.post(
            "/voice/sessions",
            json={"mode": "desktop_assistant", "text": "Hey Jarvis", "locale": "en", "speaker_id": "janon"},
        )
        self.assertEqual(create.status_code, 200)
        session = create.json()
        self.assertEqual(session["status"], "listening")
        self.assertTrue(session["wake_word_detected"])

        command = self.client.post(
            f"/voice/sessions/{session['id']}/command",
            json={"text": "Jarvis open the approval dashboard", "requested_action": "open dashboard", "speaker_id": "janon"},
        )
        self.assertEqual(command.status_code, 200)
        payload = command.json()
        self.assertEqual(payload["interaction"]["intent"], "command_execution")
        self.assertGreaterEqual(payload["interaction"]["confidence"], 0.55)

        interrupt = self.client.post(f"/voice/sessions/{session['id']}/interrupt")
        self.assertEqual(interrupt.status_code, 200)
        self.assertEqual(interrupt.json()["status"], "interrupted")

        resume = self.client.post(f"/voice/sessions/{session['id']}/resume")
        self.assertEqual(resume.status_code, 200)
        self.assertEqual(resume.json()["status"], "listening")

    def test_emergency_mode_and_voice_dashboard(self):
        create = self.client.post(
            "/voice/sessions",
            json={"mode": "conversation", "text": "Jarvis", "locale": "en", "speaker_id": "janon"},
        )
        self.assertEqual(create.status_code, 200)
        session = create.json()

        emergency = self.client.post(
            f"/voice/sessions/{session['id']}/command",
            json={"text": "Emergency shutdown all risky actions", "requested_action": "shutdown", "speaker_id": "janon"},
        )
        self.assertEqual(emergency.status_code, 200)
        self.assertEqual(emergency.json()["interaction"]["risk_level"], "CRITICAL")
        self.assertEqual(emergency.json()["interaction"]["approval_level"], "CRITICAL")

        dashboard = self.client.get("/voice/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        voice_payload = dashboard.json()
        self.assertIn("analytics", voice_payload)
        self.assertIn("sessions", voice_payload)

    def test_voice_websocket_replay_and_stress(self):
        create = self.client.post(
            "/voice/sessions",
            json={"mode": "command", "text": "Jarvis ready", "locale": "en", "speaker_id": "janon"},
        )
        session = create.json()
        with self.client.websocket_connect(f"/ws/voice/{session['id']}") as websocket:
            first = websocket.receive_json()
            self.assertEqual(first["type"], "connected")
            second = websocket.receive_json()
            self.assertEqual(second["type"], "snapshot")

        replay = self.client.post(f"/voice/sessions/{session['id']}/replay")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.json()["metadata"]["replay_of"], session["id"])

        started = time.perf_counter()
        for index in range(20):
            response = self.client.post(
                f"/voice/sessions/{session['id']}/command",
                json={"text": f"Jarvis status report run {index}", "speaker_id": "janon"},
            )
            self.assertEqual(response.status_code, 200)
        self.assertLess(time.perf_counter() - started, 10)


if __name__ == "__main__":
    unittest.main()
