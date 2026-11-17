---
name: kylinos-kyca-course-learner
description: 使用 chrome-devtools MCP 自动推进麒麟软件学院（inst.kylinos.cn）"任务课程"的在线学习。遇到 PDF 章节自动滚动到底触发完成；遇到视频章节以 1x 真实时间播放并自动续播/处理重置、等待末次上报直到 100%；每章刷完后遇到"习题检测"自动逐项分析讲解并向用户询问是否代答（默认用户自行作答，用户明确同意后我才代为勾选并提交）。This skill should be used when the user asks to automatically complete / study / 刷课 a kylinos.cn course task, or when a chrome-devtools-driven auto-learning of inst.kylinos.cn is requested.
license: MIT
agent_created: true
allowed-tools:
disable: false
---

# 麒麟 KYCA 课程自动学习

## Overview

通过 chrome-devtools MCP 操作**用户已手动打开**的 Chrome 浏览器，自动推进 `inst.kylinos.cn` 上某个"任务课程"的学习进度。课程由若干章节项组成，每项可能是 **PDF 文档**、**视频** 或 **习题检测**。本技能封装了三类章节各自的完成机制与实测踩坑点，使自动化稳定可复现。

> 关键前提：浏览器由用户自己打开并登录；本技能只负责驱动，不负责登录与鉴权。

## When to use

- 用户要求"自动完成 / 刷完 / 学习"某个 `inst.kylinos.cn` 的课程任务。
- 用户给出形如 `https://inst.kylinos.cn/#/index/taskCourse?spaceid=...&subid=...` 的课程链接。
- 用户要求接入自定义 chrome-devtools 连接器来操作课程页面。

## Prerequisites / 前置

- 已安装并连接 `chrome-devtools` MCP（连接器）。
- 用户的 Chrome 已打开目标课程页并处于登录态。
- 已知两个 ID：`spaceid`（空间/课程包 ID）与 `subid`（任务/子课程 ID），即 taskCourse URL 中的两个参数。

## 关键 URL 形态

| 页面 | 形态 |
|------|------|
| 课程任务列表 | `https://inst.kylinos.cn/#/index/taskCourse?spaceid={spaceid}&subid={subid}` |
| PDF 学习页 | `https://inst.kylinos.cn/#/coursePdf/teachTrain/{spaceid}/{sccid}/{subid}` |
| 视频学习页 | `https://inst.kylinos.cn/#/courseVideo/teachTrain/{spaceid}/{sccid}/{subid}` |

`sccid` 是章节内容 ID，每个章节项唯一。不要硬编码 sccid——从课程列表页点击"开始学习"按钮后读取 `location.href` 即可拿到（见下）。

## 主流程

1. **定位标签页**：`list_pages` 找到目标页，`select_page(bringToFront=true)` 置前（防止后台节流暂停 HLS 视频）。
2. **读取课程列表**：`navigate_page` 到 taskCourse URL（必要时 `reload`），用 `evaluate_script` 读取 `document.body.innerText`，解析章节结构与每项状态：
   - `待学习` / 灰色"开始学习"→ 未解锁（前置项未完成）。
   - `开始学习`（可点）→ 下一个待学项。
   - `已完成` / 百分比（如 `100%`、`56%`）→ 已完成或在进行中。
   - 文本含 `习题` / `习题检测` / `测验` → **习题章节（特殊处理，见下）**。
3. **逐项推进**：对下一个未完成且非习题的项，取其"开始学习"按钮 → 点击 → 从 `location.href` 拿到 `coursePdf`/`courseVideo` 路由与 `sccid` → 按类型处理。
4. **完成校验**：每项处理完后，`navigate_page` 回 taskCourse URL 刷新，再读 innerText 确认该项变为 `已完成` 且下一项解锁。列表进度只在重新加载后才刷新。
5. **遇到习题检测**：自动进入答题页、逐项分析讲解并向用户询问是否代答（默认用户自行作答，用户明确同意后我才代为勾选并提交）；习题完成后回到列表继续下一章。

> 不要用 `click(uid=...)` 传 uid 去点课程列表里的"开始学习"——参数易因 DOM 变化报错。改用 `evaluate_script` 在页面内定位按钮文本并 `.click()`，随后读 `location.href` 取路由。

## PDF 章节处理（已验证）

PDF 在 `iframe` 内用 pdf.js 渲染，完成判定 = **滚动到最后一页**。

1. 进 PDF 页后等待加载，取 iframe：`const f=document.querySelector('iframe'); const doc=f.contentDocument; const win=f.contentWindow;`
2. 阅读容器与页数（详见 `references/pdf_scroll.js`）：
   - 容器：`doc.getElementById('viewerContainer')`（回退 `doc.scrollingElement`）。
   - 总页数：`doc.getElementById('numPages').textContent`。
   - 当前页：`doc.getElementById('pageNumber').value`。
3. **循环把容器滚到底**直到当前页 = 总页数：
   ```
   c.scrollTop = c.scrollHeight; win.dispatchEvent(new Event('scroll'));
   ```
   每步间隔 ~600ms，最多 15 次；到达末页即停。
4. **停留在 PDF 页 30–60s**，等 `POST /s/SpaceStudy/readedPdf` 触发（用 `list_network_requests` 验证）。
   - ⚠️ 停在首页等 120s 也**不会**触发；必须真的滚到末页。
   - ⚠️ 未触发 readedPdf 前不要导航离开。
5. 返回列表确认 `已完成`。

## 视频章节处理（已验证，重点）

视频为 HTML5 + HLS 流（`.m3u8` + `.ts` 分片），单条约 10–20 分钟。

### 进度上报机制

- 周期 `POST /s/SpaceStudy/logStudyTimes`（约每 20s，`times=20`）。
- 请求体关键字段：`playtimes=` = 累计**内容时长**（`video.currentTime`，不是墙钟）；`alltimes=` = 视频总时长（`video.duration`）。
- 完成判定：服务端记录的 `playtimes` ≈ `alltimes`（即 100%）。

### 三个实测坑（必须处理）

1. **防刷封顶（最重要，已纠偏）**：服务端对单会话有效播放时长封顶 ≈ **累计墙钟 × 1.25**（实测 05 视频 3x 播放后只记到 37%，即 1543×0.37≈571s ≈ 墙钟455s×1.25）。
   - 因此**新会话必须按 1x（真实时间）播放**才能稳到 100%。用 3x/8x 时内容播太快、墙钟太短，封顶远低于视频时长 → 进度不足、必须重看。
   - 之所以早先用 3x 能把 04 刷到 100%，是因为当时该会话已长期累积（多次实验）墙钟足够大；**全新会话不适用**。
   - 折中：若想略快，可用 ≤1.25x（封顶系数），但 1x 留 20% 余量最稳妥。
2. **播放器重置 bug**：视频在 ≈80%（≈5 分钟墙钟处）会被重置/重载回 0%（疑似 media token 过期）。但视频可全程 seek（`seekableEnd` = 时长），重置后把 `currentTime` **拖回断点**即可续播，无需从头。
3. **末次上报丢失**：`ended` 后若立即导航离开，最后一笔 `logStudyTimes` 发不出去，进度会回退。**ended 后须停留 10–15s** 再返回列表。

### 标准做法（页面内运行器）

进入视频页、等待 `video` 元素出现后，用 `evaluate_script`（设 `waitForStableDom:false`）注入一个 1x + 自动续播 + 重置检测 + ended 退出的运行器，见 `references/video_runner.js`。要点：

- `video.playbackRate = 1; video.muted = true; video.play()`（**1x 真实时间**，封顶系数约 1.25，留余量最稳）。
- 每 1s 轮询：`paused` → 静音续播；`currentTime` 较 `lastT` 下跌 >50s（即重置）→ 设 `currentTime = lastT - 2` 续播；`ended` → 退出循环并置 `window.__vstat.ended=true`。
- 标签页务必 `bringToFront` 防后台节流（节流会触发伪暂停/重载）。
- 长视频分段 `sleep` + 轮询 `window.__vstat` 监控；若 `paused` 则续播。
- **ended 后 `sleep 10–15s`** 等末次上报，再 `navigate_page` 回 taskCourse 列表确认 100%。

> 不要为了省时用 3x/8x 或更高倍率——新会话下封顶机制会让进度永久不足（实测 3x 只记到 37%），反而要重看，得不偿失。**1x 真实时间 + 末次上报等待**是唯一稳到 100% 的做法。

## 习题检测章节处理（用户要求：自动分析 + 询问代答）

每章的 PDF/视频全部刷完后，习题检测会解锁。与"纯暂停"不同，这里要**主动分析并询问**：

1. **自动进入习题**：识别到 `习题` / `习题检测` / `测验` 项解锁后，点击进入答题页（路由 `coursePaper/teachTrain/...`）。
2. **逐项分析讲解（只读，不代点）**：
   - 用 `take_snapshot` 读取全部题目与选项（题号、题型：单选/多选/判断）。⚠️ 试卷可能延迟渲染，若首屏只有 banner（目录/答题卡/提交），等 1–2s 再取一次快照。
   - 在聊天里**逐题给出解析与参考答案**（含理由、易错点），明确标注每题答案，但**不替用户点击选项**。
3. **询问是否代答**：分析讲完后，明确问用户"是否需要我代为作答？"：
   - **默认：用户自己作答**（不代答）。
   - 若用户明确同意（如回复"代答"/"你来答"），才进入第 4 步代为作答。
   - 若用户自行作答并提交，则回复"继续"推进下一章。
4. **（仅当用户明确同意时）代为作答**：
   - 对每题，按答案定位对应选项元素（`take_snapshot` 拿 uid，`click` 选择：单选=radio、多选=checkbox、判断=A/B）。
   - 全部选完后点击 banner 内的「提交」按钮。
   - 提交后用 `take_snapshot` 核对"正确率 / 完成率"是否更新，确认提交成功。
5. **推进下一章**：习题完成后（无论谁答），回到课程列表，继续下一章的 PDF/视频，直到下一个习题检测再重复本流程。

## 工具映射（chrome-devtools MCP）

- `list_pages` / `select_page(bringToFront)` — 定位与置前标签页。
- `navigate_page(type=url|reload|back)` — 跳转/刷新/返回。
- `take_snapshot` — 取 DOM 快照定位按钮（辅助）。
- `evaluate_script` — 执行页面内 JS（滚动、注入运行器、读状态）；长轮询脚本加 `waitForStableDom:false`。
- `list_network_requests(resourceTypes=[xhr,fetch])` — 验证 `readedPdf` / `logStudyTimes` 是否触发。
- `click` — 仅在快照稳定且 uid 明确时使用；课程列表按钮优先用 `evaluate_script` 内 `.click()`。

## 进度状态速查

| 现象 | 含义 / 动作 |
|------|------|
| 列表显示 `待学习` | 前置未完成，先完成它 |
| PDF 滚到末页后 30–60s | 等 `readedPdf`，再回列表 |
| 视频 100% 但列表只 37% | 新会话用了 >1x 倍率被封顶，需 1x 重看 |
| 视频在 80% 跳回 0% | 重置 bug，运行器自动拖回续播 |
| 视频 ended 但列表非 100% | 末次上报丢失，下回 ended 后多停 10–15s |
