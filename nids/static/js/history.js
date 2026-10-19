/**
 * Radar Watchtower - Archive Log & Flight Departure Board (History)
 * Department of Computer Science, University of Nigeria, Nsukka
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    const tableBody = document.querySelector('#departureBoard tbody');
    const searchInput = document.getElementById('archiveSearch');
    const filterChips = document.querySelectorAll('.filter-chip');
    const paginationInfo = document.getElementById('archivePaginationInfo');
    const paginationControls = document.getElementById('archivePaginationBtns');

    let currentPage = 1;
    const perPage = 18;
    let currentFilter = '';
    let debounceTimer = null;

    function renderSkeleton() {
        if (!tableBody) return;
        let html = '';
        for (let i = 0; i < 8; i++) {
            html += `
                <tr>
                    <td colspan="7" style="padding: 10px; color: var(--text-dim); letter-spacing: 0.1em;">
                        [FETCHING TELEMETRY SECTOR ${i + 1}...]
                    </td>
                </tr>
            `;
        }
        tableBody.innerHTML = html;
    }

    function fetchArchive(page = 1) {
        renderSkeleton();
        currentPage = page;

        const q = searchInput ? searchInput.value.trim() : '';
        const url = new URL('/api/history', window.location.origin);
        url.searchParams.set('page', currentPage);
        url.searchParams.set('per_page', perPage);
        if (q) url.searchParams.set('q', q);
        if (currentFilter) url.searchParams.set('label', currentFilter);

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error('Archive fetch error');
                return res.json();
            })
            .then(data => {
                renderBoard(data);
                renderPagination(data);
            })
            .catch(err => {
                console.error(err);
                if (tableBody) {
                    tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--coral); padding: 20px;">[ERROR: ARCHIVE TELEMETRY FEED OFFLINE]</td></tr>`;
                }
            });
    }

    function renderBoard(data) {
        if (!tableBody) return;

        if (!data.items || data.items.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">[NO HISTORICAL LOGS MATCHING QUERY PARAMS]</td></tr>`;
            return;
        }

        let html = '';
        data.items.forEach((item, idx) => {
            const isAtt = (item.predicted_label === 'Attack');
            const confPct = Math.round(item.confidence_score * 100);
            const timePart = item.timestamp.split(' ')[1] || item.timestamp;

            html += `
                <tr class="${isAtt ? 'row-attk' : ''}" style="animation: splitFlapRow 0.25s ease backwards; animation-delay: ${(idx * 0.02).toFixed(2)}s;">
                    <td><span style="color: var(--amber); font-weight: 700;">#${item.prediction_id}</span></td>
                    <td><code>${timePart}</code></td>
                    <td><strong>${item.protocol_type.toUpperCase()}</strong></td>
                    <td><code>${item.service}</code></td>
                    <td>
                        <span style="font-weight: 800; color: ${isAtt ? 'var(--coral)' : 'var(--cyan)'}; letter-spacing: 0.08em;">
                            ${item.predicted_label.toUpperCase()}
                        </span>
                    </td>
                    <td><strong>${confPct}%</strong> (${item.confidence_score.toFixed(4)})</td>
                    <td><span style="color: var(--text-dim); font-size: 0.72rem;">SRC: ${item.src_bytes}B / DST: ${item.dst_bytes}B</span></td>
                </tr>
            `;
        });
        tableBody.innerHTML = html;
    }

    function renderPagination(data) {
        if (!paginationInfo || !paginationControls) return;

        const start = data.total === 0 ? 0 : (data.page - 1) * perPage + 1;
        const end = Math.min(data.page * perPage, data.total);
        paginationInfo.textContent = `[DISPLAYING RECORDS ${start}-${end} OF ${data.total.toLocaleString()}]`;

        let btns = '';
        const prevDis = data.page <= 1 ? 'disabled' : '';
        const nextDis = data.page >= data.total_pages ? 'disabled' : '';

        btns += `<button class="btn-ctrl" ${prevDis} data-page="${data.page - 1}">PREV SECTOR</button>`;
        btns += `<span style="font-size: 0.74rem; font-weight: 700; color: var(--amber); padding: 0 8px;">SECTOR ${data.page}/${data.total_pages}</span>`;
        btns += `<button class="btn-ctrl" ${nextDis} data-page="${data.page + 1}">NEXT SECTOR</button>`;

        paginationControls.innerHTML = btns;

        paginationControls.querySelectorAll('button[data-page]').forEach(b => {
            b.addEventListener('click', function () {
                const target = parseInt(this.getAttribute('data-page'), 10);
                if (target >= 1 && target <= data.total_pages) {
                    fetchArchive(target);
                }
            });
        });
    }

    // Filter Chips
    filterChips.forEach(chip => {
        chip.addEventListener('click', function () {
            filterChips.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            currentFilter = this.getAttribute('data-filter') || '';
            fetchArchive(1);
        });
    });

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => fetchArchive(1), 300);
        });
    }

    fetchArchive(1);
});
