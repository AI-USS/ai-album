function createTagElement(value, text, container, removeCallback) {
    const tag = document.createElement('div');
    tag.className = 'tag-badge';
    const label = document.createElement('span');
    label.textContent = text;
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'tag-close';
    close.textContent = '×';
    close.setAttribute('aria-label', `Usuń tag: ${text}`);
    close.addEventListener('click', () => { tag.remove(); removeCallback(value); });
    tag.append(label, close);
    container.append(tag);
}

function setupTags(initial) {
    const field = document.getElementById('djtags');
    const input = document.getElementById('tag-entry');
    const container = document.getElementById('tagsContainer');
    const error = document.getElementById('tag-error');
    let tags = [...new Set(initial.map(tag => tag.trim()).filter(Boolean))];
    function render() {
        container.replaceChildren();
        tags.forEach(tag => createTagElement(tag, tag, container, value => {
            tags = tags.filter(tag => tag !== value);
            render();
        }));
        field.value = tags.length ? '#' + tags.join('#') : '';
    }
    function commit() {
        const additions = input.value.split(/[,#\n]/).map(tag => tag.trim()).filter(Boolean);
        const next = [...new Set([...tags, ...additions])];
        if (next.some(tag => tag.length > 100) || (next.length ? '#' + next.join('#') : '').length > 255) {
            error.textContent = 'Skróć tagi: jeden tag może mieć do 100 znaków, a wszystkie razem do 255.';
            input.focus();
            return false;
        }
        tags = next;
        input.value = '';
        error.textContent = '';
        render();
        return true;
    }
    input.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ',') { event.preventDefault(); commit(); }
    });
    input.addEventListener('paste', () => setTimeout(() => { if (input.value.includes(',')) commit(); }, 0));
    render();
    return {commit};
}
