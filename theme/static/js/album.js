(() => {
    const filters = document.getElementById('filters-panel');
    if (filters && matchMedia('(max-width:760px)').matches && filters.dataset.hasSelection !== 'true') filters.open = false;
    const toggle = document.querySelector('.menu-toggle');
    const navigation = document.getElementById('main-navigation');
    toggle?.addEventListener('click', () => {
        const open = toggle.getAttribute('aria-expanded') !== 'true';
        toggle.setAttribute('aria-expanded', String(open));
        navigation.classList.toggle('is-open', open);
    });
    document.querySelectorAll('form[data-busy-label]').forEach(form => {
        form.addEventListener('submit', () => {
            if (!form.checkValidity()) return;
            const button = form.querySelector('[type=submit]');
            button.disabled = true;
            button.textContent = form.dataset.busyLabel;
        });
    });
})();
