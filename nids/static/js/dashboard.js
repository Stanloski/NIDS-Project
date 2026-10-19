/**
 * Radar Watchtower - Master Air Traffic Control Room & Canvas Radar
 * Department of Computer Science, University of Nigeria, Nsukka
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // -------------------------------------------------------------------------
    // 1. Radar Canvas & Particle Geometry Engine
    // -------------------------------------------------------------------------
    const canvas = document.getElementById('radarCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const hudTooltip = document.getElementById('radarHudTooltip');
    const threatVignette = document.getElementById('threatVignette');

    let width = 0;
    let height = 0;
    let cx = 0;
    let cy = 0;
    let maxRadius = 0;
    let sweepAngle = 0;
    let isTabVisible = true;

    document.addEventListener('visibilitychange', () => {
        isTabVisible = !document.hidden;
    });

    function resizeCanvas() {
        const rect = canvas.parentElement.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        width = rect.width;
        height = rect.height;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        ctx.scale(dpr, dpr);
        cx = width / 2;
        cy = height / 2;
        maxRadius = Math.max(80, Math.min(width, height) / 2 - 25);
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Blip Store
    const blips = [];
    const MAX_BLIP_AGE_NORMAL = 12000; // 12 seconds
    const MAX_BLIP_AGE_ATTACK = 16000; // 16 seconds

    function hashStringToAngle(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash % 360) * (Math.PI / 180);
    }

    function addRadarBlip(record) {
        const proto = (record.protocol || 'tcp').toLowerCase();
        const service = record.service || 'unknown';
        const isAttack = (record.label === 'Attack');

        // Ring distribution based on protocol
        let ringRatio = 0.38; // inner tcp
        if (proto.includes('udp')) ringRatio = 0.68; // mid udp
        else if (proto.includes('icmp')) ringRatio = 0.92; // outer icmp

        // Add slight random jitter (+- 5%) so overlapping services spread naturally
        const jitter = (Math.random() - 0.5) * 0.08;
        const radius = maxRadius * Math.min(0.96, Math.max(0.18, ringRatio + jitter));
        const angle = hashStringToAngle(service) + ((Math.random() - 0.5) * 0.12);

        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);

        blips.push({
            x,
            y,
            angle,
            radius,
            service,
            protocol: proto,
            label: record.label,
            confidence: record.confidence,
            timestamp: record.timestamp,
            createdAt: performance.now(),
            isAttack,
            rippleRadius: 0
        });

        // Trigger Tactical Alarm effects on Attack
        if (isAttack) {
            triggerAttackAlert();
        } else {
            if (window.Watchtower) window.Watchtower.playRadarPing();
        }
    }

    function triggerAttackAlert() {
        if (threatVignette) {
            threatVignette.classList.add('flash');
            setTimeout(() => threatVignette.classList.remove('flash'), 450);
        }
        if (window.Watchtower) window.Watchtower.playAlarmPing();
    }

    // Interactive Hover HUD Tooltip
    let mousePos = { x: -100, y: -100 };
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mousePos.x = e.clientX - rect.left;
        mousePos.y = e.clientY - rect.top;

        let hoveredBlip = null;
        for (let i = blips.length - 1; i >= 0; i--) {
            const b = blips[i];
            const dist = Math.hypot(b.x - mousePos.x, b.y - mousePos.y);
            if (dist <= 14) {
                hoveredBlip = b;
                break;
            }
        }

        if (hoveredBlip && hudTooltip) {
            hudTooltip.style.display = 'block';
            hudTooltip.style.left = `${e.clientX + 14}px`;
            hudTooltip.style.top = `${e.clientY - 20}px`;
            const isAtt = hoveredBlip.isAttack;
            hudTooltip.innerHTML = `
                <div style="font-weight: 800; color: ${isAtt ? 'var(--coral)' : 'var(--cyan)'}; letter-spacing: 0.08em;">
                    [TARGET: ${hoveredBlip.label.toUpperCase()}]
                </div>
                <div>SVC: <code>${hoveredBlip.service}</code> | PROTO: <code>${hoveredBlip.protocol.toUpperCase()}</code></div>
                <div>CONFIDENCE: <strong>${Math.round(hoveredBlip.confidence * 100)}%</strong></div>
                <div style="font-size: 0.65rem; color: var(--text-dim); margin-top: 3px;">TIME: ${hoveredBlip.timestamp}</div>
            `;
        } else if (hudTooltip) {
            hudTooltip.style.display = 'none';
        }
    });

    canvas.addEventListener('mouseleave', () => {
        mousePos.x = -100;
        mousePos.y = -100;
        if (hudTooltip) hudTooltip.style.display = 'none';
    });

    // Main 60FPS Radar Render Loop
    let lastFrameTime = performance.now();
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function renderRadar(now) {
        requestAnimationFrame(renderRadar);
        if (!isTabVisible) return;

        const delta = now - lastFrameTime;
        lastFrameTime = now;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        const isLight = document.documentElement.getAttribute('data-theme') === 'light';
        const ringColor = isLight ? 'rgba(26, 31, 43, 0.16)' : 'rgba(30, 42, 64, 0.75)';
        const crossColor = isLight ? 'rgba(26, 31, 43, 0.1)' : 'rgba(30, 42, 64, 0.45)';
        const textColor = isLight ? '#526077' : '#6F7F99';

        // 1. Draw Concentric Range Rings (TCP, UDP, ICMP)
        ctx.save();
        ctx.lineWidth = 1;
        ctx.strokeStyle = ringColor;

        const rings = [
            { r: maxRadius * 0.38, tag: 'TCP [CORE]' },
            { r: maxRadius * 0.68, tag: 'UDP [MID-RANGE]' },
            { r: maxRadius * 0.94, tag: 'ICMP [PERIMETER]' }
        ];

        rings.forEach(ring => {
            ctx.beginPath();
            ctx.arc(cx, cy, ring.r, 0, Math.PI * 2);
            ctx.stroke();

            // Label on the ring
            ctx.fillStyle = textColor;
            ctx.font = "9px 'JetBrains Mono'";
            ctx.fillText(ring.tag, cx + 8, cy - ring.r + 12);
        });

        // 2. Draw Crosshair Azimuth Lines
        ctx.strokeStyle = crossColor;
        ctx.beginPath();
        // 0-180
        ctx.moveTo(cx - maxRadius * 0.96, cy);
        ctx.lineTo(cx + maxRadius * 0.96, cy);
        // 90-270
        ctx.moveTo(cx, cy - maxRadius * 0.96);
        ctx.lineTo(cx, cy + maxRadius * 0.96);
        // Diagonal 45-225
        const d45 = maxRadius * 0.96 * 0.7071;
        ctx.moveTo(cx - d45, cy - d45);
        ctx.lineTo(cx + d45, cy + d45);
        ctx.moveTo(cx - d45, cy + d45);
        ctx.lineTo(cx + d45, cy - d45);
        ctx.stroke();

        // 3. Perimeter Degree Markings
        for (let deg = 0; deg < 360; deg += 30) {
            const rad = deg * (Math.PI / 180);
            const x1 = cx + (maxRadius * 0.94) * Math.cos(rad);
            const y1 = cy + (maxRadius * 0.94) * Math.sin(rad);
            const x2 = cx + (maxRadius * 0.97) * Math.cos(rad);
            const y2 = cy + (maxRadius * 0.97) * Math.sin(rad);
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();

            if (deg % 90 === 0) {
                const labelX = cx + (maxRadius * 1.02) * Math.cos(rad) - 8;
                const labelY = cy + (maxRadius * 1.02) * Math.sin(rad) + 4;
                ctx.fillStyle = textColor;
                ctx.font = "10px 'JetBrains Mono'";
                const compass = deg === 0 ? '090°' : deg === 90 ? '180°' : deg === 180 ? '270°' : '360°';
                ctx.fillText(compass, labelX, labelY);
            }
        }

        // 4. Rotating Sweep Beam with Fading Sector Trail
        if (!reducedMotion) {
            sweepAngle = (sweepAngle + 0.024) % (Math.PI * 2);
        }

        const trailArc = Math.PI * 0.32; // 57 degree fading beam
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, maxRadius * 0.96);
        grad.addColorStop(0, 'rgba(255, 176, 32, 0)');
        grad.addColorStop(1, isLight ? 'rgba(180, 83, 9, 0.18)' : 'rgba(255, 176, 32, 0.25)');

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, maxRadius * 0.96, sweepAngle - trailArc, sweepAngle, false);
        ctx.closePath();
        ctx.fill();

        // Leading crisp beam line
        ctx.strokeStyle = isLight ? '#B45309' : '#FFB020';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + (maxRadius * 0.96) * Math.cos(sweepAngle), cy + (maxRadius * 0.96) * Math.sin(sweepAngle));
        ctx.stroke();

        // 5. Draw Blips
        for (let i = blips.length - 1; i >= 0; i--) {
            const b = blips[i];
            const age = now - b.createdAt;
            const maxAge = b.isAttack ? MAX_BLIP_AGE_ATTACK : MAX_BLIP_AGE_NORMAL;

            if (age > maxAge) {
                blips.splice(i, 1);
                continue;
            }

            const life = 1 - (age / maxAge);

            if (b.isAttack) {
                // Expanding Shockwave Ripple
                b.rippleRadius += 0.45;
                if (b.rippleRadius < 45) {
                    ctx.beginPath();
                    ctx.strokeStyle = `rgba(255, 77, 94, ${Math.max(0, (1 - b.rippleRadius / 45) * 0.7)})`;
                    ctx.lineWidth = 1.5;
                    ctx.arc(b.x, b.y, b.rippleRadius, 0, Math.PI * 2);
                    ctx.stroke();
                }

                // Flash pulse
                const pulse = 5 + Math.sin(now * 0.015) * 2;
                ctx.fillStyle = '#FF4D5E';
                ctx.shadowColor = '#FF4D5E';
                ctx.shadowBlur = 14;
                ctx.beginPath();
                ctx.arc(b.x, b.y, pulse, 0, Math.PI * 2);
                ctx.fill();
                ctx.shadowBlur = 0;

                // Comet tail behind attack blip
                ctx.fillStyle = `rgba(255, 77, 94, ${life * 0.4})`;
                ctx.beginPath();
                ctx.arc(b.x - 3 * Math.cos(b.angle), b.y - 3 * Math.sin(b.angle), 3, 0, Math.PI * 2);
                ctx.fill();
            } else {
                // Normal Cyan Blip
                ctx.fillStyle = isLight ? `rgba(15, 118, 110, ${life})` : `rgba(79, 209, 197, ${life})`;
                ctx.beginPath();
                ctx.arc(b.x, b.y, 3.5, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        ctx.restore();
    }
    requestAnimationFrame(renderRadar);

    // -------------------------------------------------------------------------
    // 2. Left Panel: Character-by-Character SIGNAL FEED
    // -------------------------------------------------------------------------
    const signalFeedBody = document.getElementById('signalFeedBody');
    const feedQueue = [];
    let isTyping = false;

    function queueFeedLine(record) {
        const isAttack = (record.label === 'Attack');
        const timePart = record.timestamp.split(' ')[1] || record.timestamp;
        const text = isAttack
            ? `${timePart} [!] ${record.protocol}/${record.service} ATTACK ${record.confidence.toFixed(2)}`
            : `${timePart} ${record.protocol}/${record.service} NORMAL ${record.confidence.toFixed(2)}`;

        feedQueue.push({ text, isAttack });
        if (!isTyping) {
            typeNextLine();
        }
    }

    function typeNextLine() {
        if (!signalFeedBody || feedQueue.length === 0) {
            isTyping = false;
            return;
        }

        isTyping = true;
        const item = feedQueue.shift();
        const lineEl = document.createElement('div');
        lineEl.className = `feed-line ${item.isAttack ? 'feed-attack' : 'feed-normal'}`;

        if (item.isAttack) {
            lineEl.innerHTML = `<span class="blinker">&#9658;</span> `;
        }

        signalFeedBody.prepend(lineEl);

        // Keep maximum 25 lines
        while (signalFeedBody.children.length > 25) {
            signalFeedBody.removeChild(signalFeedBody.lastChild);
        }

        if (reducedMotion) {
            lineEl.textContent = item.text;
            setTimeout(typeNextLine, 100);
            return;
        }

        let charIdx = 0;
        const typingTimer = setInterval(() => {
            if (charIdx < item.text.length) {
                lineEl.textContent += item.text.charAt(charIdx);
                charIdx++;
            } else {
                clearInterval(typingTimer);
                setTimeout(typeNextLine, 80);
            }
        }, 12);
    }

    // -------------------------------------------------------------------------
    // 3. Right Panel: THREAT LEVEL, Rolling Odometer & Model Confidence
    // -------------------------------------------------------------------------
    const recent20Records = [];
    let totalPackets = 0;
    let totalAttacks = 0;

    const elTotalPackets = document.getElementById('odoRecords');
    const elTotalAttacks = document.getElementById('odoAttacks');
    const elAttackRate = document.getElementById('odoAttackRate');
    const threatSegments = document.querySelectorAll('.threat-segment');

    function updateThreatLevel(record) {
        recent20Records.push(record.label === 'Attack' ? 1 : 0);
        if (recent20Records.length > 20) {
            recent20Records.shift();
        }

        totalPackets += 1;
        if (record.label === 'Attack') totalAttacks += 1;

        const rate = (totalAttacks / totalPackets) * 100;
        const windowAttacks = recent20Records.reduce((a, b) => a + b, 0);
        const windowAttackPct = (windowAttacks / recent20Records.length) * 100;

        // Odometer updates
        if (elTotalPackets) elTotalPackets.textContent = totalPackets.toLocaleString();
        if (elTotalAttacks) elTotalAttacks.textContent = totalAttacks.toLocaleString();
        if (elAttackRate) elAttackRate.textContent = `${rate.toFixed(1)}%`;

        // 5 Threat Segments
        let activeLevel = 'CALM';
        if (windowAttackPct > 60) activeLevel = 'CRITICAL';
        else if (windowAttackPct > 35) activeLevel = 'HIGH';
        else if (windowAttackPct > 15) activeLevel = 'ELEVATED';
        else if (windowAttackPct > 0) activeLevel = 'WATCH';

        threatSegments.forEach(seg => {
            const lvl = seg.getAttribute('data-level');
            seg.classList.toggle('active', lvl === activeLevel);
        });
    }

    // -------------------------------------------------------------------------
    // 4. Bottom Strip: "PULSE" ECG Heat-strip & Ticker Tape
    // -------------------------------------------------------------------------
    const pulseCanvas = document.getElementById('pulseCanvas');
    const tickerContent = document.getElementById('tickerContent');
    const pulseRecords = []; // max 120

    function resizePulseCanvas() {
        if (!pulseCanvas) return;
        const rect = pulseCanvas.getBoundingClientRect();
        pulseCanvas.width = rect.width;
        pulseCanvas.height = rect.height;
    }
    window.addEventListener('resize', resizePulseCanvas);
    resizePulseCanvas();

    function addPulseRecord(record) {
        pulseRecords.push(record);
        if (pulseRecords.length > 120) {
            pulseRecords.shift();
        }
        drawPulseStrip();

        // Update Ticker
        if (tickerContent) {
            const timePart = record.timestamp.split(' ')[1] || record.timestamp;
            const isAtt = (record.label === 'Attack');
            const alertSnippet = ` >>> [${isAtt ? 'THREAT DETECTED' : 'BENIGN'}] ${record.protocol.toUpperCase()}/${record.service.toUpperCase()} ${record.flag} | CONF ${record.confidence.toFixed(4)} @ ${timePart}`;
            tickerContent.textContent = alertSnippet + ' ' + tickerContent.textContent.slice(0, 500);
        }
    }

    function drawPulseStrip() {
        if (!pulseCanvas) return;
        const pctx = pulseCanvas.getContext('2d');
        const pw = pulseCanvas.width;
        const ph = pulseCanvas.height;

        pctx.clearRect(0, 0, pw, ph);

        const slotWidth = Math.max(4, pw / 120);

        pulseRecords.forEach((rec, idx) => {
            const x = idx * slotWidth;
            const barHeight = Math.max(6, rec.confidence * (ph - 12));
            const y = ph - barHeight - 4;

            pctx.fillStyle = rec.label === 'Attack' ? '#FF4D5E' : '#4FD1C5';
            pctx.fillRect(x, y, slotWidth - 1, barHeight);
        });

        // Scan Head Line
        const headX = pulseRecords.length * slotWidth;
        pctx.strokeStyle = '#FFB020';
        pctx.lineWidth = 2;
        pctx.beginPath();
        pctx.moveTo(headX, 0);
        pctx.lineTo(headX, ph);
        pctx.stroke();
    }

    // -------------------------------------------------------------------------
    // 5. Physical Rocker Switch & Polling Engine
    // -------------------------------------------------------------------------
    const rockerBtn = document.getElementById('rockerSwitchBtn');
    const statusLamp = document.getElementById('statusLamp');
    const rockerLabel = document.getElementById('rockerLabel');
    let pollingInterval = null;

    function pollNextPacket() {
        fetch('/api/monitor/next')
            .then(res => {
                if (!res.ok) throw new Error('API offline');
                return res.json();
            })
            .then(record => {
                addRadarBlip(record);
                queueFeedLine(record);
                updateThreatLevel(record);
                addPulseRecord(record);
            })
            .catch(err => {
                console.error('Watchtower polling halted:', err);
                stopMonitoring();
            });
    }

    function startMonitoring() {
        if (pollingInterval) return;
        pollingInterval = setInterval(pollNextPacket, 1000);
        pollNextPacket(); // instant trigger

        if (rockerBtn) rockerBtn.classList.add('active');
        if (statusLamp) statusLamp.classList.add('lit');
        if (rockerLabel) rockerLabel.textContent = 'STANDBY (STOP)';
        if (window.Watchtower) window.Watchtower.showToast('SWEEP ACTIVE // INGESTING SIMULATED TELEMETRY', 'success');
    }

    function stopMonitoring() {
        if (!pollingInterval) return;
        clearInterval(pollingInterval);
        pollingInterval = null;

        if (rockerBtn) rockerBtn.classList.remove('active');
        if (statusLamp) statusLamp.classList.remove('lit');
        if (rockerLabel) rockerLabel.textContent = 'ENGAGE SWEEP';
        if (window.Watchtower) window.Watchtower.showToast('RADAR SWEEP PAUSED', 'info');
    }

    if (rockerBtn) {
        rockerBtn.addEventListener('click', () => {
            if (pollingInterval) stopMonitoring();
            else startMonitoring();
        });
    }

    // -------------------------------------------------------------------------
    // 6. Signature Slide-out Panel (Top Indicators)
    // -------------------------------------------------------------------------
    const sigPanel = document.getElementById('signaturePanel');
    const btnToggleSig = document.getElementById('btnToggleSignature');
    const btnCloseSig = document.getElementById('btnCloseSignature');
    const signatureBody = document.getElementById('signatureBody');

    function loadFeatureImportances() {
        fetch('/api/metrics')
            .then(res => res.json())
            .then(data => {
                if (!signatureBody || !data.feature_importance) return;
                let html = '';
                const maxScore = data.feature_importance[0]?.importance || 0.2;

                data.feature_importance.forEach((f, idx) => {
                    const pct = Math.round((f.importance / maxScore) * 100);
                    html += `
                        <div class="signature-row">
                            <div class="sig-meta">
                                <span class="sig-name">[#${idx + 1}] ${f.feature}</span>
                                <span class="sig-score">${(f.importance * 100).toFixed(2)}%</span>
                            </div>
                            <div class="sig-scanline-track">
                                <div class="sig-scanline-fill" style="width: ${pct}%"></div>
                            </div>
                        </div>
                    `;
                });
                signatureBody.innerHTML = html;
            })
            .catch(err => console.error('Failed to load signature indicators:', err));
    }

    if (btnToggleSig && sigPanel) {
        btnToggleSig.addEventListener('click', () => {
            sigPanel.classList.toggle('open');
            if (sigPanel.classList.contains('open')) {
                loadFeatureImportances();
            }
        });
    }

    if (btnCloseSig && sigPanel) {
        btnCloseSig.addEventListener('click', () => {
            sigPanel.classList.remove('open');
        });
    }

    // Initial fetch of historical stats for odometer
    fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
            totalPackets = data.total_records || 0;
            totalAttacks = data.attacks_detected || 0;
            if (elTotalPackets) elTotalPackets.textContent = totalPackets.toLocaleString();
            if (elTotalAttacks) elTotalAttacks.textContent = totalAttacks.toLocaleString();
            if (elAttackRate) elAttackRate.textContent = `${data.attack_percentage.toFixed(1)}%`;
        })
        .catch(err => console.error('Stats initial load failed:', err));
});
