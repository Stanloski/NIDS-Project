/**
 * Radar Watchtower - Batch Scanner Bay & Mosaic Array (CSV Upload)
 * Department of Computer Science, University of Nigeria, Nsukka
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const dropzone = document.getElementById('scannerDropzone');
    const fileInput = document.getElementById('batchFileInput');
    const progressBar = document.getElementById('batchProgressBar');
    const progressStatus = document.getElementById('batchProgressStatus');
    const resultsBay = document.getElementById('batchResultsBay');
    const mosaicContainer = document.getElementById('specimenMosaic');
    const btnReset = document.getElementById('btnResetScanner');

    if (!dropzone || !fileInput) return;

    ['dragenter', 'dragover'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(name => {
        dropzone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files && dt.files.length > 0) {
            handleFileUpload(dt.files[0]);
        }
    });

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    function handleFileUpload(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            if (window.Watchtower) window.Watchtower.showToast('INVALID FORMAT: CSV FILE REQUIRED', 'error');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            if (window.Watchtower) window.Watchtower.showToast('PAYLOAD EXCEEDS MAXIMUM 5 MB CAPACITY', 'error');
            return;
        }

        const csrf = document.querySelector('input[name="csrf_token"]')?.value || '';
        const formData = new FormData();
        formData.append('file', file);
        formData.append('csrf_token', csrf);

        if (resultsBay) resultsBay.style.display = 'none';
        if (progressBar) progressBar.parentElement.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';
        if (progressStatus) progressStatus.textContent = `INGESTING ${file.name}... (0%)`;

        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);
        xhr.setRequestHeader('X-CSRF-Token', csrf);

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const pct = Math.round((e.loaded / e.total) * 100);
                if (progressBar) progressBar.style.width = `${pct}%`;
                if (progressStatus) {
                    progressStatus.textContent = pct === 100
                        ? 'RUNNING RANDOM FOREST INFERENCE ACROSS VECTORS...'
                        : `INGESTING ${file.name}... (${pct}%)`;
                }
            }
        };

        xhr.onload = () => {
            let res = {};
            try {
                res = JSON.parse(xhr.responseText);
            } catch (err) {
                res = { error: 'Failed to parse batch server response.' };
            }

            if (xhr.status === 200 && res.success) {
                if (progressBar) progressBar.parentElement.style.display = 'none';
                renderMosaicResults(res);
                if (window.Watchtower) window.Watchtower.showToast('BATCH SPECIMEN CLASSIFICATION COMPLETE', 'success');
            } else {
                if (progressBar) progressBar.parentElement.style.display = 'none';
                const msg = res.error || `Upload rejected with status ${xhr.status}.`;
                if (window.Watchtower) window.Watchtower.showToast(msg, 'error');
            }
        };

        xhr.onerror = () => {
            if (progressBar) progressBar.parentElement.style.display = 'none';
            if (window.Watchtower) window.Watchtower.showToast('COMMUNICATION BUS ERROR DURING UPLOAD', 'error');
        };

        xhr.send(formData);
    }

    function renderMosaicResults(data) {
        if (!resultsBay || !mosaicContainer) return;

        document.getElementById('mosaicTotal').textContent = data.total_records.toLocaleString();
        document.getElementById('mosaicAttacks').textContent = data.attacks_detected.toLocaleString();
        document.getElementById('mosaicNormal').textContent = data.normal_traffic.toLocaleString();
        document.getElementById('mosaicRate').textContent = `${data.attack_percentage.toFixed(1)}%`;

        // Generate Mosaic square tiles
        let html = '';
        const total = Math.min(600, data.total_records);
        const attacks = data.attacks_detected;
        const attackIndices = new Set();

        // Spread attacks evenly across the sample preview
        const step = total > attacks ? Math.floor(total / attacks) : 1;
        for (let i = 0; i < attacks && i * step < total; i++) {
            attackIndices.add(i * step);
        }

        for (let i = 0; i < total; i++) {
            const isAtt = attackIndices.has(i);
            const delay = (i * 0.008).toFixed(3);
            html += `<div class="mosaic-tile ${isAtt ? 'attk' : 'norm'}" style="animation-delay: ${delay}s" title="Record #${i + 1}: ${isAtt ? 'ATTACK' : 'NORMAL'}"></div>`;
        }
        mosaicContainer.innerHTML = html;

        dropzone.style.display = 'none';
        resultsBay.style.display = 'block';
    }

    if (btnReset) {
        btnReset.addEventListener('click', () => {
            fileInput.value = '';
            resultsBay.style.display = 'none';
            dropzone.style.display = 'block';
        });
    }
});
