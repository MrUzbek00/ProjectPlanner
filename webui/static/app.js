// Small progressive enhancements. Every page works without this script.
(function () {
  // Table filtering: <input data-filter="tableId"> and <select data-filter="tableId" data-column="type">.
  function apply(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const controls = document.querySelectorAll('[data-filter="' + tableId + '"]');
    table.querySelectorAll("tbody tr").forEach(function (row) {
      let visible = true;
      controls.forEach(function (control) {
        const value = control.value.trim().toLowerCase();
        if (!value) return;
        const column = control.dataset.column;
        const haystack = column ? (row.dataset[column] || "") : row.textContent;
        if (column ? haystack.toLowerCase() !== value : !haystack.toLowerCase().includes(value)) visible = false;
      });
      row.hidden = !visible;
    });
  }
  document.querySelectorAll("[data-filter]").forEach(function (control) {
    control.addEventListener("input", function () { apply(control.dataset.filter); });
  });

  // Expand or collapse every gate card at once.
  document.querySelectorAll("[data-toggle-all]").forEach(function (button) {
    button.addEventListener("click", function () {
      const items = document.querySelectorAll(button.dataset.toggleAll);
      const open = !Array.from(items).every(function (d) { return d.open; });
      items.forEach(function (d) { d.open = open; });
    });
  });

  // A link to #gate-G3 opens that gate card.
  function openHashTarget() {
    if (!location.hash.startsWith("#gate-")) return;
    const target = document.getElementById(location.hash.slice(1));
    if (target && target.tagName === "DETAILS") {
      target.open = true;
      target.scrollIntoView({ block: "center" });
    }
  }
  window.addEventListener("hashchange", openHashTarget);
  openHashTarget();

  // Project picker on the workflow map.
  document.querySelectorAll("select[data-navigate]").forEach(function (select) {
    select.addEventListener("change", function () { location.search = select.value.replace(/^\?/, ""); });
  });

  function remember(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* storage unavailable */ }
  }
  function recall(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // Collapsible sidebar on the workflow map; the choice is remembered per browser.
  const shell = document.querySelector("[data-shell]");
  const sideToggle = document.querySelector("[data-side-toggle]");
  if (shell && sideToggle) {
    function setCollapsed(collapsed) {
      shell.classList.toggle("collapsed", collapsed);
      sideToggle.setAttribute("aria-expanded", String(!collapsed));
      sideToggle.title = collapsed ? "Expand the sidebar" : "Collapse the sidebar";
    }
    setCollapsed(recall("wm-side") === "collapsed");
    sideToggle.addEventListener("click", function () {
      const collapsed = !shell.classList.contains("collapsed");
      setCollapsed(collapsed);
      remember("wm-side", collapsed ? "collapsed" : "open");
    });
    // The stage changes size with the sidebar; let the map re-fit once the transition ends.
    shell.addEventListener("transitionend", function (event) {
      if (event.target === shell) window.dispatchEvent(new Event("resize"));
    });
  }

  // Workflow map: drag to pan, wheel to zoom around the cursor, buttons to zoom or fit.
  const stage = document.querySelector("[data-map-stage]");
  const canvas = document.querySelector("[data-map-canvas]");
  if (stage && canvas) {
    const width = Number(canvas.dataset.width);
    const height = Number(canvas.dataset.height);
    const level = document.querySelector("[data-zoom-level]");
    const MIN = 0.25, MAX = 2.5;
    let scale = 1, x = 0, y = 0;
    let fitted = true;           // follow the window size until the person moves the map
    let drag = null;             // {id, startX, startY, x, y, moved}
    let suppressClick = false;

    function apply() {
      canvas.style.transform = "translate(" + x + "px, " + y + "px) scale(" + scale + ")";
      if (level) level.textContent = Math.round(scale * 100) + "%";
    }
    function fit(animate) {
      const pad = 16;
      const sw = stage.clientWidth - pad * 2, sh = stage.clientHeight - pad * 2;
      scale = Math.max(MIN, Math.min(MAX, Math.min(sw / width, sh / height)));
      x = (stage.clientWidth - width * scale) / 2;
      y = (stage.clientHeight - height * scale) / 2;
      fitted = true;
      animated(animate, apply);
    }
    function animated(on, change) {
      stage.classList.toggle("animate", Boolean(on));
      change();
      if (on) setTimeout(function () { stage.classList.remove("animate"); }, 280);
    }
    function zoomAt(factor, px, py, animate) {
      const next = Math.max(MIN, Math.min(MAX, scale * factor));
      x = px - (px - x) * (next / scale);
      y = py - (py - y) * (next / scale);
      scale = next;
      fitted = false;
      animated(animate, apply);
    }

    stage.addEventListener("pointerdown", function (event) {
      if (event.button !== 0 || event.target.closest(".wm-tools")) return;
      drag = { id: event.pointerId, startX: event.clientX, startY: event.clientY, x: x, y: y, moved: false };
    });
    stage.addEventListener("pointermove", function (event) {
      if (!drag || event.pointerId !== drag.id) return;
      const dx = event.clientX - drag.startX, dy = event.clientY - drag.startY;
      if (!drag.moved && Math.abs(dx) + Math.abs(dy) < 4) return;  // a click, not a drag (yet)
      if (!drag.moved) {
        drag.moved = true;
        stage.setPointerCapture(event.pointerId);
        stage.classList.add("dragging");
      }
      x = drag.x + dx;
      y = drag.y + dy;
      fitted = false;
      apply();
    });
    function endDrag(event) {
      if (!drag || event.pointerId !== drag.id) return;
      if (drag.moved) suppressClick = true;
      stage.classList.remove("dragging");
      drag = null;
    }
    stage.addEventListener("pointerup", endDrag);
    stage.addEventListener("pointercancel", endDrag);
    // A drag that ends on a stage card must not open it.
    stage.addEventListener("click", function (event) {
      if (suppressClick) {
        event.preventDefault();
        event.stopPropagation();
        suppressClick = false;
      }
    }, true);

    stage.addEventListener("wheel", function (event) {
      event.preventDefault();
      const rect = stage.getBoundingClientRect();
      zoomAt(Math.exp(-event.deltaY * 0.0015), event.clientX - rect.left, event.clientY - rect.top, false);
    }, { passive: false });
    stage.addEventListener("dblclick", function (event) {
      if (!event.target.closest(".wm-card, .wm-tools")) fit(true);
    });

    document.querySelectorAll("[data-zoom]").forEach(function (button) {
      button.addEventListener("click", function () {
        const centre = [stage.clientWidth / 2, stage.clientHeight / 2];
        if (button.dataset.zoom === "fit") fit(true);
        else zoomAt(button.dataset.zoom === "in" ? 1.2 : 1 / 1.2, centre[0], centre[1], true);
      });
    });

    // Keyboard: arrows pan, + and - zoom, 0 fits, when the map has focus.
    stage.tabIndex = 0;
    stage.addEventListener("keydown", function (event) {
      const step = 60;
      const moves = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
      if (moves[event.key]) {
        x += moves[event.key][0];
        y += moves[event.key][1];
        fitted = false;
        apply();
      } else if (event.key === "+" || event.key === "=") {
        zoomAt(1.2, stage.clientWidth / 2, stage.clientHeight / 2, true);
      } else if (event.key === "-") {
        zoomAt(1 / 1.2, stage.clientWidth / 2, stage.clientHeight / 2, true);
      } else if (event.key === "0") {
        fit(true);
      } else {
        return;
      }
      event.preventDefault();
    });

    window.addEventListener("resize", function () { if (fitted) fit(false); });
    fit(false);
  }
})();
