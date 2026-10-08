"""Android app (Kivy) - simple chat client for your agent server.
Built into an APK by GitHub Actions (buildozer). Uses only stdlib for HTTP.
"""
import json
import urllib.request

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import mainthread
import threading

# CHANGE THIS to your Hugging Face Space URL
SERVER_URL = "https://YOUR-USERNAME-YOUR-SPACE.hf.space"
AGENT_TOKEN = ""  # same value as AGENT_TOKEN secret on the server


class AgentApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical", padding=8, spacing=8)
        self.scroll = ScrollView()
        self.log = Label(text="Ready.\n", size_hint_y=None, halign="left", valign="top")
        self.log.bind(texture_size=lambda i, v: setattr(i, "height", v[1]))
        self.log.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
        self.scroll.add_widget(self.log)
        root.add_widget(self.scroll)
        self.inp = TextInput(hint_text="Ja chao likho...", size_hint_y=None, height=120)
        root.add_widget(self.inp)
        btn = Button(text="Send", size_hint_y=None, height=110)
        btn.bind(on_press=self.send)
        root.add_widget(btn)
        return root

    def send(self, *_):
        text = self.inp.text.strip()
        if not text:
            return
        self.inp.text = ""
        self._append(f"\nYou: {text}")
        threading.Thread(target=self._call, args=(text,), daemon=True).start()

    def _call(self, text):
        try:
            req = urllib.request.Request(
                SERVER_URL.rstrip("/") + "/api/chat",
                data=json.dumps({"message": text}).encode(),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {AGENT_TOKEN}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                reply = json.loads(r.read().decode()).get("reply", "")
        except Exception as e:  # noqa: BLE001
            reply = f"Error: {e}"
        self._append(f"\nAgent: {reply}")

    @mainthread
    def _append(self, s):
        self.log.text += s + "\n"


if __name__ == "__main__":
    AgentApp().run()
