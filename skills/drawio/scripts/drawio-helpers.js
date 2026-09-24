// Helper library injected into the draw.io renderer by drawio-eval.mjs before
// every script. Safe to evaluate repeatedly. Exposes `window.D`; the running
// EditorUi (an App instance) is obtained through Draw.loadPlugin, which calls
// back immediately once the editor has started.
(function () {
  if (window.D && window.D.__version === 1) return;

  let ready = null;
  window.__drawioReady = function () {
    if (ready == null) {
      ready = new Promise((resolve, reject) => {
        const t = setTimeout(() => { ready = null; reject(new Error('draw.io editor not initialised yet (splash or dialog open?)')); }, 10000);
        Draw.loadPlugin(ui => { clearTimeout(t); D.ui = ui; resolve(ui); });
      });
    }
    return ready;
  };

  const D = window.D = {
    __version: 1,
    ui: null,
    get graph() { return D.ui.editor.graph; },
    get model() { return D.ui.editor.graph.getModel(); },

    // ---- inspection -------------------------------------------------------
    info() {
      const ui = D.ui, file = ui.getCurrentFile(), m = D.model;
      const all = Object.values(m.cells);
      return {
        file: file ? file.getTitle() : null,
        path: file && file.fileObject ? file.fileObject.path || null : null,
        modified: file ? file.isModified() : null,
        pages: (ui.pages || []).map(p => p.getName()),
        page: ui.currentPage ? ui.currentPage.getName() : null,
        vertices: all.filter(c => c.vertex).length,
        edges: all.filter(c => c.edge).length,
        selected: D.graph.getSelectionCells().map(c => c.id),
        dialog: ui.dialog ? ui.dialog.container.innerText.slice(0, 200) : null,
      };
    },
    cell(id) { return typeof id === 'string' ? D.model.getCell(id) : id; },
    cells(filter) {
      return Object.values(D.model.cells).filter(c => (c.vertex || c.edge) && (!filter || filter(c)));
    },
    label(c) { return D.graph.convertValueToString(D.cell(c)); },
    find(text) {
      const re = text instanceof RegExp ? text : null;
      return D.cells(c => { const l = D.label(c) || ''; return re ? re.test(l) : l.includes(text); });
    },
    describe(c) {
      c = D.cell(c);
      const g = c.geometry, out = { id: c.id, kind: c.vertex ? 'vertex' : 'edge', label: D.label(c), style: c.style || '' };
      if (c.parent && c.parent.id !== D.graph.getDefaultParent().id) out.parent = c.parent.id;
      if (c.vertex && g) Object.assign(out, { x: g.x, y: g.y, w: g.width, h: g.height });
      if (c.edge) { out.source = c.source && c.source.id; out.target = c.target && c.target.id; }
      return out;
    },
    dump() { return D.cells().map(D.describe); },

    // ---- building ---------------------------------------------------------
    // Every mutation goes through one model update so it is a single undo step.
    batch(fn) {
      const m = D.model;
      m.beginUpdate();
      try { return fn(); } finally { m.endUpdate(); }
    },
    vertex(label, style, o) {
      o = o || {};
      const parent = o.parent ? D.cell(o.parent) : D.graph.getDefaultParent();
      return D.graph.insertVertex(parent, o.id || null, label == null ? '' : label,
        o.x || 0, o.y || 0, o.w || 120, o.h || 60, style || 'rounded=1;whiteSpace=wrap;html=1;');
    },
    edge(source, target, label, style, o) {
      o = o || {};
      const parent = o.parent ? D.cell(o.parent) : D.graph.getDefaultParent();
      return D.graph.insertEdge(parent, o.id || null, label == null ? '' : label,
        D.cell(source), D.cell(target), style || 'edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;');
    },
    setLabel(c, label) { D.model.setValue(D.cell(c), label); },
    setStyle(cells, key, value) {
      cells = [].concat(cells).map(D.cell);
      D.graph.setCellStyles(key, value, cells);
    },
    move(c, x, y) {
      c = D.cell(c);
      const g = c.geometry.clone(); g.x = x; g.y = y;
      D.model.setGeometry(c, g);
    },
    resize(c, w, h) {
      c = D.cell(c);
      const g = c.geometry.clone(); g.width = w; g.height = h;
      D.model.setGeometry(c, g);
    },
    remove(cells) { D.graph.removeCells([].concat(cells).map(D.cell), true); },
    clear() { D.batch(() => D.graph.removeCells(D.cells(c => c.parent === D.graph.getDefaultParent()), true)); },
    select(cells) { D.graph.setSelectionCells([].concat(cells).map(D.cell)); },
    undo() { D.ui.editor.undoManager.undo(); },
    redo() { D.ui.editor.undoManager.redo(); },

    // ---- XML --------------------------------------------------------------
    // Current page as an <mxGraphModel> string.
    getXml() { return mxUtils.getPrettyXml(D.ui.editor.getGraphXml()); },
    // Whole file (all pages) as <mxfile>, uncompressed.
    fileXml() { return D.ui.getFileData(null, null, null, null, null, null, null, null, null, true); },
    // Replace the current page with an <mxGraphModel> (or a bare <root>) string. One undo step.
    setXml(xml) {
      let node = mxUtils.parseXml(xml).documentElement;
      if (node.nodeName === 'mxfile') node = node.getElementsByTagName('mxGraphModel')[0];
      if (node.nodeName === 'root') { const w = mxUtils.parseXml('<mxGraphModel/>'); w.documentElement.appendChild(w.importNode(node, true)); node = w.documentElement; }
      if (node == null || node.nodeName !== 'mxGraphModel') throw new Error('setXml expects <mxGraphModel>, <root> or <mxfile>');
      const tmp = new mxGraphModel();
      new mxCodec(node.ownerDocument).decode(node, tmp);
      D.batch(() => D.model.setRoot(tmp.root));
    },
    // Insert an <mxGraphModel> fragment into the current page without clearing it.
    importXml(xml, dx, dy) { return D.ui.importXml(xml, dx || 0, dy || 0, true).map(c => c.id); },

    // ---- layout & view ----------------------------------------------------
    // spec: verticalFlow | horizontalFlow | verticalTree | horizontalTree | radialTree | organic,
    // or an ELK layout array such as [{"layout":"elkLayered","config":{"elk.direction":"RIGHT"}}].
    layout(spec) {
      return new Promise(resolve => D.ui.executeLayoutSpec(spec, () => resolve(true)));
    },
    fit() { D.ui.actions.get('fitWindow').funct(); },

    // ---- pages ------------------------------------------------------------
    pages() { return D.ui.pages.map((p, i) => ({ index: i, name: p.getName(), current: p === D.ui.currentPage })); },
    addPage(name) {
      const ui = D.ui, page = ui.createPage(name, Editor.guid());
      ui.insertPage(page, ui.pages.length);
      ui.selectPage(page);
      return ui.pages.indexOf(page);
    },
    selectPage(which) {
      const ui = D.ui;
      const page = typeof which === 'number' ? ui.pages[which] : ui.pages.find(p => p.getName() === which);
      if (!page) throw new Error('no page ' + which);
      ui.selectPage(page);
    },
    renamePage(name) { D.ui.renamePage(D.ui.currentPage, name); },

    // ---- saving -----------------------------------------------------------
    // Saves the open file to its own path. Resolves when the save has landed.
    save() {
      const ui = D.ui, file = ui.getCurrentFile();
      if (!file || !file.fileObject || !file.fileObject.path)
        throw new Error('this window has no file on disk (Untitled) — reopen via drawio-start.sh <file.drawio>');
      return new Promise((resolve, reject) => {
        ui.saveFile();
        const t0 = Date.now();
        (function poll() {
          if (ui.dialog) return reject(new Error('save opened a dialog: ' + ui.dialog.container.innerText.slice(0, 200)));
          if (!file.isModified() && !file.savingFile) return resolve(file.fileObject.path);
          if (Date.now() - t0 > 15000) return reject(new Error('save did not finish within 15s'));
          setTimeout(poll, 100);
        })();
      });
    },
  };
})();
