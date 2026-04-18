# ================================================================
#  utils/voz.py — TTS + STT
# ================================================================
import threading, queue, logging
from typing import Optional, Callable
import pyttsx3, speech_recognition as sr
from config import SPEECH_LANGUAGE, SPEECH_TIMEOUT, SPEECH_PHRASE_LIMIT

log = logging.getLogger(__name__)

class SintesisVoz:
    def __init__(self, rate=155, volume=0.95):
        self._q = queue.Queue(); self._on = True
        self._rate = rate; self._vol = volume
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        e = pyttsx3.init()
        e.setProperty('rate', self._rate); e.setProperty('volume', self._vol)
        for v in e.getProperty('voices'):
            l = (v.languages[0] if v.languages else '').lower()
            if 'es' in l or 'es' in v.id.lower():
                e.setProperty('voice', v.id); break
        while self._on:
            try:
                t = self._q.get(timeout=0.5)
                if t is None: break
                e.say(t); e.runAndWait()
            except queue.Empty: continue
            except Exception as ex: log.error(f'[TTS] {ex}')

    def hablar(self, txt): 
        if txt: self._q.put(txt)

    def detener(self): 
        self._on = False; self._q.put(None)


class ReconocimientoVoz:
    def __init__(self):
        self.rec = sr.Recognizer()
        self.rec.energy_threshold = 300
        self.rec.dynamic_energy_threshold = True
        self.rec.pause_threshold = 0.8

    def escuchar(self, timeout=SPEECH_TIMEOUT, phrase_limit=SPEECH_PHRASE_LIMIT) -> Optional[str]:
        try:
            with sr.Microphone() as src:
                self.rec.adjust_for_ambient_noise(src, duration=0.5)
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=phrase_limit)
            return self.rec.recognize_google(audio, language=SPEECH_LANGUAGE)
        except (sr.WaitTimeoutError, sr.UnknownValueError): return None
        except sr.RequestError as e: log.error(f'[STT] {e}'); return None

    def escuchar_async(self, cb: Callable, **kw):
        t = threading.Thread(target=lambda: cb(self.escuchar(**kw)), daemon=True)
        t.start(); return t
