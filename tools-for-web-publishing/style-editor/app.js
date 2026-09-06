/**
 * WYSIWYG Style Studio - Main Controller
 * 
 * Provides interactive visual styling for any arbitrary HTML document:
 * - Isolated iframe preview with element picking & hover inspection
 * - Breadcrumb path & intelligent CSS selector generator
 * - Visual WYSIWYG controls (Typography, Spacing Box Model, Colors, Flexbox, Borders, Shadows)
 * - Direct bi-directional raw CSS editing
 * - Theme presets (Studio Dark, Editorial, Cyber, Clean Light)
 * - Clean export of style.css and styled HTML
 * - LocalStorage auto-save & undo/redo history
 */

(function () {
  'use strict';

  // --- STATE ---
  const state = {
    htmlContent: '',
    originalDocTitle: 'Document',
    activeSelector: 'body',
    pseudoState: '',
    styleRules: {}, // { selector: { property: value } }
    inspectMode: true,
    activeViewport: 'desktop',
    selectedElementTag: 'body',
    selectedElementClasses: [],
    selectedElementId: '',
    selectedElementPath: ['body'],
    historyStack: [],
    historyIndex: -1,
    isApplyingHistory: false
  };

  // Google Fonts to load dynamically in iframe preview
  const googleFontsMap = {
    'Inter': 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
    'Playfair Display': 'https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&display=swap',
    'Merriweather': 'https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&display=swap',
    'Lora': 'https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&display=swap',
    'Plus Jakarta Sans': 'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap',
    'Space Grotesk': 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap',
    'JetBrains Mono': 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap',
    'Roboto': 'https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap',
    'Cinzel': 'https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap'
  };

  // DOM Elements
  const previewFrame = document.getElementById('preview-frame');
  const viewportFrame = document.getElementById('viewport-frame');
  const currentSelectorDisplay = document.getElementById('current-selector-display');
  const activeTagBadge = document.getElementById('active-tag-badge');
  const elementBreadcrumbs = document.getElementById('element-breadcrumbs');
  const selectorOptions = document.getElementById('selector-options');
  const customSelectorInput = document.getElementById('custom-selector-input');
  const pseudoStateSelect = document.getElementById('pseudo-state-select');
  const rawCssTextarea = document.getElementById('raw-css-textarea');
  const rawCssSelectorLabel = document.getElementById('raw-css-selector-label');

  // Box Model Inputs
  const bmInputs = {
    'margin-top': document.getElementById('bm-margin-top'),
    'margin-right': document.getElementById('bm-margin-right'),
    'margin-bottom': document.getElementById('bm-margin-bottom'),
    'margin-left': document.getElementById('bm-margin-left'),
    'padding-top': document.getElementById('bm-padding-top'),
    'padding-right': document.getElementById('bm-padding-right'),
    'padding-bottom': document.getElementById('bm-padding-bottom'),
    'padding-left': document.getElementById('bm-padding-left')
  };

  // --- INITIALIZATION ---
  function init() {
    setupEventListeners();
    setupPaneResizer();
    setupDropdowns();
    setupModals();

    // Check for saved state in localStorage
    const saved = loadFromLocalStorage();
    if (saved && saved.html) {
      state.htmlContent = saved.html;
      state.styleRules = saved.styles || {};
      renderPreview();
      pushHistorySnapshot();
    } else {
      // Default to Studio Numerozzi portfolio sample
      loadSample('portfolio');
    }
  }

  // --- LOCAL STORAGE ---
  function saveToLocalStorage() {
    try {
      localStorage.setItem('style_studio_project', JSON.stringify({
        html: state.htmlContent,
        styles: state.styleRules,
        timestamp: Date.now()
      }));
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }
  }

  function loadFromLocalStorage() {
    try {
      const data = localStorage.getItem('style_studio_project');
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  }

  // --- HISTORY (UNDO/REDO) ---
  function pushHistorySnapshot() {
    if (state.isApplyingHistory) return;
    // Trim forward redo states
    state.historyStack = state.historyStack.slice(0, state.historyIndex + 1);
    state.historyStack.push(JSON.stringify(state.styleRules));
    if (state.historyStack.length > 50) state.historyStack.shift();
    state.historyIndex = state.historyStack.length - 1;
    updateUndoRedoButtons();
    saveToLocalStorage();
  }

  function undo() {
    if (state.historyIndex > 0) {
      state.historyIndex--;
      applyHistoryState(state.historyStack[state.historyIndex]);
    }
  }

  function redo() {
    if (state.historyIndex < state.historyStack.length - 1) {
      state.historyIndex++;
      applyHistoryState(state.historyStack[state.historyIndex]);
    }
  }

  function applyHistoryState(json) {
    state.isApplyingHistory = true;
    try {
      state.styleRules = JSON.parse(json);
      applyStylesToPreview();
      populateInspectorForSelector(getCurrentFullSelector());
      updateUndoRedoButtons();
      saveToLocalStorage();
    } finally {
      state.isApplyingHistory = false;
    }
  }

  function updateUndoRedoButtons() {
    const btnUndo = document.getElementById('btn-undo');
    const btnRedo = document.getElementById('btn-redo');
    if (btnUndo) btnUndo.disabled = state.historyIndex <= 0;
    if (btnRedo) btnRedo.disabled = state.historyIndex >= state.historyStack.length - 1;
  }

  // --- SELECTOR HANDLING ---
  function getCurrentFullSelector() {
    return state.activeSelector + state.pseudoState;
  }

  function setActiveSelector(selector, keepPseudo = false) {
    if (!keepPseudo) state.pseudoState = '';
    state.activeSelector = selector.trim();
    if (pseudoStateSelect) pseudoStateSelect.value = state.pseudoState;

    const fullSelector = getCurrentFullSelector();
    currentSelectorDisplay.textContent = fullSelector;
    rawCssSelectorLabel.textContent = fullSelector;

    // Highlight active chip in toolbar
    document.querySelectorAll('.selector-chip').forEach(chip => {
      chip.classList.toggle('active', chip.dataset.selector === selector);
    });

    populateInspectorForSelector(fullSelector);
  }

  // --- CSS RULES MANAGEMENT ---
  function getRule(selector) {
    if (!state.styleRules[selector]) {
      state.styleRules[selector] = {};
    }
    return state.styleRules[selector];
  }

  function setRuleProperty(selector, property, value, skipHistory = false) {
    const rule = getRule(selector);
    if (!value || value.trim() === '') {
      delete rule[property];
      // Clean up empty rule
      if (Object.keys(rule).length === 0) {
        delete state.styleRules[selector];
      }
    } else {
      rule[property] = value.trim();
    }

    applyStylesToPreview();
    updateRawCssDisplay(selector);
    updateInspectorBadges(selector);
    if (!skipHistory) pushHistorySnapshot();
  }

  function removeRuleProperty(selector, property) {
    if (state.styleRules[selector]) {
      delete state.styleRules[selector][property];
      if (Object.keys(state.styleRules[selector]).length === 0) {
        delete state.styleRules[selector];
      }
      applyStylesToPreview();
      populateInspectorForSelector(selector);
      pushHistorySnapshot();
    }
  }

  function resetCurrentRule() {
    const full = getCurrentFullSelector();
    if (state.styleRules[full]) {
      delete state.styleRules[full];
      applyStylesToPreview();
      populateInspectorForSelector(full);
      pushHistorySnapshot();
      showToast(`Reset styles for ${full}`);
    }
  }

  // --- CSS GENERATION ---
  function generateCSSString() {
    const lines = [];

    // Check for Google Fonts imports
    const activeFonts = new Set();
    Object.values(state.styleRules).forEach(props => {
      if (props['font-family']) {
        for (const fontName of Object.keys(googleFontsMap)) {
          if (props['font-family'].includes(fontName)) {
            activeFonts.add(fontName);
          }
        }
      }
    });

    if (activeFonts.size > 0) {
      lines.push('/* Google Fonts */');
      activeFonts.forEach(font => {
        lines.push(`@import url('${googleFontsMap[font]}');`);
      });
      lines.push('');
    }

    // Default CSS Reset rule if defined
    if (state.styleRules['*']) {
      lines.push('* {');
      for (const [prop, val] of Object.entries(state.styleRules['*'])) {
        lines.push(`  ${prop}: ${val};`);
      }
      lines.push('}\n');
    }

    // Body rule
    if (state.styleRules['body']) {
      lines.push('body {');
      for (const [prop, val] of Object.entries(state.styleRules['body'])) {
        lines.push(`  ${prop}: ${val};`);
      }
      lines.push('}\n');
    }

    // Other selectors
    for (const [sel, props] of Object.entries(state.styleRules)) {
      if (sel === '*' || sel === 'body') continue;
      if (Object.keys(props).length === 0) continue;

      lines.push(`${sel} {`);
      for (const [prop, val] of Object.entries(props)) {
        lines.push(`  ${prop}: ${val};`);
      }
      lines.push('}\n');
    }

    return lines.join('\n');
  }

  // --- PREVIEW IFRAME ENGINE ---
  function renderPreview() {
    let html = state.htmlContent;
    if (!html || html.trim() === '') {
      html = '<!DOCTYPE html><html><body><div style="padding:2rem;font-family:sans-serif;"><h3>Empty Page</h3><p>Open an HTML file or load a sample from the top bar.</p></div></body></html>';
    }

    // Check strip styles toggle
    const chkStrip = document.getElementById('chk-strip-styles');
    if (chkStrip && chkStrip.checked) {
      // Remove inline style attributes and <style> blocks
      html = html.replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '');
      html = html.replace(/<link\b[^>]*rel=["']stylesheet["'][^>]*>/gi, '');
    }

    previewFrame.srcdoc = html;

    previewFrame.onload = function () {
      injectInspectorScript();
      applyStylesToPreview();
      // Select body by default
      setActiveSelector('body');
    };
  }

  function injectInspectorScript() {
    const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
    if (!doc) return;

    // Inject highlight styles
    let highlightStyle = doc.getElementById('__styler-inspector-styles');
    if (!highlightStyle) {
      highlightStyle = doc.createElement('style');
      highlightStyle.id = '__styler-inspector-styles';
      highlightStyle.textContent = `
        .__styler-hover-outline {
          outline: 2px dashed #3b82f6 !important;
          outline-offset: -1px !important;
          cursor: crosshair !important;
        }
        .__styler-selected-outline {
          outline: 2px solid #3b82f6 !important;
          outline-offset: -1px !important;
          box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.25) !important;
        }
      `;
      doc.head.appendChild(highlightStyle);
    }

    // Inject generated CSS style tag
    let genStyle = doc.getElementById('__styler-generated-css');
    if (!genStyle) {
      genStyle = doc.createElement('style');
      genStyle.id = '__styler-generated-css';
      doc.head.appendChild(genStyle);
    }

    // Attach mouse listeners to iframe body
    doc.body.addEventListener('mouseover', function (e) {
      if (!state.inspectMode) return;
      e.stopPropagation();
      clearHovers(doc);
      if (e.target !== doc.body) {
        e.target.classList.add('__styler-hover-outline');
      }
    });

    doc.body.addEventListener('mouseout', function (e) {
      if (!state.inspectMode) return;
      e.target.classList.remove('__styler-hover-outline');
    });

    doc.body.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();

      const target = e.target;
      clearSelected(doc);
      clearHovers(doc);
      target.classList.add('__styler-selected-outline');

      handleElementSelected(target);
    });
  }

  function clearHovers(doc) {
    doc.querySelectorAll('.__styler-hover-outline').forEach(el => el.classList.remove('__styler-hover-outline'));
  }

  function clearSelected(doc) {
    doc.querySelectorAll('.__styler-selected-outline').forEach(el => el.classList.remove('__styler-selected-outline'));
  }

  function applyStylesToPreview() {
    const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
    if (!doc) return;

    let genStyle = doc.getElementById('__styler-generated-css');
    if (!genStyle) {
      genStyle = doc.createElement('style');
      genStyle.id = '__styler-generated-css';
      doc.head.appendChild(genStyle);
    }

    // Ensure Google fonts links are present in head
    Object.values(state.styleRules).forEach(props => {
      if (props['font-family']) {
        for (const [fontName, fontUrl] of Object.entries(googleFontsMap)) {
          if (props['font-family'].includes(fontName)) {
            const fontId = `google-font-${fontName.toLowerCase().replace(/\s+/g, '-')}`;
            if (!doc.getElementById(fontId)) {
              const link = doc.createElement('link');
              link.id = fontId;
              link.rel = 'stylesheet';
              link.href = fontUrl;
              doc.head.appendChild(link);
            }
          }
        }
      }
    });

    genStyle.textContent = generateCSSString();
  }

  // --- ELEMENT SELECTION & BREADCRUMBS ---
  function handleElementSelected(el) {
    const tagName = el.tagName.toLowerCase();
    const classList = Array.from(el.classList).filter(c => !c.startsWith('__styler-'));
    const id = el.id || '';

    state.selectedElementTag = tagName;
    state.selectedElementClasses = classList;
    state.selectedElementId = id;

    // Update active tag badge
    activeTagBadge.textContent = id ? `#${id}` : (classList.length > 0 ? `.${classList[0]}` : tagName);

    // Build DOM Path Breadcrumbs
    const pathElements = [];
    let curr = el;
    while (curr && curr.tagName && curr.tagName.toLowerCase() !== 'html') {
      const tag = curr.tagName.toLowerCase();
      const cls = Array.from(curr.classList).filter(c => !c.startsWith('__styler-'));
      const label = cls.length > 0 ? `${tag}.${cls[0]}` : (curr.id ? `${tag}#${curr.id}` : tag);
      pathElements.unshift({ el: curr, label, selector: cls.length > 0 ? `.${cls[0]}` : tag });
      curr = curr.parentElement;
    }
    state.selectedElementPath = pathElements;
    renderBreadcrumbs();

    // Generate Candidate Selectors
    const candidates = [];

    // 1. Tag name (e.g. h1, p, a, article)
    candidates.push({ label: tagName, selector: tagName });

    // 2. Class names
    classList.forEach(cls => {
      candidates.push({ label: `.${cls}`, selector: `.${cls}` });
    });

    // 3. ID if present
    if (id) {
      candidates.push({ label: `#${id}`, selector: `#${id}` });
    }

    // 4. Contextual / Parent combinator (e.g., .work h1 or header a)
    if (el.parentElement && el.parentElement.tagName.toLowerCase() !== 'body') {
      const parentTag = el.parentElement.tagName.toLowerCase();
      const parentClasses = Array.from(el.parentElement.classList).filter(c => !c.startsWith('__styler-'));
      const parentPrefix = parentClasses.length > 0 ? `.${parentClasses[0]}` : parentTag;
      candidates.push({ label: `${parentPrefix} ${tagName}`, selector: `${parentPrefix} ${tagName}` });
    }

    renderSelectorOptions(candidates);

    // Auto-select the most specific convenient selector:
    // If element has a class, select .class, else tag
    const defaultCandidate = classList.length > 0 ? `.${classList[0]}` : tagName;
    setActiveSelector(defaultCandidate);
  }

  function renderBreadcrumbs() {
    elementBreadcrumbs.innerHTML = '';
    state.selectedElementPath.forEach((item, index) => {
      if (index > 0) {
        const sep = document.createElement('span');
        sep.className = 'breadcrumb-separator';
        sep.textContent = '>';
        elementBreadcrumbs.appendChild(sep);
      }
      const span = document.createElement('span');
      span.className = 'breadcrumb-item';
      if (index === state.selectedElementPath.length - 1) span.classList.add('active');
      span.textContent = item.label;
      span.addEventListener('click', () => {
        const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
        clearSelected(doc);
        item.el.classList.add('__styler-selected-outline');
        handleElementSelected(item.el);
      });
      elementBreadcrumbs.appendChild(span);
    });
  }

  function renderSelectorOptions(candidates) {
    selectorOptions.innerHTML = '';
    candidates.forEach((cand, idx) => {
      const btn = document.createElement('button');
      btn.className = 'selector-chip';
      btn.dataset.selector = cand.selector;
      btn.textContent = cand.label;
      btn.addEventListener('click', () => {
        setActiveSelector(cand.selector);
      });
      selectorOptions.appendChild(btn);
    });
  }

  // --- INSPECTOR UI SYNC ---
  function populateInspectorForSelector(fullSelector) {
    const rule = state.styleRules[fullSelector] || {};

    // 1. Typography
    const fontFamilySelect = document.getElementById('css-font-family');
    const customFontInput = document.getElementById('css-font-family-custom');
    const currentFont = rule['font-family'] || '';

    let matchedOption = false;
    Array.from(fontFamilySelect.options).forEach(opt => {
      if (opt.value === currentFont) {
        fontFamilySelect.value = currentFont;
        matchedOption = true;
      }
    });
    if (!matchedOption && currentFont) {
      fontFamilySelect.value = 'custom';
      customFontInput.classList.remove('hidden');
      customFontInput.value = currentFont;
    } else {
      customFontInput.classList.add('hidden');
    }

    // Font size
    const fontSize = rule['font-size'] || '';
    const fsMatch = fontSize.match(/^([\d.]+)(rem|px|em|%)$/);
    if (fsMatch) {
      document.getElementById('css-font-size-val').value = fsMatch[1];
      document.getElementById('css-font-size-unit').value = fsMatch[2];
    } else {
      document.getElementById('css-font-size-val').value = '';
    }

    // Line height
    document.getElementById('css-line-height-val').value = rule['line-height'] || '';

    // Font weight
    document.getElementById('css-font-weight').value = rule['font-weight'] || '';

    // Letter spacing
    const letterSpacing = rule['letter-spacing'] || '';
    const lsMatch = letterSpacing.match(/^([\d.-]+)(em|px)$/);
    if (lsMatch) {
      document.getElementById('css-letter-spacing-val').value = lsMatch[1];
      document.getElementById('css-letter-spacing-unit').value = lsMatch[2];
    } else {
      document.getElementById('css-letter-spacing-val').value = '';
    }

    // Color
    const textColor = rule['color'] || '';
    document.getElementById('css-color-text').value = textColor;
    if (textColor.startsWith('#') && textColor.length === 7) {
      document.getElementById('css-color-picker').value = textColor;
    }

    // Text Align
    const textAlign = rule['text-align'] || '';
    document.querySelectorAll('#align-control .segmented-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.align === textAlign);
    });

    // Transform & Decoration
    document.getElementById('css-text-transform').value = rule['text-transform'] || '';
    document.getElementById('css-text-decoration').value = rule['text-decoration'] || '';

    // 2. Background
    const bgColor = rule['background-color'] || '';
    document.getElementById('css-bg-color-text').value = bgColor;
    if (bgColor.startsWith('#') && bgColor.length === 7) {
      document.getElementById('css-bg-color-picker').value = bgColor;
    }
    document.getElementById('css-background-custom').value = rule['background'] || '';

    // 3. Spacing (Box Model)
    ['margin-top', 'margin-right', 'margin-bottom', 'margin-left',
     'padding-top', 'padding-right', 'padding-bottom', 'padding-left'].forEach(prop => {
      const input = bmInputs[prop];
      if (input) {
        input.value = rule[prop] || '';
      }
    });

    document.getElementById('quick-margin-input').value = rule['margin'] || '';
    document.getElementById('quick-padding-input').value = rule['padding'] || '';

    // 4. Layout & Flex
    const displayVal = rule['display'] || '';
    document.getElementById('css-display').value = displayVal;
    const flexBox = document.getElementById('flex-controls');
    if (displayVal === 'flex' || displayVal === 'inline-flex') {
      flexBox.classList.remove('hidden');
      document.getElementById('css-flex-direction').value = rule['flex-direction'] || 'row';
      document.getElementById('css-flex-wrap').value = rule['flex-wrap'] || 'nowrap';
      document.getElementById('css-justify-content').value = rule['justify-content'] || 'flex-start';
      document.getElementById('css-align-items').value = rule['align-items'] || 'stretch';
      
      const gapVal = rule['gap'] || '';
      const gapMatch = gapVal.match(/^([\d.]+)(rem|px)$/);
      if (gapMatch) {
        document.getElementById('css-gap-val').value = gapMatch[1];
        document.getElementById('css-gap-unit').value = gapMatch[2];
      } else {
        document.getElementById('css-gap-val').value = '';
      }
    } else {
      flexBox.classList.add('hidden');
    }

    document.getElementById('css-width').value = rule['width'] || '';
    document.getElementById('css-max-width').value = rule['max-width'] || '';
    document.getElementById('css-min-height').value = rule['min-height'] || '';
    document.getElementById('css-overflow').value = rule['overflow'] || '';

    // 5. Borders & Radius
    const borderVal = rule['border'] || '';
    const borderWidth = rule['border-width'] || '';
    const borderStyle = rule['border-style'] || (borderVal.includes('solid') ? 'solid' : 'none');
    const borderColor = rule['border-color'] || '';
    const borderRadius = rule['border-radius'] || '0px';

    document.getElementById('css-border-style').value = borderStyle;
    document.getElementById('css-border-width-val').value = borderWidth.replace('px', '');
    document.getElementById('css-border-color-text').value = borderColor;
    if (borderColor.startsWith('#') && borderColor.length === 7) {
      document.getElementById('css-border-color-picker').value = borderColor;
    }

    document.getElementById('css-border-radius-text').value = borderRadius;
    const numRadius = parseInt(borderRadius) || 0;
    document.getElementById('css-border-radius-slider').value = Math.min(numRadius, 40);
    document.getElementById('radius-preview-text').textContent = borderRadius;

    // 6. Shadows & Effects
    const shadowVal = rule['box-shadow'] || '';
    document.getElementById('css-box-shadow').value = shadowVal;
    document.querySelectorAll('#shadow-presets .segmented-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.shadow === shadowVal);
    });

    document.getElementById('css-opacity-slider').value = rule['opacity'] !== undefined ? rule['opacity'] : '1';
    document.getElementById('css-cursor').value = rule['cursor'] || '';
    document.getElementById('css-transition').value = rule['transition'] || '';

    // 7. Update Raw CSS Box
    updateRawCssDisplay(fullSelector);

    // 8. Update Badge Counters
    updateInspectorBadges(fullSelector);
  }

  function updateRawCssDisplay(fullSelector) {
    const rule = state.styleRules[fullSelector] || {};
    const lines = [];
    for (const [prop, val] of Object.entries(rule)) {
      lines.push(`${prop}: ${val};`);
    }
    rawCssTextarea.value = lines.join('\n');
  }

  function updateInspectorBadges(fullSelector) {
    const rule = state.styleRules[fullSelector] || {};

    const typoProps = ['font-family', 'font-size', 'line-height', 'font-weight', 'letter-spacing', 'color', 'text-align', 'text-transform', 'text-decoration'];
    const bgProps = ['background-color', 'background'];
    const spacingProps = ['margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left', 'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left'];
    const layoutProps = ['display', 'flex-direction', 'flex-wrap', 'justify-content', 'align-items', 'gap', 'width', 'max-width', 'min-height', 'overflow'];
    const borderProps = ['border', 'border-width', 'border-style', 'border-color', 'border-radius'];
    const effectProps = ['box-shadow', 'opacity', 'cursor', 'transition'];

    updateBadge('badge-typography', countProps(rule, typoProps));
    updateBadge('badge-background', countProps(rule, bgProps));
    updateBadge('badge-spacing', countProps(rule, spacingProps));
    updateBadge('badge-layout', countProps(rule, layoutProps));
    updateBadge('badge-borders', countProps(rule, borderProps));
    updateBadge('badge-effects', countProps(rule, effectProps));
  }

  function countProps(rule, propList) {
    return propList.filter(p => rule[p] !== undefined && rule[p] !== '').length;
  }

  function updateBadge(id, count) {
    const badge = document.getElementById(id);
    if (!badge) return;
    badge.textContent = count;
    badge.classList.toggle('has-values', count > 0);
  }

  // --- BINDING FORM CONTROLS ---
  function setupEventListeners() {
    // Custom Selector Input
    document.getElementById('btn-apply-custom-selector').addEventListener('click', () => {
      const customVal = customSelectorInput.value.trim();
      if (customVal) {
        setActiveSelector(customVal);
      }
    });
    customSelectorInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const customVal = customSelectorInput.value.trim();
        if (customVal) setActiveSelector(customVal);
      }
    });

    // Pseudo-class select (:hover, :focus, etc.)
    pseudoStateSelect.addEventListener('change', (e) => {
      state.pseudoState = e.target.value;
      const full = getCurrentFullSelector();
      currentSelectorDisplay.textContent = full;
      rawCssSelectorLabel.textContent = full;
      populateInspectorForSelector(full);
    });

    // Reset Rule button
    document.getElementById('btn-reset-rule').addEventListener('click', resetCurrentRule);

    // Undo / Redo
    document.getElementById('btn-undo').addEventListener('click', undo);
    document.getElementById('btn-redo').addEventListener('click', redo);
    window.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      } else if ((e.metaKey || e.ctrlKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
      }
    });

    // Viewport switcher
    document.querySelectorAll('#viewport-control .segmented-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#viewport-control .segmented-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const vp = btn.dataset.viewport;
        state.activeViewport = vp;
        viewportFrame.className = `preview-viewport ${vp}`;
      });
    });

    // Inspect mode toggle
    const inspectBtn = document.getElementById('btn-toggle-inspect');
    inspectBtn.addEventListener('click', () => {
      state.inspectMode = !state.inspectMode;
      inspectBtn.classList.toggle('active', state.inspectMode);
      if (!state.inspectMode) {
        const doc = previewFrame.contentDocument || previewFrame.contentWindow.document;
        if (doc) clearHovers(doc);
      }
    });

    // Typography: Font Family
    const fontFamilySelect = document.getElementById('css-font-family');
    const customFontInput = document.getElementById('css-font-family-custom');
    fontFamilySelect.addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      if (e.target.value === 'custom') {
        customFontInput.classList.remove('hidden');
        customFontInput.focus();
      } else {
        customFontInput.classList.add('hidden');
        setRuleProperty(full, 'font-family', e.target.value);
      }
    });
    customFontInput.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'font-family', e.target.value);
    });

    // Typography: Font Size
    const fsVal = document.getElementById('css-font-size-val');
    const fsUnit = document.getElementById('css-font-size-unit');
    function updateFontSize() {
      const full = getCurrentFullSelector();
      const val = fsVal.value.trim();
      setRuleProperty(full, 'font-size', val ? `${val}${fsUnit.value}` : '');
    }
    fsVal.addEventListener('input', updateFontSize);
    fsUnit.addEventListener('change', updateFontSize);

    // Typography: Line Height
    const lhVal = document.getElementById('css-line-height-val');
    lhVal.addEventListener('input', () => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'line-height', lhVal.value.trim());
    });

    // Typography: Font Weight
    document.getElementById('css-font-weight').addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'font-weight', e.target.value);
    });

    // Typography: Letter Spacing
    const lsVal = document.getElementById('css-letter-spacing-val');
    const lsUnit = document.getElementById('css-letter-spacing-unit');
    function updateLetterSpacing() {
      const full = getCurrentFullSelector();
      const val = lsVal.value.trim();
      setRuleProperty(full, 'letter-spacing', val ? `${val}${lsUnit.value}` : '');
    }
    lsVal.addEventListener('input', updateLetterSpacing);
    lsUnit.addEventListener('change', updateLetterSpacing);

    // Text Color
    const colorPicker = document.getElementById('css-color-picker');
    const colorText = document.getElementById('css-color-text');
    colorPicker.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      colorText.value = e.target.value;
      setRuleProperty(full, 'color', e.target.value);
    });
    colorText.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'color', e.target.value);
      if (e.target.value.startsWith('#') && e.target.value.length === 7) {
        colorPicker.value = e.target.value;
      }
    });

    // Text Align
    document.querySelectorAll('#align-control .segmented-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const full = getCurrentFullSelector();
        const align = btn.dataset.align;
        const currentAlign = (state.styleRules[full] || {})['text-align'];
        const newAlign = currentAlign === align ? '' : align;
        setRuleProperty(full, 'text-align', newAlign);
        document.querySelectorAll('#align-control .segmented-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.align === newAlign);
        });
      });
    });

    // Text Transform & Decoration
    document.getElementById('css-text-transform').addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'text-transform', e.target.value);
    });
    document.getElementById('css-text-decoration').addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'text-decoration', e.target.value);
    });

    // Background Color & Palette
    const bgPicker = document.getElementById('css-bg-color-picker');
    const bgText = document.getElementById('css-bg-color-text');
    bgPicker.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      bgText.value = e.target.value;
      setRuleProperty(full, 'background-color', e.target.value);
    });
    bgText.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'background-color', e.target.value);
      if (e.target.value.startsWith('#') && e.target.value.length === 7) {
        bgPicker.value = e.target.value;
      }
    });

    // Quick Palette Swatches
    document.querySelectorAll('.quick-palette .swatch').forEach(swatch => {
      swatch.addEventListener('click', () => {
        const full = getCurrentFullSelector();
        const col = swatch.dataset.color;
        bgText.value = col;
        if (col.startsWith('#')) bgPicker.value = col;
        setRuleProperty(full, 'background-color', col);
      });
    });

    document.getElementById('css-background-custom').addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'background', e.target.value);
    });

    // Box Model inputs
    Object.entries(bmInputs).forEach(([prop, input]) => {
      input.addEventListener('input', () => {
        const full = getCurrentFullSelector();
        setRuleProperty(full, prop, input.value.trim());
      });
    });

    // Quick Margin & Padding linkers
    document.getElementById('quick-margin-input').addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'margin', e.target.value.trim());
    });
    document.getElementById('quick-padding-input').addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'padding', e.target.value.trim());
    });

    document.getElementById('btn-link-margin').addEventListener('click', () => {
      const topVal = bmInputs['margin-top'].value || '0';
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'margin', topVal);
      ['margin-top', 'margin-right', 'margin-bottom', 'margin-left'].forEach(p => {
        removeRuleProperty(full, p);
      });
      document.getElementById('quick-margin-input').value = topVal;
    });

    document.getElementById('btn-link-padding').addEventListener('click', () => {
      const topVal = bmInputs['padding-top'].value || '0';
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'padding', topVal);
      ['padding-top', 'padding-right', 'padding-bottom', 'padding-left'].forEach(p => {
        removeRuleProperty(full, p);
      });
      document.getElementById('quick-padding-input').value = topVal;
    });

    // Display & Flexbox
    const displaySelect = document.getElementById('css-display');
    displaySelect.addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      const val = e.target.value;
      setRuleProperty(full, 'display', val);
      const flexBox = document.getElementById('flex-controls');
      flexBox.classList.toggle('hidden', val !== 'flex' && val !== 'inline-flex');
    });

    ['flex-direction', 'flex-wrap', 'justify-content', 'align-items'].forEach(prop => {
      const el = document.getElementById(`css-${prop}`);
      if (el) {
        el.addEventListener('change', (e) => {
          const full = getCurrentFullSelector();
          setRuleProperty(full, prop, e.target.value);
        });
      }
    });

    // Flex Gap
    const gapVal = document.getElementById('css-gap-val');
    const gapUnit = document.getElementById('css-gap-unit');
    function updateGap() {
      const full = getCurrentFullSelector();
      const val = gapVal.value.trim();
      setRuleProperty(full, 'gap', val ? `${val}${gapUnit.value}` : '');
    }
    gapVal.addEventListener('input', updateGap);
    gapUnit.addEventListener('change', updateGap);

    // Dimensions
    ['width', 'max-width', 'min-height', 'overflow'].forEach(prop => {
      const el = document.getElementById(`css-${prop}`);
      if (el) {
        el.addEventListener('input', (e) => {
          const full = getCurrentFullSelector();
          setRuleProperty(full, prop, e.target.value.trim());
        });
        el.addEventListener('change', (e) => {
          const full = getCurrentFullSelector();
          setRuleProperty(full, prop, e.target.value.trim());
        });
      }
    });

    // Borders
    const borderStyleSelect = document.getElementById('css-border-style');
    const borderWidthVal = document.getElementById('css-border-width-val');
    const borderColorText = document.getElementById('css-border-color-text');
    const borderColorPicker = document.getElementById('css-border-color-picker');

    function updateBorder() {
      const full = getCurrentFullSelector();
      const style = borderStyleSelect.value;
      const width = borderWidthVal.value.trim();
      const color = borderColorText.value.trim();

      if (style === 'none' || (!width && !color)) {
        setRuleProperty(full, 'border', style === 'none' ? 'none' : '');
        removeRuleProperty(full, 'border-width');
        removeRuleProperty(full, 'border-style');
        removeRuleProperty(full, 'border-color');
      } else {
        setRuleProperty(full, 'border-style', style);
        if (width) setRuleProperty(full, 'border-width', `${width}px`);
        if (color) setRuleProperty(full, 'border-color', color);
      }
    }
    borderStyleSelect.addEventListener('change', updateBorder);
    borderWidthVal.addEventListener('input', updateBorder);
    borderColorPicker.addEventListener('input', (e) => {
      borderColorText.value = e.target.value;
      updateBorder();
    });
    borderColorText.addEventListener('input', (e) => {
      if (e.target.value.startsWith('#') && e.target.value.length === 7) {
        borderColorPicker.value = e.target.value;
      }
      updateBorder();
    });

    // Border Radius Slider & Pills
    const radiusSlider = document.getElementById('css-border-radius-slider');
    const radiusText = document.getElementById('css-border-radius-text');
    const radiusPreview = document.getElementById('radius-preview-text');

    radiusSlider.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      const val = `${e.target.value}px`;
      radiusText.value = val;
      radiusPreview.textContent = val;
      setRuleProperty(full, 'border-radius', val);
    });
    radiusText.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      radiusPreview.textContent = e.target.value;
      setRuleProperty(full, 'border-radius', e.target.value);
    });
    document.querySelectorAll('.preset-radius-pills .pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const full = getCurrentFullSelector();
        const rad = btn.dataset.radius;
        radiusText.value = rad;
        radiusSlider.value = parseInt(rad) || 0;
        radiusPreview.textContent = rad;
        setRuleProperty(full, 'border-radius', rad);
      });
    });

    // Box Shadow Presets & Custom
    const shadowInput = document.getElementById('css-box-shadow');
    document.querySelectorAll('#shadow-presets .segmented-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const full = getCurrentFullSelector();
        const shadow = btn.dataset.shadow;
        shadowInput.value = shadow;
        setRuleProperty(full, 'box-shadow', shadow);
        document.querySelectorAll('#shadow-presets .segmented-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
    shadowInput.addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'box-shadow', e.target.value);
    });

    // Opacity, Cursor, Transitions
    document.getElementById('css-opacity-slider').addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'opacity', e.target.value);
    });
    document.getElementById('css-cursor').addEventListener('change', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'cursor', e.target.value);
    });
    document.getElementById('css-transition').addEventListener('input', (e) => {
      const full = getCurrentFullSelector();
      setRuleProperty(full, 'transition', e.target.value);
    });

    // Clear property buttons
    document.querySelectorAll('.btn-clear-prop').forEach(btn => {
      btn.addEventListener('click', () => {
        const full = getCurrentFullSelector();
        const prop = btn.dataset.prop;
        removeRuleProperty(full, prop);
      });
    });

    // Direct Raw CSS editor for active selector
    document.getElementById('btn-sync-raw-css').addEventListener('click', applyRawCssForCurrentSelector);
    rawCssTextarea.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        applyRawCssForCurrentSelector();
      }
    });

    // Presets
    document.querySelectorAll('.btn-preset').forEach(btn => {
      btn.addEventListener('click', () => {
        applyThemePreset(btn.dataset.preset);
      });
    });

    // Open File Input
    const fileInput = document.getElementById('html-file-input');
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (evt) {
          state.htmlContent = evt.target.result;
          renderPreview();
          showToast(`Loaded ${file.name}`);
          pushHistorySnapshot();
        };
        reader.readAsText(file);
      }
    });
  }

  // --- RAW CSS PARSER / SYNCHRONIZER ---
  function applyRawCssForCurrentSelector() {
    const full = getCurrentFullSelector();
    const rawText = rawCssTextarea.value;
    const lines = rawText.split('\n');
    const newProps = {};

    lines.forEach(line => {
      const clean = line.replace(/;$/, '').trim();
      const colonIndex = clean.indexOf(':');
      if (colonIndex > 0) {
        const prop = clean.slice(0, colonIndex).trim();
        const val = clean.slice(colonIndex + 1).trim();
        if (prop && val) {
          newProps[prop] = val;
        }
      }
    });

    state.styleRules[full] = newProps;
    applyStylesToPreview();
    populateInspectorForSelector(full);
    pushHistorySnapshot();
    showToast(`Updated CSS for ${full}`);
  }

  // --- THEME PRESETS ---
  function applyThemePreset(presetName) {
    if (presetName === 'studio-dark') {
      state.styleRules = {
        '*': {
          'box-sizing': 'border-box',
          'margin': '0',
          'padding': '0'
        },
        'body': {
          'font-family': "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
          'background-color': '#0f1117',
          'color': '#f3f4f6',
          'line-height': '1.6',
          'padding': '2rem 1rem 4rem 1rem'
        },
        '.container, .content-wrapper, .page-container, main': {
          'max-width': '960px',
          'width': '100%',
          'margin': '0 auto'
        },
        'header, .site-header': {
          'display': 'flex',
          'justify-content': 'space-between',
          'align-items': 'center',
          'padding-bottom': '1.5rem',
          'margin-bottom': '2rem',
          'border-bottom': '1px solid rgba(255, 255, 255, 0.1)'
        },
        'a': {
          'color': '#9ca3af',
          'text-decoration': 'none',
          'transition': 'color 0.2s ease'
        },
        'a:hover': {
          'color': '#f3f4f6'
        },
        'article, .work, .card': {
          'background-color': '#171b24',
          'border': '1px solid #242b3a',
          'border-radius': '12px',
          'padding': '2rem',
          'box-shadow': '0 8px 30px rgba(0, 0, 0, 0.4)'
        },
        'h1, .post-title': {
          'font-size': '2rem',
          'font-weight': '700',
          'letter-spacing': '-0.02em',
          'margin-bottom': '0.75rem',
          'color': '#ffffff'
        },
        'h2': {
          'font-size': '1.4rem',
          'font-weight': '600',
          'margin-top': '1.5rem',
          'margin-bottom': '0.5rem',
          'color': '#ffffff'
        },
        'p': {
          'margin-bottom': '1.25rem',
          'color': '#d1d5db',
          'font-size': '1.05rem'
        },
        'img': {
          'max-width': '100%',
          'width': '100%',
          'height': 'auto',
          'display': 'block',
          'border-radius': '8px',
          'margin': '1.25rem 0',
          'box-shadow': '0 4px 20px rgba(0, 0, 0, 0.5)'
        },
        'blockquote': {
          'border-left': '3px solid #3b82f6',
          'padding-left': '1rem',
          'margin': '1.5rem 0',
          'color': '#9ca3af',
          'font-style': 'italic'
        },
        'button, .nav-btn, .btn-primary': {
          'display': 'inline-flex',
          'align-items': 'center',
          'padding': '0.6rem 1.2rem',
          'background-color': '#242b3a',
          'color': '#f3f4f6',
          'border-radius': '8px',
          'font-size': '0.95rem',
          'font-weight': '500',
          'border': '1px solid rgba(255, 255, 255, 0.08)',
          'cursor': 'pointer'
        },
        '.nav-bar': {
          'margin-top': '2rem',
          'display': 'flex',
          'flex-direction': 'column',
          'gap': '1.25rem'
        },
        '.nav-controls': {
          'display': 'flex',
          'justify-content': 'space-between',
          'align-items': 'center',
          'gap': '1rem'
        }
      };
    } else if (presetName === 'editorial') {
      state.styleRules = {
        '*': { 'box-sizing': 'border-box', 'margin': '0', 'padding': '0' },
        'body': {
          'background-color': '#faf8f5',
          'color': '#292524',
          'font-family': "'Merriweather', Georgia, serif",
          'line-height': '1.75',
          'padding': '3rem 1.5rem'
        },
        '.container, .content-wrapper, main': {
          'max-width': '740px',
          'margin': '0 auto'
        },
        'h1, h2, h3, .site-title': {
          'font-family': "'Playfair Display', Georgia, serif",
          'color': '#1c1917',
          'line-height': '1.3'
        },
        'h1': { 'font-size': '2.4rem', 'margin-bottom': '1rem' },
        'h2': { 'font-size': '1.6rem', 'margin-top': '2rem', 'margin-bottom': '0.75rem' },
        'p': { 'margin-bottom': '1.5rem', 'font-size': '1.1rem', 'color': '#44403c' },
        'a': { 'color': '#b45309', 'text-decoration': 'underline' },
        'blockquote': {
          'border-left': '3px solid #d97706',
          'padding': '0.5rem 1.5rem',
          'margin': '2rem 0',
          'font-style': 'italic',
          'color': '#78716c'
        }
      };
    } else if (presetName === 'modern-clean') {
      state.styleRules = {
        '*': { 'box-sizing': 'border-box', 'margin': '0', 'padding': '0' },
        'body': {
          'background-color': '#f8fafc',
          'color': '#0f172a',
          'font-family': "'Plus Jakarta Sans', sans-serif",
          'line-height': '1.6',
          'padding': '2.5rem 1.5rem'
        },
        '.container, .content-wrapper, main': {
          'max-width': '960px',
          'margin': '0 auto'
        },
        'article, .work, .card': {
          'background-color': '#ffffff',
          'border': '1px solid #e2e8f0',
          'border-radius': '12px',
          'padding': '2rem',
          'box-shadow': '0 4px 15px rgba(0, 0, 0, 0.04)'
        },
        'h1': { 'font-size': '2rem', 'font-weight': '700', 'margin-bottom': '0.75rem', 'color': '#0f172a' },
        'p': { 'color': '#475569', 'margin-bottom': '1.25rem' },
        'button, .btn-primary': {
          'background-color': '#3b82f6',
          'color': '#ffffff',
          'padding': '0.6rem 1.2rem',
          'border-radius': '6px',
          'border': 'none',
          'font-weight': '500'
        }
      };
    } else if (presetName === 'terminal') {
      state.styleRules = {
        '*': { 'box-sizing': 'border-box', 'margin': '0', 'padding': '0' },
        'body': {
          'background-color': '#0a0a0c',
          'color': '#00ff66',
          'font-family': "'JetBrains Mono', monospace",
          'line-height': '1.6',
          'padding': '2rem'
        },
        'a': { 'color': '#00e5ff', 'text-decoration': 'underline' },
        'article, .work': {
          'border': '1px solid #00ff66',
          'padding': '1.5rem'
        },
        'h1, h2, h3': { 'color': '#00e5ff', 'margin-bottom': '1rem' }
      };
    } else if (presetName === 'minimal-reset') {
      state.styleRules = {
        '*': { 'box-sizing': 'border-box', 'margin': '0', 'padding': '0' },
        'body': {
          'font-family': "system-ui, -apple-system, sans-serif",
          'line-height': '1.5',
          'color': '#111827',
          'padding': '2rem'
        },
        'h1, h2, h3': { 'margin-bottom': '0.5rem' },
        'p': { 'margin-bottom': '1rem' }
      };
    }

    applyStylesToPreview();
    populateInspectorForSelector(getCurrentFullSelector());
    pushHistorySnapshot();
    showToast(`Applied "${presetName}" theme preset`);
  }

  // --- SAMPLE LOADERS ---
  function loadSample(sampleName) {
    const sampleFiles = {
      'portfolio': 'samples/portfolio.html',
      'blog-post': 'samples/blog-post.html',
      'components': 'samples/components.html'
    };

    if (sampleName === 'minimal') {
      state.htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Minimal Sample</title>
</head>
<body>
  <div class="container">
    <header>
      <h1>Document Title</h1>
      <p class="subtitle">A clean semantic document without styles.</p>
    </header>
    <main>
      <h2>Section One</h2>
      <p>This is a paragraph of text ready for visual styling. Select any element to change its typography, color, spacing, and layout.</p>
      <button class="btn">Click Action</button>
    </main>
  </div>
</body>
</html>`;
      renderPreview();
      pushHistorySnapshot();
      showToast('Loaded minimal sample');
      return;
    }

    const filePath = sampleFiles[sampleName];
    if (filePath) {
      fetch(filePath)
        .then(res => {
          if (!res.ok) throw new Error('File not found');
          return res.text();
        })
        .then(html => {
          state.htmlContent = html;
          renderPreview();
          pushHistorySnapshot();
          showToast(`Loaded ${sampleName} sample`);
        })
        .catch(err => {
          console.error(err);
          showToast(`Error loading sample: ${err.message}`, 'error');
        });
    }
  }

  // --- EXPORT & SAVE ---
  function setupDropdowns() {
    document.querySelectorAll('.dropdown-toggle').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const parent = btn.closest('.dropdown');
        const isOpen = parent.classList.contains('open');
        document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
        if (!isOpen) parent.classList.add('open');
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
    });

    // Sample picker items
    document.querySelectorAll('#samples-menu .dropdown-item').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        loadSample(item.dataset.sample);
      });
    });

    // Export items
    document.getElementById('export-css-file').addEventListener('click', (e) => {
      e.preventDefault();
      downloadFile('style.css', generateCSSString(), 'text/css');
      showToast('Downloaded style.css');
    });

    document.getElementById('export-html-embedded').addEventListener('click', (e) => {
      e.preventDefault();
      const fullHtml = getExportHTML(true);
      downloadFile('index.html', fullHtml, 'text/html');
      showToast('Downloaded index.html with embedded CSS');
    });

    document.getElementById('export-html-linked').addEventListener('click', (e) => {
      e.preventDefault();
      const fullHtml = getExportHTML(false);
      downloadFile('index.html', fullHtml, 'text/html');
      showToast('Downloaded index.html with linked style.css');
    });

    document.getElementById('copy-css-clipboard').addEventListener('click', (e) => {
      e.preventDefault();
      navigator.clipboard.writeText(generateCSSString()).then(() => {
        showToast('CSS copied to clipboard!');
      });
    });

    document.getElementById('export-project-json').addEventListener('click', (e) => {
      e.preventDefault();
      const data = JSON.stringify({
        html: state.htmlContent,
        styles: state.styleRules,
        exportedAt: new Date().toISOString()
      }, null, 2);
      downloadFile('style-studio-project.json', data, 'application/json');
      showToast('Downloaded project configuration');
    });
  }

  function getExportHTML(embedded = true) {
    const css = generateCSSString();
    let html = state.htmlContent;

    // Clean existing style/css link
    html = html.replace(/<style id="__styler-[^>]*>[\s\S]*?<\/style>/gi, '');
    html = html.replace(/<link id="google-font-[^>]*>/gi, '');

    if (embedded) {
      const styleBlock = `\n  <style>\n${css.split('\n').map(l => '    ' + l).join('\n')}\n  </style>\n`;
      if (html.includes('</head>')) {
        return html.replace('</head>', `${styleBlock}</head>`);
      } else {
        return `<head>${styleBlock}</head>\n${html}`;
      }
    } else {
      const linkTag = `\n  <link rel="stylesheet" href="style.css">\n`;
      if (html.includes('</head>')) {
        return html.replace('</head>', `${linkTag}</head>`);
      } else {
        return `<head>${linkTag}</head>\n${html}`;
      }
    }
  }

  function downloadFile(filename, text, mimeType) {
    const blob = new Blob([text], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // --- MODALS (FULL CSS & PASTE HTML) ---
  function setupModals() {
    // Open Full CSS Modal
    document.getElementById('btn-view-css').addEventListener('click', () => {
      const fullCssEditor = document.getElementById('full-css-editor');
      fullCssEditor.value = generateCSSString();
      document.getElementById('modal-full-css').classList.remove('hidden');
    });

    document.getElementById('btn-copy-css-modal').addEventListener('click', () => {
      const fullCssEditor = document.getElementById('full-css-editor');
      navigator.clipboard.writeText(fullCssEditor.value).then(() => {
        showToast('CSS copied to clipboard!');
      });
    });

    document.getElementById('btn-download-css-modal').addEventListener('click', () => {
      const fullCssEditor = document.getElementById('full-css-editor');
      downloadFile('style.css', fullCssEditor.value, 'text/css');
      showToast('Downloaded style.css');
    });

    // Apply full CSS edits
    document.getElementById('btn-apply-full-css').addEventListener('click', () => {
      const raw = document.getElementById('full-css-editor').value;
      parseAndUpdateFullCSS(raw);
      document.getElementById('modal-full-css').classList.add('hidden');
      showToast('Stylesheet updated successfully');
    });

    // Paste HTML Modal
    document.getElementById('btn-paste-html').addEventListener('click', () => {
      document.getElementById('paste-html-textarea').value = '';
      document.getElementById('modal-paste-html').classList.remove('hidden');
    });

    document.getElementById('btn-load-pasted-html').addEventListener('click', () => {
      const pasted = document.getElementById('paste-html-textarea').value.trim();
      const strip = document.getElementById('chk-paste-strip-styles').checked;
      if (pasted) {
        state.htmlContent = pasted;
        const chkStrip = document.getElementById('chk-strip-styles');
        if (chkStrip) chkStrip.checked = strip;
        renderPreview();
        pushHistorySnapshot();
        document.getElementById('modal-paste-html').classList.add('hidden');
        showToast('Loaded pasted HTML into editor');
      }
    });

    // Close Modal buttons
    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => {
        const modalId = btn.dataset.close;
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('hidden');
      });
    });

    // Close modal on background click
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
      backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) {
          backdrop.classList.add('hidden');
        }
      });
    });
  }

  // --- CSS PARSER FOR FULL STYLESHEET ---
  function parseAndUpdateFullCSS(cssString) {
    const newRules = {};

    // Remove comments
    const cleaned = cssString.replace(/\/\*[\s\S]*?\*\//g, '');

    // Match rules: selector { ... }
    const ruleRegex = /([^{]+)\{([^}]+)\}/g;
    let match;
    while ((match = ruleRegex.exec(cleaned)) !== null) {
      const selector = match[1].trim();
      const body = match[2].trim();
      if (!selector || selector.startsWith('@import') || selector.startsWith('@keyframes')) continue;

      if (!newRules[selector]) newRules[selector] = {};

      const decls = body.split(';');
      decls.forEach(decl => {
        const colonIdx = decl.indexOf(':');
        if (colonIdx > 0) {
          const prop = decl.slice(0, colonIdx).trim();
          const val = decl.slice(colonIdx + 1).trim();
          if (prop && val) {
            newRules[selector][prop] = val;
          }
        }
      });
    }

    state.styleRules = newRules;
    applyStylesToPreview();
    populateInspectorForSelector(getCurrentFullSelector());
    pushHistorySnapshot();
  }

  // --- SPLIT PANE RESIZER ---
  function setupPaneResizer() {
    const resizer = document.getElementById('pane-resizer');
    const inspectorPane = document.getElementById('inspector-pane');
    let isDragging = false;

    resizer.addEventListener('mousedown', (e) => {
      isDragging = true;
      resizer.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= 320 && newWidth <= 750) {
        inspectorPane.style.width = `${newWidth}px`;
      }
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        resizer.classList.remove('resizing');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    });
  }

  // --- TOAST NOTIFICATIONS ---
  function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 2800);
  }

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
