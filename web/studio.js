document.addEventListener('DOMContentLoaded', () => {
    // --- Elements: Tabs & Layout ---
    const body = document.body;
    const tabDocx = document.getElementById('tab-docx');
    const tabPdf = document.getElementById('tab-pdf');
    const paneDocx = document.getElementById('pane-docx');
    const panePdf = document.getElementById('pane-pdf');
    const systemStatus = document.getElementById('system-status');

    // --- Elements: Exam Studio ---
    const qDrop = document.getElementById('q-dropzone');
    const qInput = document.getElementById('q-input');
    const qStatus = document.getElementById('q-status');
    const aDrop = document.getElementById('a-dropzone');
    const aInput = document.getElementById('a-input');
    const aStatus = document.getElementById('a-status');
    const examTitleInput = document.getElementById('exam-title');
    const paperFormatSelect = document.getElementById('paper-format');
    const execDocxBtn = document.getElementById('exec-docx');

    // --- Elements: PDF Toolbox ---
    const pdfDrop = document.getElementById('pdf-dropzone');
    const pdfInput = document.getElementById('pdf-input');
    const pdfStatusDisplay = document.getElementById('pdf-status');
    const pdfModeSelect = document.getElementById('pdf-mode');
    const pdfValLabel = document.getElementById('pdf-val-label');
    const pdfValInput = document.getElementById('pdf-value');
    const execPdfBtn = document.getElementById('exec-pdf');

    // --- Elements: Shared ---
    const viewerFrame = document.getElementById('viewer-frame');
    const viewerControls = document.getElementById('viewer-controls');
    const archiveList = document.getElementById('archive-list');
    const toast = document.getElementById('toast');

    let fileQ = null;
    let fileA = null;
    let filePDF = null;

    // --- Tab Logic ---
    tabDocx.onclick = () => {
        tabDocx.className = 'tab-btn active';
        tabPdf.className = 'tab-btn';
        paneDocx.classList.remove('hidden');
        panePdf.classList.add('hidden');
        body.setAttribute('data-theme', 'docx');
    };

    tabPdf.onclick = () => {
        tabPdf.className = 'tab-btn active';
        tabDocx.className = 'tab-btn';
        panePdf.classList.remove('hidden');
        paneDocx.classList.add('hidden');
        body.setAttribute('data-theme', 'pdf');
        refreshArchive();
    };

    // --- Interaction: Exams ---
    qDrop.onclick = () => qInput.click();
    qInput.onchange = (e) => {
        fileQ = e.target.files[0];
        if (fileQ) {
            qStatus.textContent = `📄 ${fileQ.name}`;
            qStatus.style.display = 'block';
            execDocxBtn.disabled = false;
        }
    };

    aDrop.onclick = () => aInput.click();
    aInput.onchange = (e) => {
        fileA = e.target.files[0];
        if (fileA) {
            aStatus.textContent = `🔑 KEY: ${fileA.name}`;
            aStatus.style.display = 'block';
        }
    };

    // --- Interaction: PDF ---
    pdfDrop.onclick = () => pdfInput.click();
    pdfInput.onchange = (e) => {
        filePDF = e.target.files[0];
        if (filePDF) {
            pdfStatusDisplay.textContent = `📄 ${filePDF.name}`;
            pdfStatusDisplay.style.display = 'block';
            execPdfBtn.disabled = false;
        }
    };

    pdfModeSelect.onchange = () => {
        if (pdfModeSelect.value === 'split') {
            pdfValLabel.textContent = 'Chunk Size (Pages)';
            pdfValInput.value = 50;
        } else {
            pdfValLabel.textContent = 'Compression Quality (1-100)';
            pdfValInput.value = 60;
        }
    };

    // --- Logic: Exec Exam ---
    execDocxBtn.onclick = async () => {
        if (!fileQ) return;
        execDocxBtn.disabled = true;
        updateStatus("EXAM PIPELINE STARTED", "cyan");
        updateToast("Uploading Exam Assets...", true);

        try {
            const formData = new FormData();
            formData.append('question_doc', fileQ);
            if (fileA) formData.append('answer_doc', fileA);

            const upResp = await fetch('/api/upload', { method: 'POST', body: formData });
            const upData = await upResp.json();
            if (!upData.success) throw new Error(upData.error);

            updateToast("Extracting Content & Parsing...", true);
            const procData = new FormData();
            procData.append('q_path', upData.q_path);
            if (upData.a_path) procData.append('a_path', upData.a_path);
            procData.append('title', examTitleInput.value || upData.original_name);

            const procResp = await fetch('/api/process', { method: 'POST', body: procData });
            const pData = await procResp.json();
            if (!pData.success) throw new Error(pData.error);

            updateToast("Pipeline Succeeded!", false);
            updateStatus("PREVIEW READY", "cyan");
            
            // Automatic Preview via dedicated renderer
            const timestamp = new Date().getTime();
            viewerFrame.src = `web/viewer.html?file=${pData.preview_file}&lite=true&t=${timestamp}`;
            
            // Show Finalize Controls
            viewerControls.innerHTML = `
                <div style="display: flex; gap: 0.5rem; align-items: center">
                    <button onclick="finalize('${pData.preview_file}')" class="btn-execute" style="margin: 0; padding: 0.4rem 0.8rem; font-size: 0.7rem; background: rgba(6, 182, 212, 0.2); border-color: #06b6d4; color: #06b6d4;">
                        FINALIZE STANDARD
                    </button>
                    <button onclick="finalizeLegacy('${pData.preview_file}')" class="btn-execute" style="margin: 0; padding: 0.4rem 0.8rem; font-size: 0.7rem; background: rgba(245, 158, 11, 0.2); border-color: #f59e0b; color: #f59e0b;">
                        <i class="fa-solid fa-graduation-cap"></i> EXPORT LEGACY (EXAM)
                    </button>
                </div>
            `;
            refreshArchive();
        } catch (err) {
            updateStatus("PIPELINE ERROR", "#ef4444");
            updateToast(`ERROR: ${err.message}`, false);
        } finally {
            execDocxBtn.disabled = false;
        }
    };

    // --- Logic: Exec PDF ---
    execPdfBtn.onclick = async () => {
        if (!filePDF) return;
        execPdfBtn.disabled = true;
        updateStatus("PDF OPTIMIZATION BUSY", "indigo");
        updateToast(`Running PDF ${pdfModeSelect.value}...`, true);

        try {
            const formData = new FormData();
            formData.append('pdf_file', filePDF);
            formData.append('mode', pdfModeSelect.value);
            formData.append('value', pdfValInput.value);

            const resp = await fetch('/api/pdf/process', { method: 'POST', body: formData });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            updateToast(`Success: ${data.message}`, false);
            updateStatus("PDF COMPLETED", "indigo");
            
            // Auto Download
            const a = document.createElement('a');
            a.href = `/output/${data.download_file}`;
            a.download = data.download_file;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            refreshArchive();
        } catch (err) {
            updateStatus("PDF ERROR", "#ef4444");
            updateToast(`ERROR: ${err.message}`, false);
        } finally {
            execPdfBtn.disabled = false;
        }
    };

    // --- Helpers ---
    function updateStatus(msg, color) {
        systemStatus.textContent = msg.toUpperCase();
        systemStatus.style.color = color;
    }

    function updateToast(msg, loading) {
        toast.innerHTML = `<div style="display: flex; align-items: center; gap: 0.75rem; color: #fff; font-size: 0.85rem">
            ${loading ? '<i class="fa-solid fa-spinner fa-spin"></i>' : '<i class="fa-solid fa-circle-check" style="color: #10b981"></i>'}
            <span>${msg}</span>
        </div>`;
        toast.classList.remove('hidden');
        if (!loading) setTimeout(() => toast.classList.add('hidden'), 4000);
    }

    async function refreshArchive() {
        try {
            const resp = await fetch('/api/manifest');
            const data = await resp.json();
            archiveList.innerHTML = data.reverse().map(item => {
                const isJson = item.filename.endsWith('.json');
                const clickAction = isJson 
                    ? `window.open('web/viewer.html?file=${item.filename}&lite=true', '_blank')`
                    : `window.open('output/${item.filename}', '_blank')`;
                
                return `
                    <div class="archive-item" onclick="${clickAction}">
                        <i class="fa-solid ${isJson ? 'fa-file-code cyan' : 'fa-file-pdf indigo'}"></i>
                        <div style="flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis">
                            <div style="font-weight: 800">${item.title}</div>
                            <div style="font-size: 0.65rem; color: var(--text-muted)">${new Date(item.timestamp).toLocaleTimeString()}</div>
                        </div>
                    </div>
                `;
            }).join('');
        } catch (e) {}
    }

    window.finalizeLegacy = async (filename, forcedPaperType) => {
        updateToast("Generating Legacy Export (Math Rendering)...", true);
        try {
            const formData = new FormData();
            formData.append('filename', filename);
            const paperType = forcedPaperType || (paperFormatSelect ? paperFormatSelect.value : 'normal');
            formData.append('paper_type', paperType);
            const resp = await fetch('/api/finalize/legacy', { method: 'POST', body: formData });
            const data = await resp.json();
            if (data.success) {
                updateToast("Legacy Export Complete!", false);
                
                // Trigger Download
                const a = document.createElement('a');
                a.href = `/output/${data.final_file}`;
                a.download = data.final_file;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                refreshArchive();
            } else {
                throw new Error(data.error);
            }
        } catch (e) { 
            updateToast("Export Failed", false);
            alert("Legacy Transformation Error: " + e.message); 
        }
    };

    window.finalize = async (filename) => {
        updateToast("Exporting Final JSON...", true);
        try {
            const formData = new FormData();
            formData.append('filename', filename);
            const resp = await fetch('/api/finalize', { method: 'POST', body: formData });
            const data = await resp.json();
            if (data.success) {
                updateToast("JSON Saved Successfully!", false);
                
                // Trigger Proper Download
                const a = document.createElement('a');
                a.href = `/output/${data.final_file}`;
                a.download = data.final_file;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                refreshArchive();
            }
        } catch (e) { alert(e.message); }
    };

    refreshArchive();
});
