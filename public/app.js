// Application State
let blocks = [];
let nextBlockId = 1;

// DOM Elements
const blocksContainer = document.getElementById('blocks-container');
const emptyPlaceholder = document.getElementById('empty-placeholder');
const elementsCountSpan = document.getElementById('elements-count');
const btnGenerate = document.getElementById('btn-generate');
const toastEl = document.getElementById('toast');

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Add block listeners
    document.querySelectorAll('.btn-palette').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-type');
            addBlock(type);
        });
    });

    // Generate PDF listener
    btnGenerate.addEventListener('click', generatePDF);
    
    // Seed sample blocks to make it easy for first-time use
    seedSampleData();
});

// Toast alert helper
function showToast(message, type = 'success') {
    toastEl.textContent = message;
    toastEl.className = `toast toast-${type}`;
    toastEl.classList.remove('hidden');

    setTimeout(() => {
        toastEl.classList.add('hidden');
    }, 4000);
}

// Update elements counters and empty states
function updateUIState() {
    elementsCountSpan.textContent = `${blocks.length} ${blocks.length === 1 ? 'elemento' : 'elementos'}`;
    
    if (blocks.length === 0) {
        emptyPlaceholder.style.display = 'flex';
    } else {
        emptyPlaceholder.style.display = 'none';
    }
}

// Add block to stack
function addBlock(type) {
    const blockId = `block-${nextBlockId++}`;
    const newBlock = {
        id: blockId,
        type: type,
        // Block-specific fields
        text: '',
        file1: null,
        file2: null,
        fileName1: '',
        fileName2: ''
    };

    blocks.push(newBlock);
    renderBlocks();
    updateUIState();
    
    // Smooth scroll to the newly added block
    const cardEl = document.getElementById(blockId);
    if (cardEl) {
        cardEl.scrollIntoView({ behavior: 'smooth' });
    }
}

// Delete block from stack
function deleteBlock(id) {
    blocks = blocks.filter(b => b.id !== id);
    renderBlocks();
    updateUIState();
}

// Move block up or down
function moveBlock(id, direction) {
    const idx = blocks.findIndex(b => b.id === id);
    if (idx === -1) return;

    if (direction === 'up' && idx > 0) {
        // Swap elements
        const temp = blocks[idx];
        blocks[idx] = blocks[idx - 1];
        blocks[idx - 1] = temp;
    } else if (direction === 'down' && idx < blocks.length - 1) {
        // Swap elements
        const temp = blocks[idx];
        blocks[idx] = blocks[idx + 1];
        blocks[idx + 1] = temp;
    }

    renderBlocks();
}

// Renders the list of blocks
function renderBlocks() {
    // Save current values from DOM to state first
    saveAllInputsToState();

    // Clear previous dynamic elements
    const dynamicCards = blocksContainer.querySelectorAll('.block-card');
    dynamicCards.forEach(c => c.remove());

    blocks.forEach((block, index) => {
        const card = createBlockCard(block, index);
        blocksContainer.appendChild(card);
        setupImageDragAndDrop(block.id);
    });
}

// Save inputs currently typed in the DOM to the internal state array
function saveAllInputsToState() {
    blocks.forEach(block => {
        const card = document.getElementById(block.id);
        if (!card) return;

        if (block.type === 'title' || block.type === 'subtitle' || block.type === 'text') {
            const input = card.querySelector('.block-input');
            if (input) block.text = input.value;
        }
    });
}

// Create Card DOM element
function createBlockCard(block, index) {
    const card = document.createElement('div');
    card.id = block.id;
    card.className = 'block-card';
    card.setAttribute('data-type', block.type);

    // Create header area
    const header = document.createElement('div');
    header.className = 'block-header';

    const titleArea = document.createElement('div');
    titleArea.className = 'block-title-area';
    
    const badge = document.createElement('span');
    badge.className = 'block-badge';
    badge.textContent = translateType(block.type);
    titleArea.appendChild(badge);

    const titleLabel = document.createElement('h4');
    titleLabel.textContent = `Posición #${index + 1}`;
    titleArea.appendChild(titleLabel);

    header.appendChild(titleArea);

    // Create controls
    const controls = document.createElement('div');
    controls.className = 'block-controls';

    // Up arrow button
    const btnUp = document.createElement('button');
    btnUp.className = 'btn-control';
    btnUp.innerHTML = '▲';
    btnUp.title = 'Subir elemento';
    btnUp.disabled = index === 0;
    btnUp.addEventListener('click', () => moveBlock(block.id, 'up'));
    controls.appendChild(btnUp);

    // Down arrow button
    const btnDown = document.createElement('button');
    btnDown.className = 'btn-control';
    btnDown.innerHTML = '▼';
    btnDown.title = 'Bajar elemento';
    btnDown.disabled = index === blocks.length - 1;
    btnDown.addEventListener('click', () => moveBlock(block.id, 'down'));
    controls.appendChild(btnDown);

    // Delete button
    const btnDelete = document.createElement('button');
    btnDelete.className = 'btn-control btn-delete';
    btnDelete.innerHTML = '🗑️';
    btnDelete.title = 'Eliminar elemento';
    btnDelete.addEventListener('click', () => deleteBlock(block.id));
    controls.appendChild(btnDelete);

    header.appendChild(controls);
    card.appendChild(header);

    // Create content area
    const content = document.createElement('div');
    content.className = 'block-content';

    if (block.type === 'title') {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'block-input';
        input.value = block.text;
        input.placeholder = 'Escribe el título principal aquí...';
        content.appendChild(input);
    } 
    else if (block.type === 'subtitle') {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'block-input';
        input.value = block.text;
        input.placeholder = 'Escribe el subtítulo de la sección...';
        content.appendChild(input);
    } 
    else if (block.type === 'text') {
        const textarea = document.createElement('textarea');
        textarea.className = 'block-input';
        textarea.value = block.text;
        textarea.placeholder = 'Escribe el párrafo explicativo... Puedes usar <b>negritas</b> o <i>cursivas</i>.';
        content.appendChild(textarea);
    } 
    else if (block.type === 'image') {
        content.innerHTML = `
            <div class="image-upload-zone" id="zone-1-${block.id}">
                <span class="upload-icon">📁</span>
                <p id="label-1-${block.id}">Arrastra tu captura de pantalla aquí o haz clic para buscar</p>
                <input type="file" id="file-1-${block.id}" accept="image/*">
            </div>
            <div class="image-preview-container hidden" id="preview-container-1-${block.id}">
                <img id="preview-1-${block.id}" src="#" alt="Vista previa">
                <button class="btn-remove-preview" id="btn-remove-1-${block.id}">Quitar</button>
            </div>
        `;
    } 
    else if (block.type === 'double_images') {
        content.innerHTML = `
            <div class="double-upload-grid">
                <div class="upload-column">
                    <div class="image-upload-zone" id="zone-1-${block.id}">
                        <span class="upload-icon">🖼️</span>
                        <p id="label-1-${block.id}">Imagen Izquierda</p>
                        <input type="file" id="file-1-${block.id}" accept="image/*">
                    </div>
                    <div class="image-preview-container hidden" id="preview-container-1-${block.id}">
                        <img id="preview-1-${block.id}" src="#" alt="Vista previa">
                        <button class="btn-remove-preview" id="btn-remove-1-${block.id}">Quitar</button>
                    </div>
                </div>
                <div class="upload-column">
                    <div class="image-upload-zone" id="zone-2-${block.id}">
                        <span class="upload-icon">🖼️</span>
                        <p id="label-2-${block.id}">Imagen Derecha</p>
                        <input type="file" id="file-2-${block.id}" accept="image/*">
                    </div>
                    <div class="image-preview-container hidden" id="preview-container-2-${block.id}">
                        <img id="preview-2-${block.id}" src="#" alt="Vista previa">
                        <button class="btn-remove-preview" id="btn-remove-2-${block.id}">Quitar</button>
                    </div>
                </div>
            </div>
        `;
    }

    card.appendChild(content);

    // If card already has loaded files, update preview immediately
    setTimeout(() => {
        if (block.file1) displayImagePreview(block.id, 1, block.file1);
        if (block.file2) displayImagePreview(block.id, 2, block.file2);
    }, 0);

    return card;
}

// Translates block type for badges
function translateType(type) {
    switch(type) {
        case 'title': return 'Título';
        case 'subtitle': return 'Subtítulo';
        case 'text': return 'Texto';
        case 'image': return 'Imagen Simple';
        case 'double_images': return 'Doble Imagen';
        default: return type;
    }
}

// Setup Drag & Drop files logic
function setupImageDragAndDrop(blockId) {
    const block = blocks.find(b => b.id === blockId);
    if (!block) return;

    setupColumnDragAndDrop(blockId, 1);
    if (block.type === 'double_images') {
        setupColumnDragAndDrop(blockId, 2);
    }
}

function setupColumnDragAndDrop(blockId, fileIndex) {
    const zone = document.getElementById(`zone-${fileIndex}-${blockId}`);
    const input = document.getElementById(`file-${fileIndex}-${blockId}`);
    if (!zone || !input) return;

    // Trigger click on click input file
    zone.addEventListener('click', () => input.click());

    // File change handler
    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(blockId, fileIndex, e.target.files[0]);
        }
    });

    // Drag-over styling
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleSelectedFile(blockId, fileIndex, e.dataTransfer.files[0]);
        }
    });
}

// Handles files selection and preview rendering
function handleSelectedFile(blockId, fileIndex, file) {
    if (!file.type.startsWith('image/')) {
        showToast('El archivo seleccionado debe ser una imagen.', 'error');
        return;
    }

    const block = blocks.find(b => b.id === blockId);
    if (!block) return;

    if (fileIndex === 1) {
        block.file1 = file;
        block.fileName1 = file.name;
    } else {
        block.file2 = file;
        block.fileName2 = file.name;
    }

    displayImagePreview(blockId, fileIndex, file);
}

// Render image preview
function displayImagePreview(blockId, fileIndex, file) {
    const zone = document.getElementById(`zone-${fileIndex}-${blockId}`);
    const previewContainer = document.getElementById(`preview-container-${fileIndex}-${blockId}`);
    const imgEl = document.getElementById(`preview-${fileIndex}-${blockId}`);
    const btnRemove = document.getElementById(`btn-remove-${fileIndex}-${blockId}`);

    if (!zone || !previewContainer || !imgEl || !btnRemove) return;

    // Set src to object URL
    imgEl.src = URL.createObjectURL(file);
    
    // Toggle displays
    zone.classList.add('hidden');
    previewContainer.classList.remove('hidden');

    // Remove file listener
    btnRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        
        const block = blocks.find(b => b.id === blockId);
        if (block) {
            if (fileIndex === 1) {
                block.file1 = null;
                block.fileName1 = '';
            } else {
                block.file2 = null;
                block.fileName2 = '';
            }
        }

        // Toggle back display
        previewContainer.classList.add('hidden');
        zone.classList.remove('hidden');
        imgEl.src = '#';
        
        // Reset input file value
        const input = document.getElementById(`file-${fileIndex}-${blockId}`);
        if (input) input.value = '';
    });
}

// Pre-fill samples to make the GUI visual on first load
function seedSampleData() {
    addBlock('title');
    addBlock('text');
    addBlock('subtitle');
    addBlock('image');

    // Update text content of seeded blocks
    setTimeout(() => {
        if (blocks[0]) blocks[0].text = "Análisis e Informe de Inicialización de Sistemas";
        if (blocks[1]) blocks[1].text = "Este reporte visual muestra cómo se organiza el documento e introduce imágenes largas de código middleware.";
        if (blocks[2]) blocks[2].text = "1. Estructura de Control y Ruteador Principal";
        renderBlocks();
    }, 100);
}

// Generate PDF via API POST request
async function generatePDF() {
    saveAllInputsToState();

    if (blocks.length === 0) {
        showToast('Debes agregar al menos un elemento al reporte.', 'error');
        return;
    }

    // Check images
    for (let block of blocks) {
        if (block.type === 'image' && !block.file1) {
            showToast('Por favor, carga una imagen para el bloque de Imagen Simple.', 'error');
            return;
        }
        if (block.type === 'double_images' && (!block.file1 || !block.file2)) {
            showToast('Por favor, carga ambas imágenes para el bloque de Doble Imagen.', 'error');
            return;
        }
    }

    // Toggle loading states
    const btnText = btnGenerate.querySelector('span');
    const spinner = btnGenerate.querySelector('.spinner');
    btnGenerate.disabled = true;
    spinner.classList.remove('hidden');
    btnText.textContent = "Procesando...";

    try {
        const formData = new FormData();
        
        // Build config schema
        const config = [];
        blocks.forEach(block => {
            const item = { type: block.type };
            
            if (block.type === 'title' || block.type === 'subtitle' || block.type === 'text') {
                item.text = block.text;
            } 
            else if (block.type === 'image') {
                const fileField = `file_1_${block.id}`;
                item.file_id = fileField;
                formData.append(fileField, block.file1);
            } 
            else if (block.type === 'double_images') {
                const fileField1 = `file_1_${block.id}`;
                const fileField2 = `file_2_${block.id}`;
                item.file_id1 = fileField1;
                item.file_id2 = fileField2;
                formData.append(fileField1, block.file1);
                formData.append(fileField2, block.file2);
            }
            
            config.push(item);
        });

        formData.append('config', JSON.stringify(config));

        // Append layout details
        const filename = document.getElementById('doc-filename').value || 'reporte.pdf';
        const pagesize = document.getElementById('doc-pagesize').value;
        const margins = parseFloat(document.getElementById('doc-margins').value) || 54.0;
        const minSplit = parseInt(document.getElementById('doc-min-split').value) || 100;

        formData.append('filename', filename);
        formData.append('page_size', pagesize);
        formData.append('min_split_height', minSplit);
        formData.append('margin_left', margins);
        formData.append('margin_right', margins);
        formData.append('margin_top', margins);
        formData.append('margin_bottom', margins);

        // Fetch API request
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.message || 'Error al generar el documento.');
        }

        // Receive binary response stream
        const blob = await response.blob();
        
        // Trigger browser download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showToast('¡PDF generado e iniciado para descarga con éxito!', 'success');

    } catch (err) {
        console.error(err);
        showToast(err.message || 'Hubo un error al procesar el PDF.', 'error');
    } finally {
        // Restore buttons state
        btnGenerate.disabled = false;
        spinner.classList.add('hidden');
        btnText.textContent = "Generar PDF";
    }
}
