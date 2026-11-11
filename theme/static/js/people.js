function personValues(annotation) {
    return Object.fromEntries((annotation.body || []).map(body => [body.purpose, body.value]));
}

function createPersonPicker(values, onChange) {
    const people = JSON.parse(document.getElementById('available-people').textContent);
    const container = document.createElement('div');
    container.className = 'person-picker';
    const title = document.createElement('p');
    const selected = people.find(person => person.id === values.personId);
    title.textContent = selected ? `${selected.name} ${selected.surname}` : (values.name && values.lastName ? `${values.name} ${values.lastName}` : 'Do podpisania');
    title.className = 'person-current';
    container.append(title);
    function apply(next) {
        title.textContent = next.name && next.lastName ? `${next.name} ${next.lastName}${next.newPerson ? ' · nowa osoba' : ''}` : 'Do podpisania';
        onChange(next);
    }
    const label = document.createElement('label');
    label.textContent = 'Znajdź osobę w albumie';
    const search = document.createElement('input');
    search.type = 'search';
    search.placeholder = 'Imię lub nazwisko';
    search.autocomplete = 'off';
    label.append(search);
    container.append(label);
    const results = document.createElement('div');
    results.className = 'person-results';
    function renderResults() {
        results.replaceChildren();
        const query = search.value.trim().toLocaleLowerCase('pl');
        const matches = people.filter(person => `${person.name} ${person.surname}`.toLocaleLowerCase('pl').includes(query));
        matches.slice(0, 20).forEach(person => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-secondary';
            button.textContent = `${person.name} ${person.surname}`;
            if (people.filter(other => other.name === person.name && other.surname === person.surname).length > 1) button.textContent += ` (osoba ${person.id})`;
            button.addEventListener('click', () => apply({personId: person.id, name: person.name, lastName: person.surname, newPerson: false}));
            results.append(button);
        });
        if (!matches.length) { const text = document.createElement('p'); text.textContent = 'Brak pasujących osób. Możesz dodać nową poniżej.'; results.append(text); }
        if (matches.length > 20) { const text = document.createElement('p'); text.textContent = 'Wpisz więcej znaków, aby zawęzić listę.'; results.append(text); }
    }
    search.addEventListener('input', renderResults);
    search.addEventListener('keydown', event => { if (event.key === 'Enter') event.preventDefault(); });
    renderResults();
    container.append(results);
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = 'Dodaj nową osobę';
    details.append(summary);
    function field(text, value) {
        const label = document.createElement('label');
        label.textContent = text;
        const input = document.createElement('input');
        input.type = 'text'; input.maxLength = 100; input.value = value || '';
        label.append(input); details.append(label); return input;
    }
    const name = field('Imię', values.newPerson ? values.name : '');
    const surname = field('Nazwisko', values.newPerson ? values.lastName : '');
    const error = document.createElement('p'); error.className = 'errorlist'; error.setAttribute('role', 'status');
    const add = document.createElement('button'); add.type = 'button'; add.className = 'btn btn-secondary'; add.textContent = 'Przypisz nową osobę';
    add.addEventListener('click', () => {
        if (!name.value.trim() || !surname.value.trim()) { error.textContent = 'Podaj imię i nazwisko.'; return; }
        apply({personId: null, name: name.value.trim(), lastName: surname.value.trim(), newPerson: true});
    });
    [name, surname].forEach(input => input.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); add.click(); } }));
    details.append(error, add); container.append(details);
    const clear = document.createElement('button'); clear.type = 'button'; clear.className = 'btn btn-secondary'; clear.textContent = 'Pozostaw bez podpisu';
    clear.addEventListener('click', () => apply({personId: null, name: null, lastName: null, newPerson: false}));
    container.append(clear);
    return container;
}

function labelBodies(values) {
    return Object.entries(values).map(([purpose, value]) => ({type: 'TextualBody', purpose, value}));
}

function setupFaceList(anno, image, markDirty) {
    const list = document.getElementById('face-list');
    let selectedId = null;
    function highlight(id) {
        selectedId = id;
        [...list.children].forEach(card => card.classList.toggle('is-selected', card.dataset.faceId === String(id)));
    }
    function render() {
        list.replaceChildren();
        const annotations = anno.getAnnotations();
        if (!annotations.length) { list.textContent = 'Nie ma jeszcze oznaczonych twarzy. Możesz zaznaczyć twarz na zdjęciu lub zapisać je bez podpisów.'; return; }
        annotations.forEach((annotation, index) => {
            const values = personValues(annotation);
            const card = document.createElement('section'); card.className = 'face-card'; card.dataset.faceId = String(annotation.id);
            const select = document.createElement('button'); select.type = 'button'; select.className = 'face-thumbnail'; select.setAttribute('aria-label', `Pokaż twarz ${index + 1} na zdjęciu`);
            const canvas = document.createElement('canvas'); canvas.width = 90; canvas.height = 90;
            const [x, y, width, height] = annotation.target.selector.value.split(':')[1].split(',').map(Number);
            canvas.getContext('2d').drawImage(image, x, y, width, height, 0, 0, 90, 90);
            select.append(canvas); select.addEventListener('click', () => { anno.selectAnnotation(annotation.id); highlight(annotation.id); image.scrollIntoView({block: 'center', behavior: 'smooth'}); });
            const heading = document.createElement('h4'); heading.textContent = `Twarz ${index + 1} · ${values.name && values.lastName ? (values.newPerson ? 'Nowa osoba' : 'Podpisana') : 'Do podpisania'}`;
            const picker = createPersonPicker(values, next => {
                const updated = {...annotation, body: labelBodies(next)};
                anno.removeAnnotation(annotation.id); anno.addAnnotation(updated); markDirty(); render();
            });
            const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'btn btn-secondary'; remove.textContent = 'Usuń zaznaczenie twarzy';
            remove.addEventListener('click', () => { anno.removeAnnotation(annotation.id); markDirty(); render(); });
            card.append(select, heading, picker, remove); list.append(card);
        });
        highlight(selectedId);
    }
    anno.on('clickAnnotation', annotation => {
        highlight(annotation.id);
        const card = [...list.children].find(card => card.dataset.faceId === String(annotation.id));
        card?.scrollIntoView({block: 'nearest', behavior: 'smooth'});
    });
    return {render};
}
