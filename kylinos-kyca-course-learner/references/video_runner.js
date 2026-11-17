/**
 * video_runner.js — 麒麟课程视频章节的页面内自动播放运行器
 *
 * 用法：用 chrome-devtools 的 evaluate_script 执行以下函数体（包成 async 函数，
 * 并设 waitForStableDom:false）。运行后通过轮询 window.__vstat 监控进度。
 *
 * 设计要点（均已实测验证）：
 *  1. playbackRate = 1，muted = true。**新会话必须 1x（真实时间）**：服务端按"累计墙钟×~1.25"封顶记录的 playtimes，
 *     3x/8x 会让内容播太快、墙钟太短，封顶远低于视频时长（实测 3x 只记到 37%）。早期 3x 能到 100% 是因为会话墙钟已长期累积。
 *     若想略快可用 ≤1.25x（封顶系数），但 1x 留 20% 余量最稳。
 *  2. 每 1s 轮询：paused 则静音续播（防后台节流导致的伪暂停）。
 *  3. 检测"重置 bug"：currentTime 相对 lastT 下跌 >50s（≈80% 处被重置回 0），
 *     把 currentTime 拖回 lastT-2 续播，不从头。
 *  4. ended 退出循环，置 window.__vstat.ended=true。
 *  5. 运行器退出后，调用方须再 sleep 10–15s 等末次 logStudyTimes 上报，
 *     然后才 navigate 回课程列表确认 100%。
 */

// ===== 复制以下函数体到 evaluate_script 的 function() { ... } 中 =====
async function runKylinosVideo() {
  const v = document.querySelector('video');
  if (!v) return { err: 'no video element' };

  window.__vstat = { t: 0, ended: false, resets: 0, lastT: 0, startedAt: Date.now() };
  v.muted = true;
  v.playbackRate = 1;
  let p = v.play();
  if (p && p.catch) p.catch(() => {});

  while (true) {
    await new Promise(r => setTimeout(r, 1000));

    if (v.ended) {
      window.__vstat.ended = true;
      window.__vstat.t = v.currentTime;
      break;
    }

    if (v.paused) {
      v.muted = true;
      v.play().catch(() => {});
    }

    if (v.currentTime > window.__vstat.lastT + 1) {
      // 正常前进
      window.__vstat.lastT = v.currentTime;
    } else if (v.currentTime < window.__vstat.lastT - 50) {
      // 检测到重置（跳回开头）：拖回断点续播
      window.__vstat.resets++;
      try { v.currentTime = Math.max(0, window.__vstat.lastT - 2); } catch (e) {}
      v.muted = true;
      v.play().catch(() => {});
    }

    window.__vstat.t = v.currentTime;
  }
  return 'runner finished, ended=' + window.__vstat.ended;
}
// 在 evaluate_script 中调用：runKylinosVideo();  （await 由 async 函数自动处理）
// ===== 复制结束 =====


/**
 * 监控快照（轮询用，单独执行）：
 *   () => window.__vstat || { none: true }
 */

/**
 * 进入视频页后，先用这段确认元素与可拖动性（诊断重置/封顶问题时用）：
 *   () => {
 *     const v = document.querySelector('video');
 *     return {
 *       hasVideo: !!v,
 *       duration: v ? v.duration : null,
 *       seekableEnd: v && v.seekable.length ? v.seekable.end(0) : null,
 *       error: v && v.error ? { code: v.error.code, msg: v.error.message } : null,
 *       networkState: v ? v.networkState : null,
 *       readyState: v ? v.readyState : null
 *     };
 *   }
 */

/**
 * 进度百分比速读：
 *   () => {
 *     const v = document.querySelector('video');
 *     if (!v) return { err: 'no video' };
 *     if (v.paused) { v.muted = true; v.play().catch(()=>{}); }
 *     return {
 *       rate: v.playbackRate, paused: v.paused,
 *       t: Math.round(v.currentTime), dur: Math.round(v.duration),
 *       ended: v.ended, pct: (v.currentTime / v.duration * 100).toFixed(1)
 *     };
 *   }
 */
