/**
 * Radar Watchtower - Core Instrument Operations & Audio Synthesizer
 * Department of Computer Science, University of Nigeria, Nsukka
 */

(function () {
    'use strict';

    // 1. Live Chronometer with Seconds
    function initClock() {
        const clockEl = document.getElementById('liveClock');
        if (!clockEl) return;

        function updateClock() {
            const now = new Date();
            const h = String(now.getUTCHours()).padStart(2, '0');
            const m = String(now.getUTCMinutes()).padStart(2, '0');
            const s = String(now.getUTCSeconds()).padStart(2, '0');
            clockEl.textContent = `${h}:${m}:${s} UTC`;
        }
        updateClock();
        setInterval(updateClock, 1000);
    }

    // 2. Day / Tactical Night Theme Management
    const THEME_KEY = 'watchtower_theme';
    const htmlElem = document.documentElement;

    function applyTheme(theme) {
        if (theme === 'light') {
            htmlElem.setAttribute('data-theme', 'light');
        } else {
            htmlElem.removeAttribute('data-theme');
        }
        localStorage.setItem(THEME_KEY, theme);
        const label = document.getElementById('themeToggleLabel');
        if (label) {
            label.textContent = theme === 'light' ? 'NIGHT' : 'DAY';
        }
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    function initTheme() {
        const urlParams = new URLSearchParams(window.location.search);
        const queryTheme = urlParams.get('theme');
        if (queryTheme) {
            applyTheme(queryTheme);
            return;
        }

        const saved = localStorage.getItem(THEME_KEY);
        if (saved) {
            applyTheme(saved);
        } else {
            applyTheme('dark');
        }
    }

    function toggleTheme() {
        const current = htmlElem.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        applyTheme(current === 'light' ? 'dark' : 'light');
    }

    // 3. Web Audio API Tactical Synthesizer (Sonar / Alarm)
    let audioCtx = null;
    let audioEnabled = false;

    function initAudio() {
        const audioBtn = document.getElementById('audioToggleBtn');
        const audioLabel = document.getElementById('audioToggleLabel');
        if (!audioBtn) return;

        audioBtn.addEventListener('click', () => {
            if (!audioCtx) {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (AudioContextClass) {
                    audioCtx = new AudioContextClass();
                }
            }
            if (audioCtx && audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            audioEnabled = !audioEnabled;
            audioBtn.classList.toggle('active', audioEnabled);
            if (audioLabel) {
                audioLabel.textContent = audioEnabled ? 'AUDIO: ON' : 'AUDIO: OFF';
            }
            if (audioEnabled) {
                playRadarPing();
            }
        });
    }

    function playRadarPing() {
        if (!audioEnabled || !audioCtx) return;
        try {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, audioCtx.currentTime); // High clear ping
            gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.35);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.35);
        } catch (e) {
            console.error('Audio error:', e);
        }
    }

    function playAlarmPing() {
        if (!audioEnabled || !audioCtx) return;
        try {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(650, audioCtx.currentTime);
            osc.frequency.exponentialRampToValueAtTime(320, audioCtx.currentTime + 0.28);
            gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.3);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.3);
        } catch (e) {
            console.error('Audio error:', e);
        }
    }

    // 4. Password Toggle
    function setupPasswordToggles() {
        document.querySelectorAll('.password-toggle-btn').forEach(btn => {
            btn.addEventListener('click', function () {
                const targetId = this.getAttribute('data-target');
                const input = targetId ? document.getElementById(targetId) : this.previousElementSibling;
                if (!input) return;
                const isPass = input.type === 'password';
                input.type = isPass ? 'text' : 'password';
                const eyeOpen = this.querySelector('.eye-open');
                const eyeClosed = this.querySelector('.eye-closed');
                if (eyeOpen && eyeClosed) {
                    eyeOpen.style.display = isPass ? 'none' : 'block';
                    eyeClosed.style.display = isPass ? 'block' : 'none';
                }
            });
        });
    }

    // 5. Tactical Notification Banner
    function showToast(msg, type = 'info') {
        let container = document.getElementById('watchtowerToastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'watchtowerToastContainer';
            container.style.cssText = `
                position: fixed;
                bottom: 110px;
                right: 20px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                z-index: 1000;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = 'tactical-frame';
        toast.style.cssText = `
            padding: 8px 14px;
            font-family: var(--font-mono);
            font-size: 0.76rem;
            color: ${type === 'error' ? 'var(--coral)' : type === 'success' ? 'var(--cyan)' : 'var(--amber)'};
            border-color: ${type === 'error' ? 'var(--coral)' : type === 'success' ? 'var(--cyan)' : 'var(--amber)'};
            box-shadow: 0 4px 16px rgba(0,0,0,0.6);
            letter-spacing: 0.05em;
            pointer-events: auto;
            transition: all 0.25s ease;
        `;
        toast.innerHTML = `<span>[SYS] ${msg}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    }

    document.addEventListener('DOMContentLoaded', () => {
        initTheme();
        initClock();
        initAudio();
        setupPasswordToggles();

        const themeBtn = document.getElementById('themeToggleBtn');
        if (themeBtn) {
            themeBtn.addEventListener('click', toggleTheme);
        }
    });

    window.Watchtower = {
        playRadarPing,
        playAlarmPing,
        showToast,
        toggleTheme
    };
})();
