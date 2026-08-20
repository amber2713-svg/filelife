const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const demoBtn = document.getElementById('demo-btn');
const newChatBtn = document.getElementById('new-chat-btn');
const modeBadge = document.getElementById('mode-badge');
const modelEl = document.getElementById('model-name');
const apiStatusEl = document.getElementById('api-status');
const agentStatusEl = document.getElementById('agent-status');
const toolItems = document.querySelectorAll('.tool-item');

let sessionId = null;
let isGenerating = false;

// --- Sanitize & Markdown ---
const ALLOWED_TAGS = new Set([
    'p','br','h1','h2','h3','h4','strong','em','b','i',
    'ul','ol','li','table','thead','tbody','tr','th','td',
    'pre','code','blockquote','hr','a','div','span',
]);
const ALLOWED_ATTRS = new Set(['href','class']);

function sanitize(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    function clean(node) {
        for (const child of [...node.childNodes]) {
            if (child.nodeType === Node.ELEMENT_NODE) {
                const tag = child.tagName.toLowerCase();
                if (!ALLOWED_TAGS.has(tag)) { child.remove(); continue; }
                for (const attr of [...child.attributes]) {
                    if (attr.name.startsWith('on')) { child.removeAttribute(attr.name); continue; }
                    if (!ALLOWED_ATTRS.has(attr.name)) { child.removeAttribute(attr.name); continue; }
                    if (attr.name === 'href' && attr.value.trim().toLowerCase().startsWith('javascript:')) {
                        child.removeAttribute(attr.name);
                    }
                }
                clean(child);
            }
        }
    }
    clean(doc.body);
    return doc.body.innerHTML;
}

function md(text) {
    if (!text) return '';
    let h = text;
    h = h.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
    h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');
    h = h.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
    h = h.replace(/^---$/gm, '<hr>');
    h = h.replace(/^- (.+)$/gm, '<li>$1</li>');
    h = h.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    h = h.replace(/\n\n/g, '</p><p>');
    h = h.replace(/\n/g, '<br>');
    if (!h.startsWith('<')) h = '<p>' + h + '</p>';
    return h;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- UI Helpers ---
function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    const avatar = role === 'user' ? 'U' : 'A';
    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-body">
            <div class="message-content">${role === 'user' ? escapeHtml(content) : sanitize(md(content))}</div>
        </div>
    `;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
}

function createStepsContainer() {
    const div = document.createElement('div');
    div.className = 'agent-steps';
    div.id = 'current-steps';
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
}

function addStep(container, step) {
    const div = document.createElement('div');

    if (step.type === 'thought') {
        div.className = 'step step-thought';
        div.innerHTML = `<span class="step-icon"></span><div class="step-content">${escapeHtml(step.content)}</div>`;
    } else if (step.type === 'tool_call') {
        div.className = 'step step-tool-call';
        div.innerHTML = `
            <span class="step-icon"></span>
            <div class="step-content">
                <div>调用工具: <span class="step-tool-name">${escapeHtml(step.tool_name)}</span></div>
                <div class="step-tool-args">${escapeHtml(step.tool_args)}</div>
            </div>`;
        // Highlight tool in sidebar
        toolItems.forEach(el => {
            el.classList.toggle('active', el.textContent === step.tool_name);
        });
    } else if (step.type === 'tool_result') {
        div.className = 'step step-tool-result';
        const preview = step.content.length > 200 ? step.content.slice(0, 200) + '...' : step.content;
        div.innerHTML = `<span class="step-icon"></span><div class="step-content">${escapeHtml(preview)}</div>`;
    }

    container.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addThinkingIndicator() {
    const div = document.createElement('div');
    div.className = 'agent-thinking';
    div.id = 'thinking-indicator';
    const spinner = document.createElement('div');
    spinner.className = 'spinner';
    const span = document.createElement('span');
    span.textContent = 'Agent 思考中...';
    div.appendChild(spinner);
    div.appendChild(span);
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function removeThinkingIndicator() {
    const el = document.getElementById('thinking-indicator');
    if (el) el.remove();
}

function setInputEnabled(enabled) {
    isGenerating = !enabled;
    inputEl.disabled = !enabled;
    sendBtn.disabled = !enabled;
    agentStatusEl.textContent = enabled ? '空闲' : '运行中';
    if (enabled) {
        inputEl.focus();
        toolItems.forEach(el => el.classList.remove('active'));
    }
}

// --- Core Logic ---
async function sendMessage(text) {
    if (!text.trim() || isGenerating) return;

    addMessage('user', text);
    inputEl.value = '';
    inputEl.style.height = 'auto';
    setInputEnabled(false);

    const stepsContainer = createStepsContainer();
    addThinkingIndicator();

    try {
        const resp = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, session_id: sessionId }),
        });

        const data = await resp.json();
        removeThinkingIndicator();

        if (data.error) {
            addMessage('assistant', `错误: ${data.error}`);
        } else {
            sessionId = data.session_id;

            // Show thinking steps
            if (data.steps) {
                for (const step of data.steps) {
                    if (step.type !== 'content') {
                        addStep(stepsContainer, step);
                    }
                }
            }

            // Show final content
            addMessage('assistant', data.content);
        }
    } catch (err) {
        removeThinkingIndicator();
        addMessage('assistant', `请求失败: ${err.message}。请确认服务正在运行。`);
    }

    setInputEnabled(true);
}

// --- Event Listeners ---
sendBtn.addEventListener('click', () => sendMessage(inputEl.value));

inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(inputEl.value);
    }
});

inputEl.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
});

demoBtn.addEventListener('click', async () => {
    if (isGenerating) return;
    setInputEnabled(false);
    demoBtn.textContent = '生成中...';

    const stepsContainer = createStepsContainer();
    addThinkingIndicator();

    try {
        const resp = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: "我是中科大计算机科学与技术专业大三上的学生，绩点3.7/4.0，专业排名前15%，六级550分，有一篇CCF-B会议的在投论文，参加过ACM-ICPC区域赛获铜奖。目标院校是清华、北大、中科院计算所的计算机相关专业。请帮我制定一份详细的保研攻略。",
                session_id: sessionId,
            }),
        });

        const data = await resp.json();
        removeThinkingIndicator();

        if (!data.error) {
            sessionId = data.session_id;
            addMessage('user', data.input || "演示输入");
            if (data.steps) {
                for (const step of data.steps) {
                    if (step.type !== 'content') {
                        addStep(stepsContainer, step);
                    }
                }
            }
            addMessage('assistant', data.content);
        } else {
            addMessage('assistant', `演示失败: ${data.error}`);
        }
    } catch (err) {
        removeThinkingIndicator();
        addMessage('assistant', `演示失败: ${err.message}`);
    }

    demoBtn.textContent = '一键演示';
    setInputEnabled(true);
});

newChatBtn.addEventListener('click', () => {
    sessionId = null;
    messagesEl.innerHTML = '';
    addMessage('assistant',
        '新对话已开始！我是保研Agent，会通过自主搜索和分析为你生成保研攻略。\n\n请告诉我你的情况，或直接点击"一键演示"。'
    );
});

document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const input = btn.dataset.input;
        if (input) sendMessage(input);
    });
});

// --- Init ---
(async () => {
    try {
        const resp = await fetch('/api/config');
        const cfg = await resp.json();
        modelEl.textContent = cfg.llm_model;
        if (cfg.has_api_key) {
            modeBadge.textContent = 'API模式';
            modeBadge.classList.add('active');
            apiStatusEl.textContent = '已连接';
            apiStatusEl.classList.add('online');
            apiStatusEl.classList.remove('offline');
        } else {
            modeBadge.textContent = 'Mock模式';
            apiStatusEl.textContent = 'Mock';
        }
    } catch (e) {
        console.warn('Failed to load config:', e);
    }
})();
