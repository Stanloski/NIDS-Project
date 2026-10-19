/**
 * Radar Watchtower - Specimen Scanner (Manual Predict)
 * Department of Computer Science, University of Nigeria, Nsukka
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const form = document.getElementById('specimenForm');
    const scanline = document.getElementById('specimenScanline');
    const verdictWrap = document.getElementById('verdictStampWrap');
    const verdictStamp = document.getElementById('verdictStamp');
    const verdictScore = document.getElementById('verdictScore');
    const verdictRing = document.getElementById('verdictRingFill');
    const verdictMeta = document.getElementById('verdictMeta');
    const btnSubmit = document.getElementById('btnSubmitSpecimen');

    const SAMPLE_NORMAL = {
        "duration": 2, "protocol_type": "tcp", "service": "ftp_data", "flag": "SF",
        "src_bytes": 12983, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0, "root_shell": 0,
        "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0,
        "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
        "count": 1, "srv_count": 1, "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 0.0,
        "srv_rerror_rate": 0.0, "same_srv_rate": 1.0, "diff_srv_rate": 0.0, "srv_diff_host_rate": 0.0,
        "dst_host_count": 134, "dst_host_srv_count": 86, "dst_host_same_srv_rate": 0.61,
        "dst_host_diff_srv_rate": 0.04, "dst_host_same_src_port_rate": 0.61,
        "dst_host_srv_diff_host_rate": 0.02, "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 0.0, "dst_host_srv_rerror_rate": 0.0
    };

    const SAMPLE_ATTACK = {
        "duration": 0, "protocol_type": "tcp", "service": "private", "flag": "REJ",
        "src_bytes": 0, "dst_bytes": 0, "land": 0, "wrong_fragment": 0, "urgent": 0,
        "hot": 0, "num_failed_logins": 0, "logged_in": 0, "num_compromised": 0, "root_shell": 0,
        "su_attempted": 0, "num_root": 0, "num_file_creations": 0, "num_shells": 0,
        "num_access_files": 0, "num_outbound_cmds": 0, "is_host_login": 0, "is_guest_login": 0,
        "count": 229, "srv_count": 10, "serror_rate": 0.0, "srv_serror_rate": 0.0, "rerror_rate": 1.0,
        "srv_rerror_rate": 1.0, "same_srv_rate": 0.04, "diff_srv_rate": 0.06, "srv_diff_host_rate": 0.0,
        "dst_host_count": 255, "dst_host_srv_count": 10, "dst_host_same_srv_rate": 0.04,
        "dst_host_diff_srv_rate": 0.06, "dst_host_same_src_port_rate": 0.0,
        "dst_host_srv_diff_host_rate": 0.0, "dst_host_serror_rate": 0.0,
        "dst_host_srv_serror_rate": 0.0, "dst_host_rerror_rate": 1.0, "dst_host_srv_rerror_rate": 1.0
    };

    function populateFields(data) {
        Object.keys(data).forEach(key => {
            const input = document.getElementById(`spec_${key}`);
            if (input) input.value = data[key];
        });
        if (verdictWrap) verdictWrap.classList.remove('show');
    }

    const tabNormal = document.getElementById('tabLoadNormal');
    const tabAttack = document.getElementById('tabLoadAttack');

    if (tabNormal) {
        tabNormal.addEventListener('click', () => {
            populateFields(SAMPLE_NORMAL);
            if (window.Watchtower) window.Watchtower.showToast('PRELOADED BENIGN TELEMETRY SPECIMEN', 'success');
        });
    }

    if (tabAttack) {
        tabAttack.addEventListener('click', () => {
            populateFields(SAMPLE_ATTACK);
            if (window.Watchtower) window.Watchtower.showToast('PRELOADED HOSTILE ANOMALY SPECIMEN', 'error');
        });
    }

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const inputs = form.querySelectorAll('input, select');
            const payload = {};
            let missingField = '';

            inputs.forEach(el => {
                if (el.name && el.name !== 'csrf_token') {
                    const val = el.value.trim();
                    if (val === '') {
                        if (!missingField) missingField = el.name;
                    }
                    payload[el.name] = val;
                }
            });

            if (missingField) {
                if (window.Watchtower) window.Watchtower.showToast(`VALIDATION ERROR: '${missingField}' IS REQUIRED`, 'error');
                return;
            }

            const csrf = document.querySelector('input[name="csrf_token"]')?.value || '';

            // Laser Scan Sweep Animation
            if (scanline) {
                scanline.classList.remove('scanning');
                void scanline.offsetWidth; // reflow
                scanline.classList.add('scanning');
            }

            if (btnSubmit) {
                btnSubmit.disabled = true;
                btnSubmit.textContent = '[ SCANNING TELEMETRY MATRIX... ]';
            }

            fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrf
                },
                body: JSON.stringify(payload)
            })
            .then(async res => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Classification failed');
                return data;
            })
            .then(res => {
                // Wait for scanline sweep to complete (approx 800ms)
                setTimeout(() => {
                    renderVerdict(res);
                }, 850);
            })
            .catch(err => {
                if (window.Watchtower) window.Watchtower.showToast(err.message, 'error');
            })
            .finally(() => {
                setTimeout(() => {
                    if (btnSubmit) {
                        btnSubmit.disabled = false;
                        btnSubmit.textContent = '[ INITIATE TARGET CLASSIFICATION ]';
                    }
                }, 900);
            });
        });
    }

    function renderVerdict(data) {
        if (!verdictWrap || !verdictStamp) return;

        const isAttack = (data.label === 'Attack');
        verdictStamp.textContent = isAttack ? 'MALICIOUS THREAT DETECTED' : 'BENIGN NETWORK TRAFFIC';
        verdictStamp.className = `verdict-stamp ${isAttack ? 'attack' : 'normal'}`;

        const confPct = Math.round(data.confidence * 100);
        if (verdictScore) verdictScore.textContent = `${confPct}% CONFIDENCE`;
        if (verdictMeta) verdictMeta.textContent = `TARGET AUDIT #${data.prediction_id} // RECORDED ${data.timestamp}`;

        // Ring animation (circ = 2 * pi * 36 ~= 226)
        if (verdictRing) {
            const circ = 226;
            const offset = circ - (circ * data.confidence);
            verdictRing.style.stroke = isAttack ? 'var(--coral)' : 'var(--cyan)';
            verdictRing.style.strokeDasharray = `${circ}`;
            verdictRing.style.strokeDashoffset = `${circ}`;
            setTimeout(() => {
                verdictRing.style.strokeDashoffset = `${offset}`;
            }, 50);
        }

        verdictWrap.classList.add('show');
        verdictWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        if (isAttack) {
            if (window.Watchtower) window.Watchtower.playAlarmPing();
        } else {
            if (window.Watchtower) window.Watchtower.playRadarPing();
        }
    }
});
