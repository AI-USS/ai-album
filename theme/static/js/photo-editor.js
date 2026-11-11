(() => {
    const form = document.getElementById('photo-form');
    if (!form) return;
    const editing = form.dataset.editing === 'true';
    const image = document.getElementById('image');
    const preview = document.getElementById('image-container');
    const fileInput = document.getElementById('awers');
    const status = document.getElementById('face-status');
    const save = document.getElementById('save-photo');
    const retry = document.getElementById('retry-recognition');
    const payload = document.getElementById('additional_data');
    const tags = setupTags(JSON.parse(document.getElementById('initial-tags').textContent));
    let dirty = false, saving = false, editorReady = false;
    form.addEventListener('input', () => { dirty = true; });
    form.addEventListener('change', () => { dirty = true; });
    form.addEventListener('click', event => { if (event.target.closest('.tag-close')) dirty = true; });
    window.addEventListener('beforeunload', event => {
        if (dirty && !saving) { event.preventDefault(); event.returnValue = ''; }
    });
    let faceList;
    let anno, generation = 0, detectionGeneration = 0, controller, objectUrl;
    function initialize() {
        anno?.destroy();
        editorReady = false;
        anno = Annotorious.init({image, widgets: [PersonWidget], formatters: [NameAndLastNameFormatter]});
        faceList = setupFaceList(anno, image, () => { dirty = true; });
        ['createAnnotation', 'updateAnnotation', 'deleteAnnotation'].forEach(name => anno.on(name, () => { if (editorReady) dirty = true; queueMicrotask(() => faceList.render()); }));
    }
    async function detect(file, current) {
        controller?.abort();
        const attempt = ++detectionGeneration;
        const activeController = new AbortController();
        controller = activeController;
        const signal = activeController.signal;
        const timer = setTimeout(() => activeController.abort(), 45000);
        status.textContent = 'Szukamy twarzy i rozpoznajemy osoby…';
        retry.hidden = true;
        save.disabled = true;
        try {
            const data = new FormData();
            data.append('file', file);
            const response = await fetch(form.dataset.recognizeUrl, {method: 'POST', body: data, signal});
            if (!response.ok) throw new Error();
            const faces = Object.values(await response.json());
            if (current !== generation || attempt !== detectionGeneration) return;
            let recognized = 0;
            anno.clearAnnotations();
            faces.forEach((face, index) => {
                const [top, right, bottom, left] = face.coords;
                if (face.recognized) recognized++;
                anno.addAnnotation({id: `detected-${current}-${index}`, type: 'Annotation', body: [
                    {type: 'TextualBody', purpose: 'personId', value: face.id},
                    {type: 'TextualBody', purpose: 'name', value: face.name},
                    {type: 'TextualBody', purpose: 'lastName', value: face.last_name},
                ], target: {selector: {type: 'FragmentSelector', conformsTo: 'http://www.w3.org/TR/media-frags/', value: `xywh=pixel:${left},${top},${right-left},${bottom-top}`}}});
            });
            faceList.render();
            status.textContent = faces.length ? `Wykryte twarze: ${faces.length}. Rozpoznane osoby: ${recognized}. Kliknij ramkę, aby sprawdzić lub uzupełnić podpis.` : 'Nie wykryto twarzy. Możesz zaznaczyć osobę ręcznie lub zapisać zdjęcie bez oznaczeń.';
        } catch (_) {
            if (current === generation && attempt === detectionGeneration) {
                status.textContent = 'Nie udało się rozpoznać osób. Spróbuj ponownie, podpisz twarze ręcznie lub zapisz zdjęcie bez oznaczeń.';
                retry.hidden = false;
            }
        } finally {
            clearTimeout(timer);
            if (current === generation && attempt === detectionGeneration) save.disabled = false;
        }
    }
    fileInput?.addEventListener('change', async () => {
        const current = ++generation;
        controller?.abort();
        save.disabled = true;
        const file = fileInput.files[0];
        retry.hidden = true;
        if (!file) { preview.hidden = true; status.textContent = 'Wybierz zdjęcie.'; return; }
        if (objectUrl) URL.revokeObjectURL(objectUrl);
        objectUrl = URL.createObjectURL(file);
        image.src = objectUrl;
        preview.hidden = false;
        try {
            await image.decode();
            if (current !== generation) return;
            initialize();
            editorReady = true;
            await detect(file, current);
        } catch (_) {
            if (current === generation) status.textContent = 'Nie można wyświetlić tego pliku. Wybierz poprawne zdjęcie.';
        }
    });
    retry.addEventListener('click', () => { if (fileInput.files[0]) detect(fileInput.files[0], generation); });
    if (editing) {
        (async () => {
            try {
                await image.decode();
                initialize();
                let annotations = JSON.parse(document.getElementById('initial-annotations').textContent) || [];
                if (payload.value) { try { annotations = JSON.parse(payload.value); } catch (_) {} }
                annotations.forEach(annotation => anno.addAnnotation(annotation));
                status.textContent = 'Kliknij ramkę twarzy, aby sprawdzić podpis. Możesz też zaznaczyć brakującą twarz ręcznie.';
                faceList.render();
                editorReady = true;
                save.disabled = false;
            } catch (_) { status.textContent = 'Nie udało się wczytać zdjęcia lub oznaczeń. Odśwież stronę przed edycją.'; }
        })();
    }
    form.addEventListener('submit', event => {
        event.preventDefault();
        if (!form.reportValidity() || !anno || !tags.commit()) return;
        payload.value = JSON.stringify(anno.getAnnotations());
        save.disabled = true;
        save.textContent = 'Zapisywanie i aktualizacja rozpoznawania…';
        document.getElementById('save-status').textContent = 'Poczekaj na zakończenie zapisu.';
        saving = true;
        HTMLFormElement.prototype.submit.call(form);
    });
})();
