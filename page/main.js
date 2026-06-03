(function () {
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeLabel = document.getElementById("themeLabel");
  const progressBar = document.getElementById("progressBar");
  const toTop = document.getElementById("toTop");
  const scatterMount = document.getElementById("overallScatter");
  const scatterDetails = document.getElementById("scatterDetails");
  const leaderboardTabs = document.getElementById("leaderboardTabs");
  const leaderboardStatus = document.getElementById("leaderboardStatus");
  const leaderboardTableWrap = document.getElementById("leaderboardTableWrap");
  const leaderboardSummary = document.getElementById("leaderboardSummary");
  const leaderboardFormula = document.getElementById("leaderboardFormula");
  const sortButtons = Array.from(document.querySelectorAll("[data-sort]"));

  const state = {
    data: null,
    sort: "proc",
    view: "overall"
  };

  function getSavedTheme() {
    return localStorage.getItem("pibench-theme") || "light";
  }

  function updateThemeLabel() {
    if (!themeLabel) return;
    const theme = root.dataset.theme || "light";
    themeLabel.textContent = theme === "dark" ? "Light" : "Dark";
  }

  function setTheme(theme) {
    root.dataset.theme = theme;
    localStorage.setItem("pibench-theme", theme);
    updateThemeLabel();
  }

  function updateProgress() {
    if (!progressBar) return;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const ratio = max <= 0 ? 0 : window.scrollY / max;
    progressBar.style.transform = `scaleX(${Math.min(1, Math.max(0, ratio))})`;
    if (toTop) {
      toTop.classList.toggle("visible", window.scrollY > 600);
    }
  }

  function createNode(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function createSvgNode(name, attrs = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }

  function formatScore(value) {
    return Number(value).toFixed(1);
  }

  function formatError(value) {
    return value === null || value === undefined ? "" : `±${formatScore(value)}`;
  }

  function requireFiniteNumber(value, label) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      throw new Error(`Invalid leaderboard value: ${label}`);
    }
    return number;
  }

  function normalizeLeaderboard(payload) {
    if (!payload || !Array.isArray(payload.domains) || !Array.isArray(payload.models)) {
      throw new Error("leaderboard.json must include domains and models arrays.");
    }

    const domains = payload.domains.map((domain, index) => {
      if (!domain || typeof domain.id !== "string" || typeof domain.label !== "string") {
        throw new Error(`Invalid domain at index ${index}.`);
      }
      return { id: domain.id, label: domain.label };
    });

    const models = payload.models.map((model, index) => {
      if (!model || typeof model.name !== "string") {
        throw new Error(`Invalid model at index ${index}.`);
      }
      const overall = model.overall || {};
      const proc = overall.proc || {};
      const comp = overall.comp || {};
      const domainMetrics = {};

      domains.forEach((domain) => {
        const scores = model.domains && model.domains[domain.id];
        if (!scores) {
          throw new Error(`${model.name} is missing domain scores for ${domain.id}.`);
        }
        domainMetrics[domain.id] = {
          proc: requireFiniteNumber(scores.proc, `${model.name}.${domain.id}.proc`),
          comp: requireFiniteNumber(scores.comp, `${model.name}.${domain.id}.comp`)
        };
      });

      return {
        name: model.name,
        organization: typeof model.organization === "string" ? model.organization : "",
        color: typeof model.color === "string" ? model.color : "#2563eb",
        proc: requireFiniteNumber(proc.mean, `${model.name}.overall.proc.mean`),
        procSd: proc.sd === undefined ? null : requireFiniteNumber(proc.sd, `${model.name}.overall.proc.sd`),
        comp: requireFiniteNumber(comp.mean, `${model.name}.overall.comp.mean`),
        compSd: comp.sd === undefined ? null : requireFiniteNumber(comp.sd, `${model.name}.overall.comp.sd`),
        domainMetrics,
        domains: domains.map((domain) => [
          domain.label,
          domainMetrics[domain.id].proc,
          domainMetrics[domain.id].comp
        ]),
        originalIndex: index
      };
    });

    return {
      version: payload.version || "",
      defaultSort: payload.defaultSort === "comp" ? "comp" : "proc",
      domains,
      models
    };
  }

  function getScores(model, view) {
    if (view === "overall") {
      return {
        proc: model.proc,
        procSd: model.procSd,
        comp: model.comp,
        compSd: model.compSd
      };
    }
    const scores = model.domainMetrics[view];
    return {
      proc: scores.proc,
      procSd: null,
      comp: scores.comp,
      compSd: null
    };
  }

  function getViewLabel(view) {
    if (!state.data || view === "overall") return "all tasks";
    const domain = state.data.domains.find((item) => item.id === view);
    return domain ? domain.label : "selected domain";
  }

  function sortModels(models) {
    const primary = state.sort;
    const secondary = primary === "proc" ? "comp" : "proc";
    return [...models].sort((a, b) => {
      const aScores = getScores(a, state.view);
      const bScores = getScores(b, state.view);
      const primaryDelta = bScores[primary] - aScores[primary];
      if (primaryDelta !== 0) return primaryDelta;
      const secondaryDelta = bScores[secondary] - aScores[secondary];
      if (secondaryDelta !== 0) return secondaryDelta;
      return a.originalIndex - b.originalIndex;
    });
  }

  function renderTabs() {
    if (!leaderboardTabs || !state.data) return;
    const tabs = [{ id: "overall", label: "Overall" }, ...state.data.domains];

    leaderboardTabs.replaceChildren(...tabs.map((tab) => {
      const button = createNode("button", "leaderboard-tab", tab.label);
      button.type = "button";
      button.dataset.view = tab.id;
      const active = state.view === tab.id;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
      button.addEventListener("click", () => {
        state.view = tab.id;
        renderLeaderboard();
      });
      return button;
    }));
  }

  function renderSortButtons() {
    sortButtons.forEach((button) => {
      const active = button.dataset.sort === state.sort;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
  }

  function renderMetricCell(scores, metric) {
    const td = createNode("td", `leaderboard-metric ${metric === state.sort ? "is-primary" : ""}`);
    const value = scores[metric];
    const sd = scores[`${metric}Sd`];
    const valueNode = createNode("span", "leaderboard-score-value", formatScore(value));
    const errorNode = createNode("span", "leaderboard-score-error", formatError(sd));

    if (metric === state.sort) {
      const barCell = createNode("div", "leaderboard-bar-cell");
      const track = createNode("span", "leaderboard-bar-track");
      const fill = createNode("span", "leaderboard-bar-fill");
      fill.style.width = `${Math.max(0, Math.min(100, value))}%`;
      track.appendChild(fill);
      barCell.append(track, valueNode);
      if (errorNode.textContent) barCell.appendChild(errorNode);
      td.appendChild(barCell);
    } else {
      td.append(valueNode);
      if (errorNode.textContent) td.appendChild(errorNode);
    }

    return td;
  }

  function renderLeaderboardTable(sortedModels) {
    const table = createNode("table", "leaderboard-table dynamic-leaderboard");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const metricPrefix = state.view === "overall" ? "Avg " : "";

    ["#", "Model", `${metricPrefix}Proc`, `${metricPrefix}Comp`].forEach((label) => {
      headerRow.appendChild(createNode("th", "", label));
    });
    thead.appendChild(headerRow);

    const tbody = document.createElement("tbody");
    sortedModels.forEach((model, index) => {
      const scores = getScores(model, state.view);
      const row = document.createElement("tr");
      row.className = "leaderboard-row";

      const rankCell = createNode("td", "leaderboard-rank-cell");
      const rank = createNode("span", `leaderboard-rank rank-${index < 3 ? index + 1 : "n"}`, String(index + 1));
      rankCell.appendChild(rank);

      const modelCell = createNode("th", "leaderboard-model-cell");
      modelCell.scope = "row";
      const modelWrap = createNode("div", "leaderboard-model");
      const swatch = createNode("span", "leaderboard-model-swatch");
      swatch.style.setProperty("--model-color", model.color);
      const modelText = createNode("span", "leaderboard-model-text");
      modelText.appendChild(createNode("span", "leaderboard-model-name", model.name));
      if (model.organization) {
        modelText.appendChild(createNode("span", "leaderboard-model-org", model.organization));
      }
      modelWrap.append(swatch, modelText);
      modelCell.appendChild(modelWrap);

      row.append(rankCell, modelCell, renderMetricCell(scores, "proc"), renderMetricCell(scores, "comp"));
      tbody.appendChild(row);
    });

    table.append(thead, tbody);
    return table;
  }

  function renderLeaderboard() {
    if (!state.data || !leaderboardTableWrap) return;

    renderTabs();
    renderSortButtons();

    const sortedModels = sortModels(state.data.models);
    const table = renderLeaderboardTable(sortedModels);
    leaderboardTableWrap.hidden = false;
    leaderboardTableWrap.replaceChildren(table);

    if (leaderboardStatus) {
      leaderboardStatus.hidden = true;
      leaderboardStatus.textContent = "";
    }
    if (leaderboardSummary) {
      const metric = state.sort === "proc" ? "Avg Proc" : "Avg Comp";
      leaderboardSummary.textContent = `Current view: ranked by ${metric} on ${getViewLabel(state.view)}.`;
    }
    if (leaderboardFormula) {
      leaderboardFormula.textContent = state.sort === "proc"
        ? "Avg Proc = hidden intents completed by the agent or elicited through focused clarification"
        : "Avg Comp = verifiable checklist items satisfied by the full trajectory and artifacts";
    }
  }

  function setLeaderboardError(error) {
    if (leaderboardTableWrap) {
      leaderboardTableWrap.hidden = true;
      leaderboardTableWrap.replaceChildren();
    }
    if (leaderboardStatus) {
      leaderboardStatus.hidden = false;
      leaderboardStatus.textContent = `Unable to load leaderboard: ${error.message}`;
    }
  }

  function renderDetails(item) {
    if (!scatterDetails || !item) return;

    const detailModel = createNode("div", "scatter-detail-model");
    const swatch = createNode("span", "detail-swatch");
    swatch.style.setProperty("--point-color", item.color);
    detailModel.append(swatch, createNode("span", "scatter-detail-name", item.name));

    const overallGrid = createNode("div", "overall-score-grid");
    [
      ["Avg Proc", item.proc, item.procSd],
      ["Avg Comp", item.comp, item.compSd]
    ].forEach(([label, value, sd]) => {
      const box = document.createElement("div");
      box.append(
        createNode("span", "", label),
        createNode("span", "overall-score-value", `${formatScore(value)} ${formatError(sd)}`.trim())
      );
      overallGrid.appendChild(box);
    });

    const domainList = createNode("div", "domain-score-list");
    domainList.setAttribute("aria-label", `${item.name} domain performance`);
    item.domains.forEach(([name, proc, comp]) => {
      const row = createNode("div", "domain-score-row");
      const values = createNode("div", "domain-score-values");
      values.append(
        createNode("span", "", `Proc: ${formatScore(proc)}`),
        createNode("span", "", `Comp: ${formatScore(comp)}`)
      );
      row.append(createNode("span", "", name), values);
      domainList.appendChild(row);
    });

    scatterDetails.replaceChildren(detailModel, overallGrid, domainList);
  }

  function getTickRange(values) {
    const min = Math.min(...values);
    const max = Math.max(...values);
    let start = Math.max(0, Math.floor((min - 4) / 5) * 5);
    let end = Math.min(100, Math.ceil((max + 4) / 5) * 5);
    if (end - start < 10) {
      start = Math.max(0, start - 5);
      end = Math.min(100, end + 5);
    }
    const ticks = [];
    for (let tick = start; tick <= end; tick += 5) ticks.push(tick);
    return { domain: [start, end], ticks };
  }

  function appendTooltipLine(tooltip, text, className) {
    tooltip.appendChild(createNode("span", className || "", text));
  }

  function initOverallScatter(resultData) {
    if (!scatterMount || !resultData || resultData.length === 0) return;

    const width = 980;
    const height = 600;
    const margin = { top: 48, right: 122, bottom: 92, left: 96 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const xRange = getTickRange(resultData.map((item) => item.comp));
    const yRange = getTickRange(resultData.map((item) => item.proc));
    const xDomain = xRange.domain;
    const yDomain = yRange.domain;

    const xScale = (value) => margin.left + ((value - xDomain[0]) / (xDomain[1] - xDomain[0])) * plotWidth;
    const yScale = (value) => margin.top + (1 - ((value - yDomain[0]) / (yDomain[1] - yDomain[0]))) * plotHeight;

    const svg = createSvgNode("svg", {
      class: "scatter-svg",
      viewBox: `0 0 ${width} ${height}`,
      "aria-labelledby": "overall-scatter-title"
    });

    svg.appendChild(createSvgNode("rect", {
      class: "scatter-plot-area",
      x: margin.left,
      y: margin.top,
      width: plotWidth,
      height: plotHeight,
      rx: 8
    }));

    xRange.ticks.forEach((tick) => {
      const x = xScale(tick);
      svg.appendChild(createSvgNode("line", {
        class: "scatter-grid-line",
        x1: x,
        y1: margin.top,
        x2: x,
        y2: height - margin.bottom
      }));
      const label = createSvgNode("text", {
        class: "scatter-tick",
        x,
        y: height - margin.bottom + 28,
        "text-anchor": "middle"
      });
      label.textContent = tick;
      svg.appendChild(label);
    });

    yRange.ticks.forEach((tick) => {
      const y = yScale(tick);
      svg.appendChild(createSvgNode("line", {
        class: "scatter-grid-line",
        x1: margin.left,
        y1: y,
        x2: width - margin.right,
        y2: y
      }));
      const label = createSvgNode("text", {
        class: "scatter-tick",
        x: margin.left - 18,
        y: y + 5,
        "text-anchor": "end"
      });
      label.textContent = tick;
      svg.appendChild(label);
    });

    svg.appendChild(createSvgNode("line", {
      class: "scatter-axis",
      x1: margin.left,
      y1: height - margin.bottom,
      x2: width - margin.right,
      y2: height - margin.bottom
    }));
    svg.appendChild(createSvgNode("line", {
      class: "scatter-axis",
      x1: margin.left,
      y1: margin.top,
      x2: margin.left,
      y2: height - margin.bottom
    }));

    const diagonalStart = Math.max(xDomain[0], yDomain[0]);
    const diagonalEnd = Math.min(xDomain[1], yDomain[1]);
    svg.appendChild(createSvgNode("line", {
      class: "scatter-reference-line",
      x1: xScale(diagonalStart),
      y1: yScale(diagonalStart),
      x2: xScale(diagonalEnd),
      y2: yScale(diagonalEnd)
    }));

    const xLabel = createSvgNode("text", {
      class: "scatter-axis-label",
      x: margin.left + plotWidth / 2,
      y: height - 26,
      "text-anchor": "middle"
    });
    xLabel.textContent = "Average task completion, Comp (%)";
    svg.appendChild(xLabel);

    const yLabel = createSvgNode("text", {
      class: "scatter-axis-label",
      x: -margin.top - plotHeight / 2,
      y: 30,
      transform: "rotate(-90)",
      "text-anchor": "middle"
    });
    yLabel.textContent = "Average proactive intent recovery, Proc (%)";
    svg.appendChild(yLabel);

    const tooltip = createNode("div", "scatter-tooltip");
    tooltip.hidden = true;

    const pointsLayer = createSvgNode("g", { class: "scatter-points" });
    const labelLayer = createSvgNode("g", { class: "scatter-labels" });
    const labelBoxes = [];
    const pointPositions = resultData.map((item) => ({
      x: xScale(item.comp),
      y: yScale(item.proc)
    }));
    const pointBoxes = pointPositions.map((point) => ({
      x: point.x - 12,
      y: point.y - 12,
      width: 24,
      height: 24
    }));
    const labelPlacements = new Array(resultData.length);
    const pointNodes = [];
    const labelNodes = [];
    const labelPlacementOverrides = {
      "DeepSeek V4 Flash": [
        { dx: 18, dy: -22, anchor: "end", leader: true, priority: -80 }
      ]
    };

    function estimateLabelWidth(text) {
      return Math.max(42, text.length * 7.15);
    }

    function boxOverlapArea(a, b) {
      const x = Math.max(0, Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x));
      const y = Math.max(0, Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y));
      return x * y;
    }

    function paddedBox(box, pad) {
      return {
        x: box.x - pad,
        y: box.y - pad,
        width: box.width + pad * 2,
        height: box.height + pad * 2
      };
    }

    function boxOverflowAmount(box) {
      const pad = 6;
      return (
        Math.max(0, margin.left + pad - box.x) +
        Math.max(0, margin.top + pad - box.y) +
        Math.max(0, box.x + box.width - (width - margin.right - pad)) +
        Math.max(0, box.y + box.height - (height - margin.bottom - pad))
      );
    }

    function pointDistanceToBox(point, box) {
      const dx = Math.max(box.x - point.x, 0, point.x - (box.x + box.width));
      const dy = Math.max(box.y - point.y, 0, point.y - (box.y + box.height));
      return Math.hypot(dx, dy);
    }

    function scoreLabelBox(box, pointIndex, option) {
      const point = pointPositions[pointIndex];
      const labelCollisionBox = paddedBox(box, 5);
      const labelCollision = labelBoxes.reduce((sum, placed) => sum + boxOverlapArea(labelCollisionBox, placed), 0);
      const pointCollision = pointBoxes.reduce((sum, placed) => sum + boxOverlapArea(box, placed), 0);
      const overflow = boxOverflowAmount(box);
      const distance = pointDistanceToBox(point, box);
      const distancePenalty = Math.max(0, distance - 22) ** 2 + Math.max(0, 8 - distance) ** 2 * 3;
      return (
        overflow * 20000 +
        labelCollision * 900 +
        pointCollision * 180 +
        distancePenalty +
        option.priority
      );
    }

    function labelCandidate(item, x, y, option) {
      const widthEstimate = estimateLabelWidth(item.name);
      const heightEstimate = 15;
      const labelX = x + option.dx;
      const labelY = y + option.dy;
      const boxX = option.anchor === "end"
        ? labelX - widthEstimate
        : option.anchor === "middle"
          ? labelX - widthEstimate / 2
          : labelX;
      return {
        x: boxX,
        y: labelY - 11,
        width: widthEstimate,
        height: heightEstimate,
        labelX,
        labelY,
        anchor: option.anchor,
        leader: option.leader,
        priority: option.priority
      };
    }

    function placeLabel(item, x, y, pointIndex) {
      const override = labelPlacementOverrides[item.name] && labelPlacementOverrides[item.name][0];
      if (override) {
        const chosen = labelCandidate(item, x, y, override);
        labelBoxes.push(paddedBox(chosen, 5));
        return chosen;
      }

      const candidates = [
        { dx: 0, dy: -18, anchor: "middle", priority: 0 },
        { dx: 0, dy: 25, anchor: "middle", priority: 1 },
        { dx: 16, dy: -12, anchor: "start", priority: 4 },
        { dx: -16, dy: -12, anchor: "end", priority: 4 },
        { dx: 16, dy: 22, anchor: "start", priority: 5 },
        { dx: -16, dy: 22, anchor: "end", priority: 5 },
        { dx: 24, dy: 4, anchor: "start", priority: 8 },
        { dx: -24, dy: 4, anchor: "end", priority: 8 },
        { dx: 0, dy: -36, anchor: "middle", leader: true, priority: 18 },
        { dx: 0, dy: 43, anchor: "middle", leader: true, priority: 19 },
        { dx: 28, dy: -30, anchor: "start", leader: true, priority: 24 },
        { dx: -28, dy: -30, anchor: "end", leader: true, priority: 24 },
        { dx: 28, dy: 40, anchor: "start", leader: true, priority: 25 },
        { dx: -28, dy: 40, anchor: "end", leader: true, priority: 25 }
      ].map((option) => labelCandidate(item, x, y, option));

      candidates.sort((a, b) => scoreLabelBox(a, pointIndex, a) - scoreLabelBox(b, pointIndex, b));
      const chosen = candidates[0];
      labelBoxes.push(paddedBox(chosen, 5));
      return chosen;
    }

    pointPositions
      .map((point, index) => {
        const density = pointPositions.reduce((sum, other, otherIndex) => {
          if (index === otherIndex) return sum;
          const distance = Math.hypot(point.x - other.x, point.y - other.y);
          return sum + 1 / Math.max(16, distance);
        }, 0);
        return { index, density, labelWidth: estimateLabelWidth(resultData[index].name) };
      })
      .sort((a, b) => (b.density - a.density) || (b.labelWidth - a.labelWidth))
      .forEach(({ index }) => {
        const point = pointPositions[index];
        labelPlacements[index] = placeLabel(resultData[index], point.x, point.y, index);
      });

    function setActive(index, event) {
      const item = resultData[index];
      if (!item) return;
      pointNodes.forEach((node, nodeIndex) => {
        const active = nodeIndex === index;
        node.classList.toggle("is-active", active);
        node.querySelector(".scatter-point-dot").setAttribute("r", active ? "13" : "8.5");
        if (labelNodes[nodeIndex]) labelNodes[nodeIndex].classList.toggle("is-active", active);
      });
      renderDetails(item);

      tooltip.replaceChildren();
      appendTooltipLine(tooltip, item.name, "scatter-tooltip-title");
      appendTooltipLine(
        tooltip,
        `Overall: Proc ${formatScore(item.proc)} ${formatError(item.procSd)}; Comp ${formatScore(item.comp)} ${formatError(item.compSd)}`.trim()
      );
      item.domains.forEach(([name, proc, comp]) => {
        appendTooltipLine(tooltip, `${name}: Proc ${formatScore(proc)}; Comp ${formatScore(comp)}`);
      });
      if (!event) {
        tooltip.hidden = true;
        return;
      }
      tooltip.hidden = false;

      const bounds = scatterMount.getBoundingClientRect();
      const pointX = xScale(item.comp) / width * bounds.width;
      const pointY = yScale(item.proc) / height * bounds.height;
      const eventX = event && "clientX" in event ? event.clientX - bounds.left : pointX;
      const eventY = event && "clientY" in event ? event.clientY - bounds.top : pointY;
      const maxX = Math.max(8, bounds.width - 272);
      const maxY = Math.max(8, bounds.height - 190);
      const tooltipX = Math.min(maxX, Math.max(8, eventX + 14));
      const tooltipY = Math.min(maxY, Math.max(8, eventY - 82));
      tooltip.style.transform = `translate(${tooltipX}px, ${tooltipY}px)`;
    }

    resultData.forEach((item, index) => {
      const { x, y } = pointPositions[index];
      const group = createSvgNode("g", {
        class: "scatter-point",
        tabindex: "0",
        role: "button",
        "aria-label": `${item.name}: average Proc ${formatScore(item.proc)}, average Comp ${formatScore(item.comp)}`,
        transform: `translate(${x} ${y})`
      });
      const halo = createSvgNode("circle", { class: "scatter-point-halo", r: 18 });
      const circle = createSvgNode("circle", {
        class: "scatter-point-dot",
        r: 8.5,
        fill: item.color
      });
      const labelPlacement = labelPlacements[index];
      if (labelPlacement.leader) {
        labelLayer.appendChild(createSvgNode("line", {
          class: "scatter-label-leader",
          x1: labelPlacement.anchor === "end"
            ? labelPlacement.labelX + 4
            : labelPlacement.anchor === "middle"
              ? labelPlacement.labelX
              : labelPlacement.labelX - 4,
          y1: labelPlacement.labelY - 4,
          x2: x,
          y2: y
        }));
      }
      const label = createSvgNode("text", {
        class: "scatter-point-label",
        x: labelPlacement.labelX,
        y: labelPlacement.labelY,
        "text-anchor": labelPlacement.anchor
      });
      label.textContent = item.name;
      labelLayer.appendChild(label);
      labelNodes.push(label);
      group.append(halo, circle);
      group.addEventListener("mouseenter", (event) => setActive(index, event));
      group.addEventListener("mousemove", (event) => setActive(index, event));
      group.addEventListener("focus", (event) => setActive(index, event));
      group.addEventListener("click", (event) => setActive(index, event));
      group.addEventListener("mouseleave", () => {
        tooltip.hidden = true;
      });
      pointsLayer.appendChild(group);
      pointNodes.push(group);
    });

    svg.append(pointsLayer, labelLayer);
    scatterMount.replaceChildren(svg, tooltip);
    const defaultIndex = resultData.findIndex((item) => item.name === "Claude Opus 4.6");
    setActive(defaultIndex >= 0 ? defaultIndex : 0);
  }

  async function loadLeaderboard() {
    if (!leaderboardTableWrap) return;
    try {
      if (leaderboardStatus) {
        leaderboardStatus.hidden = false;
        leaderboardStatus.textContent = "Loading leaderboard...";
      }
      const response = await fetch("leaderboard.json", { cache: "no-cache" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();
      state.data = normalizeLeaderboard(payload);
      state.sort = state.data.defaultSort;
      renderLeaderboard();
      initOverallScatter(state.data.models);
      updateProgress();
    } catch (error) {
      setLeaderboardError(error);
      if (scatterMount) scatterMount.replaceChildren();
      if (scatterDetails) scatterDetails.replaceChildren();
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      setTheme(root.dataset.theme === "dark" ? "light" : "dark");
    });
  }

  if (toTop) {
    toTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  sortButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const sort = button.dataset.sort;
      if (sort !== "proc" && sort !== "comp") return;
      state.sort = sort;
      renderLeaderboard();
    });
  });

  window.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  setTheme(getSavedTheme());
  loadLeaderboard();
  updateProgress();
}());
