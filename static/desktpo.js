let selectedFileBase64 = null, selectedMimeType = null;
const chatHistory = document.getElementById('chat-history');

// デフォルトの座標（広島）
const DEFAULT_LAT = 34.397;
const DEFAULT_LON = 132.475;



// --- 🚀 ウィジェット更新のメイン処理 ---
async function updateWidgets() {
    // 1. 時計の更新
    setInterval(() => {
        const clockEl = document.getElementById('clock');
        if (clockEl) clockEl.innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'});
    }, 1000);

    // 2. ニュースの取得
    fetch(`https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja`)
        .then(r=>r.json())
        .then(d=>{
            const container = document.getElementById('news-container');
            if (container) container.innerHTML = d.items.slice(0, 10).map(i => `<div class="news-item"><a href="${i.link}" target="_blank" class="news-link">${i.title}</a></div>`).join('');
        });

    // 3. 位置情報を取得して、天気と地図を更新
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                updateWeatherAndMap(pos.coords.latitude, pos.coords.longitude);
            },
            (err) => {
                console.warn("位置情報の取得に失敗しました。デフォルト（広島）を表示します。");
                updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON);
            }
        );
    } else {
        updateWeatherAndMap(DEFAULT_LAT, DEFAULT_LON);
    }
}

// 天気APIとWindy地図を更新する関数
function updateWeatherAndMap(lat, lon) {
    // 天気予報の更新
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true`)
        .then(r=>r.json())
        .then(d=>document.getElementById('weather').innerText = `${Math.round(d.current_weather.temperature)}°C`);

    // Windy地図の更新
    const mapIframe = document.getElementById('weather-map');
    if (mapIframe) {
        mapIframe.src = `https://embed.windy.com/embed2.html?lat=${lat}&lon=${lon}&detailLat=${lat}&detailLon=${lon}&width=400&height=300&zoom=10&level=surface&overlay=radar&product=radar&menu=&message=&marker=&calendar=now&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1`;
    }
}

// --- 🚀 ページ読み込み時の処理 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();  // 履歴の読み込み
    updateWidgets(); // ウィジェットの更新（位置情報含む）

    // モバイル用初期表示設定
    if (window.innerWidth <= 768) switchTab('chat');
});

// --- タブ切り替え ---
window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById(t + '-panel');
    if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
    if (e) e.currentTarget.classList.add('active');
};

// --- コピーボタン ---
function addCopyButtons(container) {
    container.querySelectorAll('pre').forEach((pre) => {
        const code = pre.querySelector('code');
        if (!code || pre.querySelector('.copy-btn')) return;
        const button = document.createElement('button');
        button.innerText = 'Copy';
        button.className = 'copy-btn';
        button.onclick = () => {
            navigator.clipboard.writeText(code.innerText).then(() => {
                button.innerText = 'Copied!';
                setTimeout(() => button.innerText = 'Copy', 2000);
            });
        };
        pre.appendChild(button);
    });
}

// --- UIへのメッセージ追加 ---
function addMessageToUI(role, text) {
    const hist = document.getElementById('chat-history');
    const bubble = document.createElement('div');
    const displayRole = role === 'assistant' ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    // 🕒 現在時刻を取得 (例: 23:55)
    const now = new Date();
    const timeStr = now.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });

    if (displayRole === 'gemini') {
        const content = marked.parse(text);
        bubble.innerHTML = `
            <div class="ai-avatar">L</div>
            <div class="message-content">
                <div class="res-txt">${content}</div>
                <span class="message-time">${timeStr}</span>
            </div>
        `;
        addCopyButtons(bubble);
    } else {
        // ユーザー側の表示
        bubble.innerHTML = `
            <div class="message-text">${text}</div>
            <span class="message-time">${timeStr}</span>
        `;
    }

    hist.appendChild(bubble);
    hist.scrollTop = hist.scrollHeight;
    return bubble;
}

// --- 履歴の読み込み ---
async function loadHistory() {
    try {
        const response = await fetch('/history');
        if (!response.ok) return;
        const history = await response.json();
        const chatHistoryElement = document.getElementById('chat-history');
        chatHistoryElement.innerHTML = '';
        history.forEach(msg => {
            addMessageToUI(msg.role, msg.content);
        });
        chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
    } catch (error) {
        console.error("履歴の読み込みエラー:", error);
    }
}

// --- タイピングエフェクト ---
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
                addCopyButtons(el);
                res();
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        type();
    });
}

async function uploadToHDD(file) {
    const formData = new FormData();
    formData.append('file', file);

    // アップロード中をロゴで演出
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');

    try {
        const res = await fetch('/upload_to_hdd', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            // 保存場所をしゅんたさんに報告
            addMessageToUI('assistant', `ファイルを HDD の \`${data.path}\` に保存したよ！いつでも読み取れるからね。`);
        } else {
            console.error("Upload failed:", data.error);
        }
    } catch (err) {
        console.error("Upload error:", err);
    } finally {
        if (logo) logo.classList.remove('is-thinking');
    }
}

// --- 修正：ファイル選択時の挙動 ---
document.getElementById('fileInput').onchange = (e) => {
    const f = e.target.files[0];
    if (!f) return;

    // 1. まずは HDD にアップロードを実行
    uploadToHDD(f);

    // 2. 画像ならチャットのプレビュー（Geminiへの送信準備）を行う
    if (f.type.startsWith('image/')) {
        const r = new FileReader();
        r.onload = (e) => {
            selectedFileBase64 = e.target.result.split(',')[1];
            selectedMimeType = f.type;
            document.getElementById('preview-container').innerHTML = `<img src="${e.target.result}" style="max-height:80px; border-radius:10px;">`;
            document.getElementById('preview-container').style.display = 'block';
        };
        r.readAsDataURL(f);
    }
};

// --- メッセージ送信 (WebSocket版) ---
function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    const model = document.querySelector('input[name="modelSelect"]:checked').value;
    
    if (!text && !selectedFileBase64) return;

    // 自分の発言だけ即座に出す
    addMessageToUI('user', text);
    input.value = '';

    // 🚀 サーバーに依頼を投げるだけにする
    socket.emit('chat_request', {
        message: text,
        model: model,
        image: selectedFileBase64,
        mime_type: selectedMimeType
    });

    selectedFileBase64 = null;
    document.getElementById('preview-container').style.display = 'none';
    
    // 💡 ここで 'assistant' バブルを作っていた 1 行を削除！
}

// --- スクロール・音声・ファイル・スワイプ等の各種イベント ---
let scrollInterval = null;
function startScroll(amount) {
    chatHistory.scrollBy({ top: amount, behavior: 'auto' });
    scrollInterval = setInterval(() => { chatHistory.scrollBy({ top: amount, behavior: 'auto' }); }, 30);
}
function stopScroll() { if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null; } }

const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
rec.lang = 'ja-JP';
document.getElementById('micBtn').onclick = () => { rec.start(); document.body.classList.add('recording'); };
rec.onresult = (e) => { document.getElementById('geminiInput').value = e.results[0][0].transcript; ask(); };
rec.onend = () => { document.body.classList.remove('recording'); };

document.getElementById('sendBtn').onclick = ask;
document.getElementById('geminiInput').onkeydown = (e) => { if(e.key==='Enter') ask(); };
document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();
document.getElementById('fileInput').onchange = (e) => {
    const f = e.target.files[0]; if (!f) return;
    const r = new FileReader(); r.onload = (e) => {
        selectedFileBase64 = e.target.result.split(',')[1]; selectedMimeType = f.type;
        document.getElementById('preview-container').innerHTML = `<img src="${e.target.result}" style="max-height:80px; border-radius:10px;">`;
        document.getElementById('preview-container').style.display = 'block';
    }; r.readAsDataURL(f);
};

// スワイプ遷移
let touchStartX = 0; let touchEndX = 0;
const tabs = ['news', 'chat', 'calendar'];
window.addEventListener('touchstart', e => { touchStartX = e.changedTouches[0].screenX; }, false);
window.addEventListener('touchend', e => { touchEndX = e.changedTouches[0].screenX; handleSwipe(); }, false);
function handleSwipe() {
    const distance = touchEndX - touchStartX;
    const activeNav = document.querySelector('.nav-item.active');
    if (!activeNav) return;
    const currentTab = activeNav.innerText.includes('ニュース') ? 'news' :
                       activeNav.innerText.includes('チャット') ? 'chat' : 'calendar';
    const currentIndex = tabs.indexOf(currentTab);
    if (distance > 70 && currentIndex > 0) switchTab(tabs[currentIndex - 1]);
    else if (distance < -70 && currentIndex < 2) switchTab(tabs[currentIndex + 1]);
}

// PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js').catch(err => console.log('SW Error', err));
    });
}

socket.on('sys_status', (data) => {
    const tempElement = document.getElementById('cpu-temp');
    if (tempElement && data.cpu_temp) {
        tempElement.innerText = `${data.cpu_temp}°C`;
        
        // 🌡️ おまけ：温度が高い（65度以上）ときに色を変える演出
        tempElement.style.color = parseFloat(data.cpu_temp) > 65 ? "#ff4444" : "var(--accent)";
    }
});

// 🚀 STEP 3: ロード中の演出（非同期処理中）
socket.on('ai_thinking', (data) => {
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.add('is-thinking');

    if (!document.getElementById('thinking-bubble')) {
        // 💬 思考中のバリエーション
        const phrases = ["うーん……", "えーっと……", "確認中だよ……", "ちょっと待ってね……"];
        const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];

        const bubble = addMessageToUI('assistant', randomPhrase);
        bubble.id = 'thinking-bubble';
    }
});

// 🚀 STEP 4: 応答の表示
// 🚀 STEP 4: 応答の表示（完全版）
socket.on('chat_update', async (data) => {
    // 1. 名札（ID）を頼りにドット（思考中バブル）を消す
    const tempBubble = document.getElementById('thinking-bubble');
    if (tempBubble) tempBubble.remove();

    // 2. ロゴの光る演出を止める（もしCSSクラスを作っている場合）
    const logo = document.querySelector('.brand-logo');
    if (logo) logo.classList.remove('is-thinking');

    // 3. 【同期】スマホなど他デバイスからの送信を画面に反映
    // 自分の画面にまだ自分のメッセージが出ていなければ追加する
    const lastUserMsg = chatHistory.querySelector('.message.user:last-child');
    if (!lastUserMsg || lastUserMsg.innerText !== data.user_message) {
        addMessageToUI('user', data.user_message);
    }

    // 4. 本物のメッセージバブルを作成して表示
    const bubble = addMessageToUI('assistant', '');
    const resTxtElement = bubble.querySelector('.res-txt');
    
    // 5. タイピング演出 ＋ 音声再生
    await runTypewriter(resTxtElement, data.response, data.voice_url);

    // 6. 🚀 アプリ起動信号があれば実行
    if (data.launch_url) {
        console.log("🚀 Launching app:", data.launch_url);
        window.location.href = data.launch_url;
    }
});