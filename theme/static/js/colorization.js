(() => {
    const panel = document.getElementById('colorization-panel');
    if (!panel) return;
    const button = panel.querySelector('button');
    const message = panel.querySelector('[role="status"]');
    const preview = panel.querySelector('[data-preview]');
    const image = preview.querySelector('img');
    const link = preview.querySelector('a');
    let timer;
    const labels = {idle: '', queued: 'Oczekuje w kolejce…', running: 'Kolorowanie…', succeeded: 'Gotowe', failed: 'Nie udało się pokolorować zdjęcia. Spróbuj ponownie.'};
    function render(data) {
        const active = ['queued', 'running'].includes(data.status);
        button.disabled = active;
        button.textContent = data.has_result ? 'Pokoloruj ponownie' : 'Pokoloruj zdjęcie';
        panel.dataset.hasResult = data.has_result ? '1' : '0';
        message.textContent = labels[data.status] || '';
        if (data.has_result && data.image_url) {
            if (image && image.dataset.resultVersion !== data.result_version) {
                image.src = data.image_url + '?v=' + encodeURIComponent(data.result_version);
                image.dataset.resultVersion = data.result_version;
            }
            link.href = data.image_url + '?download=1';
            preview.hidden = false;
        }
        panel.dispatchEvent?.(new CustomEvent('colorization:updated', {detail: data}));
        if (active) timer = setTimeout(refresh, 3000);
    }
    async function refresh() {
        clearTimeout(timer);
        try {
            const response = await fetch(panel.dataset.statusUrl);
            if (!response.ok) throw new Error();
            render(await response.json());
        } catch (_) {
            message.textContent = 'Brak połączenia. Ponawiam sprawdzenie statusu…';
            timer = setTimeout(refresh, 10000);
        }
    }
    button.addEventListener('click', async () => {
        clearTimeout(timer);
        button.disabled = true;
        try {
            const response = await fetch(panel.dataset.startUrl, {
                method: 'POST',
                headers: {'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value},
                body: new URLSearchParams({regenerate: panel.dataset.hasResult || '0'})
            });
            if (!response.ok) throw new Error();
            await refresh();
        } catch (_) {
            message.textContent = 'Nie udało się uruchomić kolorowania. Spróbuj ponownie.';
            button.disabled = false;
        }
    });
    refresh();
    window.addEventListener('pagehide', () => clearTimeout(timer));
})();
