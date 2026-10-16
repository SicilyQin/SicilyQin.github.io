# -*- coding: utf-8 -*-
"""
生成“重写版”内页（博客 / 云盘 / 满屏漂浮爱心），替代原来那几个打不开的第三方网址。
每页都是自包含的：只依赖本地文件和同目录的 style.css，不引用任何外部 CDN，离线可用。

跑法：
    python _tools/make_pages.py
产出：
    pages/style.css
    pages/blog.html        （博客：搜索 + 标签筛选 + 文章卡）
    pages/post-1..5.html   （文章详情，含“返回列表 / 返回主页”）
    pages/drive.html       （云盘：搜索 + 分类 + 收藏 + 可编辑文件清单）
    pages/hearts.html      （满屏漂浮爱心：canvas 粒子 + 输入文字）
    其他页面/文本/爱心.html （旧路径的入口页，自动跳到 pages/hearts.html）
"""
import os
import json
import struct
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = os.path.join(ROOT, 'pages')
os.makedirs(PAGES, exist_ok=True)

BACK_HOME = '../index.html'

CSS = r"""
:root {
  --bg-1: #0b1026;
  --bg-2: #131a3a;
  --card: rgba(255, 255, 255, 0.06);
  --card-hover: rgba(255, 255, 255, 0.12);
  --line: rgba(255, 255, 255, 0.12);
  --text: #eaf0ff;
  --text-dim: #9fb0d0;
  --accent: #6ea8ff;
  --accent-2: #b57bff;
}
[data-theme="Light"] {
  --bg-1: #eef3ff;
  --bg-2: #dfe8ff;
  --card: rgba(255, 255, 255, 0.72);
  --card-hover: rgba(255, 255, 255, 0.95);
  --line: rgba(20, 40, 90, 0.12);
  --text: #14203a;
  --text-dim: #5b6b8c;
  --accent: #2f6bff;
  --accent-2: #8a3ffc;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", system-ui, sans-serif;
  color: var(--text);
  background:
    radial-gradient(1200px 600px at 12% -10%, rgba(110, 168, 255, 0.35), transparent 60%),
    radial-gradient(900px 500px at 88% 0%, rgba(181, 123, 255, 0.30), transparent 55%),
    linear-gradient(160deg, var(--bg-1), var(--bg-2));
  min-height: 100vh;
  transition: background 0.4s ease, color 0.4s ease;
}
a { color: inherit; text-decoration: none; }

.wrap { max-width: 1080px; margin: 0 auto; padding: 28px 20px 64px; }

.topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 26px;
}
.back, .theme-btn, .chip {
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--text);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 14px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: background 0.25s ease, transform 0.15s ease;
}
.back:hover, .theme-btn:hover, .chip:hover { background: var(--card-hover); }
.back:active, .theme-btn:active, .chip:active { transform: scale(0.96); }
.chip.active { border-color: var(--accent); color: var(--accent); }
.spacer { flex: 1; }

h1.title {
  font-size: 30px;
  margin: 0 0 6px;
  font-weight: 700;
  background: linear-gradient(120deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  display: inline-block;
}
.subtitle { color: var(--text-dim); font-size: 14px; margin: 0 0 22px; }

.search-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.search-row input[type="search"], .search-row input[type="text"] {
  flex: 1;
  min-width: 220px;
  padding: 11px 16px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--card);
  color: var(--text);
  font-size: 14px;
  outline: none;
}
.search-row input::placeholder { color: var(--text-dim); }
.search-row input:focus { border-color: var(--accent); }

.grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }

.card {
  display: block;
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 16px;
  padding: 18px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition: transform 0.2s ease, background 0.25s ease, box-shadow 0.25s ease;
  animation: rise 0.45s ease both;
}
.card:hover {
  transform: translateY(-3px);
  background: var(--card-hover);
  box-shadow: 0 14px 34px -18px rgba(0, 0, 0, 0.75);
}
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
.card h2 { font-size: 18px; margin: 0 0 8px; font-weight: 600; }
.card p { margin: 0; color: var(--text-dim); font-size: 13px; line-height: 1.7; }
.meta { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; font-size: 12px; color: var(--text-dim); }
.tag { border: 1px solid var(--line); border-radius: 999px; padding: 2px 10px; }

.article { border: 1px solid var(--line); background: var(--card); border-radius: 18px; padding: 28px; }
.article h2 { margin: 26px 0 10px; font-size: 20px; }
.article p, .article li { line-height: 1.95; color: var(--text); font-size: 15px; }
.article code {
  background: rgba(127, 127, 127, 0.18);
  padding: 2px 6px;
  border-radius: 6px;
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
}
.article pre {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px;
  overflow: auto;
}
.article pre code { background: none; padding: 0; }
.empty { color: var(--text-dim); padding: 40px 0; text-align: center; }

/* 云盘 */
.file-row {
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid var(--line);
  background: var(--card);
  border-radius: 14px;
  padding: 14px 16px;
  transition: background 0.2s ease, transform 0.15s ease;
}
.file-row:hover { background: var(--card-hover); transform: translateX(2px); }
.file-icon { font-size: 22px; width: 30px; text-align: center; }
.file-main { flex: 1; min-width: 0; }
.file-name { font-size: 15px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-sub { display: block; font-size: 12px; color: var(--text-dim); margin-top: 4px; }
.file-size { font-size: 12px; color: var(--text-dim); white-space: nowrap; }
.star { font-size: 18px; cursor: pointer; background: none; border: none; color: var(--text-dim); }
.star.on { color: #ffcf5c; }
.list { display: grid; gap: 10px; }
.storage-tip {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 14px 16px;
  color: var(--text-dim);
  font-size: 13px;
  line-height: 1.8;
  margin-top: 22px;
}
.storage-tip code { color: var(--accent); }

/* 关于我 / 留言板 / 打字机 / 画板 共用补充样式 */
.about-head { display: flex; gap: 18px; align-items: center; flex-wrap: wrap; margin-bottom: 20px; }
.about-avatar { width: 92px; height: 92px; border-radius: 50%; object-fit: cover; border: 2px solid var(--line); }
.kv { display: grid; gap: 8px; margin: 14px 0 0; }
.kv div { font-size: 14px; color: var(--text-dim); }
.kv b { color: var(--text); font-weight: 600; margin-right: 6px; }
.chip-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 14px 0 0; }
textarea {
  width: 100%; min-height: 96px; resize: vertical; padding: 12px 14px;
  border-radius: 12px; border: 1px solid var(--line); background: var(--card);
  color: var(--text); font-size: 14px; font-family: inherit; outline: none;
}
textarea:focus { border-color: var(--accent); }
.msg { border: 1px solid var(--line); background: var(--card); border-radius: 12px; padding: 14px 16px; }
.msg .who { font-size: 13px; font-weight: 600; }
.msg .when { font-size: 12px; color: var(--text-dim); margin-left: 8px; }
.msg .what { font-size: 14px; line-height: 1.8; margin-top: 6px; white-space: pre-wrap; word-break: break-word; }
.tw-stage {
  border: 1px solid var(--line); background: var(--card); border-radius: 18px;
  padding: 40px 28px; min-height: 240px; display: flex; align-items: center;
  font-size: 26px; line-height: 1.7; letter-spacing: 1px;
}
.tw-caret { display: inline-block; width: 12px; margin-left: 2px; background: var(--accent); animation: blink 1s steps(1) infinite; }
@keyframes blink { 50% { opacity: 0; } }
input[type="range"] { width: 160px; }
canvas.board { width: 100%; height: 460px; border: 1px solid var(--line); border-radius: 14px; background: #fff; touch-action: none; }
.swatch { width: 26px; height: 26px; border-radius: 50%; border: 2px solid var(--line); cursor: pointer; }
.swatch.on { border-color: var(--accent); transform: scale(1.12); }
"""

# ---------------------------------------------------------------- 文章数据
POSTS = [
    {
        'slug': 'post-1',
        'title': '把首页那堆坏链修完了',
        'date': '2026-08-19',
        'tags': ['网站', '折腾'],
        'excerpt': '四个卡片终于全都点得动：实验室和图片墙换成站内页面，博客和云盘这两个原本指着别人域名的卡，现在有了自己的落地页。',
        'body': [
            ('h', '坏在哪'),
            ('p', '原来的首页上，四个卡片有三个是坏的：实验室那张写的是本机绝对路径 <code>D:\\cyy\\code\\html\\...</code>，另一张只写了裸域名 <code>SicilyQin.github.io</code>（浏览器会当成相对路径），博客和云盘则指向原模板作者 zyyo 的域名。'),
            ('h', '怎么修的'),
            ('ul', [
                '实验室 → 站内 <code>其他页面/文本/文本/Font effect.html</code>，并且把原来跳 <code>D:/cyy/...</code> 的返回逻辑改成跳首页。',
                '图片墙 → 站内图片页，9 张图原来全是 <code>D:\\素材\\图片\\...</code>，现在换成本地生成的渐变壁纸。',
                '博客 / 云盘 → 不再指向别人的站，换成自己写的两个落地页。',
            ]),
            ('h', '顺手做的事'),
            ('p', 'LOGO 背景、手机端二维码这类写死的 <code>/homepage/homepage-main/xxx</code> 路径全改成了相对路径；不存在的 <code>index.scss</code> 引用删了；GitHub 图标原来指向一个 404 的账号地址，也改对了。'),
        ],
    },
    {
        'slug': 'post-2',
        'title': '给图片墙配了 9 张占位壁纸',
        'date': '2026-08-18',
        'tags': ['CSS', '图片'],
        'excerpt': '真图还在 D 盘那个读不到的文件夹里，先用脚本生成的渐变壁纸把版面撑起来，现在照片墙已经支持直接塞自己的照片了。',
        'body': [
            ('h', '为什么不用别人现成的图'),
            ('p', '图片墙是个横向视差滚动，9 个格子空一格就很明显，所以先让它有东西可看。占位图用脚本生成成 1600×1000 的 SVG，每张配色不同，风格统一。'),
            ('h', '加自己的照片'),
            ('p', '把照片放进一个文件夹，然后：'),
            ('code', 'python _tools/use_my_wallpapers.py "D:\\素材\\图片"'),
            ('p', '脚本会把图按文件名排序复制成 <code>static/img/gallery/photo-01.jpg</code>、<code>photo-02.jpg</code>…（接着已有编号往后排，不会覆盖），然后自动重跑生成器，让「图片墙」和「云盘」清单一起更新。'),
            ('p', '想清空重来就 <code>python _tools/use_my_wallpapers.py --reset</code>，只剩占位壁纸。'),
        ],
    },
    {
        'slug': 'post-3',
        'title': '满屏漂浮爱心，用 canvas 重写了一遍',
        'date': '2026-08-17',
        'tags': ['JavaScript', 'canvas'],
        'excerpt': '原来看的那个爱心页打不开了，于是自己写了一个：文字采样成粒子、往上升、带光晕和拖尾，输入什么字就飘什么字。',
        'body': [
            ('h', '思路'),
            ('p', '在一个离屏 canvas 上把文字画出来，逐像素采样出“有字”的坐标，这些坐标就是粒子要去的目标点；每帧让粒子带着阻尼靠向目标，再叠加一点随机横向摆动和上升位移，看起来就是飘起来的爱心。'),
            ('h', '几个细节'),
            ('ul', [
                '按 devicePixelRatio 缩放，高分屏不糊。',
                '粒子颜色从粉色渐变到紫色，透明度随机，做出景深。',
                '文字太长会提示，避免采样点太多把帧率拖死。',
            ]),
            ('p', '页面在这里：<code>pages/hearts.html</code>，输入框里换文字试试。'),
        ],
    },
    {
        'slug': 'post-4',
        'title': '云盘页到底要不要“真”上传',
        'date': '2026-08-16',
        'tags': ['网站', '计划'],
        'excerpt': '静态站没有后端，上传是没法凭空变出来的。先把清单和检索做扎实，真要传文件再挂后端。',
        'body': [
            ('h', '现状'),
            ('p', '这个站是纯静态的 GitHub Pages，浏览器里<strong>不能</strong>直接往仓库写文件——那需要服务端凭证。所以现在的云盘页是一个“文件清单 + 搜索 + 收藏”，清单存在一个 JSON 里，改起来就是改文本。'),
            ('h', '想要真上传的话'),
            ('ul', [
                '接一个第三方对象存储（图床 / S3 兼容），前端直传，清单记下外链。',
                '或者干脆用 GitHub Releases 挂文件，页面里贴下载链接。',
                '再或者把清单交给一个 Serverless 函数来管。',
            ]),
            ('p', '这三条哪条都行，看你更想省事还是更想自己掌控。'),
        ],
    },
    {
        'slug': 'post-5',
        'title': '关于这个站的一点记录',
        'date': '2026-01-05',
        'tags': ['随笔'],
        'excerpt': '模板是别人的，内容得是自己的。慢慢把边上那些不属于本站的东西摘干净。',
        'body': [
            ('h', '它从哪来'),
            ('p', '这个页面是照着网上的一个个人主页模板改的，左侧信息卡 + 中间卡片区，配色和动效都挺舒服。模板自带了一些指向作者自己站点的链接，一开始没在意，后来发现那些域名有的已经打不开了。'),
            ('h', '打算怎么弄'),
            ('ul', [
                '所有点得动的卡片，要么指向本站的真实页面，要么干脆不跳转，不放死链。',
                '别人的资源（CDN、统计脚本、歌单）能用就留着，用不了就换成本地的。',
                '内容自己写，写不动就少写点，反正这站主要是给自己看的。',
            ]),
        ],
    },
]


def render_post(p):
    parts = []
    for kind, value in p['body']:
        if kind == 'h':
            parts.append('<h2>%s</h2>' % value)
        elif kind == 'p':
            parts.append('<p>%s</p>' % value)
        elif kind == 'code':
            parts.append('<pre><code>%s</code></pre>' % value.replace('<', '&lt;').replace('>', '&gt;'))
        elif kind == 'ul':
            parts.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % i for i in value))
    body = '\n'.join(parts)
    tags = ''.join('<span class="tag">%s</span>' % t for t in p['tags'])
    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="Dark">
<head>
<meta charset="UTF-8">
<title>%(title)s · 博客</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css">
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <a class="back" href="./blog.html">&larr; 返回列表</a>
    <a class="back" href="%(home)s">返回主页</a>
    <div class="spacer"></div>
    <button class="theme-btn" id="themeBtn" type="button">切换主题</button>
  </div>
  <div class="article">
    <h1 class="title">%(title)s</h1>
    <p class="subtitle">%(date)s · %(tags)s</p>
    %(body)s
  </div>
</div>
<script>
(function () {
  var KEY = 'sq-theme';
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) { root.dataset.theme = saved; }
  var btn = document.getElementById('themeBtn');
  btn.addEventListener('click', function () {
    var next = root.dataset.theme === 'Light' ? 'Dark' : 'Light';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });
})();
</script>
</body>
</html>
""" % {
        'title': p['title'],
        'date': p['date'],
        'tags': tags,
        'body': body,
        'home': BACK_HOME,
    }


POSTS_JSON = json.dumps(
    [
        {
            'slug': p['slug'],
            'title': p['title'],
            'date': p['date'],
            'tags': p['tags'],
            'excerpt': p['excerpt'],
        }
        for p in POSTS
    ],
    ensure_ascii=False,
    indent=2,
)

BLOG_HTML = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="Dark">
<head>
<meta charset="UTF-8">
<title>博客 · SicilyQin</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css">
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <a class="back" href="%(home)s">&larr; 返回主页</a>
    <a class="back" href="./drive.html">云盘</a>
    <div class="spacer"></div>
    <button class="theme-btn" id="themeBtn" type="button">切换主题</button>
  </div>

  <h1 class="title">博客</h1>
  <p class="subtitle">记录摆烂日常 · 共 <span id="count">0</span> 篇</p>

  <div class="search-row">
    <input id="q" type="search" placeholder="搜索标题、摘要、标签…">
  </div>
  <div class="search-row" id="tagRow"></div>

  <div class="grid" id="list"></div>
  <div class="empty" id="empty" style="display:none">没有匹配的文章</div>

  <div class="storage-tip">
    这些文章都是页面自带的静态数据（<code>pages/blog.html</code> 里那段 <code>POSTS</code>），想加文章就复制一条改字段，不用任何后端。详情页放在 <code>pages/post-N.html</code>。
  </div>
</div>

<script>
var POSTS = %(posts_json)s;

(function () {
  var KEY = 'sq-theme';
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) { root.dataset.theme = saved; }
  document.getElementById('themeBtn').addEventListener('click', function () {
    var next = root.dataset.theme === 'Light' ? 'Dark' : 'Light';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });

  var listEl = document.getElementById('list');
  var emptyEl = document.getElementById('empty');
  var qEl = document.getElementById('q');
  var tagRow = document.getElementById('tagRow');
  var activeTag = '';

  var tags = [];
  POSTS.forEach(function (p) {
    p.tags.forEach(function (t) { if (tags.indexOf(t) < 0) tags.push(t); });
  });

  var allBtn = document.createElement('button');
  allBtn.className = 'chip active';
  allBtn.type = 'button';
  allBtn.textContent = '全部';
  allBtn.addEventListener('click', function () { activeTag = ''; syncChips(); render(); });
  tagRow.appendChild(allBtn);

  tags.forEach(function (t) {
    var b = document.createElement('button');
    b.className = 'chip';
    b.type = 'button';
    b.textContent = t;
    b.dataset.tag = t;
    b.addEventListener('click', function () { activeTag = (activeTag === t ? '' : t); syncChips(); render(); });
    tagRow.appendChild(b);
  });

  function syncChips() {
    [].forEach.call(tagRow.querySelectorAll('.chip'), function (c) {
      var t = c.dataset.tag || '';
      c.classList.toggle('active', t === activeTag);
    });
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function render() {
    var q = qEl.value.trim().toLowerCase();
    var shown = POSTS.filter(function (p) {
      if (activeTag && p.tags.indexOf(activeTag) < 0) return false;
      if (!q) return true;
      var hay = (p.title + ' ' + p.excerpt + ' ' + p.tags.join(' ')).toLowerCase();
      return hay.indexOf(q) >= 0;
    });

    listEl.innerHTML = shown.map(function (p, i) {
      return '<a class="card" href="./' + p.slug + '.html" style="animation-delay:' + (i * 40) + 'ms">' +
        '<h2>' + esc(p.title) + '</h2>' +
        '<p>' + esc(p.excerpt) + '</p>' +
        '<div class="meta"><span>' + esc(p.date) + '</span>' +
        p.tags.map(function (t) { return '<span class="tag">' + esc(t) + '</span>'; }).join('') +
        '</div></a>';
    }).join('');

    document.getElementById('count').textContent = String(shown.length);
    emptyEl.style.display = shown.length ? 'none' : 'block';
  }

  qEl.addEventListener('input', render);
  render();
})();
</script>
</body>
</html>
""" % {'posts_json': POSTS_JSON, 'home': BACK_HOME}

# ---------------------------------------------------------------- 云盘页
def _img_size(path):
    """读图片文件头拿宽高，不依赖 Pillow。读不出来就返回 (0, 0)。"""
    try:
        with open(path, 'rb') as f:
            head = f.read(32)
            if head[:2] == b'\xff\xd8':          # JPEG
                f.seek(2)
                while True:
                    b = f.read(1)
                    while b and b != b'\xff':
                        b = f.read(1)
                    marker = f.read(1)
                    while marker == b'\xff':
                        marker = f.read(1)
                    if not marker:
                        return 0, 0
                    m = marker[0]
                    if m in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf):
                        f.read(3)
                        h, w = struct.unpack('>HH', f.read(4))
                        return w, h
                    seg = f.read(2)
                    if len(seg) < 2:
                        return 0, 0
                    f.seek(struct.unpack('>H', seg)[0] - 2, 1)
            elif head[:8] == b'\x89PNG\r\n\x1a\n':   # PNG
                w, h = struct.unpack('>II', head[16:24])
                return w, h
            elif head[:3] == b'GIF':                 # GIF
                w, h = struct.unpack('<HH', head[6:10])
                return w, h
            elif head[:4] == b'RIFF' and head[8:12] == b'WEBP':
                fmt = head[12:16]
                if fmt == b'VP8X':
                    w = 1 + (head[24] | head[25] << 8 | head[26] << 16)
                    h = 1 + (head[27] | head[28] << 8 | head[29] << 16)
                    return w, h
                if fmt == b'VP8 ':
                    w = struct.unpack('<H', head[26:28])[0] & 0x3fff
                    h = struct.unpack('<H', head[28:30])[0] & 0x3fff
                    return w, h
                if fmt == b'VP8L':
                    bits = head[21] | head[22] << 8 | head[23] << 16 | head[24] << 24
                    return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
    except Exception:
        pass
    return 0, 0


def gallery_files():
    """扫描 static/img/gallery/，给「图片墙」和「云盘」生成条目。
    自己的照片（photo-*.jpg 等）排在前头，占位壁纸 wall-*.svg 排后面。"""
    gdir = os.path.join(ROOT, 'static', 'img', 'gallery')
    exts = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg', '.bmp')
    names = []
    if os.path.isdir(gdir):
        for n in sorted(os.listdir(gdir)):
            if os.path.isfile(os.path.join(gdir, n)) and n.lower().endswith(exts):
                names.append(n)
    photos = [n for n in names if not n.lower().startswith('wall-')]
    walls = [n for n in names if n.lower().startswith('wall-')]
    out = []
    for n in photos + walls:
        path = os.path.join(gdir, n)
        w, h = _img_size(path)
        kb = os.path.getsize(path) / 1024.0
        out.append({
            'name': n,
            'url': '../../static/img/gallery/' + n,
            'drive_url': '../static/img/gallery/' + n,
            'size': ('%d×%d' % (w, h)) if w and h else ('%.0f KB' % kb),
            'kb': '%.0f KB' % kb,
            'date': time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(path))),
            'tag': '占位壁纸' if n.lower().startswith('wall-') else '我的照片',
        })
    return out


GALLERY_ITEMS = gallery_files()

DRIVE_FILES = (
    [{'name': g['name'], 'url': g['drive_url'], 'size': g['size'], 'date': g['date'],
      'kind': '图片', 'tag': g['tag']} for g in GALLERY_ITEMS]
    + [
        {'name': '图片墙.html', 'url': '../其他页面/博客/图片.html', 'size': '网页', 'date': '2026-08-18', 'kind': '网页', 'tag': '横向视差图集'},
        {'name': 'Font effect.html', 'url': '../其他页面/文本/文本/Font effect.html', 'size': '网页', 'date': '2026-01-05', 'kind': '网页', 'tag': '字体特效'},
        {'name': '满屏漂浮爱心.html', 'url': './hearts.html', 'size': '网页', 'date': '2026-08-19', 'kind': '网页', 'tag': 'canvas 特效'},
        {'name': '头像.jpg', 'url': '../头像.jpg', 'size': '948×948', 'date': '2026-01-05', 'kind': '图片', 'tag': '站内素材'},
        {'name': 'paycode.png', 'url': '../paycode.png', 'size': '142 KB', 'date': '2026-01-05', 'kind': '图片', 'tag': '站内素材'},
        {'name': 'qq.png', 'url': '../qq.png', 'size': '256 KB', 'date': '2026-01-05', 'kind': '图片', 'tag': '站内素材'},
    ]
)

DRIVE_JSON = json.dumps(DRIVE_FILES, ensure_ascii=False, indent=2)

DRIVE_HTML = """<!DOCTYPE html>
<html lang="zh-CN" data-theme="Dark">
<head>
<meta charset="UTF-8">
<title>云盘 · SicilyQin</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css">
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <a class="back" href="%(home)s">&larr; 返回主页</a>
    <a class="back" href="./blog.html">博客</a>
    <div class="spacer"></div>
    <button class="theme-btn" id="themeBtn" type="button">切换主题</button>
  </div>

  <h1 class="title">云盘</h1>
  <p class="subtitle">存储收集文件 · <span id="count">0</span> 项 · 收藏只存在你自己的浏览器里</p>

  <div class="search-row">
    <input id="q" type="search" placeholder="搜索文件名、标签…">
  </div>
  <div class="search-row" id="kindRow"></div>

  <div class="list" id="list"></div>
  <div class="empty" id="empty" style="display:none">没有匹配的文件</div>

  <div class="storage-tip">
    <strong>怎么加文件：</strong>打开 <code>pages/drive.html</code>，最下面的 <code>FILES</code> 数组里照着已有的一条复制、改 <code>name</code> / <code>url</code> / <code>size</code> 就行。
    线上的图片和文件放在仓库里，用相对路径引用即可。<br>
    <strong>关于真上传：</strong>纯静态站没法直接写入文件，要真上传得挂一个对象存储（图床 / S3 兼容）或 GitHub Releases，页面里放外链。要接哪种说一声。
  </div>
</div>

<script>
var FILES = %(files_json)s;

(function () {
  var KEY = 'sq-theme';
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) { root.dataset.theme = saved; }
  document.getElementById('themeBtn').addEventListener('click', function () {
    var next = root.dataset.theme === 'Light' ? 'Dark' : 'Light';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });

  var STAR_KEY = 'sq-drive-stars';
  var stars = [];
  try { stars = JSON.parse(localStorage.getItem(STAR_KEY) || '[]'); } catch (e) { stars = []; }
  function saveStars() { try { localStorage.setItem(STAR_KEY, JSON.stringify(stars)); } catch (e) {} }

  var listEl = document.getElementById('list');
  var emptyEl = document.getElementById('empty');
  var qEl = document.getElementById('q');
  var kindRow = document.getElementById('kindRow');
  var activeKind = '';

  var kinds = [];
  FILES.forEach(function (f) { if (kinds.indexOf(f.kind) < 0) kinds.push(f.kind); });

  var allBtn = document.createElement('button');
  allBtn.className = 'chip active';
  allBtn.type = 'button';
  allBtn.textContent = '全部';
  allBtn.addEventListener('click', function () { activeKind = ''; syncChips(); render(); });
  kindRow.appendChild(allBtn);

  kinds.forEach(function (k) {
    var b = document.createElement('button');
    b.className = 'chip';
    b.type = 'button';
    b.textContent = k;
    b.dataset.kind = k;
    b.addEventListener('click', function () { activeKind = (activeKind === k ? '' : k); syncChips(); render(); });
    kindRow.appendChild(b);
  });

  function syncChips() {
    [].forEach.call(kindRow.querySelectorAll('.chip'), function (c) {
      c.classList.toggle('active', (c.dataset.kind || '') === activeKind);
    });
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function iconOf(f) {
    if (f.kind === '图片') return '\\uD83D\\uDDBC\\uFE0F';
    if (f.kind === '网页') return '\\uD83C\\uDF10';
    return '\\uD83D\\uDCC4';
  }

  function render() {
    var q = qEl.value.trim().toLowerCase();
    var shown = FILES.filter(function (f) {
      if (activeKind && f.kind !== activeKind) return false;
      if (!q) return true;
      return (f.name + ' ' + f.tag + ' ' + f.kind).toLowerCase().indexOf(q) >= 0;
    });

    listEl.innerHTML = shown.map(function (f, i) {
      var starOn = stars.indexOf(f.name) >= 0 ? ' on' : '';
      return '<div class="file-row" style="animation:rise .4s ease both;animation-delay:' + (i * 30) + 'ms">' +
        '<span class="file-icon">' + iconOf(f) + '</span>' +
        '<span class="file-main">' +
          '<a class="file-name" href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.name) + '</a>' +
          '<span class="file-sub">' + esc(f.kind) + ' · ' + esc(f.tag) + ' · ' + esc(f.date) + '</span>' +
        '</span>' +
        '<span class="file-size">' + esc(f.size) + '</span>' +
        '<button class="star' + starOn + '" type="button" title="收藏" data-name="' + esc(f.name) + '">\\u2605</button>' +
      '</div>';
    }).join('');

    document.getElementById('count').textContent = String(shown.length);
    emptyEl.style.display = shown.length ? 'none' : 'block';
  }

  listEl.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('.star') : null;
    if (!btn) return;
    e.preventDefault();
    var name = btn.getAttribute('data-name');
    var idx = stars.indexOf(name);
    if (idx >= 0) { stars.splice(idx, 1); btn.classList.remove('on'); }
    else { stars.push(name); btn.classList.add('on'); }
    saveStars();
  });

  qEl.addEventListener('input', render);
  render();
})();
</script>
</body>
</html>
""" % {'files_json': DRIVE_JSON, 'home': BACK_HOME}

# ---------------------------------------------------------------- 满屏漂浮爱心
HEARTS_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>满屏漂浮爱心</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #07060f; }
  canvas { display: block; width: 100vw; height: 100vh; }
  .ui {
    position: fixed; left: 0; right: 0; bottom: 26px;
    display: flex; gap: 10px; justify-content: center; align-items: center;
    flex-wrap: wrap; padding: 0 16px;
    font-family: "Microsoft YaHei", system-ui, sans-serif;
    z-index: 10;
  }
  .ui input {
    width: min(360px, 60vw);
    padding: 11px 16px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.25);
    background: rgba(255, 255, 255, 0.08);
    color: #ffe9f2;
    font-size: 15px;
    outline: none;
    backdrop-filter: blur(6px);
  }
  .ui input::placeholder { color: rgba(255, 255, 255, 0.45); }
  .ui button, .ui a {
    border: 1px solid rgba(255, 255, 255, 0.25);
    background: rgba(255, 255, 255, 0.08);
    color: #ffe9f2;
    border-radius: 999px;
    padding: 11px 20px;
    font-size: 15px;
    cursor: pointer;
    text-decoration: none;
    backdrop-filter: blur(6px);
  }
  .ui button:hover, .ui a:hover { background: rgba(255, 255, 255, 0.18); }
  .hint {
    position: fixed; top: 18px; left: 0; right: 0; text-align: center;
    color: rgba(255, 255, 255, 0.4); font-size: 13px;
    font-family: "Microsoft YaHei", system-ui, sans-serif;
    pointer-events: none;
  }
</style>
</head>
<body>
<canvas id="cv"></canvas>
<div class="hint">输入文字回车，粒子会重新拼成它；点画面也会落一撮心</div>
<div class="ui">
  <input id="txt" type="text" value="SicilyQin" maxlength="12" placeholder="输入 1-12 个字">
  <button id="go" type="button">飘起来</button>
  <a href="../index.html">返回主页</a>
</div>

<script>
(function () {
  var cv = document.getElementById('cv');
  var ctx = cv.getContext('2d');
  var W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);
  var particles = [];
  var hueBase = 330;
  var mouse = { x: -9999, y: -9999 };
  var time = 0;
  var lastFrame = 0;

  function resize() {
    W = window.innerWidth;
    H = window.innerHeight;
    cv.width = Math.floor(W * DPR);
    cv.height = Math.floor(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    build();
  }

  // 在离屏画布上画文字，逐像素采样出目标点
  function sampleText(text) {
    var off = document.createElement('canvas');
    off.width = W;
    off.height = H;
    var octx = off.getContext('2d');
    var size = Math.min(W / (text.length * 0.72 + 1.2), H * 0.32);
    size = Math.max(48, Math.min(size, 220));
    octx.fillStyle = '#fff';
    octx.textAlign = 'center';
    octx.textBaseline = 'middle';
    octx.font = '700 ' + size + 'px "Microsoft YaHei", "PingFang SC", system-ui, sans-serif';
    octx.fillText(text, W / 2, H / 2 - 20);

    var data = octx.getImageData(0, 0, off.width, off.height).data;
    // 采样间距按文字面积自适应：字数多就把间距放大，粒子总量稳定在 2500 左右
    var area = Math.max(W, H) * size * 1.6;
    var gap = Math.max(4, Math.round(Math.sqrt(area / 1400) * 0.5));
    var pts = [];
    for (var y = 0; y < off.height; y += gap) {
      for (var x = 0; x < off.width; x += gap) {
        if (data[(y * off.width + x) * 4 + 3] > 128) pts.push({ x: x, y: y });
      }
    }
    return pts;
  }

  function build() {
    var text = (document.getElementById('txt').value || 'SicilyQin').trim().slice(0, 12) || '爱心';
    var pts = sampleText(text);
    var next = [];

    for (var i = 0; i < pts.length; i++) {
      var target = pts[i];
      var old = particles[i];
      next.push({
        x: old ? old.x : Math.random() * W,
        y: old ? old.y : H + Math.random() * 200,
        tx: target.x,
        ty: target.y,
        baseY: target.y,
        vx: 0,
        vy: 0,
        r: 0.9 + Math.random() * 1.6,
        hue: hueBase + (target.x / W) * 70 - 35,
        alpha: 0.5 + Math.random() * 0.5,
        wob: Math.random() * Math.PI * 2,
        wobSpeed: 0.01 + Math.random() * 0.02
      });
    }
    particles = next;
  }

  function step() {
    lastFrame = Date.now();
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = 'rgba(7, 6, 15, 0.38)';
    ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'lighter';
    time += 1;
    var span = H + 160;
    var drift = time * 0.55;
    var offset = drift % span;

    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      p.wob += p.wobSpeed;

      // 目标点：整段文字作为整体慢慢上浮，飘出画面就从底部重新进入
      var ty = p.baseY - offset;
      while (ty < -140) ty += span;

      var dx = p.tx - p.x;
      var dy = ty - p.y;
      p.vx = (p.vx + dx * 0.07) * 0.82;
      p.vy = (p.vy + dy * 0.07) * 0.82;

      // 鼠标轻推
      var mx = p.x - mouse.x, my = p.y - mouse.y;
      var d2 = mx * mx + my * my;
      if (d2 < 10000 && d2 > 0.01) {
        var f = (1 - Math.sqrt(d2) / 100) * 2.2;
        p.vx += (mx / Math.sqrt(d2)) * f;
        p.vy += (my / Math.sqrt(d2)) * f;
      }

      p.x += p.vx + Math.sin(p.wob) * 0.4;
      p.y += p.vy;

      var grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
      grad.addColorStop(0, 'hsla(' + p.hue + ', 100%, 72%, ' + p.alpha + ')');
      grad.addColorStop(1, 'hsla(' + (p.hue + 18) + ', 100%, 60%, 0)');
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(step);
  }

  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', function (e) { mouse.x = e.clientX; mouse.y = e.clientY; });
  window.addEventListener('mouseout', function () { mouse.x = mouse.y = -9999; });

  document.getElementById('go').addEventListener('click', build);
  document.getElementById('txt').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') build();
  });

  function tick() {
    if (Date.now() - lastFrame > 40) step();
  }

  resize();
  step();
  // requestAnimationFrame 在标签页不处于前台时几乎不跑，用一个定时器兜底，保证动画始终在推进
  if (window.requestAnimationFrame) requestAnimationFrame(tick);
  setInterval(tick, 33);
})();
</script>
</body>
</html>
"""

# 旧路径的入口页：原来这里指向那个打不开的第三方爱心页
HEARTS_ENTRY = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>满屏漂浮爱心</title>
<meta http-equiv="refresh" content="0; url=../../../pages/hearts.html">
<script>location.replace('../../../pages/hearts.html');</script>
<style>
  body { margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;
         background: #07060f; color: #ffd7e6;
         font-family: "Microsoft YaHei", system-ui, sans-serif; }
  a { color: #ff9ec4; }
</style>
</head>
<body>
  <div>
    正在打开满屏漂浮爱心…
    没跳转的话点 <a href="../../../pages/hearts.html">这里</a>。
  </div>
</body>
</html>
"""


GALLERY_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>图片墙 · SicilyQin</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css">
<style>
  /* 返回主页按钮 */
  .back-home {
    position: fixed; top: 16px; left: 16px; z-index: 99;
    padding: 8px 16px; border-radius: 999px;
    background: rgba(0, 0, 0, 0.55); color: #fff; font-size: 14px;
    font-family: 'Hepta Slab', 'Microsoft YaHei', sans-serif;
    text-decoration: none; backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px);
    transition: background 0.3s ease;
  }
  .back-home:hover { background: rgba(0, 0, 0, 0.8); }
  .scroll-hint {
    position: fixed; right: 16px; bottom: 14px; z-index: 99;
    color: #55524e; font-size: 13px; font-family: 'Hepta Slab', 'Microsoft YaHei', sans-serif;
    background: rgba(255, 255, 255, 0.72); padding: 6px 12px; border-radius: 999px;
  }
  .img-wrapper { cursor: zoom-in; }
  .img-wrapper img { max-width: 52vh; max-height: 56vh; }
  /* 灯箱 */
  #lightbox {
    position: fixed; inset: 0; z-index: 200; display: none;
    align-items: center; justify-content: center;
    background: rgba(8, 8, 12, 0.9); padding: 4vh 4vw;
  }
  #lightbox.on { display: flex; }
  #lightbox img {
    max-width: 92vw; max-height: 82vh; width: auto; height: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
    background: #fff; padding: 10px;
  }
  #lightbox .lb-bar {
    position: absolute; bottom: 4vh; left: 50%; transform: translateX(-50%);
    color: #f2f2f2; font-size: 14px; font-family: 'Hepta Slab', 'Microsoft YaHei', sans-serif;
    background: rgba(0, 0, 0, 0.5); padding: 8px 16px; border-radius: 999px; white-space: nowrap;
  }
  #lightbox .lb-bar a { color: #8fd3ff; }
</style>
</head>
<body>

<a class="back-home" href="../../index.html">&larr; 返回主页</a>
<span class="scroll-hint">滚轮 / 拖动滚动 &nbsp;·&nbsp; 点图放大</span>

<div style="width:100%;">
  <div class="external" style="width:100%">
    <div class="horizontal-scroll-wrapper" id="strip"></div>
  </div>
</div>

<div id="lightbox">
  <img id="lb-img" src="" alt="">
  <div class="lb-bar"><span id="lb-name"></span> · <span id="lb-size"></span> &nbsp;|&nbsp; <a href="#" id="lb-open" target="_blank" rel="noopener">在新标签打开原图</a></div>
</div>

<script>
var ITEMS = __GALLERY_ITEMS__;

(function () {
  // 视差错位：和原来那 9 张手工排的节奏一样，图片多于 9 张就循环使用
  var STAGGER = ['slower', 'faster', 'slower vertical', 'slower slower-down', '',
                 'slower', 'faster1', 'slower slower2', '', 'faster', 'last'];

  var strip = document.getElementById('strip');
  strip.innerHTML = ITEMS.map(function (it, i) {
    return '<div class="img-wrapper ' + STAGGER[i % STAGGER.length] + '" data-i="' + i + '">' +
      '<a><img src="' + it.url + '" alt="' + it.name + '"></a></div>';
  }).join('');

  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lb-img');
  var lbName = document.getElementById('lb-name');
  var lbSize = document.getElementById('lb-size');

  strip.addEventListener('click', function (e) {
    var wrap = e.target.closest ? e.target.closest('.img-wrapper') : null;
    if (!wrap) return;
    e.preventDefault();
    var it = ITEMS[Number(wrap.dataset.i)];
    if (!it) return;
    lbImg.src = it.url;
    lbName.textContent = it.name;
    lbSize.textContent = it.size;
    document.getElementById('lb-open').href = it.url;
    lb.classList.add('on');
  });

  lb.addEventListener('click', function (e) {
    if (e.target === lbImg) return;   // 点图本身不关
    lb.classList.remove('on');
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') lb.classList.remove('on');
  });
})();
</script>
</body>
</html>
""".replace('__GALLERY_ITEMS__', json.dumps(
    [{'name': g['name'], 'url': g['url'], 'size': g['size']} for g in GALLERY_ITEMS],
    ensure_ascii=False, indent=2))


def redirect_page(title, target, message):
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>%(title)s</title>
<meta http-equiv="refresh" content="0; url=%(target)s">
<script>location.replace('%(target)s');</script>
<style>
  body { margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center;
         background: #0b1026; color: #cfe0ff;
         font-family: "Microsoft YaHei", system-ui, sans-serif; }
  a { color: #8ab4ff; }
</style>
</head>
<body>
  <div>%(message)s 没跳转的话点 <a href="%(target)s">这里</a>。</div>
</body>
</html>
""" % {'title': title, 'target': target, 'message': message}


def page(title, body, subtitle=''):
    """统一页壳：返回主页 + 主题切换 + 深浅色脚本"""
    sub = ('<p class="subtitle">%s</p>' % subtitle) if subtitle else ''
    return """<!DOCTYPE html>
<html lang="zh-CN" data-theme="Dark">
<head>
<meta charset="UTF-8">
<title>%(title)s · SicilyQin</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css">
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <a class="back" href="%(home)s">&larr; 返回主页</a>
    <a class="back" href="./blog.html">博客</a>
    <a class="back" href="./drive.html">云盘</a>
    <div class="spacer"></div>
    <button class="theme-btn" id="themeBtn" type="button">切换主题</button>
  </div>
%(sub)s
%(body)s
</div>
<script>
(function () {
  var KEY = 'sq-theme';
  var root = document.documentElement;
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  if (saved) { root.dataset.theme = saved; }
  var btn = document.getElementById('themeBtn');
  if (btn) btn.addEventListener('click', function () {
    var next = root.dataset.theme === 'Light' ? 'Dark' : 'Light';
    root.dataset.theme = next;
    try { localStorage.setItem(KEY, next); } catch (e) {}
  });
})();
</script>
%(extra)s
</body>
</html>
""" % {'title': title, 'body': body, 'sub': sub, 'home': BACK_HOME, 'extra': ''}


ABOUT_BODY = """  <h1 class="title">关于我</h1>
  <p class="subtitle">一个把课余时间都花在网页上的高三学生</p>

  <div class="article">
    <div class="about-head">
      <img class="about-avatar" src="../头像.jpg" alt="头像">
      <div>
        <div style="font-size:22px;font-weight:700;">SicilyQin</div>
        <div style="color:var(--text-dim);font-size:14px;margin-top:6px;">China-Henan · Sias · 出生 2007.3</div>
      </div>
    </div>

    <p>整天半吊子和不学无术的坏孩子，梦想成为庄稼地里的读书人。喜欢折腾网页，写点小东西放在<a href="./drive.html">云盘</a>和实验室里。</p>

    <h2>联系方式</h2>
    <div class="kv">
      <div><b>邮箱</b><a href="mailto:1451462630@qq.com">1451462630@qq.com</a></div>
      <div><b>GitHub</b><a href="https://github.com/SicilyQin/SicilyQin.github.io" target="_blank" rel="noopener">SicilyQin/SicilyQin.github.io</a></div>
    </div>

    <h2>在折腾什么</h2>
    <div class="chip-row">
      <span class="chip">网页</span><span class="chip">C</span><span class="chip">JavaScript</span>
      <span class="chip">Linux</span><span class="chip">音乐</span><span class="chip">琴</span>
    </div>

    <h2>时间线</h2>
    <div class="kv">
      <div><b>2024.1</b>正如彼梦会醒来一般，此梦也终有梦醒之时</div>
      <div><b>2007.3</b>出生</div>
    </div>

    <div class="storage-tip">这一页的内容都写在 <code>pages/about.html</code> 里，想改直接改文字。</div>
  </div>
"""

GUESTBOOK_BODY = """  <h1 class="title">留言板</h1>
  <p class="subtitle">想说什么就写点什么 · 共 <span id="count">0</span> 条</p>

  <div class="search-row">
    <input id="nick" type="text" placeholder="你的名字（可留空）" maxlength="20" style="max-width:220px">
  </div>
  <textarea id="text" placeholder="写点什么…（比如：这个站挺好看的）" maxlength="500"></textarea>
  <div class="search-row" style="margin-top:12px">
    <button class="chip active" id="send" type="button">发布留言</button>
    <button class="chip" id="clear" type="button">清空全部</button>
    <span id="tip" style="color:var(--text-dim);font-size:13px;align-self:center"></span>
  </div>

  <div class="list" id="list" style="margin-top:22px"></div>
  <div class="empty" id="empty">还没有留言，你可以第一个写</div>

  <div class="storage-tip">
    <strong>说明：</strong>这是纯静态站，没有后台，所以留言存在<strong>你自己浏览器的 localStorage</strong> 里（换设备或清缓存就没了）。
    想让所有人都能看见，得挂一个后端或第三方评论服务（比如 Giscus / Waline），要接的话说一声。
  </div>

<script>
(function () {
  var KEY = 'sq-guestbook';
  var listEl = document.getElementById('list');
  var emptyEl = document.getElementById('empty');
  var nickEl = document.getElementById('nick');
  var textEl = document.getElementById('text');
  var tipEl = document.getElementById('tip');

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { return []; }
  }
  function save(v) { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {} }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function fmt(ts) {
    var d = new Date(ts);
    function p(n) { return (n < 10 ? '0' : '') + n; }
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function render() {
    var msgs = load();
    document.getElementById('count').textContent = String(msgs.length);
    emptyEl.style.display = msgs.length ? 'none' : 'block';
    listEl.innerHTML = msgs.map(function (m) {
      return '<div class="msg"><span class="who">' + esc(m.nick || '匿名') + '</span>' +
        '<span class="when">' + fmt(m.ts) + '</span>' +
        '<div class="what">' + esc(m.text) + '</div></div>';
    }).join('');
  }

  document.getElementById('send').addEventListener('click', function () {
    var t = textEl.value.trim();
    if (!t) { tipEl.textContent = '先写点内容吧'; return; }
    var msgs = load();
    msgs.unshift({ nick: nickEl.value.trim() || '匿名', text: t, ts: Date.now() });
    save(msgs);
    textEl.value = '';
    tipEl.textContent = '已保存（存在你这台设备上）';
    render();
  });

  document.getElementById('clear').addEventListener('click', function () {
    if (!load().length) return;
    if (!confirm('清空这台设备上的全部留言？')) return;
    save([]);
    tipEl.textContent = '已清空';
    render();
  });

  render();
})();
</script>
"""

TYPEWRITER_BODY = """  <h1 class="title">打字机效果</h1>
  <p class="subtitle">一个字一个字敲出来，带光标闪烁和可选音效</p>

  <div class="tw-stage"><span><span id="out"></span><span class="tw-caret">&nbsp;</span></span></div>

  <div class="search-row">
    <input id="txt" type="text" value="愿许秋风知我意，事事如意上心头" maxlength="60" style="flex:1">
  </div>
  <div class="search-row">
    <span style="color:var(--text-dim);align-self:center">速度</span>
    <input id="speed" type="range" min="30" max="400" value="140" step="10">
    <button class="chip active" id="go" type="button">开始打字</button>
    <button class="chip" id="sound" type="button">音效：关</button>
  </div>

  <div class="storage-tip">输入任意文字，点「开始打字」重来一遍；音效用 WebAudio 现场合成，不加载任何外部文件。</div>

<script>
(function () {
  var out = document.getElementById('out');
  var txt = document.getElementById('txt');
  var speed = document.getElementById('speed');
  var soundBtn = document.getElementById('sound');
  var timer = null;
  var soundOn = false;
  var audioCtx = null;

  function beep() {
    if (!soundOn) return;
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      var o = audioCtx.createOscillator(), g = audioCtx.createGain();
      o.type = 'square';
      o.frequency.value = 1500 + Math.random() * 700;
      g.gain.value = 0.035;
      o.connect(g); g.connect(audioCtx.destination);
      o.start();
      g.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.03);
      o.stop(audioCtx.currentTime + 0.04);
    } catch (e) {}
  }

  soundBtn.addEventListener('click', function () {
    soundOn = !soundOn;
    soundBtn.textContent = '音效：' + (soundOn ? '开' : '关');
    soundBtn.classList.toggle('active', soundOn);
  });

  function run() {
    if (timer) { clearInterval(timer); timer = null; }
    var s = txt.value || '你好';
    var i = 0;
    out.textContent = '';
    timer = setInterval(function () {
      out.textContent += s.charAt(i++);
      beep();
      if (i >= s.length) { clearInterval(timer); timer = null; }
    }, Number(speed.value));
  }

  document.getElementById('go').addEventListener('click', run);
  txt.addEventListener('keydown', function (e) { if (e.key === 'Enter') run(); });
  speed.addEventListener('input', function () { if (timer) run(); });
  run();
})();
</script>
"""

BOARD_BODY = """  <h1 class="title">画板</h1>
  <p class="subtitle">随手涂两笔 · 支持撤销、清空、存成图片</p>

  <div class="search-row" id="colors" style="align-items:center">
    <span style="color:var(--text-dim);align-self:center">颜色</span>
    <input id="picker" type="color" value="#1b2440" style="width:44px;height:34px;border:1px solid var(--line);border-radius:8px;background:none">
    <span style="color:var(--text-dim);align-self:center;margin-left:10px">粗细</span>
    <input id="size" type="range" min="1" max="40" value="6">
    <span id="sizeVal" style="color:var(--text-dim);align-self:center">6</span>
    <button class="chip" id="eraser" type="button">橡皮</button>
    <button class="chip" id="undo" type="button">撤销</button>
    <button class="chip" id="clear" type="button">清空</button>
    <button class="chip active" id="save" type="button">保存图片</button>
  </div>

  <canvas class="board" id="board" width="1000" height="620"></canvas>

  <div class="storage-tip">画完点「保存图片」会下载一张 PNG；canvas 尺寸固定 1000×620，手机上也能用手指画。</div>

<script>
(function () {
  var cv = document.getElementById('board');
  var ctx = cv.getContext('2d');
  var picker = document.getElementById('picker');
  var sizeEl = document.getElementById('size');
  var sizeVal = document.getElementById('sizeVal');
  var eraser = false;
  var snapshot = null;
  var drawing = false;
  var last = null;

  function clearAll() {
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, cv.width, cv.height);
  }
  function pushUndo() {
    try { snapshot = ctx.getImageData(0, 0, cv.width, cv.height); } catch (e) {}
  }
  function stamp(x, y) {
    ctx.fillStyle = eraser ? '#ffffff' : picker.value;
    ctx.beginPath();
    ctx.arc(x, y, Number(sizeEl.value) / 2, 0, Math.PI * 2);
    ctx.fill();
  }
  function pos(e) {
    var r = cv.getBoundingClientRect();
    return {
      x: (e.clientX - r.left) * (cv.width / r.width),
      y: (e.clientY - r.top) * (cv.height / r.height)
    };
  }

  cv.addEventListener('pointerdown', function (e) {
    pushUndo();
    drawing = true;
    last = pos(e);
    stamp(last.x, last.y);
    cv.setPointerCapture && cv.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  cv.addEventListener('pointermove', function (e) {
    if (!drawing) return;
    var p = pos(e);
    ctx.strokeStyle = eraser ? '#ffffff' : picker.value;
    ctx.lineWidth = Number(sizeEl.value);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    last = p;
    e.preventDefault();
  });
  window.addEventListener('pointerup', function () { drawing = false; });
  cv.addEventListener('pointerleave', function () { drawing = false; });

  sizeEl.addEventListener('input', function () { sizeVal.textContent = sizeEl.value; });
  eraser.addEventListener('click', function () {
    eraser = !eraser;
    eraser.classList.toggle('active', eraser);
    eraser.textContent = eraser ? '橡皮：开' : '橡皮';
  });
  document.getElementById('undo').addEventListener('click', function () {
    if (snapshot) ctx.putImageData(snapshot, 0, 0);
  });
  document.getElementById('clear').addEventListener('click', function () {
    pushUndo();
    clearAll();
  });
  document.getElementById('save').addEventListener('click', function () {
    var a = document.createElement('a');
    a.download = 'drawing.png';
    a.href = cv.toDataURL('image/png');
    a.click();
  });

  clearAll();
})();
</script>
"""


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return path


if __name__ == '__main__':
    made = []
    made.append(write('pages/style.css', CSS.strip() + '\n'))
    made.append(write('pages/blog.html', BLOG_HTML))
    for p in POSTS:
        made.append(write('pages/%s.html' % p['slug'], render_post(p)))
    made.append(write('pages/drive.html', DRIVE_HTML))
    made.append(write('pages/hearts.html', HEARTS_HTML))
    made.append(write('pages/about.html', page('关于我', ABOUT_BODY)))
    made.append(write('pages/guestbook.html', page('留言板', GUESTBOOK_BODY)))
    made.append(write('pages/typewriter.html', page('打字机效果', TYPEWRITER_BODY)))
    made.append(write('pages/board.html', page('画板', BOARD_BODY)))
    made.append(write('其他页面/文本/爱心.html', HEARTS_ENTRY))
    made.append(write('其他页面/博客/图片.html', GALLERY_HTML))
    # 原来那两个指着 zyyo.net 的 Typecho 静态壳（脱离原站后样式和文章全丢），统一转到新博客页
    made.append(write('其他页面/博客/博客.html', redirect_page(
        '博客 · SicilyQin', '../../../pages/blog.html', '正在打开新的博客页…')))
    made.append(write('其他页面/博客/博客 - 副本.html', redirect_page(
        '博客 · SicilyQin', '../../../pages/blog.html', '正在打开新的博客页…')))
    for m in made:
        print('written:', os.path.relpath(m, ROOT))
