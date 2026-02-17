const socket = io();

let selectedFileBase64 = null, selectedMimeType = null, selectedFileObj = null;
const chatHistory = document.getElementById('chat-history');

// デフォルトの座標（広島周辺）
const DEFAULT_LAT = 34.397;
const DEFAULT_LON = 132.475;

// --- 🚀 ウィジェット（時計・ニュース・天気）の更新 ---
async function updateWidgets() {
    // 時計の更新（1秒ごと）
    setInterval(() => {
        const clockEl = document.getElementById('clock');
        if (clockEl) clockEl.innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'});
    }, 1000);

    // ニュースの取得
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

    // 天気と地図の更新（位置情報が取れれば現在地、取れなければデフォルト）
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
    // 天気
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`)
        .then(r => r.json())
        .then(d => {
            const weatherEl = document.getElementById('weather');
            if (weatherEl) weatherEl.innerText = `${Math.round(d.current_weather.temperature)}°C`;
        });

    // 雨雲レーダー
    const mapIframe = document.getElementById('weather-map');
    if (mapIframe) {
        mapIframe.src = `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&detailLat=${lat}&detailLon=${lon}&width=400&height=300&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1`;
    }
}

// --- 🚀 UIへのメッセージ追加 ---
function addMessageToUI(role, text, imageData = null) {
    const bubble = document.createElement('div');
    const displayRole = role === 'assistant' ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    let imgSrc = "";
    if (imageData) {
        imgSrc = (imageData.startsWith('uploads/') || imageData.startsWith('/uploads/')) 
                 ? (imageData.startsWith('/') ? imageData : "/" + imageData)
                 : "data:image/jpeg;base64," + imageData;
    }

    const imageHtml = imgSrc ? `<img src="${imgSrc}" style="max-width: 100%; border-radius: 10px; margin-bottom: 8px; display: block;">` : "";
    const timeStr = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

    if (displayRole === 'gemini') {
        bubble.innerHTML = `<div class="ai-avatar">L</div><div class="message-content"><div class="res-txt">${marked.parse(text)}</div><span class="message-time">${timeStr}</span></div>`;
    } else {
        bubble.innerHTML = `${imageHtml}<div class="message-text">${text}</div><span class="message-time">${timeStr}</span>`;
    }
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return bubble;
}

// --- 🚀 送信処理 ---
async function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    if (!text && !selectedFileBase64) return;

    // 🚀 1. サーバーを待たずに、まずロゴを光らせてバブルを出す（生命感！）
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');
    
    if (!document.getElementById('thinking-bubble')) {
        const bubble = addMessageToUI('assistant', "確認中だよ……");
        bubble.id = 'thinking-bubble';
    }

    // 自分の発言を即座に表示
    addMessageToUI('user', text, selectedFileBase64);
    input.value = '';

    // 裏側でアップロード処理
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

    // サーバーへ送信
    socket.emit('chat_request', { 
        message: text, 
        model: document.querySelector('input[name="modelSelect"]:checked').value, 
        image: selectedFileBase64, 
        image_url: imagePath, 
        mime_type: selectedMimeType 
    });

    selectedFileBase64 = null; selectedFileObj = null;
    document.getElementById('preview-container').style.display = 'none';
}

// --- 🚀 起動時処理とイベント登録 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    updateWidgets(); // ウィジェット起動

    // エンターキーで送信する設定
    document.getElementById('geminiInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            ask();
        }
    });

    // タブ切り替え機能の初期化
    if (window.innerWidth <= 768) switchTab('chat');
});

// ファイル選択（プレビューのみ）
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

// 履歴読み込み
async function loadHistory() {
    const res = await fetch('/history');
    if (!res.ok) return;
    const history = await res.json();
    chatHistory.innerHTML = '';
    history.forEach(msg => addMessageToUI(msg.role, msg.content, msg.image_url));
}

// --- 🚀 Socket受信イベント ---

socket.on('sys_status', (data) => {
    const tempEl = document.getElementById('cpu-temp');
    if (tempEl && data.cpu_temp) {
        tempEl.innerText = `${data.cpu_temp}°C`;
        tempEl.style.color = parseFloat(data.cpu_temp) > 65 ? "#ff4444" : "var(--accent)";
    }
});

socket.on('ai_thinking', () => {
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');
    if (!document.getElementById('thinking-bubble')) {
        const bubble = addMessageToUI('assistant', "確認中だよ……");
        bubble.id = 'thinking-bubble';
    }
});

socket.on('chat_update', (data) => {
    document.getElementById('thinking-bubble')?.remove();
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.remove('is-thinking');
    const lastUserMsg = chatHistory.querySelector('.message.user:last-child');
    const lastText = lastUserMsg ? (lastUserMsg.querySelector('.message-text')?.innerText || "") : "";
    if (!lastUserMsg || lastText !== data.user_message) {
        addMessageToUI('user', data.user_message, data.image_url);
    } else if (data.image_url && lastUserMsg) {
        const img = lastUserMsg.querySelector('img');
        if (img) img.src = "/" + data.image_url;
    }
    addMessageToUI('assistant', data.response);
});

socket.on('error_message', (data) => {
    document.getElementById('thinking-bubble')?.remove();
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.remove('is-thinking');
    addMessageToUI('assistant', `⚠️ ${data.response}`);
});

// --- 🚀 グローバル関数（HTMLから呼び出す用） ---
window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById(t + '-panel');
    if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
    if (e) e.currentTarget.classList.add('active');
};

document.getElementById('sendBtn').onclick = ask;
document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();