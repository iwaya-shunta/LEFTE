const socket = io();

// 状態管理変数
let selectedFileBase64 = null, selectedMimeType = null, selectedFileObj = null;
let scrollInterval;

// 🚀 IDの不整合対策（HTML側がどちらのIDでも動作するようにガード）
const getChatElement = () => document.getElementById('chatBox') || document.getElementById('chat-history');

// デフォルトの座標（広島周辺）
const DEFAULT_LAT = 34.397;
const DEFAULT_LON = 132.475;

// --- 🚀 ウィジェット（時計・ニュース・天気）の更新 ---
async function updateWidgets() {
    // 時計（1秒ごと）
    setInterval(() => {
        const clockEl = document.getElementById('clock');
        if (clockEl) clockEl.innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'});
    }, 1000);

    // ニュース取得
    fetch(`https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja`)
        .then(r => r.json())
        .then(d => {
            const container = document.getElementById('news-container');
            if (container) {
                container.innerHTML = d.items.slice(0, 10).map(i => `
                    <div class="news-item">
                        <a href="${i.link}" target="_blank" class="news-link">${i.title}</a>
                    </div>`).join('');
            }
        });

    // 位置情報に基づいた天気
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => updateWeatherAndMap(pos.coords.latitude, pos.coords.longitude),
            () => updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON)
        );
    } else {
        updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON);
    }
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

// --- 🚀 UIへのメッセージ追加 ---
function addMessageToUI(role, text, imageData = null, voiceUrl = null) {
    const chatBox = getChatElement();
    if (!chatBox) return;

    const bubble = document.createElement('div');
    const displayRole = (role === 'assistant' || role === 'gemini') ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    const timeStr = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

    // 画像パスの正規化
    let imageHtml = "";
    if (imageData) {
        const imgSrc = imageData.startsWith('data:') ? imageData : (imageData.startsWith('/') ? imageData : "/" + imageData);
        imageHtml = `<img src="${imgSrc}" style="max-width: 100%; border-radius: 12px; margin-bottom: 8px; display: block;">`;
    }

    if (displayRole === 'gemini') {
        bubble.innerHTML = `
            <div class="ai-avatar">L</div>
            <div class="message-content">
                <div class="res-txt">${marked.parse(text)}</div>
                <div class="message-footer" style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                    <span class="message-time" style="font-size:10px; opacity:0.5;">${timeStr}</span>
                    ${voiceUrl ? `<button class="voice-btn" onclick="playVoice('${voiceUrl}')">🔊 Listen</button>` : ''}
                </div>
            </div>`;
    } else {
        bubble.innerHTML = `${imageHtml}<div class="message-text">${text}</div><span class="message-time" style="align-self:flex-end; font-size:10px; opacity:0.5; margin-top:4px;">${timeStr}</span>`;
    }
    
    chatBox.appendChild(bubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    return bubble;
}

// --- 🚀 音声再生（キャッシュ対策済み） ---
function playVoice(url) {
    // 🚀 タイムスタンプを付けてブラウザのキャッシュと転送エラーを回避
    const audio = new Audio(url + "?t=" + new Date().getTime());
    audio.play().catch(e => console.error("🔊 音声再生エラー:", e));
}

// --- 🚀 音声認識（マイク） ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    console.error("❌ このブラウザは音声認識に対応していない。Chromeを使用すること。");
} else {
    const recognition = new SpeechRecognition();
    recognition.lang = 'ja-JP';
    recognition.interimResults = true;
    recognition.continuous = false;

    const micBtn = document.getElementById('micBtn');
    
    recognition.onstart = () => {
        console.log("🎤 音声認識開始。");
        micBtn?.classList.add('recording');
    };

    recognition.onerror = (event) => {
        console.error("❌ 音声認識エラー:", event.error);
        if (event.error === 'not-allowed') {
            alert("マイクの使用が許可されていない。設定を確認すること。");
        }
    };

    recognition.onend = () => {
        console.log("🎤 音声認識終了。");
        micBtn?.classList.remove('recording');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const isFinal = event.results[0].isFinal;

        const inputEl = document.getElementById('geminiInput');
        if (inputEl) {
            inputEl.value = transcript;
            if (isFinal) {
                recognition.stop();
                ask();
            }
        }
    };

    if (micBtn) {
        micBtn.onclick = () => recognition.start();
    }
}

// --- 🚀 履歴の読み込み ---
async function loadHistory() {
    try {
        const res = await fetch('/history');
        if (!res.ok) return;
        const historyData = await res.json();
        const chatBox = getChatElement();
        if (chatBox) {
            chatBox.innerHTML = '';
            historyData.forEach(msg => {
                addMessageToUI(msg.role, msg.content, msg.image_url, msg.voice_url);
            });
        }
    } catch (e) {
        console.error("📜 履歴読み込みエラー:", e);
    }
}

// --- 🚀 送信処理 ---
async function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    if (!text && !selectedFileBase64) return;

    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');

    addMessageToUI('user', text, selectedFileBase64);
    
    if (!document.getElementById('thinking-bubble')) {
        const bubble = addMessageToUI('assistant', "確認中だよ……");
        bubble.id = 'thinking-bubble';
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
        message: text, 
        model: model, 
        image: imagePath ? null : selectedFileBase64, 
        image_url: imagePath, 
        mime_type: selectedMimeType 
    });

    selectedFileBase64 = null; selectedFileObj = null;
    document.getElementById('preview-container').style.display = 'none';
}

// --- 🚀 スクロール制御 ---
window.startScroll = function(offset) {
    const chatBox = getChatElement();
    if (chatBox) {
        scrollInterval = setInterval(() => {
            chatBox.scrollTop += offset;
        }, 30);
    }
};

window.stopScroll = function() {
    clearInterval(scrollInterval);
};

// --- 🚀 イベント登録と初期化 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    updateWidgets();

    document.getElementById('sendBtn').onclick = ask;
    document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();

    document.getElementById('geminiInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            ask();
        }
    });

    // テスト再生ボタン
    document.getElementById('testVoiceBtn')?.addEventListener('click', () => {
        playVoice('/wav_files/test.wav');
    });

    if (window.innerWidth <= 768) {
        switchTab('chat');
    }
});

// ファイル選択プレビュー
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

// Socketイベント
socket.on('chat_update', (data) => {
    document.getElementById('thinking-bubble')?.remove();
    document.querySelector('.brand-logo')?.classList.remove('is-thinking');

    addMessageToUI('assistant', data.response, null, data.voice_url);

    if (data.voice_url) {
        playVoice(data.voice_url);
    }
});

socket.on('sys_status', (data) => {
    const tempEl = document.getElementById('cpu-temp');
    if (tempEl && data.cpu_temp) {
        tempEl.innerText = `${data.cpu_temp}°C`;
        tempEl.style.color = parseFloat(data.cpu_temp) > 65 ? "#ff4444" : "var(--accent)";
    }
});

window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { 
        p.style.display = 'none'; 
        p.classList.remove('active-panel'); 
    });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const target = document.getElementById(t + '-panel');
    if (target) { 
        target.style.display = 'flex'; 
        target.classList.add('active-panel'); 
    }
    
    if (e) e.currentTarget.classList.add('active');
    else {
        const navItems = document.querySelectorAll('.nav-item');
        if (t === 'news') navItems[0].classList.add('active');
        if (t === 'chat') navItems[1].classList.add('active');
    }
};