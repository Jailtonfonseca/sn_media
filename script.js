// TODO: JavaScript code will go here

const STORAGE_KEYS = {
    settings: 'bloggerStudioSettings',
    savedClipMetrics: 'savedClipMetrics',
    userNotes: 'bloggerStudioUserNotes'
};

        function showSection(sectionId) {
         // Get all sections
         const sections = document.querySelectorAll('main section');
         // Hide all sections
         sections.forEach(section => {
             section.classList.remove('active-section');
             section.classList.add('hidden-section'); // Ensure it's hidden
             section.style.display = ''; // Remove inline style if any
         });
         // Show the target section
         const activeSection = document.getElementById(sectionId);
         if (activeSection) {
             activeSection.classList.remove('hidden-section');
             activeSection.classList.add('active-section');
         } else {
             console.error("Section with ID '" + sectionId + "' not found.");
         }
     }

    // The DOMContentLoaded listener below will call showSection('warnings'),
    // which will now correctly apply 'active-section' to the warnings section
    // and 'hidden-section' to others.

    const settingsForm = document.getElementById('settingsForm');
    const settingsMessage = document.getElementById('settingsMessage');

    function saveSettings() {
        const settings = {
            apiKey: document.getElementById('apiKey').value.trim(),
            defaultDuration: parseInt(document.getElementById('defaultDuration').value, 10),
            outputFormat: document.getElementById('outputFormat').value,
            addFade: document.getElementById('addFade').checked,
            audioOption: document.querySelector('input[name="audioOption"]:checked').value
        };

        if (isNaN(settings.defaultDuration) || settings.defaultDuration <= 0) {
            settingsMessage.textContent = 'Erro: Duração padrão inválida.';
            settingsMessage.style.color = 'red';
            return;
        }

        localStorage.setItem(STORAGE_KEYS.settings, JSON.stringify(settings));
        settingsMessage.textContent = 'Configurações salvas com sucesso!';
        settingsMessage.style.color = 'green';
        setTimeout(() => { settingsMessage.textContent = ''; }, 3000);
        console.log('Settings saved:', settings);
    }

    function loadSettings() {
        const savedSettings = localStorage.getItem(STORAGE_KEYS.settings);
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            document.getElementById('apiKey').value = settings.apiKey || '';
            document.getElementById('defaultDuration').value = settings.defaultDuration || 30;
            document.getElementById('outputFormat').value = settings.outputFormat || '9:16';
            document.getElementById('addFade').checked = typeof settings.addFade === 'boolean' ? settings.addFade : true;

            const audioOptionElement = document.querySelector(`input[name="audioOption"][value="${settings.audioOption || 'keep'}"]`);
            if (audioOptionElement) {
                audioOptionElement.checked = true;
            } else {
                // Default to 'keep' if saved value is invalid
                document.getElementById('audioOriginal').checked = true;
            }
            console.log('Settings loaded:', settings);
        } else {
            // Default values if nothing is saved (redundant if form has defaults, but good practice)
            document.getElementById('defaultDuration').value = 30;
            document.getElementById('outputFormat').value = '9:16';
            document.getElementById('addFade').checked = true;
            document.getElementById('audioOriginal').checked = true;
            console.log('No settings found in localStorage, using defaults.');
        }
    }

    // Modify the DOMContentLoaded listener to also load settings
    // --- Start: Variables related to FFmpeg ---
    const { createFFmpeg, fetchFile } = FFmpeg; // Destructure from FFmpeg global
    let ffmpeg; // Will hold the FFmpeg instance
    let ffmpegLoaded = false;
    const ffmpegLogEl = document.getElementById('ffmpegLog'); // Renamed to avoid conflict with function name
    const loadFFmpegButton = document.getElementById('loadFFmpegButton');
    // --- End: Variables related to FFmpeg ---

    const videoUpload = document.getElementById('videoUpload');
    const videoPlayer = document.getElementById('videoPlayer');
    const videoPreviewContainer = document.getElementById('videoPreviewContainer');
    let uploadedFile = null; // To store the File object

    // --- Start: FFmpeg Initialization ---
    async function loadFFmpeg() {
        if (!ffmpeg) {
            ffmpegLogEl.textContent = 'Carregando FFmpeg-core.js... (pode levar alguns instantes)';
            loadFFmpegButton.disabled = true;
            try {
                ffmpeg = createFFmpeg({
                    log: true, // Enables detailed logging in the console
                    corePath: 'https://unpkg.com/@ffmpeg/core@0.11.0/dist/ffmpeg-core.js',
                });
                await ffmpeg.load();
                ffmpegLoaded = true;
                ffmpegLogEl.textContent = 'FFmpeg carregado com sucesso!';
                loadFFmpegButton.style.display = 'none'; // Hide button after loading
                console.log('FFmpeg loaded successfully');
            } catch (error) {
                ffmpegLogEl.textContent = 'Erro ao carregar FFmpeg: ' + error;
                console.error('FFmpeg loading error:', error);
                loadFFmpegButton.disabled = false; // Re-enable button on error
                ffmpegLoaded = false;
            }
        } else {
            ffmpegLogEl.textContent = 'FFmpeg já está carregado.';
            loadFFmpegButton.style.display = 'none';
        }
    }
    // --- End: FFmpeg Initialization ---

    videoUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            uploadedFile = file; // Store the file object
            const fileURL = URL.createObjectURL(file);
            videoPlayer.src = fileURL;
            videoPreviewContainer.style.display = 'block';
            console.log('Video file selected:', uploadedFile.name);

            if (!ffmpegLoaded) {
                ffmpegLogEl.textContent = 'Vídeo carregado. Clique em "Carregar FFmpeg" se ainda não o fez.';
            }
        } else {
            videoPreviewContainer.style.display = 'none';
            videoPlayer.src = '';
            uploadedFile = null;
        }
    });

    async function fetchVideoMetadata() {
        const youtubeUrl = document.getElementById('youtubeUrl').value;
        const videoMetadataDisplay = document.getElementById('videoMetadataDisplay');
        const videoTitleEl = document.getElementById('videoTitle'); // Renamed to avoid conflict
        const videoDescriptionEl = document.getElementById('videoDescription'); // Renamed to avoid conflict
        const chaptersListEl = document.getElementById('chaptersList'); // Renamed to avoid conflict

        videoTitleEl.textContent = '-';
        videoDescriptionEl.textContent = '-';
        chaptersListEl.innerHTML = ''; // Clear previous chapters

        if (!youtubeUrl.trim()) {
            alert('Por favor, insira uma URL do YouTube.');
            videoMetadataDisplay.style.display = 'none';
            return;
        }

        const savedSettings = JSON.parse(localStorage.getItem('bloggerStudioSettings'));
        const apiKey = savedSettings ? savedSettings.apiKey : '';

        if (!apiKey) {
            alert('Chave da API do YouTube não encontrada nas Configurações. Não é possível buscar metadados.');
            videoMetadataDisplay.style.display = 'none';
            return;
        }

        let videoId;
        try {
            const url = new URL(youtubeUrl);
            if (url.hostname === 'youtu.be') {
                videoId = url.pathname.substring(1);
            } else if (url.hostname === 'www.youtube.com' || url.hostname === 'youtube.com') {
                videoId = url.searchParams.get('v');
            }
            if (!videoId) throw new Error('Invalid YouTube URL');
        } catch (e) {
            alert('URL do YouTube inválida.');
            videoMetadataDisplay.style.display = 'none';
            return;
        }

        videoMetadataDisplay.style.display = 'block';
        videoTitleEl.textContent = 'Buscando...';
        videoDescriptionEl.textContent = 'Buscando...';
        chaptersListEl.innerHTML = '<li>Buscando capítulos...</li>';

        const apiUrl = `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id=${videoId}&key=${apiKey}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Erro da API do YouTube: ${errorData.error.message} (Code: ${response.status})`);
            }
            const data = await response.json();

            if (data.items && data.items.length > 0) {
                const item = data.items[0];
                videoTitleEl.textContent = item.snippet.title || 'Não encontrado';
                videoDescriptionEl.textContent = item.snippet.description.substring(0, 300) + '...' || 'Não encontrada';

                const foundChapters = parseChaptersFromDescription(item.snippet.description);
                if (foundChapters.length > 0) {
                    chaptersListEl.innerHTML = ''; // Clear "Buscando..."
                    foundChapters.forEach(chapter => {
                        const li = document.createElement('li');
                        // const chapterStartTimeSeconds = timeToSeconds(chapter.time); // timeToSeconds is defined later
                        li.textContent = `${chapter.time} - ${chapter.title}`;
                        li.title = `Clique para usar este capítulo como base para um segmento. Início: ${chapter.time}.`;
                        // li.style.cursor = 'pointer'; // Already in CSS
                        li.onclick = () => {
                            segmentStartTimeInput.value = chapter.time;
                            const nextChapterIndex = foundChapters.indexOf(chapter) + 1;
                            if (nextChapterIndex < foundChapters.length) {
                                segmentEndTimeInput.value = foundChapters[nextChapterIndex].time;
                            } else if (videoPlayer.duration && !isNaN(videoPlayer.duration)) {
                                 segmentEndTimeInput.value = secondsToTime(videoPlayer.duration); // secondsToTime defined later
                            } else {
                                segmentEndTimeInput.value = '';
                            }
                            segmentTitleInput.value = chapter.title;
                            segmentStartTimeInput.focus();
                            console.log('Chapter clicked to populate segment fields:', chapter);
                            // Clear any previous error messages from manual segment addition
                            if(typeof segmentErrorDisplay !== 'undefined') segmentErrorDisplay.textContent = '';
                        };
                        chaptersListEl.appendChild(li);
                    });
                } else {
                    chaptersListEl.innerHTML = '<li>Nenhum capítulo parseável encontrado na descrição.</li>';
                }

            } else {
                videoTitleEl.textContent = 'Vídeo não encontrado.';
                videoDescriptionEl.textContent = '';
                chaptersListEl.innerHTML = '<li>Informações não disponíveis.</li>';
            }
        } catch (error) {
            console.error('Erro ao buscar metadados do YouTube:', error);
            alert('Erro ao buscar metadados: ' + error.message);
            videoTitleEl.textContent = 'Erro ao buscar.';
            videoDescriptionEl.textContent = error.message;
            chaptersListEl.innerHTML = '<li>Erro ao buscar capítulos.</li>';
            videoMetadataDisplay.style.display = 'block';
        }
    }

    function parseChaptersFromDescription(description) {
        const chapters = [];
        if (!description) return chapters;
        const chapterRegex = /(\d{1,2}:?\d{1,2}:?\d{2})\s+(.+)/g;
        let match;
        while ((match = chapterRegex.exec(description)) !== null) {
            chapters.push({ time: match[1], title: match[2].trim() });
        }
        return chapters;
    }

    document.addEventListener('DOMContentLoaded', () => {
        showSection('warnings');
        loadSettings();
        // Initialize variables that depend on DOM elements being present
        // Note: ffmpegLogEl, loadFFmpegButton, videoUpload, videoPlayer, videoPreviewContainer are already initialized globally
        // as they are obtained by getElementById. This is fine.
        renderCuttingQueue(); // Initialize the queue display
    });

    // --- Start: Variables related to Segment Management ---
    const segmentStartTimeInput = document.getElementById('segmentStartTime');
    const segmentEndTimeInput = document.getElementById('segmentEndTime');
    const segmentTitleInput = document.getElementById('segmentTitle');
    const segmentErrorDisplay = document.getElementById('segmentError');
    const cuttingQueueList = document.getElementById('cuttingQueueList');
    const startProcessingButton = document.getElementById('startProcessingButton');
    const queueStatusMessage = document.getElementById('queueStatusMessage');

    let segmentsToCut = []; // Array to hold segment objects {id, startTimeSeconds, endTimeSeconds, title, status}
    let nextSegmentId = 0; // For unique IDs for segments
    // --- End: Variables related to Segment Management ---

    // --- Start: Time Conversion Utilities ---
    // Helper function to convert HH:MM:SS or MM:SS or SS to seconds
    function timeToSeconds(timeStr) {
        if (typeof timeStr === 'number') return timeStr;
        if (!timeStr || typeof timeStr !== 'string') return NaN;

        const parts = timeStr.split(':').map(Number);
        let seconds = 0;
        if (parts.length === 3) { // HH:MM:SS
            if (isNaN(parts[0]) || isNaN(parts[1]) || isNaN(parts[2])) return NaN;
            seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
        } else if (parts.length === 2) { // MM:SS
            if (isNaN(parts[0]) || isNaN(parts[1])) return NaN;
            seconds = parts[0] * 60 + parts[1];
        } else if (parts.length === 1) { // SS
            if (isNaN(parts[0])) return NaN;
            seconds = parts[0];
        } else {
            return NaN;
        }
        return seconds >= 0 ? seconds : NaN;
    }

    // Helper function to convert seconds to HH:MM:SS format
    function secondsToTime(totalSeconds) {
        if (isNaN(totalSeconds) || totalSeconds < 0) return '00:00:00';
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = Math.floor(totalSeconds % 60);
        return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    // --- End: Time Conversion Utilities ---

    // --- Start: Segment Management Functions ---
    function addManualSegmentToQueue() {
        segmentErrorDisplay.textContent = ''; // Clear previous errors
        const startTimeRaw = segmentStartTimeInput.value;
        const endTimeRaw = segmentEndTimeInput.value;
        const title = segmentTitleInput.value.trim() || `Clipe ${segmentsToCut.length + 1}`;

        const startTime = timeToSeconds(startTimeRaw);
        const endTime = timeToSeconds(endTimeRaw);

        if (isNaN(startTime)) {
            segmentErrorDisplay.textContent = 'Tempo de início inválido. Use HH:MM:SS ou segundos.';
            return;
        }
        if (isNaN(endTime)) {
            segmentErrorDisplay.textContent = 'Tempo de fim inválido. Use HH:MM:SS ou segundos.';
            return;
        }
        if (endTime <= startTime) {
            segmentErrorDisplay.textContent = 'O tempo de fim deve ser maior que o tempo de início.';
            return;
        }
        if (uploadedFile && videoPlayer.duration && !isNaN(videoPlayer.duration) && endTime > videoPlayer.duration) {
            segmentErrorDisplay.textContent = `O tempo de fim (${secondsToTime(endTime)}) excede a duração do vídeo (${secondsToTime(videoPlayer.duration)}).`;
            return;
        }

        addSegmentToQueue(startTime, endTime, title, 'manual');
        segmentStartTimeInput.value = '';
        segmentEndTimeInput.value = '';
        segmentTitleInput.value = '';
    }

    function addSegmentToQueue(startTime, endTime, title, source = 'manual') {
        const segment = {
            id: nextSegmentId++,
            startTimeSeconds: startTime,
            endTimeSeconds: endTime,
            title: title,
            source: source,
            status: 'Pendente' // Possible statuses: Pendente, Processando, Concluído, Erro
        };
        segmentsToCut.push(segment);
        renderCuttingQueue();
        console.log('Segment added to queue:', segment);
    }

    function removeSegmentFromQueue(segmentId) {
        segmentsToCut = segmentsToCut.filter(s => s.id !== segmentId);
        renderCuttingQueue();
    }

    function renderCuttingQueue() {
        cuttingQueueList.innerHTML = ''; // Clear current list
        if (segmentsToCut.length === 0) {
            queueStatusMessage.textContent = 'Nenhum segmento na fila.';
            startProcessingButton.style.display = 'none';
            return;
        }

        queueStatusMessage.textContent = '';
        segmentsToCut.forEach(segment => {
            const li = document.createElement('li');
            li.innerHTML = `
                <strong>${segment.title}</strong> (De: ${secondsToTime(segment.startTimeSeconds)} Para: ${secondsToTime(segment.endTimeSeconds)}) - <em>Status: ${segment.status}</em>
                <button onclick="removeSegmentFromQueue(${segment.id})" style="margin-left: 10px; background-color: #d9534f; color:white; border:none; padding: 5px 10px; border-radius:3px; cursor:pointer;">Remover</button>
            `;
            // TODO: Add edit button later if needed
            cuttingQueueList.appendChild(li);
        });

        startProcessingButton.style.display = 'block';
        startProcessingButton.disabled = false; // Ensure it's enabled if there are items
    }
    // --- End: Segment Management Functions ---

    // (Keep existing variables: ffmpeg, ffmpegLoaded, uploadedFile, segmentsToCut, etc.)
    // (Keep existing time conversion utilities)

    // --- Start: Processed Clips Management ---
    let processedClips = []; // Array to store { id, title, blob, originalSegment, downloadUrl }
    let nextProcessedClipId = 0;
    // --- End: Processed Clips Management ---

    // --- Start: FFmpeg Progress Handling ---
    // The ffmpegProgressDisplay element is created and added to DOM in DOMContentLoaded
    // The progress listener is attached in the updated loadFFmpeg function.
    // --- End: FFmpeg Progress Handling ---


    // --- Start: FFmpeg Core Logic ---
    async function executeFFmpegCut(segment) {
        if (!ffmpegLoaded || !ffmpeg) {
            throw new Error("FFmpeg não está carregado.");
        }
        if (!uploadedFile) {
            throw new Error("Nenhum arquivo de vídeo carregado.");
        }

        const inputFileName = `input_${segment.id}_${Date.now()}.mp4`; // Unique input name
        const outputFileName = `output_${segment.id}_${Date.now()}.mp4`; // Unique output name
        let command = [];
        const settings = JSON.parse(localStorage.getItem('bloggerStudioSettings')) || {};
        const addFade = settings.addFade !== undefined ? settings.addFade : true;
        const audioOption = settings.audioOption || 'keep';
        const outputFormat = settings.outputFormat || '9:16';
        const clipDuration = segment.endTimeSeconds - segment.startTimeSeconds;
        const ffmpegProgressDisplay = document.getElementById('ffmpegProgressDisplay');

        try {
            ffmpegLogEl.textContent = `Preparando para processar: ${segment.title}`;
            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Escrevendo arquivo de entrada para FFmpeg FS...';

            ffmpeg.FS('writeFile', inputFileName, await fetchFile(uploadedFile));
            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Arquivo de entrada escrito.';

            // Base command
            command.push('-ss', String(segment.startTimeSeconds));
            command.push('-to', String(segment.endTimeSeconds));
            command.push('-i', inputFileName);

            // Video Filters
            let vfComplex = [];
            if (addFade && clipDuration > 1) { // Ensure fade duration isn't longer than clip
                const fadeDuration = Math.min(0.5, clipDuration / 2);
                vfComplex.push(`fade=t=in:st=0:d=${fadeDuration},fade=t=out:st=${clipDuration - fadeDuration}:d=${fadeDuration}`);
            }

            switch (outputFormat) {
                case '9:16': // Vertical
                    vfComplex.push("scale='if(gt(a,9/16),720,-2)':'if(gt(a,9/16),-2,1280)',crop=720:1280,setsar=1");
                    break;
                case '1:1': // Square
                    vfComplex.push("scale='if(gt(a,1),1080,-2)':'if(gt(a,1),-2,1080)',crop=1080:1080,setsar=1");
                    break;
                case '16:9': // Horizontal
                     vfComplex.push("scale='if(lt(a,16/9),1280,-2)':'if(lt(a,16/9),-2,720)',crop=1280:720,setsar=1");
                    break;
                case 'original':
                    // No scaling/padding
                    break;
            }

            if (vfComplex.length > 0) {
                command.push('-vf', vfComplex.join(','));
            }

            if (audioOption === 'remove') {
                command.push('-an');
            } else {
                command.push('-c:a', 'aac', '-b:a', '128k');
            }

            command.push('-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-movflags', '+faststart');
            command.push(outputFileName);

            console.log('Executing FFmpeg command for segment ' + segment.id + ':', command.join(' '));
            ffmpegLogEl.textContent = `Processando: ${segment.title} (Pode levar um tempo...)`;
            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Progresso do FFmpeg: 0%';

            await ffmpeg.run(...command);

            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Leitura do arquivo de saída...';
            const data = ffmpeg.FS('readFile', outputFileName);

            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Limpando arquivos do FFmpeg FS...';
            ffmpeg.FS('unlink', inputFileName);
            ffmpeg.FS('unlink', outputFileName);
            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = '';

            return new Blob([data.buffer], { type: 'video/mp4' });

        } catch (error) {
            console.error(`Erro ao processar segmento ${segment.id} (${segment.title}):`, error);
            ffmpegLogEl.textContent = `Erro em ${segment.title}: ${error.message.substring(0,100)}...`;
            if(ffmpegProgressDisplay) ffmpegProgressDisplay.textContent = 'Erro durante o processamento.';
            try {
                ffmpeg.FS('unlink', inputFileName); // Attempt cleanup
                ffmpeg.FS('unlink', outputFileName); // Attempt cleanup
            } catch (e) { /* ignore cleanup errors */ }
            throw error;
        }
    }

    async function processCuttingQueue() {
        if (!ffmpegLoaded) {
            alert("FFmpeg não está carregado. Por favor, clique em 'Carregar FFmpeg' primeiro na seção de Processamento de Vídeo.");
            queueStatusMessage.textContent = "FFmpeg não carregado.";
            return;
        }
        if (!uploadedFile) {
            alert("Nenhum arquivo de vídeo foi carregado. Por favor, faça upload de um vídeo primeiro.");
            queueStatusMessage.textContent = "Vídeo não carregado.";
            return;
        }
        const segmentsToProcess = segmentsToCut.filter(s => s.status === 'Pendente' || s.status === 'Erro');
        if (segmentsToProcess.length === 0) {
            alert("Nenhum segmento pendente ou com erro para processar.");
            queueStatusMessage.textContent = "Nenhum segmento para processar.";
            return;
        }

        startProcessingButton.disabled = true;
        queueStatusMessage.textContent = `Iniciando processamento de ${segmentsToProcess.length} segmento(s)...`;

        for (let i = 0; i < segmentsToProcess.length; i++) {
            const segment = segmentsToProcess[i];
            segment.status = 'Processando';
            renderCuttingQueue();
            queueStatusMessage.textContent = `Processando clipe ${i + 1} de ${segmentsToProcess.length}: "${segment.title}"...`;

            try {
                const videoBlob = await executeFFmpegCut(segment);
                segment.status = 'Concluído';
                // segment.blob = videoBlob; // Not needed on segment itself if directly put into processedClips

                const newClip = {
                    id: `clip_${nextProcessedClipId++}`,
                    title: segment.title,
                    blob: videoBlob,
                    originalSegmentId: segment.id,
                    timestamp: new Date().toISOString(),
                    downloadUrl: URL.createObjectURL(videoBlob),
                    platformsPosted: [],
                    metrics: { views: 0, likes: 0, comments: 0 },
                    postingNotes: "" // Initialize postingNotes
                };
                processedClips.push(newClip);
                console.log("Clip processed and added:", newClip.title, newClip.downloadUrl);

            } catch (error) {
                segment.status = 'Erro';
                console.error(`Falha ao processar segmento ${segment.id}: ${segment.title}`, error);
                queueStatusMessage.textContent = `Erro ao processar "${segment.title}". Verifique o console.`;
            }
            renderCuttingQueue();
        }

        queueStatusMessage.textContent = "Processamento da fila concluído.";
        startProcessingButton.disabled = false;

        if (processedClips.length > 0 && segmentsToProcess.some(s => s.status === 'Concluído')) {
            alert("Processamento concluído! Verifique a seção 'Clipes Gerados'.");
            showSection('generatedClips');
            if (typeof renderGeneratedClips === "function") {
                renderGeneratedClips();
            } else {
                console.warn("renderGeneratedClips function not yet defined.");
            }
        }
    }
    // --- End: FFmpeg Core Logic ---

    // --- Start: Update loadFFmpeg to attach progress listener ---
    async function loadFFmpeg() {
        if (ffmpegLoaded && ffmpeg) {
            ffmpegLogEl.textContent = 'FFmpeg já está carregado.';
            if(loadFFmpegButton) loadFFmpegButton.style.display = 'none';
            return;
        }
        if (!ffmpeg) {
             ffmpeg = createFFmpeg({
                log: true,
                corePath: 'https://unpkg.com/@ffmpeg/core@0.11.0/dist/ffmpeg-core.js',
             });
        }

        ffmpeg.setProgress(({ ratio }) => {
            const progressDisplay = document.getElementById('ffmpegProgressDisplay');
            if (progressDisplay) { // Check if element exists
                if (ratio >= 0 && ratio <= 1) {
                    const percentage = Math.round(ratio * 100);
                    progressDisplay.textContent = `Progresso do FFmpeg: ${percentage}%`;
                }
                if (ratio === 1) {
                     setTimeout(() => { progressDisplay.textContent = ''; }, 3000);
                }
            }
        });

        ffmpegLogEl.textContent = 'Carregando FFmpeg-core.js... (pode levar alguns instantes)';
        if(loadFFmpegButton) loadFFmpegButton.disabled = true;
        try {
            await ffmpeg.load();
            ffmpegLoaded = true;
            ffmpegLogEl.textContent = 'FFmpeg carregado com sucesso!';
            if(loadFFmpegButton) loadFFmpegButton.style.display = 'none';
            console.log('FFmpeg loaded successfully');
        } catch (error) {
            ffmpegLogEl.textContent = 'Erro ao carregar FFmpeg: ' + error;
            console.error('FFmpeg loading error:', error);
            if(loadFFmpegButton) loadFFmpegButton.disabled = false;
            ffmpegLoaded = false;
            ffmpeg = null;
        }
    }
    // --- End: Update loadFFmpeg ---

    // --- Start: DOMContentLoaded adjustments ---
    document.addEventListener('DOMContentLoaded', () => {
        showSection('warnings');
        loadSettings();
        renderCuttingQueue();

        const ffmpegStatusDiv = document.getElementById('ffmpegStatus');
        if (ffmpegStatusDiv && !document.getElementById('ffmpegProgressDisplay')) {
            const progressDisplayElement = document.createElement('div');
            progressDisplayElement.id = 'ffmpegProgressDisplay';
            progressDisplayElement.style.marginTop = '10px';
            ffmpegStatusDiv.appendChild(progressDisplayElement);
        }
    });
    // --- End: DOMContentLoaded adjustments ---

    // --- Start: Generated Clips Section Logic ---
    const clipsGallery = document.getElementById('clipsGallery');

    function getSavedClipsMetadata() {
        return JSON.parse(localStorage.getItem(STORAGE_KEYS.savedClipMetrics)) || [];
    }

    function persistAllClipsMetadata() {
        // This function is more of a utility if a global save is needed.
        // The current design uses saveClipInfoToStorage for individual saves.
        const allMetadata = getSavedClipsMetadata();
        processedClips.forEach(sessionClip => {
            const existingIndex = allMetadata.findIndex(m => m.id === sessionClip.id);
            // Create metadata object similar to saveClipInfoToStorage
            const metadataToSave = {
                id: sessionClip.id,
                title: sessionClip.title,
                originalVideoFile: uploadedFile ? uploadedFile.name : "Nome do arquivo não disponível",
                originalSegmentId: sessionClip.originalSegmentId,
                timestamp: sessionClip.timestamp,
                platformsPosted: sessionClip.platformsPosted || [],
                postLinks: sessionClip.postLinks || {},
                metrics: sessionClip.metrics || { views: 0, likes: 0, comments: 0 },
                postingNotes: sessionClip.postingNotes || "", // Add postingNotes
                startTimeSeconds: segmentsToCut.find(s => s.id === sessionClip.originalSegmentId)?.startTimeSeconds,
                endTimeSeconds: segmentsToCut.find(s => s.id === sessionClip.originalSegmentId)?.endTimeSeconds,
            };
            if (existingIndex > -1) {
                allMetadata[existingIndex] = metadataToSave;
            } else {
                allMetadata.push(metadataToSave);
            }
        });
        localStorage.setItem(STORAGE_KEYS.savedClipMetrics, JSON.stringify(allMetadata));
        console.log("All session clips metadata (potentially) persisted.");
    }

    function saveClipInfoToStorage(clipId) {
        const clip = processedClips.find(c => c.id === clipId);
        if (!clip) {
            console.error("Clip not found in current session to save info:", clipId);
            return;
        }

        const card = document.getElementById(`clipCard_${clipId}`);
        if (!card) {
            console.error("Clip card not found in DOM for clipId:", clipId);
            return;
        }

        const platforms = Array.from(card.querySelectorAll('input[name^="platform_"]:checked')).map(cb => cb.value);
        clip.platformsPosted = platforms;

        clip.postLinks = clip.postLinks || {};
        platforms.forEach(platform => {
            const linkInput = card.querySelector(`input[name="link_${platform}_${clipId}"]`);
            if (linkInput) clip.postLinks[platform] = linkInput.value.trim();
        });

        clip.metrics = {
            views: parseInt(card.querySelector(`input[name="views_${clipId}"]`).value, 10) || 0,
            likes: parseInt(card.querySelector(`input[name="likes_${clipId}"]`).value, 10) || 0,
            comments: parseInt(card.querySelector(`input[name="comments_${clipId}"]`).value, 10) || 0,
        };

        const postingNotes = card.querySelector(`textarea[name="notes_${clipId}"]`).value.trim();
        clip.postingNotes = postingNotes;

        let allMetadata = getSavedClipsMetadata();
        const existingIndex = allMetadata.findIndex(m => m.id === clipId);
        const metadataToSave = {
            id: clip.id,
            title: clip.title,
            originalVideoFile: uploadedFile ? uploadedFile.name : "Nome do arquivo não disponível",
            originalSegmentId: clip.originalSegmentId,
            timestamp: clip.timestamp,
            platformsPosted: clip.platformsPosted,
            postLinks: clip.postLinks,
            metrics: clip.metrics,
            postingNotes: clip.postingNotes, // Save postingNotes
            startTimeSeconds: segmentsToCut.find(s => s.id === clip.originalSegmentId)?.startTimeSeconds,
            endTimeSeconds: segmentsToCut.find(s => s.id === clip.originalSegmentId)?.endTimeSeconds,
        };

        if (existingIndex > -1) {
            allMetadata[existingIndex] = metadataToSave;
        } else {
            allMetadata.push(metadataToSave);
        }
        localStorage.setItem(STORAGE_KEYS.savedClipMetrics, JSON.stringify(allMetadata));

        alert(`Informações do clipe "${clip.title}" salvas!`);
        console.log("Clip info saved to localStorage:", metadataToSave);

        if (typeof renderMetricsAnalysis === "function") {
            renderMetricsAnalysis();
        }

        // Check if the generatedClips section is currently active and re-render it
        const generatedClipsSection = document.getElementById('generatedClips');
        // Check class instead of style.display as styles are class-driven now
        if (generatedClipsSection && generatedClipsSection.classList.contains('active-section')) {
            renderGeneratedClips();
        }
    }

    function removeClipFromSessionAndStorage(clipId) {
        const sessionIndex = processedClips.findIndex(c => c.id === clipId);
        if (sessionIndex > -1) {
            if (processedClips[sessionIndex].downloadUrl && processedClips[sessionIndex].downloadUrl.startsWith('blob:')) {
                URL.revokeObjectURL(processedClips[sessionIndex].downloadUrl);
            }
            processedClips.splice(sessionIndex, 1);
        }

        let allMetadata = getSavedClipsMetadata();
        allMetadata = allMetadata.filter(m => m.id !== clipId);
        localStorage.setItem(STORAGE_KEYS.savedClipMetrics, JSON.stringify(allMetadata));

        alert('Clipe removido da sessão e do histórico.');
        renderGeneratedClips();
        if (typeof renderMetricsAnalysis === "function") {
            renderMetricsAnalysis();
        }
    }

    function renderGeneratedClips() {
        if (!clipsGallery) {
            console.error("clipsGallery element not found in DOM.");
            return;
        }
        clipsGallery.innerHTML = '';
        if (processedClips.length === 0) {
            clipsGallery.innerHTML = '<p>Nenhum clipe foi gerado ou processado nesta sessão ainda. Vá para "Processamento de Vídeo" para criar clipes.</p>';
            return;
        }

        const platformOptions = [
            { value: 'YTShorts', label: 'YT Shorts' },
            { value: 'Reels', label: 'Reels (Insta)' },
            { value: 'TikTok', label: 'TikTok' },
            { value: 'Kwai', label: 'Kwai' },
            { value: 'Outra', label: 'Outra' }
        ];

        processedClips.forEach(clip => {
            const clipCard = document.createElement('div');
            clipCard.id = `clipCard_${clip.id}`;
            clipCard.className = 'clip-card';

            const savedMetadata = (getSavedClipsMetadata()).find(m => m.id === clip.id);
            const displayMetrics = savedMetadata ? savedMetadata.metrics : (clip.metrics || { views: 0, likes: 0, comments: 0 });
            const displayPlatforms = savedMetadata ? savedMetadata.platformsPosted : (clip.platformsPosted || []);
            const displayPostLinks = savedMetadata ? savedMetadata.postLinks : (clip.postLinks || {});
            const displayPostingNotes = savedMetadata ? (savedMetadata.postingNotes || "") : (clip.postingNotes || "");

            // Apply posted style if any platform is checked
            if (displayPlatforms.length > 0) {
                clipCard.classList.add('clip-card-posted');
            } else {
                clipCard.classList.remove('clip-card-posted'); // Ensure it's removed if no platforms
            }

            let platformsHTML = '<h4>Plataformas Postadas:</h4>';
            platformOptions.forEach(opt => {
                const isChecked = displayPlatforms.includes(opt.value) ? 'checked' : '';
                const linkValue = displayPostLinks[opt.value] || '';
                platformsHTML += `
                    <div>
                        <input type="checkbox" id="platform_${opt.value}_${clip.id}" name="platform_${opt.value}_${clip.id}" value="${opt.value}" ${isChecked}>
                        <label for="platform_${opt.value}_${clip.id}">${opt.label}</label>
                        <input type="url" name="link_${opt.value}_${clip.id}" placeholder="Link da postagem em ${opt.label}" value="${linkValue}" style="width: 50%; margin-left: 10px; ${isChecked ? 'display:inline-block;' : 'display:none;'}">
                    </div>`;
            });

            clipCard.innerHTML = `
                <div>
                    <h3 style="display: inline;">${clip.title}</h3>
                    <button type="button" class="copy-title-btn" onclick="copyClipTitle('${clip.id}', this)">Copy Title</button>
                </div>
                <video src="${clip.downloadUrl}" controls width="320" style="max-width:100%; height:auto;"></video>
                <br>
                <a href="${clip.downloadUrl}" download="${clip.title.replace(/[^a-z0-9_\-]/gi, '_')}.mp4" class="button-like">Baixar Clipe</a>
                <hr>
                <h4>Registrar Publicação e Métricas:</h4>
                ${platformsHTML}
                <div style="margin-top:10px;">
                    <label for="views_${clip.id}">Views:</label>
                    <input type="number" id="views_${clip.id}" name="views_${clip.id}" value="${displayMetrics.views}" min="0">
                    <label for="likes_${clip.id}" style="margin-left:10px;">Likes:</label>
                    <input type="number" id="likes_${clip.id}" name="likes_${clip.id}" value="${displayMetrics.likes}" min="0">
                    <label for="comments_${clip.id}" style="margin-left:10px;">Comentários:</label>
                    <input type="number" id="comments_${clip.id}" name="comments_${clip.id}" value="${displayMetrics.comments}" min="0">
                </div>
                <h4 style="margin-top:15px;">Notas para Postagem:</h4>
                <textarea id="notes_${clip.id}" name="notes_${clip.id}" rows="3" style="width: 95%; padding: 5px;" placeholder="Lembretes para esta postagem (hashtags, @menções, ideias)...">${displayPostingNotes}</textarea>
                <button type="button" onclick="saveClipInfoToStorage('${clip.id}')" style="margin-top:10px;">Salvar Informações do Clipe</button>
                <button type="button" onclick="removeClipFromSessionAndStorage('${clip.id}')" style="margin-top:10px; background-color:#d9534f; color:white; border:none; padding: 8px 12px; border-radius:4px; cursor:pointer;">Remover Clipe (da Sessão e Histórico)</button>
            `;
            clipsGallery.appendChild(clipCard);

            platformOptions.forEach(opt => {
                const checkbox = clipCard.querySelector(`#platform_${opt.value}_${clip.id}`);
                const linkInput = clipCard.querySelector(`input[name="link_${opt.value}_${clip.id}"]`);
                if (checkbox && linkInput) {
                    checkbox.onchange = () => {
                        linkInput.style.display = checkbox.checked ? 'inline-block' : 'none';
                    };
                }
            });
        });
    }

    // Modify showSection (ensure it's defined globally or passed around)
    // Assuming originalShowSection was defined earlier or showSection is global
    if (typeof window.showSection === 'function') {
        const originalShowSectionFunc = window.showSection;
        window.showSection = function(sectionId) {
            originalShowSectionFunc(sectionId);
            if (sectionId === 'generatedClips') {
                renderGeneratedClips();
            }
            if (sectionId === 'metricsAnalysis') {
                if (typeof renderMetricsAnalysis === "function") {
                    renderMetricsAnalysis();
                } else {
                    // console.warn("renderMetricsAnalysis function not yet defined for section:", sectionId);
                }
            }
        };
    } else {
        console.error("Original showSection function not found. Cannot augment it.");
        // Fallback or define showSection if it's the first time it's fully defined here.
        // For this exercise, we assume it was defined before and we are modifying it.
    }
    // --- End: Generated Clips Section Logic ---

    // --- Start: Metrics Analysis Section Logic ---
    const metricsTableBody = document.getElementById('metricsTableBody');
    const noMetricsDataP = document.getElementById('noMetricsData');
    const insightsList = document.getElementById('insightsList');
    const userPerformanceNotes = document.getElementById('userPerformanceNotes');
    const notesMessage = document.getElementById('notesMessage');
    // const metricsTable = document.getElementById('metricsTable'); // Not strictly needed globally if accessed in function

    function calculateEngagementRate(views, likes, comments) {
        if (views === 0) return 0;
        return ((likes + comments) / views) * 100; // As percentage
    }

    function renderMetricsAnalysis() {
        const savedClips = getSavedClipsMetadata();
        const metricsTable = document.getElementById('metricsTable'); // Get here for local scope use

        if(metricsTableBody) metricsTableBody.innerHTML = '';
        if(insightsList) insightsList.innerHTML = '';

        if (!savedClips || savedClips.length === 0) {
            if(noMetricsDataP) noMetricsDataP.style.display = 'block';
            if(metricsTable) metricsTable.style.display = 'none';
            if(insightsList) insightsList.innerHTML = '<li>Nenhum dado para gerar insights.</li>';
            loadUserNotes(); // Load notes even if no metrics
            return;
        }

        if(noMetricsDataP) noMetricsDataP.style.display = 'none';
        if(metricsTable) metricsTable.style.display = 'table';

        let totalViewsAll = 0;
        let totalLikesAll = 0;
        let totalCommentsAll = 0;
        const platformPerformance = {};
        const durationCategories = {
            "0-15s": { views: 0, likes: 0, comments: 0, count: 0, totalDuration: 0 },
            "16-30s": { views: 0, likes: 0, comments: 0, count: 0, totalDuration: 0 },
            "31-45s": { views: 0, likes: 0, comments: 0, count: 0, totalDuration: 0 },
            "46-60s": { views: 0, likes: 0, comments: 0, count: 0, totalDuration: 0 },
            ">60s": { views: 0, likes: 0, comments: 0, count: 0, totalDuration: 0 }
        };

        savedClips.forEach(clip => {
            const metrics = clip.metrics || { views: 0, likes: 0, comments: 0 };
            const engagement = calculateEngagementRate(metrics.views, metrics.likes, metrics.comments);
            const duration = (clip.endTimeSeconds !== undefined && clip.startTimeSeconds !== undefined) ? (clip.endTimeSeconds - clip.startTimeSeconds) : NaN;

            let linksHTML = '';
            if(clip.postLinks) {
                for (const [platform, link] of Object.entries(clip.postLinks)) {
                    if(link) linksHTML += `<a href="${link}" target="_blank">${platform}</a> `;
                }
            }

            const row = metricsTableBody.insertRow();
            row.innerHTML = `
                <td>${clip.title || 'N/A'}</td>
                <td>${!isNaN(duration) ? duration.toFixed(1) : 'N/A'}</td>
                <td>${(clip.platformsPosted || []).join(', ') || 'N/A'}</td>
                <td>${metrics.views}</td>
                <td>${metrics.likes}</td>
                <td>${metrics.comments}</td>
                <td>${engagement.toFixed(2)}%</td>
                <td>${linksHTML || 'N/A'}</td>
            `;

            totalViewsAll += metrics.views;
            totalLikesAll += metrics.likes;
            totalCommentsAll += metrics.comments;

            (clip.platformsPosted || []).forEach(platform => {
                if (!platformPerformance[platform]) {
                    platformPerformance[platform] = { views: 0, likes: 0, comments: 0, count: 0 };
                }
                platformPerformance[platform].views += metrics.views;
                platformPerformance[platform].likes += metrics.likes;
                platformPerformance[platform].comments += metrics.comments;
                platformPerformance[platform].count++;
            });

            if (!isNaN(duration)) {
                let category = ">60s";
                if (duration <= 15) category = "0-15s";
                else if (duration <= 30) category = "16-30s";
                else if (duration <= 45) category = "31-45s";
                else if (duration <= 60) category = "46-60s";

                durationCategories[category].views += metrics.views;
                durationCategories[category].likes += metrics.likes;
                durationCategories[category].comments += metrics.comments;
                durationCategories[category].count++;
                durationCategories[category].totalDuration += duration;
            }
        });

        // Generate Simple Insights
        if (totalViewsAll > 0) {
            insightsList.innerHTML += `<li>Média de Engajamento Geral: ${calculateEngagementRate(totalViewsAll, totalLikesAll, totalCommentsAll).toFixed(2)}%</li>`;
        }

        for (const [platform, data] of Object.entries(platformPerformance)) {
            if (data.count > 0 && data.views > 0) {
                const engagement = calculateEngagementRate(data.views, data.likes, data.comments);
                insightsList.innerHTML += `<li>Plataforma ${platform}: ${data.count} clipe(s), média de ${Math.round(data.views / data.count)} views, engajamento de ${engagement.toFixed(2)}%.</li>`;
            }
        }

        let bestDurationCategory = null;
        let maxAvgViewsDuration = -1;

        for (const [category, data] of Object.entries(durationCategories)) {
            if (data.count > 0) {
                const avgViews = data.views / data.count;
                const avgDuration = data.totalDuration / data.count;
                const engagement = calculateEngagementRate(data.views, data.likes, data.comments);
                insightsList.innerHTML += `<li>Clipes com duração na faixa ${category} (média ${avgDuration.toFixed(1)}s): ${data.count} clipe(s) tiveram em média ${avgViews.toFixed(0)} views e engajamento de ${engagement.toFixed(2)}%.</li>`;
                if (avgViews > maxAvgViewsDuration) {
                    maxAvgViewsDuration = avgViews;
                    bestDurationCategory = category;
                }
            }
        }
        if (bestDurationCategory) {
             insightsList.innerHTML += `<li><strong>Sugestão:</strong> Clipes na faixa de duração "${bestDurationCategory}" tiveram a maior média de visualizações (${maxAvgViewsDuration.toFixed(0)} views).</li>`;
        }

        if(insightsList.innerHTML === '<li>Nenhum dado para gerar insights.</li>' && savedClips.length > 0){
            insightsList.innerHTML = '<li>Dados insuficientes ou muito uniformes para gerar insights comparativos detalhados. Continue postando e registrando!</li>';
        } else if (savedClips.length > 0 && insightsList.childNodes.length === 0) {
             insightsList.innerHTML = '<li>Não foi possível gerar insights específicos com os dados atuais.</li>';
        } else if (insightsList.innerHTML === '') { // Fallback if it's still empty
             insightsList.innerHTML = '<li>Nenhum dado para gerar insights.</li>';
        }

        loadUserNotes(); // Load user notes when rendering this section
    }

    function saveUserNotes() {
        if(userPerformanceNotes) {
            localStorage.setItem(STORAGE_KEYS.userNotes, userPerformanceNotes.value);
        }
        if(notesMessage) {
            notesMessage.textContent = 'Anotações salvas!';
            notesMessage.style.color = 'green';
            setTimeout(() => { notesMessage.textContent = ''; }, 3000);
        }
    }

    function loadUserNotes() {
        if(userPerformanceNotes) {
            userPerformanceNotes.value = localStorage.getItem(STORAGE_KEYS.userNotes) || '';
        }
    }
    // --- End: Metrics Analysis Section Logic ---

// --- Start: Copy Clip Title Logic ---
function copyClipTitle(clipId, buttonElement) {
    const clip = processedClips.find(c => c.id === clipId);
    if (!clip || !clip.title) {
        console.error('Clip or title not found for ID:', clipId);
        buttonElement.textContent = 'Error!';
        setTimeout(() => {
            buttonElement.textContent = 'Copy Title';
        }, 2000);
        return;
    }
    const titleToCopy = clip.title;

    if (!navigator.clipboard) {
        console.error('Clipboard API not available.');
        buttonElement.textContent = 'No API!'; // Indicate clipboard API is not available
         setTimeout(() => {
            buttonElement.textContent = 'Copy Title';
        }, 2000);
        return;
    }

    navigator.clipboard.writeText(titleToCopy).then(() => {
        const originalButtonText = 'Copy Title'; // Assuming this is the default
        buttonElement.textContent = 'Copied!';
        buttonElement.disabled = true;
        setTimeout(() => {
            buttonElement.textContent = originalButtonText;
            buttonElement.disabled = false;
        }, 2000); // Revert after 2 seconds
    }).catch(err => {
        console.error('Failed to copy title: ', err);
        const originalButtonText = 'Copy Title';
        buttonElement.textContent = 'Failed!';
        setTimeout(() => {
            buttonElement.textContent = originalButtonText;
        }, 2000);
    });
}
// --- End: Copy Clip Title Logic ---
// --- Start: Import/Export Logic ---
function exportAllData() {
    const statusP = document.getElementById('importExportStatus');
    try {
        const settingsData = localStorage.getItem(STORAGE_KEYS.settings);
        const clipsData = localStorage.getItem(STORAGE_KEYS.savedClipMetrics);
        const notesData = localStorage.getItem(STORAGE_KEYS.userNotes);

        const backupData = {
            [STORAGE_KEYS.settings]: settingsData ? JSON.parse(settingsData) : null,
            [STORAGE_KEYS.savedClipMetrics]: clipsData ? JSON.parse(clipsData) : [],
            [STORAGE_KEYS.userNotes]: notesData || ""
        };

        const jsonString = JSON.stringify(backupData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = 'blogger-studio-backup.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        URL.revokeObjectURL(url);
        statusP.textContent = 'Data exported successfully!';
        statusP.style.color = 'green';
    } catch (error) {
        console.error("Error exporting data:", error);
        statusP.textContent = 'Error exporting data. Check console.';
        statusP.style.color = 'red';
    }
    setTimeout(() => { statusP.textContent = ''; }, 5000);
}

function triggerImport() {
    const statusP = document.getElementById('importExportStatus');
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];

    if (!file) {
        statusP.textContent = 'Please select a file to import.';
        statusP.style.color = 'red';
        setTimeout(() => { statusP.textContent = ''; }, 3000);
        return;
    }

    const reader = new FileReader();
    reader.onload = function(event) {
        processImportedData(event.target.result);
    };
    reader.onerror = function() {
        statusP.textContent = 'Error reading file.';
        statusP.style.color = 'red';
        setTimeout(() => { statusP.textContent = ''; }, 5000);
    };
    reader.readAsText(file);
}

function processImportedData(jsonDataString) {
    const statusP = document.getElementById('importExportStatus');
    let importedData;
    try {
        importedData = JSON.parse(jsonDataString);
    } catch (e) {
        statusP.textContent = 'Error: Invalid JSON file.';
        statusP.style.color = 'red';
        setTimeout(() => { statusP.textContent = ''; }, 5000);
        return;
    }

    // Validate data structure
    if (!importedData ||
        importedData[STORAGE_KEYS.settings] === undefined ||
        importedData[STORAGE_KEYS.savedClipMetrics] === undefined ||
        importedData[STORAGE_KEYS.userNotes] === undefined) {
        statusP.textContent = 'Error: File does not contain valid backup data structure.';
        statusP.style.color = 'red';
        setTimeout(() => { statusP.textContent = ''; }, 5000);
        return;
    }

    // Store the data
    if (importedData[STORAGE_KEYS.settings]) {
        localStorage.setItem(STORAGE_KEYS.settings, JSON.stringify(importedData[STORAGE_KEYS.settings]));
    } else {
        localStorage.removeItem(STORAGE_KEYS.settings);
    }

    if (importedData[STORAGE_KEYS.savedClipMetrics]) {
        localStorage.setItem(STORAGE_KEYS.savedClipMetrics, JSON.stringify(importedData[STORAGE_KEYS.savedClipMetrics]));
        // Repopulate in-memory processedClips from the imported data
        processedClips = JSON.parse(localStorage.getItem(STORAGE_KEYS.savedClipMetrics)) || [];
        // Note: Blob URLs for videos in processedClips won't be valid.
        // For now, we accept this. A more robust solution would re-evaluate how video blobs are handled/stored or warn user.
        // We need to re-create download URLs if they were blob URLs
        processedClips.forEach(clip => {
            if (clip.blob && clip.blob.type && clip.blob.size) { // Heuristic: check if it's a stored representation of a blob
                // This is a placeholder. Actual blob reconstruction from plain JSON is not direct.
                // For now, if blob URLs are critical, this import won't restore video playback without further changes.
                // The metadata (title, metrics, etc.) will be restored.
                console.warn(`Clip "${clip.title}" video data was likely a Blob and cannot be directly restored from JSON. Download URL may be invalid.`);
                // If we had stored the data as base64, we could reconstruct:
                // const byteCharacters = atob(clip.blob.base64Data);
                // const byteNumbers = new Array(byteCharacters.length);
                // for (let i = 0; i < byteCharacters.length; i++) {
                // byteNumbers[i] = byteCharacters.charCodeAt(i);
                // }
                // const byteArray = new Uint8Array(byteNumbers);
                // const actualBlob = new Blob([byteArray], {type: clip.blob.type});
                // clip.downloadUrl = URL.createObjectURL(actualBlob);
                // clip.blob = actualBlob; // restore the actual blob
            } else if (clip.downloadUrl && clip.downloadUrl.startsWith('blob:')) {
                 // If it was a blob URL, it's now invalid. We can't recreate it from JSON alone.
                 // We'll leave the metadata, but the video won't play from this URL.
                 console.warn(`Clip "${clip.title}" had a blob URL that is now invalid after import.`);
            }
        });

    } else {
        localStorage.setItem(STORAGE_KEYS.savedClipMetrics, JSON.stringify([]));
        processedClips = []; // Reset in-memory array too
    }

    if (importedData[STORAGE_KEYS.userNotes] !== undefined) {
        localStorage.setItem(STORAGE_KEYS.userNotes, importedData[STORAGE_KEYS.userNotes]);
    } else {
        localStorage.removeItem(STORAGE_KEYS.userNotes);
    }

    statusP.textContent = 'Data imported successfully! Refreshing application state...';
    statusP.style.color = 'green';

    // Reload application state/UI
    loadSettings();
    loadUserNotes(); // This function updates the textarea
    renderGeneratedClips(); // Will now use the repopulated processedClips
    renderMetricsAnalysis();

    // Show the settings section to confirm changes
    showSection('settings');

    document.getElementById('importFile').value = ''; // Clear the file input

    setTimeout(() => { statusP.textContent = ''; }, 5000);
}
// --- End: Import/Export Logic ---