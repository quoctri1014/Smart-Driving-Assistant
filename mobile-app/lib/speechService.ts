/**
 * speechService.ts
 * ----------------
 * Hệ thống âm thanh cảnh báo & giọng đọc tiếng Việt cho Mobile App:
 * - Hỗ trợ cả mobile native (qua expo-speech nếu có) và web fallback (Web Speech API).
 * - Cơ chế hàng đợi (queue) chống đọc đè.
 * - Hỗ trợ bật/tắt (mute) và điều chỉnh âm lượng.
 */

let ExpoSpeech: any = null;
try {
  ExpoSpeech = require('expo-speech');
} catch {
  ExpoSpeech = null;
}

class MobileSpeechService {
  private isMuted: boolean = false;
  private volume: number = 0.9;
  private lastSpokenText: string = "";
  private lastSpokenTime: number = 0;

  public setMuted(muted: boolean) {
    this.isMuted = muted;
    if (muted) {
      this.stop();
    }
  }

  public setVolume(vol: number) {
    this.volume = Math.max(0, Math.min(1, vol));
  }

  public stop() {
    if (ExpoSpeech && typeof ExpoSpeech.stop === 'function') {
      ExpoSpeech.stop();
    } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  public speak(text: string, priority: 'normal' | 'critical' = 'normal') {
    if (this.isMuted || !text) return;

    const now = Date.now();
    // Chống đọc lặp cùng câu trong 4 giây
    if (text === this.lastSpokenText && (now - this.lastSpokenTime) < 4000) {
      return;
    }

    if (priority === 'critical') {
      this.stop();
    }

    this.lastSpokenText = text;
    this.lastSpokenTime = now;

    if (ExpoSpeech && typeof ExpoSpeech.speak === 'function') {
      ExpoSpeech.speak(text, {
        language: 'vi-VN',
        pitch: 1.0,
        rate: 1.05,
      });
    } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'vi-VN';
      utterance.rate = 1.05;
      utterance.volume = this.volume;
      window.speechSynthesis.speak(utterance);
    }
  }

  public handleDecisionAudio(soundAlert?: string | null, speechPrompt?: string | null) {
    if (speechPrompt) {
      const priority = soundAlert === 'alarm_critical' ? 'critical' : 'normal';
      this.speak(speechPrompt, priority);
    }
  }
}

export const mobileSpeechService = new MobileSpeechService();
