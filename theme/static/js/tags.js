function createTagElement(value, text, container, removeCallback) {
    const tagElement = document.createElement('div');
    tagElement.className = 'tag-badge';
    tagElement.textContent = text;

    const closeButton = document.createElement('span');
    closeButton.className = 'tag-close';
    closeButton.textContent = '×';
    closeButton.onclick = function () {
        container.removeChild(tagElement);
        removeCallback(value);
    };

    tagElement.appendChild(closeButton);
    container.appendChild(tagElement);
}