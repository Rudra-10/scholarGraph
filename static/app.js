const API_BASE = '';

// ═══════════ STATE ═══════════
let graphReady = false;
let chatHistory = [];

// ═══════════ TOAST ═══════════
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ═══════════ SCREEN SWITCHING ═══════════
function showWorkspace() {
  document.getElementById('landing-screen').classList.remove('active');
  document.getElementById('workspace-screen').classList.add('active');
}

function showLanding() {
  document.getElementById('workspace-screen').classList.remove('active');
  document.getElementById('landing-screen').classList.add('active');

  // Reset workspace state
  if (visNetwork) {
    visNetwork.destroy();
    visNetwork = null;
  }
  document.getElementById('graph-network').innerHTML = '';
  document.getElementById('graph-network').style.display = 'none';
  document.getElementById('graph-empty-state').style.display = 'flex';
  document.getElementById('graph-stats').textContent = '';

  document.getElementById('chat-messages').innerHTML = '';
  chatHistory = [];
  graphReady = false;

  document.getElementById('landing-arxiv-input').value = '';
  document.getElementById('sidebar-arxiv-input').value = '';
  document.getElementById('chat-input').value = '';

  document.getElementById('workspace-title').textContent = 'ScholarGraph';
  document.getElementById('workspace-subtitle').textContent = 'CITATION INTELLIGENCE WORKSPACE';
}

// ═══════════ API CALLS ═══════════
async function ingestPaper(arxivId, depth, maxPapers) {
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ arxiv_id: arxivId, depth: depth, max_papers: maxPapers }),
  });
  return res.json();
}

async function askQuestion(question) {
  const res = await fetch(`${API_BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

async function fetchGraph() {
  const res = await fetch(`${API_BASE}/api/graph`);
  return res.json();
}

// ═══════════ GRAPH RENDERING (vis-network) ═══════════
let visNetwork = null;

async function renderGraph() {
  const data = await fetchGraph();

  const emptyState = document.getElementById('graph-empty-state');
  const networkDiv = document.getElementById('graph-network');

  if (!data.nodes || data.nodes.length === 0) {
    emptyState.style.display = 'flex';
    networkDiv.style.display = 'none';
    return;
  }

  emptyState.style.display = 'none';
  networkDiv.style.display = 'block';

  const nodes = data.nodes.map(n => ({
    id: n.id,
    label: n.title.length > 28 ? n.title.slice(0, 28) + '…' : n.title,
    title: `${n.title}${n.year ? ' (' + n.year + ')' : ''}`,
    color: {
      background: n.is_root ? '#D9B888' : '#8FB39B',
      border: n.is_root ? '#D9B888' : '#8FB39B',
      highlight: { background: '#EDEAE0', border: '#D9B888' },
    },
    font: { color: '#C8C2B2', size: 11, face: 'Inter' },
    size: n.is_root ? 22 : 14,
  }));

  const edges = data.edges.map(e => ({
    from: e.source,
    to: e.target,
    arrows: 'to',
    color: { color: '#2A312E', highlight: '#D9B888' },
    width: 1,
  }));

  const options = {
    nodes: { shape: 'dot', borderWidth: 0 },
    edges: { smooth: { type: 'continuous' } },
    physics: {
      stabilization: { iterations: 150 },
      barnesHut: { gravitationalConstant: -3000, springLength: 110, springConstant: 0.04 },
    },
    interaction: { hover: true, tooltipDelay: 100 },
  };

  if (visNetwork) {
    visNetwork.setData({ nodes, edges });
  } else {
    visNetwork = new vis.Network(networkDiv, { nodes, edges }, options);
  }

  document.getElementById('graph-stats').textContent =
    `${data.nodes.length} PAPERS · ${data.edges.length} CITATION EDGES`;
}

// ═══════════ CHAT ═══════════
let currentAudio = null;
let currentPlayingButton = null;

async function playTextAloud(text, buttonEl) {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
    if (currentPlayingButton) {
      currentPlayingButton.classList.remove('playing');
    }
  }

  if (currentPlayingButton === buttonEl) {
    currentPlayingButton = null;
    return;
  }

  buttonEl.classList.add('playing');
  currentPlayingButton = buttonEl;

  try {
    const res = await fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error('Speech synthesis request failed');

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    currentAudio = new Audio(url);

    currentAudio.onended = () => {
      buttonEl.classList.remove('playing');
      if (currentPlayingButton === buttonEl) currentPlayingButton = null;
      currentAudio = null;
    };

    currentAudio.onerror = () => {
      buttonEl.classList.remove('playing');
      if (currentPlayingButton === buttonEl) currentPlayingButton = null;
      currentAudio = null;
      showToast('Error playing audio', 'error');
    };

    await currentAudio.play();
  } catch (err) {
    showToast(err.message, 'error');
    buttonEl.classList.remove('playing');
    if (currentPlayingButton === buttonEl) currentPlayingButton = null;
  }
}

function appendMessage(role, content, isLoading = false, cypher = null) {
  const container = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;
  const bubble = document.createElement('div');
  bubble.className = `bubble ${role}${isLoading ? ' loading' : ''}`;
  bubble.textContent = content;

  if (role === 'assistant' && !isLoading) {
    const speakBtn = document.createElement('button');
    speakBtn.className = 'speak-btn';
    speakBtn.title = 'Read aloud';
    speakBtn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>';
    speakBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      playTextAloud(content, speakBtn);
    });
    bubble.appendChild(speakBtn);
  }

  row.appendChild(bubble);
  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
  return row;
}

async function handleSendQuestion() {
  const input = document.getElementById('chat-input');
  const question = input.value.trim();
  if (!question) return;

  if (!graphReady) {
    showToast('Please ingest a paper first using the sidebar.', 'error');
    return;
  }

  input.value = '';
  appendMessage('user', question);

  const loadingRow = appendMessage('assistant', 'Querying graph…', true);

  try {
    const result = await askQuestion(question);
    loadingRow.remove();
    appendMessage('assistant', result.answer, false, result.cypher);
  } catch (err) {
    loadingRow.remove();
    appendMessage('assistant', `Error: ${err.message}`);
  }
}

// ═══════════ INGESTION ═══════════
async function handleIngest(arxivId, depth, maxPapers, buttonEl) {
  if (!arxivId || !arxivId.trim()) {
    showToast('Please enter an arXiv ID', 'error');
    return;
  }

  const originalContent = buttonEl ? buttonEl.innerHTML : null;
  const loadingOverlay = document.getElementById('graph-loading-state');
  
  if (buttonEl) {
    buttonEl.disabled = true;
    buttonEl.innerHTML = '<span>Crawling…</span>';
  }
  if (loadingOverlay) {
    loadingOverlay.style.display = 'flex';
  }

  try {
    const result = await ingestPaper(arxivId.trim(), depth, maxPapers);

    if (result.status === 'error') {
      showToast(`Error: ${result.error}`, 'error');
      return;
    }

    graphReady = true;
    document.getElementById('workspace-title').textContent = result.root_title;
    document.getElementById('workspace-subtitle').textContent =
      'CITATION WORKSPACE · POWERED BY NEO4J + SARVAM AI';

    showToast(`Stored ${result.papers_stored} papers`, 'success');
    await renderGraph();
  } catch (err) {
    showToast(`Request failed: ${err.message}`, 'error');
  } finally {
    if (loadingOverlay) {
      loadingOverlay.style.display = 'none';
    }
    if (buttonEl) {
      buttonEl.disabled = false;
      buttonEl.innerHTML = originalContent;
    }
  }
}

// ═══════════ BACKGROUND CANVAS ANIMATION ═══════════
function initNetworkCanvas() {
  const canvas = document.getElementById('network-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  const NODE_COUNT = 30;
  const nodes = [];
  for (let i = 0; i < NODE_COUNT; i++) {
    nodes.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.2,
      r: Math.random() * 1.6 + 1.4,
    });
  }

  const flashes = [];

  function maybeSpawnFlash() {
    if (Math.random() < 0.025 && flashes.length < 3) {
      const a = nodes[Math.floor(Math.random() * nodes.length)];
      const b = nodes[Math.floor(Math.random() * nodes.length)];
      if (a !== b) flashes.push({ a, b, progress: 0 });
    }
  }

  function draw() {
    if (canvas.width === 0 || canvas.height === 0) {
      requestAnimationFrame(draw);
      return;
    }
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    }

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = `rgba(120, 130, 120, ${0.1 * (1 - dist / 150)})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(217, 184, 136, 0.6)';
      ctx.fill();
    }

    maybeSpawnFlash();
    for (let i = flashes.length - 1; i >= 0; i--) {
      const f = flashes[i];
      f.progress += 0.013;
      if (f.progress >= 1) { flashes.splice(i, 1); continue; }

      const fade = f.progress < 0.5 ? f.progress * 2 : (1 - f.progress) * 2;

      ctx.beginPath();
      ctx.moveTo(f.a.x, f.a.y);
      ctx.lineTo(f.b.x, f.b.y);
      ctx.strokeStyle = `rgba(217, 184, 136, ${0.55 * fade})`;
      ctx.lineWidth = 1.3;
      ctx.stroke();

      const px = f.a.x + (f.b.x - f.a.x) * f.progress;
      const py = f.a.y + (f.b.y - f.a.y) * f.progress;
      ctx.beginPath();
      ctx.arc(px, py, 2.4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(217, 184, 136, ${fade})`;
      ctx.fill();
    }

    requestAnimationFrame(draw);
  }
  draw();
}

// ═══════════ MICROPHONE RECORDING (STT) ═══════════
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

function setupMicrophone() {
  const micBtn = document.getElementById('chat-mic-btn');
  if (!micBtn) return;

  micBtn.addEventListener('click', async () => {
    if (isRecording) {
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
      }
      micBtn.classList.remove('recording');
      isRecording = false;
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        
        let mimeType = 'audio/webm';
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        }

        mediaRecorder = new MediaRecorder(stream, { mimeType });
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunks.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach(track => track.stop());

          const audioBlob = new Blob(audioChunks, { type: mimeType });
          if (audioBlob.size === 0) {
            showToast('No audio recorded', 'error');
            return;
          }

          showToast('Transcribing audio...', 'success');
          const formData = new FormData();
          formData.append('file', audioBlob, 'audio.webm');

          try {
            const res = await fetch('/api/transcribe', {
              method: 'POST',
              body: formData
            });

            if (!res.ok) throw new Error('Transcription failed');
            const data = await res.json();
            
            if (data.text) {
              const chatInput = document.getElementById('chat-input');
              chatInput.value = data.text;
              chatInput.focus();
              showToast('Audio transcribed successfully!', 'success');
            } else {
              showToast('Could not transcribe audio.', 'error');
            }
          } catch (err) {
            showToast(err.message, 'error');
          }
        };

        mediaRecorder.start();
        micBtn.classList.add('recording');
        isRecording = true;
        showToast('Recording... click mic again to stop', 'success');
      } catch (err) {
        showToast('Microphone access denied or not supported', 'error');
        console.error(err);
      }
    }
  });
}

// ═══════════ EVENT WIRING ═══════════
document.addEventListener('DOMContentLoaded', () => {
  initNetworkCanvas();

  // Workspace: sliders
  const depthSlider = document.getElementById('depth-slider');
  const maxPapersSlider = document.getElementById('max-papers-slider');

  // Landing: trace lineage
  document.getElementById('landing-trace-btn').addEventListener('click', async () => {
    const arxivId = document.getElementById('landing-arxiv-input').value.trim();
    if (!arxivId) {
      showToast('Enter an arXiv ID first.', 'error');
      return;
    }
    showWorkspace();
    document.getElementById('sidebar-arxiv-input').value = arxivId;
    const depth = parseInt(depthSlider.value);
    const maxPapers = parseInt(maxPapersSlider.value);
    await handleIngest(arxivId, depth, maxPapers, document.getElementById('build-graph-btn'));
  });

  document.getElementById('landing-arxiv-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') document.getElementById('landing-trace-btn').click();
  });

  // Landing: skip to workspace
  document.getElementById('skip-to-workspace').addEventListener('click', showWorkspace);

  // Landing: example pills
  document.querySelectorAll('.example-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.getElementById('landing-arxiv-input').value = pill.dataset.id;
    });
  });

  // Workspace: back to landing
  document.getElementById('back-to-landing').addEventListener('click', showLanding);

  // Workspace: sliders listeners
  depthSlider.addEventListener('input', () => {
    document.getElementById('depth-val').textContent = depthSlider.value;
  });
  maxPapersSlider.addEventListener('input', () => {
    document.getElementById('max-papers-val').textContent = maxPapersSlider.value;
  });

  // Workspace: build graph button
  document.getElementById('build-graph-btn').addEventListener('click', () => {
    const arxivId = document.getElementById('sidebar-arxiv-input').value;
    const depth = parseInt(depthSlider.value);
    const maxPapers = parseInt(maxPapersSlider.value);
    handleIngest(arxivId, depth, maxPapers, document.getElementById('build-graph-btn'));
  });

  // Workspace: quick start examples
  document.querySelectorAll('.example-row').forEach(row => {
    row.addEventListener('click', () => {
      document.getElementById('sidebar-arxiv-input').value = row.dataset.id;
    });
  });

  // Workspace: chat
  document.getElementById('chat-send-btn').addEventListener('click', handleSendQuestion);
  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSendQuestion();
  });

  // Setup mic recording handler
  setupMicrophone();
});