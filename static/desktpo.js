const socket = io();

// 状態管理
let selectedFileBase64 = null, selectedMimeType = null, selectedFileObj = null;
let scrollInterval;
let currentAudio = null;
let isLiveMode = false;
let recognition = null;

// IDの不整合対策
const getChatElement = () => document.getElementById('chatBox') || document.getElementById('chat-history');
const DEFAULT_LAT = 34.397;
const DEFAULT_LON = 132.475;

// ショートカットデータ (Library用)
// static/desktpo.js の修正箇所
const myShortcuts = [
    { name: "YouTube", url: "https://www.youtube.com", icon: "📺", category: "media" },
    { name: "GitHub", url: "https://github.com", icon: "🐙", category: "work" },
    { name: "Twitter", url: "https://twitter.com", icon: "🐦", category: "sns" },
    { name: "Gmail", url: "https://mail.google.com", icon: "📧", category: "work" },
    { name: "Netflix", url: "https://www.netflix.com", icon: "🎬", category: "media" },
    
    // 🚀 ここにゲームを追加！
    { 
        name: "ZZZ", 
        url: "C:\\Program Files\\HoYoPlay\\games\\ZenlessZoneZero Game\\ZenlessZoneZero.exe", 
        icon: "⚔️", 
        category: "game",
        type: "app" // 🚀 type を app にするのがミソ
    }
];

// --- 🚀 ウィジェット更新 (時計・ニュース・天気) ---
async function updateWidgets() {
    setInterval(() => {
        const clockEl = document.getElementById('clock');
        if (clockEl) clockEl.innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'});
    }, 1000);

    // 🚀 ニュース更新 (サーバー経由の /get_news を使用)
    updateNews();
    setInterval(updateNews, 3600000);

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => updateWeatherAndMap(pos.coords.latitude, pos.coords.longitude),
            () => updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON)
        );
    } else {
        updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON);
    }
}

async function updateNews() {
    const container = document.getElementById('news-container');
    if (!container) return;
    try {
        const response = await fetch('/get_news');
        const data = await response.json();
        if (data.news && data.news.length > 0) {
            container.innerHTML = data.news.slice(0, 10).map(item => `
                <div class="news-item">
                    <a href="${item.link}" target="_blank" class="news-link">▶ ${item.title}</a>
                </div>`).join('');
        }
    } catch (e) { console.error("News error:", e); }
}

function updateWeatherAndMap(lat, lon) {
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`)
        .then(r => r.json())
        .then(d => {
            const weatherEl = document.getElementById('weather');
            if (weatherEl) weatherEl.innerText = `${Math.round(d.current_weather.temperature)}°C`;
        });
    const mapIframe = document.getElementById('weather-map');
    if (mapIframe) {
        mapIframe.src = `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&detailLat=${lat}&detailLon=${lon}&width=400&height=300&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1`;
    }
}

async function launchApp(path) {
    const res = await fetch('/launch_app', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path })
    });
    const result = await res.json();
    if (!result.success) alert("起動エラー: " + result.error);
}

// static/desktpo.js の renderLauncher 関数を修正

// static/desktpo.js の renderLauncher を以下に差し替え
function renderLauncher(category = 'all') {
    const grid = document.getElementById('launcher-grid');
    if (!grid) return;
    grid.innerHTML = '';
    const filtered = category === 'all' ? myShortcuts : myShortcuts.filter(s => s.category === category);

    filtered.forEach(item => {
        const card = document.createElement('a');
        card.className = "shortcut-card";

        if (item.type === 'app') {
            // 🚀 サーバーを介さず、直接 Windows のプロトコルを呼び出すよ
            card.href = `lefte-launch://${item.url}`;
        } else {
            card.href = item.url;
            card.target = "_blank";
        }
        card.innerHTML = `<div class="icon-box">${item.icon}</div><span>${item.name}</span>`;
        grid.appendChild(card);
    });
}

function filterShortcuts(category) {
    document.querySelectorAll('.genre-item').forEach(el => {
        el.classList.remove('active');
        if(el.textContent.includes(category) || (category === 'all' && el.textContent === '全て')) {
            el.classList.add('active');
        }
    });
    renderLauncher(category);
}

// --- 💬 チャット機能 (ここが抜けていました！) ---
function addMessageToUI(role, text, imageData = null, voiceUrl = null, timestamp = null) {
    const chatBox = getChatElement();
    if (!chatBox) return;

    const bubble = document.createElement('div');
    const displayRole = (role === 'assistant' || role === 'gemini') ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    // 🚀 修正：表示用テキストから [slow], [fast], [normal] を消す
    const displayText = text.replace(/\[(slow|fast|normal)\]/g, '');

    let timeStr;
    if (timestamp) {
        timeStr = timestamp.substring(11, 16);
    } else {
        timeStr = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
    }

    let imageHtml = "";
    if (imageData) {
        const imgSrc = imageData.startsWith('data:') ? imageData : (imageData.startsWith('/') ? imageData : "/" + imageData);
        imageHtml = `<img src="${imgSrc}" style="max-width: 100%; border-radius: 12px; margin-bottom: 8px; display: block;">`;
    }

    if (displayRole === 'gemini') {
        bubble.innerHTML = `
            <div class="ai-avatar">L</div>
            <div class="message-content">
                <div class="res-txt">${marked.parse(displayText)}</div> <!-- 🚀 ここを displayText に変更 -->
                <div class="message-footer" style="display:flex; justify-content:flex-end; align-items:center; gap:10px; margin-top:5px; opacity:0.6; font-size:10px;">
                    <span>${timeStr}</span>
                    ${voiceUrl ? `<span style="cursor:pointer; color:var(--accent);" onclick="playVoice('${voiceUrl}')">🔊 Listen</span>` : ''}
                </div>
            </div>`;
    } else {
        // ユーザー側のメッセージからも一応タグを消しておくと安心
        bubble.innerHTML = `${imageHtml}<div class="message-text">${displayText}</div><span class="message-time" style="align-self:flex-end; font-size:10px; opacity:0.5; margin-top:4px;">${timeStr}</span>`;
    }
    
    chatBox.appendChild(bubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    return bubble;
}

function playVoice(url) {
    const audio = new Audio(url + "?t=" + new Date().getTime());
    audio.play().catch(e => console.error("🔊 音声再生エラー:", e));
}

async function loadHistory() {
    try {
        const res = await fetch('/history');
        if (!res.ok) return;
        const historyData = await res.json();
        const chatBox = getChatElement();
        if (chatBox) {
            chatBox.innerHTML = '';
            historyData.forEach(msg => {
                // 🚀 引数の最後に msg.timestamp を追加
                addMessageToUI(msg.role, msg.content, msg.image_url, msg.voice_url, msg.timestamp);
            });
        }
    } catch (e) { console.error("📜 履歴読み込みエラー:", e); }
}

async function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    if (!text && !selectedFileBase64) return;

    document.querySelector('.brand-logo')?.classList.add('is-thinking');
    addMessageToUI('user', text, selectedFileBase64);
    
    if (!document.getElementById('thinking-bubble')) {
        const bubble = addMessageToUI('assistant', "確認中だよ……");
        bubble.id = 'thinking-bubble';
    }

    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }

    const model = document.querySelector('input[name="modelSelect"]:checked').value;
    input.value = '';

    let imagePath = null;
    if (selectedFileObj) {
        const formData = new FormData();
        formData.append('file', selectedFileObj);
        try {
            const res = await fetch('/upload_to_hdd', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.success) imagePath = data.path;
        } catch (err) { console.error("Upload failed", err); }
    }

    socket.emit('chat_request', { 
        message: text, model: model, image: imagePath ? null : selectedFileBase64, 
        image_url: imagePath, mime_type: selectedMimeType 
    });

    selectedFileBase64 = null; selectedFileObj = null;
    document.getElementById('preview-container').style.display = 'none';
}

// --- 🎤 音声認識 ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.interimResults = true;
    recognition.onstart = () => document.getElementById('micBtn')?.classList.add('recording');
    recognition.onend = () => document.getElementById('micBtn')?.classList.remove('recording');
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const inputEl = document.getElementById('geminiInput');
        if (inputEl) {
            inputEl.value = transcript;
            if (event.results[0].isFinal) { recognition.stop(); ask(); }
        }
    };
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.onclick = () => recognition.start();
}

function initLiveMode() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return alert("お使いのブラウザは音声認識に対応していません。");

    recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
        // 🚀 エコーガード：L.E.F.T.E.が喋っている最中なら無視する
        if (currentAudio && !currentAudio.paused) {
            console.log("AIが喋っているので無視しました");
            return;
        }

        const lastIndex = event.results.length - 1;
        const text = event.results[lastIndex][0].transcript;

        if (event.results[lastIndex].isFinal && text.trim().length > 0) {
            console.log("Live認識確定:", text);
            const input = document.getElementById('geminiInput');
            if (input) {
                input.value = text;
                ask(); // 既存の送信関数を呼び出し
            }
        }
    };

    recognition.onend = () => {
        if (isLiveMode) recognition.start(); // 自動再起動
    };
}

// desktpo.js 内の toggleLiveMode 関数を探して書き換え
// static/desktpo.js 内の toggleLiveMode を修正
function toggleLiveMode() {
    isLiveMode = !isLiveMode;
    const btn = document.getElementById('liveModeBtn');
    const span = btn.querySelector('span');

    if (isLiveMode) {
        if (!recognition) initLiveMode();
        recognition.start();
        btn.classList.add('active');
        span.innerText = "LIVE"; // 短くスッキリさせる
    } else {
        if (recognition) recognition.stop();
        btn.classList.remove('active');
        span.innerText = "LIVE"; // 常にLIVEで、色だけで状態を表す
    }
}

// --- 🚀 初期化・イベント ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    updateWidgets();
    renderLauncher('all');

    document.getElementById('sendBtn').onclick = ask;
    document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();
    document.getElementById('geminiInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask(); }
    });

    if (window.innerWidth <= 768) switchTab('chat');
});

document.getElementById('fileInput').onchange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    selectedFileObj = f;
    const r = new FileReader();
    r.onload = (ev) => {
        selectedFileBase64 = ev.target.result.split(',')[1];
        selectedMimeType = f.type;
        const preview = document.getElementById('preview-container');
        preview.innerHTML = `<img src="${ev.target.result}" style="max-height:80px; border-radius:10px;">`;
        preview.style.display = 'block';
    };
    r.readAsDataURL(f);
};

socket.on('chat_update', (data) => {
    document.getElementById('thinking-bubble')?.remove();
    document.querySelector('.brand-logo')?.classList.remove('is-thinking');
    addMessageToUI('assistant', data.response, null, data.voice_url);
    if (data.voice_url) {
        // もし既に再生中の音があれば止める（割り込みへの準備）
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }

        currentAudio = new Audio(data.voice_url);
        
        // 再生開始
        currentAudio.play().catch(e => {
            console.warn("ブラウザの制限で自動再生がブロックされました。一度画面をクリックしてください。");
        });

        // 再生が終わったらリセット
        currentAudio.onended = () => { currentAudio = null; };
    }
});

socket.on('sys_status', (data) => {
    const tempEl = document.getElementById('cpu-temp');
    if (tempEl && data.cpu_temp) {
        tempEl.innerText = `${data.cpu_temp}°C`;
        tempEl.style.color = parseFloat(data.cpu_temp) > 65 ? "#ff4444" : "var(--accent)";
    }
});

// static/desktpo.js のイベントリスナーが並んでいるところに追加
socket.on('voice_ready', (data) => {
    if (data.voice_url) {
        console.log("🔊 音声が完成しました:", data.voice_url);
        
        // もし既に再生中の音があれば止める
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }

        currentAudio = new Audio(data.voice_url);
        currentAudio.play().catch(e => {
            console.warn("ブラウザにより自動再生がブロックされました。画面をクリックしてください。");
        });
    }
});

window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById(t + '-panel');
    if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
    if (e) e.currentTarget.classList.add('active');
    else {
        const navItems = document.querySelectorAll('.nav-item');
        if (t === 'news') navItems[0].classList.add('active');
        if (t === 'chat') navItems[1].classList.add('active');
    }
};

window.startScroll = function(offset) {
    const chatBox = getChatElement();
    if (chatBox) scrollInterval = setInterval(() => { chatBox.scrollTop += offset; }, 30);
};
window.stopScroll = function() { clearInterval(scrollInterval); };