/**
 * pdf_scroll.js — 麒麟课程 PDF 章节"滚动到末页触发完成"的页面内脚本
 *
 * 完成机制（已验证）：PDF 在 iframe 内用 pdf.js 渲染，必须滚动到最后一页，
 * 约 30–60s 后才会触发 POST /s/SpaceStudy/readedPdf 并标记"已完成"。
 * 停在首页等待不会触发。
 *
 * 用法：用 chrome-devtools 的 evaluate_script 执行以下函数体。
 */

// 1) 进入 PDF 页、确认 iframe 与页数（诊断用）：
//   () => {
//     const f = document.querySelector('iframe');
//     if (!f) return { err: 'no iframe' };
//     const doc = f.contentDocument;
//     return {
//       total: doc.getElementById('numPages') ? doc.getElementById('numPages').textContent : null,
//       pageNow: doc.getElementById('pageNumber') ? doc.getElementById('pageNumber').value : null,
//       hasViewer: !!doc.querySelector('#viewer')
//     };
//   }

// 2) 滚动到末页（核心）：把阅读容器 scrollTop 设为 scrollHeight 并派发 scroll 事件。
//    循环到当前页 == 总页数即停。
//   async () => {
//     const f = document.querySelector('iframe');
//     const doc = f.contentDocument;
//     const win = f.contentWindow;
//     const c = doc.getElementById('viewerContainer') || doc.scrollingElement;
//     const last = parseInt((doc.getElementById('numPages').textContent || '').replace(/[^\d]/g, '')) || 99;
//     for (let i = 0; i < 15; i++) {
//       c.scrollTop = c.scrollHeight;
//       win.dispatchEvent(new Event('scroll'));
//       await new Promise(r => setTimeout(r, 600));
//       const p = parseInt(doc.getElementById('pageNumber').value) || 1;
//       if (p >= last) return { done: true, page: p, last };
//     }
//     return { done: false, page: parseInt(doc.getElementById('pageNumber').value) || 1, last };
//   }

// 3) 停留 30–60s 后，用 list_network_requests 确认 readedPdf 已触发，再回列表。
//    也可主动轮询当前页：
//   () => {
//     const f = document.querySelector('iframe');
//     const doc = f.contentDocument;
//     return {
//       pageNow: doc.getElementById('pageNumber').value,
//       scrollRatio: (() => {
//         const c = doc.getElementById('viewerContainer') || doc.scrollingElement;
//         return (c.scrollTop / c.scrollHeight).toFixed(2);
//       })()
//     };
//   }

/**
 * 提醒：
 *  - 必须真滚到末页，停在首页等 120s 也不触发。
 *  - readedPdf 触发前不要 navigate 离开 PDF 页。
 *  - 回到课程列表（reload taskCourse URL）后进度才刷新。
 */
