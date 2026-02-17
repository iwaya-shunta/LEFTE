let selectedFileBase64 = null, selectedMimeType = null;
let uploadedImagePath = null; // 🚀 保存されたパスを保持する変数
const chatHistory = document.getElementById('chat-history');

// デフォルトの座標（広島）
const DEFAULT_LAT = 34.397;
const DEFAULT_LON = 132.475;

// --- 🚀 ウィジェット更新 ---
async function updateWidgets() {
    setInterval(() => {
        const clockEl = document.getElementById('clock');
        if (clockEl) clockEl.innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'});
    }, 1000);

    fetch(`https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja`)
        .then(r=>r.json())
        .then(d=>{
            const container = document.getElementById('news-container');
            if (container) container.innerHTML = d.items.slice(0, 10).map(i => `<div class="news-item"><a href="${i.link}" target="_blank" class="news-link">${i.title}</a></div>`).join('');
        });

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
        .then(r=>r.json())
        .then(d=>document.getElementById('weather').innerText = `${Math.round(d.current_weather.temperature)}°C`);

    const mapIframe = document.getElementById('weather-map');
    if (mapIframe) {
        mapIframe.src = `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&detailLat=${lat}&detailLon=${lon}&width=400&height=300&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1`;
    }
}

// --- 🚀 起動時処理 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    updateWidgets();
    if (window.innerWidth <= 768) switchTab('chat');
});

window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById(t + '-panel');
    if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
    if (e) e.currentTarget.classList.add('active');
};

function addCopyButtons(container) {
    container.querySelectorAll('pre').forEach((pre) => {
        const code = pre.querySelector('code');
        if (!code || pre.querySelector('.copy-btn')) return;
        const button = document.createElement('button');
        button.innerText = 'Copy'; button.className = 'copy-btn';
        button.onclick = () => {
            navigator.clipboard.writeText(code.innerText).then(() => {
                button.innerText = 'Copied!';
                setTimeout(() => button.innerText = 'Copy', 2000);
            });
        };
        pre.appendChild(button);
    });
}

// --- UIへのメッセージ追加（画像対応版） ---
function addMessageToUI(role, text, imageData = null) {
    const hist = document.getElementById('chat-history');
    const bubble = document.createElement('div');
    const displayRole = role === 'assistant' ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

    // 🚀 imageData が "uploads/..." ならパス、そうでなければ DataURL
    let imgSrc = imageData;
    if (imageData && !imageData.startsWith('data:') && !imageData.startsWith('/')) {
        imgSrc = "/" + imageData; 
    }
    let imageHtml = imageData ? `<img src="${imgSrc}" style="max-width: 100%; border-radius: 10px; margin-bottom: 8px; display: block;">` : "";

    if (displayRole === 'gemini') {
        const content = marked.parse(text);
        bubble.innerHTML = `<div class="ai-avatar">L</div><div class="message-content"><div class="res-txt">${content}</div><span class="message-time">${timeStr}</span></div>`;
    } else {
        bubble.innerHTML = `${imageHtml}<div class="message-text">${text}</div><span class="message-time">${timeStr}</span>`;
    }
    hist.appendChild(bubble);
    hist.scrollTop = hist.scrollHeight;
    return bubble;
}

// --- メッセージ送信 ---
function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    const model = document.querySelector('input[name="modelSelect"]:checked').value;
    if (!text && !selectedFileBase64) return;

    // UIにはプレビューを表示
    addMessageToUI('user', text, selectedFileBase64); 
    input.value = '';

    socket.emit('chat_request', {
        message: text,
        model: model,
        image: selectedFileBase64,
        image_url: uploadedImagePath, // 🚀 ここでHDDパスを送る！
        mime_type: selectedMimeType
    });

    selectedFileBase64 = null;
    uploadedImagePath = null; // 🚀 送信後にリセット
    document.getElementById('preview-container').style.display = 'none';
}

// --- HDDアップロード ---
async function uploadToHDD(file) {
    const formData = new FormData();
    formData.append('file', file);
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');

    try {
        const res = await fetch('/upload_to_hdd', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success) {
            uploadedImagePath = data.path; // 🚀 保存されたパスを保持！
            addMessageToUI('assistant', `HDDに保存したよ！`);
        }
    } catch (err) { console.error("Upload error:", err); }
    finally { if (logo) logo.classList.remove('is-thinking'); }
}

// --- 🚀 ファイル選択時の挙動（ここを一本化しました） ---
document.getElementById('fileInput').onchange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    
    // 1. HDDに保存
    uploadToHDD(f); 

    // 2. 画像ならプレビュー作成
    const r = new FileReader();
    r.onload = (event) => {
        selectedFileBase64 = event.target.result.split(',')[1];
        selectedMimeType = f.type;
        document.getElementById('preview-container').innerHTML = `<img src="${event.target.result}" style="max-height:80px; border-radius:10px;">`;
        document.getElementById('preview-container').style.display = 'block';
    };
    r.readAsDataURL(f);
};

// --- その他イベント ---
document.getElementById('sendBtn').onclick = ask;
document.getElementById('geminiInput').onkeydown = (e) => { if(e.key==='Enter') ask(); };
document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();

// 履歴読み込み
async function loadHistory() {
    const response = await fetch('/history');
    if (!response.ok) return;
    const history = await response.json();
    const histEl = document.getElementById('chat-history');
    histEl.innerHTML = '';
    // 🚀 msg.image_url を渡す
    history.forEach(msg => addMessageToUI(msg.role, msg.content, msg.image_url));
    histEl.scrollTop = histEl.scrollHeight;
}

// タイピング & 音声
async function runTypewriter(el, fullTxt, url) {
    const displayTxt = fullTxt.replace(/\(.*\)/g, '').replace(/（.*）/g, '');
    let i = 0; el.innerHTML = "";
    const audio = new Audio(url);
    const av = el.parentElement.parentElement.querySelector('.ai-avatar');
    audio.onplay = () => av.classList.add('speaking-icon');
    audio.onended = () => av.classList.remove('speaking-icon');
    audio.play();
    return new Promise(res => {
        function type() {
            if (i < displayTxt.length) {
                el.innerText += displayTxt.charAt(i); i++;
                setTimeout(type, 30);
            } else {
                el.innerHTML = marked.parse(displayTxt);
                addCopyButtons(el); res();
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        type();
    });
}

// Socket受信
socket.on('sys_status', (data) => {
    const tempElement = document.getElementById('cpu-temp');
    if (tempElement && data.cpu_temp) {
        tempElement.innerText = `${data.cpu_temp}°C`;
        tempElement.style.color = parseFloat(data.cpu_temp) > 65 ? "#ff4444" : "var(--accent)";
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

socket.on('chat_update', async (data) => {
    const tempBubble = document.getElementById('thinking-bubble');
    if (tempBubble) tempBubble.remove();
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.remove('is-thinking');

    const lastUserMsg = chatHistory.querySelector('.message.user:last-child');
    if (!lastUserMsg || lastUserMsg.innerText !== data.user_message) {
        addMessageToUI('user', data.user_message);
    }

    const bubble = addMessageToUI('assistant', '');
    await runTypewriter(bubble.querySelector('.res-txt'), data.response, data.voice_url);
    if (data.launch_url) window.location.href = data.launch_url;
});

// 🚀 追加：サーバーからのエラーを受け取る
socket.on('error_message', (data) => {
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.remove('is-thinking');

    const tempBubble = document.getElementById('thinking-bubble');
    if (tempBubble) tempBubble.remove();

    addMessageToUI('assistant', `⚠️ ${data.response}`);
    console.error("L.E.F.T.E. Error:", data.response);
});