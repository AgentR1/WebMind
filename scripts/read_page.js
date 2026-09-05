// Executed in the selected document by read-page. No page state is changed.
(() => {
  const options = __WEBMIND_OPTIONS__;
  const ignoredTags = new Set([
    'SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'NAV', 'ASIDE', 'FOOTER',
    'FORM', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'SVG', 'CANVAS', 'IFRAME'
  ]);
  const blockTags = new Set([
    'ADDRESS', 'ARTICLE', 'BLOCKQUOTE', 'DD', 'DIV', 'DL', 'DT', 'FIGCAPTION',
    'FIGURE', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HEADER', 'HR', 'LI', 'MAIN',
    'OL', 'P', 'PRE', 'SECTION', 'TABLE', 'TD', 'TH', 'TR', 'UL'
  ]);
  const styles = new WeakMap();
  const styleOf = el => {
    if (!styles.has(el)) styles.set(el, getComputedStyle(el));
    return styles.get(el);
  };
  const hidden = el => {
    const style = styleOf(el);
    return el.hidden || el.getAttribute('aria-hidden') === 'true' ||
      style.display === 'none' || style.visibility === 'hidden' ||
      style.visibility === 'collapse' || style.contentVisibility === 'hidden' ||
      Number(style.opacity) === 0;
  };
  const hiddenByAncestor = el => {
    for (let current = el; current; current = current.parentElement) {
      if (hidden(current)) return true;
      const parent = current.parentElement;
      if (parent && parent.tagName === 'DETAILS' && !parent.open) {
        const summary = Array.from(parent.children).find(child => child.tagName === 'SUMMARY');
        if (current !== summary) return true;
      }
    }
    return false;
  };
  const noise = (el, root) => {
    if (ignoredTags.has(el.tagName)) return true;
    const role = el.getAttribute('role');
    if (['navigation', 'banner', 'contentinfo', 'complementary'].includes(role)) return true;
    // Article headers often contain useful titles and author information.
    return el.tagName === 'HEADER' && root === document.body && !el.closest('article,main,[role="main"]');
  };
  const normalize = text => text.replace(/\r/g, '').split('\n')
    .map(line => line.replace(/[\t\f\v \u00a0]+/g, ' ').trim()).join('\n')
    .replace(/\n{3,}/g, '\n\n').trim();
  const clip = (text, limit) => Array.from(text).slice(0, limit).join('');

  function collect(root, includeElements = false) {
    const chunks = [];
    const elements = [];
    // An explicit stack handles deeply nested documents without recursion limits.
    const stack = [{node: root, closing: false}];
    while (stack.length) {
      const {node, closing} = stack.pop();
      if (closing) { chunks.push('\n'); continue; }
      if (node.nodeType === Node.TEXT_NODE) { chunks.push(node.nodeValue); continue; }
      if (node.nodeType !== Node.ELEMENT_NODE || hidden(node) || noise(node, root)) continue;
      if (includeElements) elements.push(node);
      if (node.tagName === 'BR') { chunks.push('\n'); continue; }
      const style = styleOf(node);
      const block = blockTags.has(node.tagName) || ['block', 'list-item', 'table-row'].includes(style.display);
      if (block) { chunks.push('\n'); stack.push({node, closing: true}); }
      // Collapsed details retain computed styles for their unrendered content.
      const children = node.tagName === 'DETAILS' && !node.open
        ? Array.from(node.children).filter(child => child.tagName === 'SUMMARY').slice(0, 1)
        : node.childNodes;
      for (let i = children.length - 1; i >= 0; i--) {
        stack.push({node: children[i], closing: false});
      }
    }
    return {text: normalize(chunks.join('')), elements};
  }

  let root;
  let extraction;
  if (options.selector) {
    let matches;
    try { matches = document.querySelectorAll(options.selector); }
    catch (_) { return {ok: false, error: 'invalid CSS selector', selector: options.selector}; }
    if (!matches.length) return {ok: false, error: 'selector not found', selector: options.selector};
    if (matches.length !== 1) return {ok: false, error: 'selector is ambiguous; use a unique selector', selector: options.selector};
    root = matches[0];
    if (hiddenByAncestor(root)) return {ok: false, error: 'selected content is hidden', selector: options.selector};
    extraction = {method: 'selector', selector: options.selector};
  } else {
    const seen = new Set();
    const candidates = [];
    for (const [selector, weight] of [
      ['[itemprop="articleBody"]', 1.25], ['#js_content', 1.25],
      ['article', 1.15], ['main', 1], ['[role="main"]', 1]
    ]) {
      for (const el of document.querySelectorAll(selector)) {
        if (seen.has(el) || hiddenByAncestor(el)) continue;
        seen.add(el);
        let inNoise = false;
        for (let parent = el.parentElement; parent; parent = parent.parentElement) {
          if (noise(parent, document.body)) { inNoise = true; break; }
        }
        if (inNoise) continue;
        const text = collect(el).text;
        if (text) candidates.push({el, selector, score: text.length * weight});
      }
    }
    candidates.sort((a, b) => b.score - a.score);
    root = candidates.length ? candidates[0].el : document.body;
    extraction = candidates.length
      ? {method: 'semantic', selector: candidates[0].selector}
      : {method: 'body', selector: 'body'};
  }
  if (!root) return {ok: false, error: 'document has no readable body'};
  const content = collect(root, true);
  if (!content.text) return {ok: false, error: 'selected region has no readable text', extraction};

  const headings = [];
  const links = [];
  const seenLinks = new Set();
  for (const el of content.elements) {
    if (/^H[1-6]$/.test(el.tagName)) {
      const text = collect(el).text;
      if (text) headings.push({level: Number(el.tagName[1]), text: clip(text, 300)});
    }
    if (el.tagName === 'A' && el.hasAttribute('href')) {
      let url;
      try { url = new URL(el.getAttribute('href'), document.baseURI); }
      catch (_) { continue; }
      if (!['http:', 'https:'].includes(url.protocol) || seenLinks.has(url.href)) continue;
      seenLinks.add(url.href);
      links.push({text: clip(collect(el).text || el.getAttribute('aria-label') || '', 300), url: url.href});
    }
  }
  const title = document.title.trim() || (headings.find(h => h.level === 1) || {}).text || '';
  const text = clip(content.text, options.maxChars);
  return {
    ok: true,
    title,
    url: location.href,
    lang: document.documentElement.lang || '',
    text,
    headings: headings.slice(0, 100),
    links: links.slice(0, options.maxLinks),
    extraction,
    truncated: {
      text: text.length < content.text.length,
      links: links.length > options.maxLinks,
      headings: headings.length > 100
    }
  };
})()
