(function () {
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeLabel = document.getElementById("themeLabel");
  const progressBar = document.getElementById("progressBar");
  const toTop = document.getElementById("toTop");
  const scatterMount = document.getElementById("overallScatter");
  const scatterDetails = document.getElementById("scatterDetails");

  const resultData = [
    {
      model: "GPT-5.4",
      proc: 67.0,
      comp: 65.6,
      procSd: 2.1,
      compSd: 1.8,
      color: "#2563eb",
      domains: [
        ["Researcher", 46.0, 66.4],
        ["Marketer", 78.2, 67.1],
        ["Pharmacist", 75.9, 71.5],
        ["Law Trainee", 56.9, 61.9],
        ["Financier", 78.1, 61.2]
      ]
    },
    {
      model: "Gemini 3.1 Pro",
      proc: 57.1,
      comp: 60.0,
      procSd: 0.9,
      compSd: 0.8,
      color: "#0f766e",
      domains: [
        ["Researcher", 41.1, 59.2],
        ["Marketer", 65.0, 62.1],
        ["Pharmacist", 71.0, 72.1],
        ["Law Trainee", 50.0, 55.3],
        ["Financier", 58.6, 51.1]
      ]
    },
    {
      model: "Claude Opus 4.6",
      proc: 65.5,
      comp: 67.6,
      procSd: 1.4,
      compSd: 1.5,
      color: "#b45309",
      domains: [
        ["Researcher", 50.3, 74.5],
        ["Marketer", 75.0, 74.6],
        ["Pharmacist", 82.8, 68.6],
        ["Law Trainee", 45.7, 57.2],
        ["Financier", 73.8, 63.2]
      ]
    },
    {
      model: "DeepSeek V3.2",
      proc: 53.3,
      comp: 57.8,
      procSd: 1.9,
      compSd: 3.0,
      color: "#be123c",
      domains: [
        ["Researcher", 29.0, 66.9],
        ["Marketer", 69.1, 59.4],
        ["Pharmacist", 75.9, 62.6],
        ["Law Trainee", 33.2, 51.1],
        ["Financier", 59.1, 48.9]
      ]
    },
    {
      model: "MiniMax M2.7",
      proc: 55.6,
      comp: 60.0,
      procSd: 3.2,
      compSd: 1.8,
      color: "#7c3aed",
      domains: [
        ["Researcher", 33.4, 63.9],
        ["Marketer", 71.9, 61.9],
        ["Pharmacist", 77.1, 63.6],
        ["Law Trainee", 38.6, 52.5],
        ["Financier", 57.2, 58.1]
      ]
    },
    {
      model: "Kimi K2.5",
      proc: 61.4,
      comp: 53.9,
      procSd: 2.1,
      compSd: 0.8,
      color: "#475569",
      domains: [
        ["Researcher", 39.4, 52.6],
        ["Marketer", 68.2, 59.7],
        ["Pharmacist", 81.8, 78.3],
        ["Law Trainee", 46.5, 44.4],
        ["Financier", 71.1, 34.4]
      ]
    },
    {
      model: "Kimi K2.6",
      proc: 63.8,
      comp: 62.0,
      procSd: 1.3,
      compSd: 1.2,
      color: "#64748b",
      domains: [
        ["Researcher", 43.9, 60.3],
        ["Marketer", 69.5, 69.6],
        ["Pharmacist", 77.8, 85.3],
        ["Law Trainee", 48.7, 55.5],
        ["Financier", 79.2, 39.4]
      ]
    },
    {
      model: "Seed2.0 Pro",
      proc: 58.4,
      comp: 52.1,
      procSd: 0.9,
      compSd: 3.8,
      color: "#15803d",
      domains: [
        ["Researcher", 38.9, 59.6],
        ["Marketer", 71.4, 44.2],
        ["Pharmacist", 77.0, 67.6],
        ["Law Trainee", 46.0, 44.7],
        ["Financier", 58.7, 44.5]
      ]
    },
    {
      model: "GLM-5.1",
      proc: 58.4,
      comp: 63.6,
      procSd: 0.8,
      compSd: 2.9,
      color: "#0891b2",
      domains: [
        ["Researcher", 41.8, 61.6],
        ["Marketer", 62.6, 69.1],
        ["Pharmacist", 75.2, 70.3],
        ["Law Trainee", 45.5, 57.3],
        ["Financier", 66.7, 59.8]
      ]
    },
    {
      model: "Qwen3.6 Plus",
      proc: 64.0,
      comp: 64.1,
      procSd: 1.1,
      compSd: 0.6,
      color: "#c2410c",
      domains: [
        ["Researcher", 40.1, 70.0],
        ["Marketer", 77.5, 66.6],
        ["Pharmacist", 79.7, 70.2],
        ["Law Trainee", 45.7, 60.2],
        ["Financier", 77.1, 53.6]
      ]
    }
  ];

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

  function formatScore(value) {
    return Number(value).toFixed(1);
  }

  function renderDetails(item) {
    if (!scatterDetails || !item) return;

    const domainRows = item.domains.map(([name, proc, comp]) => `
      <div class="domain-score-row">
        <span>${name}</span>
        <div class="domain-score-values">
          <span><b>Proc:</b> ${formatScore(proc)}</span>
          <span><b>Comp:</b> ${formatScore(comp)}</span>
        </div>
      </div>
    `).join("");

    scatterDetails.innerHTML = `
      <div class="scatter-detail-model">
        <span class="detail-swatch" style="--point-color: ${item.color}"></span>
        <strong>${item.model}</strong>
      </div>
      <div class="overall-score-grid">
        <div>
          <span>Avg Proc</span>
          <strong>${formatScore(item.proc)} <small>+/- ${formatScore(item.procSd)}</small></strong>
        </div>
        <div>
          <span>Avg Comp</span>
          <strong>${formatScore(item.comp)} <small>+/- ${formatScore(item.compSd)}</small></strong>
        </div>
      </div>
      <div class="domain-score-list" aria-label="${item.model} domain performance">
        ${domainRows}
      </div>
    `;
  }

  function initOverallScatter() {
    if (!scatterMount) return;

    const svgNS = "http://www.w3.org/2000/svg";
    const width = 940;
    const height = 580;
    const margin = { top: 34, right: 46, bottom: 78, left: 78 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const xDomain = [50, 70];
    const yDomain = [50, 70];
    const xTicks = [50, 55, 60, 65, 70];
    const yTicks = [50, 55, 60, 65, 70];

    const xScale = (value) => margin.left + ((value - xDomain[0]) / (xDomain[1] - xDomain[0])) * plotWidth;
    const yScale = (value) => margin.top + (1 - ((value - yDomain[0]) / (yDomain[1] - yDomain[0]))) * plotHeight;
    const create = (name, attrs = {}) => {
      const node = document.createElementNS(svgNS, name);
      Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
      return node;
    };

    const svg = create("svg", {
      class: "scatter-svg",
      viewBox: `0 0 ${width} ${height}`,
      "aria-labelledby": "overall-scatter-title"
    });

    const plotArea = create("rect", {
      class: "scatter-plot-area",
      x: margin.left,
      y: margin.top,
      width: plotWidth,
      height: plotHeight,
      rx: 8
    });
    svg.appendChild(plotArea);

    xTicks.forEach((tick) => {
      const x = xScale(tick);
      svg.appendChild(create("line", {
        class: "scatter-grid-line",
        x1: x,
        y1: margin.top,
        x2: x,
        y2: height - margin.bottom
      }));
      const label = create("text", {
        class: "scatter-tick",
        x,
        y: height - margin.bottom + 28,
        "text-anchor": "middle"
      });
      label.textContent = tick;
      svg.appendChild(label);
    });

    yTicks.forEach((tick) => {
      const y = yScale(tick);
      svg.appendChild(create("line", {
        class: "scatter-grid-line",
        x1: margin.left,
        y1: y,
        x2: width - margin.right,
        y2: y
      }));
      const label = create("text", {
        class: "scatter-tick",
        x: margin.left - 18,
        y: y + 5,
        "text-anchor": "end"
      });
      label.textContent = tick;
      svg.appendChild(label);
    });

    svg.appendChild(create("line", {
      class: "scatter-axis",
      x1: margin.left,
      y1: height - margin.bottom,
      x2: width - margin.right,
      y2: height - margin.bottom
    }));
    svg.appendChild(create("line", {
      class: "scatter-axis",
      x1: margin.left,
      y1: margin.top,
      x2: margin.left,
      y2: height - margin.bottom
    }));

    svg.appendChild(create("line", {
      class: "scatter-reference-line",
      x1: xScale(50),
      y1: yScale(50),
      x2: xScale(70),
      y2: yScale(70)
    }));

    const xLabel = create("text", {
      class: "scatter-axis-label",
      x: margin.left + plotWidth / 2,
      y: height - 26,
      "text-anchor": "middle"
    });
    xLabel.textContent = "Average task completion, Comp (%)";
    svg.appendChild(xLabel);

    const yLabel = create("text", {
      class: "scatter-axis-label",
      x: -margin.top - plotHeight / 2,
      y: 24,
      transform: "rotate(-90)",
      "text-anchor": "middle"
    });
    yLabel.textContent = "Average proactive intent recovery, Proc (%)";
    svg.appendChild(yLabel);

    const tooltip = document.createElement("div");
    tooltip.className = "scatter-tooltip";
    tooltip.hidden = true;

    const pointsLayer = create("g", { class: "scatter-points" });
    const labelOffsets = [
      [12, -14],
      [22, 26],
      [12, -14],
      [12, 21],
      [22, 30],
      [12, -14],
      [12, 21],
      [12, -14],
      [12, 21]
    ];
    const pointNodes = [];

    function setActive(index, event) {
      const item = resultData[index];
      pointNodes.forEach((node, nodeIndex) => {
        const active = nodeIndex === index;
        node.classList.toggle("is-active", active);
        node.querySelector(".scatter-point-dot").setAttribute("r", active ? "13" : "8.5");
      });
      renderDetails(item);

      const tooltipDomains = item.domains.map(([name, proc, comp]) => `
        <span>${name}: Proc ${formatScore(proc)}; Comp ${formatScore(comp)}</span>
      `).join("");
      tooltip.innerHTML = `
        <strong>${item.model}</strong>
        <span>Overall: Proc ${formatScore(item.proc)} +/- ${formatScore(item.procSd)}; Comp ${formatScore(item.comp)} +/- ${formatScore(item.compSd)}</span>
        ${tooltipDomains}
      `;
      tooltip.hidden = false;

      const bounds = scatterMount.getBoundingClientRect();
      const pointX = xScale(item.comp) / width * bounds.width;
      const pointY = yScale(item.proc) / height * bounds.height;
      const eventX = event && "clientX" in event ? event.clientX - bounds.left : pointX;
      const eventY = event && "clientY" in event ? event.clientY - bounds.top : pointY;
      const tooltipX = Math.min(bounds.width - 272, Math.max(8, eventX + 14));
      const tooltipY = Math.min(bounds.height - 190, Math.max(8, eventY - 82));
      tooltip.style.transform = `translate(${tooltipX}px, ${tooltipY}px)`;
    }

    resultData.forEach((item, index) => {
      const x = xScale(item.comp);
      const y = yScale(item.proc);
      const group = create("g", {
        class: "scatter-point",
        tabindex: "0",
        role: "button",
        "aria-label": `${item.model}: average Proc ${formatScore(item.proc)}, average Comp ${formatScore(item.comp)}`,
        transform: `translate(${x} ${y})`
      });
      const halo = create("circle", { class: "scatter-point-halo", r: 18 });
      const circle = create("circle", {
        class: "scatter-point-dot",
        r: 8.5,
        fill: item.color
      });
      const [dx, dy] = labelOffsets[index] || [12, index % 2 === 0 ? -14 : 21];
      const label = create("text", {
        class: "scatter-point-label",
        x: dx,
        y: dy,
        "text-anchor": "start"
      });
      label.textContent = item.model;
      group.append(halo, circle, label);
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

    svg.appendChild(pointsLayer);
    scatterMount.replaceChildren(svg, tooltip);
    setActive(resultData.findIndex((item) => item.model === "Claude Opus 4.6"));
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

  window.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  setTheme(getSavedTheme());
  initOverallScatter();
  updateProgress();
}());
