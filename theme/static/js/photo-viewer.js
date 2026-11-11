(() => {
    const viewer = document.getElementById('photo-viewer');
    if (!viewer) return;
    const image = document.getElementById('viewer-image');
    const stage = viewer.querySelector('.viewer-stage');
    const status = document.getElementById('viewer-status');
    const download = document.getElementById('viewer-download');
    const zoom = document.getElementById('viewer-zoom');
    const buttons = [...viewer.querySelectorAll('[data-variant]')];
    const labels = {original: 'Oryginał', color: 'Wersja kolorowa AI', reverse: 'Tył zdjęcia'};
    const downloads = {original: 'Pobierz oryginał', color: 'Pobierz wersję kolorową', reverse: 'Pobierz tył zdjęcia'};
    let selected = 'original';
    function show(variant) {
        const url = image.dataset[variant];
        if (!url) return;
        selected = variant;
        image.src = url;
        image.alt = labels[variant];
        buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.variant === selected)));
        download.href = url + (url.includes('?') ? '&' : '?') + 'download=1';
        download.textContent = downloads[variant];
        status.textContent = `Oglądasz: ${labels[variant].toLowerCase()}.`;
    }
    buttons.forEach(button => button.addEventListener('click', () => show(button.dataset.variant)));
    document.getElementById('show-color').addEventListener('click', () => show('color'));
    image.addEventListener('error', () => { status.textContent = 'Nie udało się wczytać tej wersji zdjęcia. Wybierz wersję ponownie lub odśwież stronę.'; });
    zoom.addEventListener('click', () => {
        const expanded = stage.classList.toggle('is-zoomed');
        zoom.setAttribute('aria-pressed', String(expanded));
        zoom.textContent = expanded ? 'Dopasuj do ekranu' : 'Powiększ zdjęcie';
    });
    document.getElementById('colorization-panel').addEventListener('colorization:updated', event => {
        const data = event.detail;
        if (!data.has_result || !data.image_url) return;
        const url = data.image_url + '?v=' + encodeURIComponent(data.result_version);
        const changed = image.dataset.color !== url;
        image.dataset.color = url;
        buttons.find(button => button.dataset.variant === 'color').disabled = false;
        // Respect the selected variant, including when regeneration finishes.
        if (selected === 'color' && changed) show('color');
    });
})();
