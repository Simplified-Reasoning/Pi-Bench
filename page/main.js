(function () {
  const root = document.documentElement;
  const themeToggle = document.getElementById("themeToggle");
  const themeLabel = document.getElementById("themeLabel");
  const languageToggle = document.getElementById("languageToggle");
  const languageLabel = document.getElementById("languageLabel");
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

  const copy = {
    en: {
      htmlLang: "en",
      title: "π-Bench: Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows",
      metaDescription: "π-Bench is a benchmark for evaluating proactive personal assistant agents in long-horizon personal workflows with hidden intents.",
      ogTitle: "π-Bench",
      ogDescription: "Evaluating proactive personal assistant agents in long-horizon workflows.",
      brandAria: "π-Bench home",
      primaryNavAria: "Primary navigation",
      navOverview: "Overview",
      navDesign: "Design",
      navEvaluation: "Evaluation",
      navResources: "Resources",
      themeToggleAria: "Toggle theme",
      themeDark: "Dark",
      themeLight: "Light",
      languageLabel: "中文",
      languageToggleAria: "Switch to Chinese",
      heroEyebrow: "Proactive Personal Assistant Benchmark",
      heroSubtitle: "Evaluating Proactive Personal Assistant Agents in Long-Horizon Workflows",
      buttonCode: "Code",
      buttonData: "Data",
      buttonPaper: "Paper",
      overviewFigureAlt: "π-Bench benchmark overview",
      overviewCaption: "π-Bench evaluates whether a personal assistant can recover hidden user intents across persistent sessions, act through tools and workspace artifacts, and finish the task.",
      overviewTitle: "Benchmark Overview",
      scaleAria: "π-Bench scale",
      statTasks: "multi-turn tasks",
      statPersonas: "domain personas",
      statIntents: "hidden intents",
      statGraders: "checklist and rule graders",
      motivationAria: "π-Bench motivation",
      overviewStep1Title: "Initial request",
      overviewStep1Body: "The user gives a short request that names the visible deliverable, but not every preference, constraint, or dependency.",
      overviewStep2Title: "Hidden intents",
      overviewStep2Body: "Missing habits, preferences, constraints, and task dependencies are recoverable from profiles, prior sessions, workspace files, app state, tool results, and cross-session context.",
      overviewStep3Title: "Agent behavior",
      overviewStep3Body: "π-Bench tests whether the agent infers what it can, asks focused questions when needed, and carries those decisions through later turns, tool use, and artifact revisions.",
      overviewLead: "π-Bench evaluates long-horizon personal assistant workflows in persistent project environments. The user gives a short request, but completing it well may depend on preferences, constraints, files, and decisions revealed in earlier sessions and reused later.",
      overviewBody1: "Each task starts with a natural but underspecified instruction. The agent works inside a persistent workspace, interacts with the user, uses tools, and creates or revises artifacts. Hidden intents are the missing but recoverable requirements: for example, a deck template, preferred metrics, naming conventions, project-specific constraints, or dependencies established in prior work. Some hidden intents are available from the start, while others are revealed gradually through interaction, tool use, or workspace inspection.",
      overviewBody2: "This is different from evaluating only explicit instructions, isolated memory recall, or short GUI actions. π-Bench asks whether an agent can decide which context matters, when to ask for clarification, and how to carry those decisions into workspace artifacts.",
      overviewBody3: "The benchmark separates two questions. <strong>Completeness</strong> measures whether the final workflow succeeds, including the explicit request and the relevant hidden intents. <strong>Proactivity</strong> measures whether the agent reduces the user's specification burden by inferring hidden intents from context or asking targeted clarifying questions early enough to guide later work.",
      designTitle: "Benchmark Design",
      designLead: "π-Bench is organized around persistent user episodes, underspecified task sessions, and two complementary scores: proactive intent recovery and task completion.",
      designFlowAria: "π-Bench benchmark design flow",
      designEpisodeLabel: "Episode",
      designEpisodeTitle: "Persistent user workflow",
      designEpisodeBody: "Each persona has one 20-session episode in a shared workspace. Preferences, files, prior outputs, and dependencies can carry over.",
      userRolesAria: "User roles",
      domainResearcher: "Researcher",
      domainMarketer: "Marketer",
      domainLawTrainee: "Law Trainee",
      domainPharmacist: "Pharmacist",
      domainFinancier: "Financier",
      sourceHistory: "history",
      sourceWorkspace: "workspace",
      sourceApps: "apps",
      sourceTools: "tools",
      sourceSkills: "skills",
      designSessionLabel: "Session",
      designSessionTitle: "Interaction with hidden intents",
      designSessionBody: "A natural initial request leaves some requirements unstated. The agent uses context, tools, files, and focused clarification while hidden intents are tracked.",
      designScoringLabel: "Scoring",
      designScoringTitle: "Proactivity and completeness",
      designScoringBody: "Proc counts agent-driven hidden-intent resolution. Comp checks verifiable requirements across the full trajectory, tool records, and artifacts.",
      metricProcPill: "completed or elicited hidden intents",
      metricCompPill: "satisfied checklist criteria",
      evaluationTitle: "Evaluation",
      evaluationIntro: "π-Bench reports <strong>Proc</strong> and <strong>Comp</strong> as two main metrics.",
      metricRelationAria: "Proc and Comp relationship",
      procCardTitle: "Did the agent reduce underspecification in a proactive way?",
      procCardBody: "Proc measures the share of hidden intents resolved proactively: an intent counts when the agent <strong>satisfies it directly</strong> through its response, tool use, or artifacts, or <strong>asks a targeted clarifying question</strong> about the specific missing preference, constraint, or dependency before proceeding. Intents surfaced only by user-provided information are not counted as proactive.",
      compCardTitle: "Did the final trajectory satisfy the task?",
      compCardBody: "Comp is the average <strong>checklist score</strong> over verifiable task requirements. Checklist graders read the <strong>full trajectory</strong>, including tool records and produced artifacts, to assess whether the resulting workflow satisfies the required outcomes.",
      leaderboardKicker: "Leaderboard",
      leaderboardTitle: "Benchmark Leaderboard",
      leaderboardRankingNote: "The leaderboard ranks by <strong>Avg Proc by default</strong>. Use the <strong>Rank by</strong> control to switch to <strong>Avg Comp</strong>; the two rankings can differ, so model quality should be read across both metrics.",
      rankByMetric: "Rank by metric",
      leaderboardRankingAria: "Leaderboard ranking metric",
      leaderboardViewsAria: "Leaderboard views",
      metricLabel: "Metric",
      higherBetter: "higher is better",
      overallPerformanceTitle: "Overall Performance",
      scatterAria: "Scatter plot comparing average proactive intent recovery and completion performance by model",
      resourcesTitle: "Resources",
      resourceCodeSub: "GitHub repository",
      resourceDataSub: "users, episodes, tasks",
      citationTitle: "Citation",
      footerText: "π-Bench is intended for controlled evaluation of proactive personal assistant agents. Systems built for real users should preserve user agency, protect private data, and involve domain experts when decisions carry real-world consequences.",
      toTopAria: "Back to top",
      rank: "#",
      model: "Model",
      proc: "Proc",
      comp: "Comp",
      avgProc: "Avg Proc",
      avgComp: "Avg Comp",
      allTasks: "all tasks",
      selectedDomain: "selected domain",
      tabOverall: "Overall",
      loadingLeaderboard: "Loading leaderboard...",
      unableToLoadLeaderboard: "Unable to load leaderboard",
      formulaProc: "Avg Proc = hidden intents completed by the agent or elicited through focused clarification",
      formulaComp: "Avg Comp = verifiable checklist items satisfied by the full trajectory and artifacts",
      axisComp: "Average task completion, Comp (%)",
      axisProc: "Average proactive intent recovery, Proc (%)",
      leaderboardSummary: (metric, view) => `Current view: ranked by ${metric} on ${view}.`,
      tooltipOverall: (item) => `Overall: Proc ${formatScore(item.proc)} ${formatError(item.procSd)}; Comp ${formatScore(item.comp)} ${formatError(item.compSd)}`.trim(),
      tooltipDomain: (name, proc, comp) => `${name}: Proc ${formatScore(proc)}; Comp ${formatScore(comp)}`,
      domainPerformanceAria: (name) => `${name} domain performance`,
      scatterPointAria: (item) => `${item.name}: average Proc ${formatScore(item.proc)}, average Comp ${formatScore(item.comp)}`,
      domains: {
        researcher: "Researcher",
        marketer: "Marketer",
        pharmacist: "Pharmacist",
        law_trainee: "Law Trainee",
        financier: "Financier"
      }
    },
    zh: {
      htmlLang: "zh-Hans",
      title: "π-Bench：评测长期工作流中的主动式个人助理智能体",
      metaDescription: "π-Bench 是一个用于评测主动式个人助理智能体的基准，关注带有隐藏意图的长期个人工作流。",
      ogTitle: "π-Bench",
      ogDescription: "评测长期工作流中的主动式个人助理智能体。",
      brandAria: "π-Bench 主页",
      primaryNavAria: "主导航",
      navOverview: "概览",
      navDesign: "设计",
      navEvaluation: "评测",
      navResources: "资源",
      themeToggleAria: "切换主题",
      themeDark: "深色",
      themeLight: "浅色",
      languageLabel: "English",
      languageToggleAria: "切换到英文",
      heroEyebrow: "主动式个人助理基准",
      heroSubtitle: "评测长期工作流中的主动式个人助理智能体",
      buttonCode: "代码",
      buttonData: "数据",
      buttonPaper: "论文",
      overviewFigureAlt: "π-Bench 基准概览图",
      overviewCaption: "π-Bench 评测个人助理能否在持续会话中恢复隐藏用户意图，通过工具和工作区产物行动，并完成任务。",
      overviewTitle: "基准概览",
      scaleAria: "π-Bench 规模",
      statTasks: "多轮任务",
      statPersonas: "领域角色",
      statIntents: "隐藏意图",
      statGraders: "清单与规则评测器",
      motivationAria: "π-Bench 动机",
      overviewStep1Title: "初始请求",
      overviewStep1Body: "用户给出简短请求，说明可见交付物，但不会把所有偏好、约束或依赖都明确写出。",
      overviewStep2Title: "隐藏意图",
      overviewStep2Body: "缺失的习惯、偏好、约束和任务依赖，可以从用户画像、历史会话、工作区文件、应用状态、工具结果和跨会话上下文中恢复。",
      overviewStep3Title: "智能体行为",
      overviewStep3Body: "π-Bench 测试智能体能否推断可推断的信息，在必要时提出聚焦问题，并把这些决策贯彻到后续轮次、工具使用和产物修订中。",
      overviewLead: "π-Bench 在持久化项目环境中评测长期个人助理工作流。用户只给出简短请求，但高质量完成任务可能依赖早期会话中暴露并在之后复用的偏好、约束、文件和决策。",
      overviewBody1: "每个任务都从自然但不完整的指令开始。智能体在持久化工作区中工作，与用户交互，使用工具，并创建或修订产物。隐藏意图指那些缺失但可恢复的需求，例如演示文稿模板、偏好的指标、命名规范、项目特定约束，或先前工作中建立的依赖。有些隐藏意图一开始就可获得，另一些则会通过交互、工具使用或工作区检查逐步显露。",
      overviewBody2: "这不同于只评测显式指令、孤立记忆召回或短程 GUI 操作。π-Bench 关注智能体能否判断哪些上下文真正相关、何时需要澄清，以及如何把这些决策落实到工作区产物中。",
      overviewBody3: "该基准区分两个问题。<strong>Completeness</strong> 衡量最终工作流是否成功，包括显式请求和相关隐藏意图。<strong>Proactivity</strong> 衡量智能体是否通过从上下文中推断隐藏意图，或足够早地提出有针对性的澄清问题，来降低用户的说明负担并指导后续工作。",
      designTitle: "基准设计",
      designLead: "π-Bench 围绕持久化用户 episode、带有欠规范信息的任务 session，以及两个互补分数组织：主动意图恢复和任务完成度。",
      designFlowAria: "π-Bench 基准设计流程",
      designEpisodeLabel: "Episode",
      designEpisodeTitle: "持久化用户工作流",
      designEpisodeBody: "每个角色在共享工作区中拥有一个 20 个 session 的 episode。偏好、文件、先前产物和依赖都可以跨 session 延续。",
      userRolesAria: "用户角色",
      domainResearcher: "研究员",
      domainMarketer: "市场营销",
      domainLawTrainee: "法律实习生",
      domainPharmacist: "药剂师",
      domainFinancier: "金融从业者",
      sourceHistory: "历史",
      sourceWorkspace: "工作区",
      sourceApps: "应用",
      sourceTools: "工具",
      sourceSkills: "技能",
      designSessionLabel: "Session",
      designSessionTitle: "带隐藏意图的交互",
      designSessionBody: "自然的初始请求会留下部分未说明需求。智能体在跟踪隐藏意图的同时，使用上下文、工具、文件和聚焦澄清来推进任务。",
      designScoringLabel: "Scoring",
      designScoringTitle: "主动性与完成度",
      designScoringBody: "Proc 统计由智能体主动驱动的隐藏意图解决情况。Comp 检查完整轨迹、工具记录和产物中的可验证需求。",
      metricProcPill: "完成或引出的隐藏意图",
      metricCompPill: "满足的清单标准",
      evaluationTitle: "评测",
      evaluationIntro: "π-Bench 使用 <strong>Proc</strong> 和 <strong>Comp</strong> 作为两个主要指标。",
      metricRelationAria: "Proc 与 Comp 的关系",
      procCardTitle: "智能体是否以主动方式减少欠规范信息？",
      procCardBody: "Proc 衡量被主动解决的隐藏意图比例：当智能体通过回复、工具使用或产物<strong>直接满足该意图</strong>，或在继续推进前就具体缺失的偏好、约束或依赖<strong>提出有针对性的澄清问题</strong>时，该意图会被计入。仅由用户主动提供的信息暴露出的意图，不计为主动。",
      compCardTitle: "最终轨迹是否满足任务？",
      compCardBody: "Comp 是可验证任务需求上的平均<strong>清单分数</strong>。清单评测器会读取包含工具记录和产物在内的<strong>完整轨迹</strong>，判断最终工作流是否满足所需结果。",
      leaderboardKicker: "排行榜",
      leaderboardTitle: "基准排行榜",
      leaderboardRankingNote: "排行榜默认按 <strong>Avg Proc</strong> 排序。可以使用 <strong>排序指标</strong> 控件切换到 <strong>Avg Comp</strong>；两个排序可能不同，因此模型质量应结合两个指标一起阅读。",
      rankByMetric: "排序指标",
      leaderboardRankingAria: "排行榜排序指标",
      leaderboardViewsAria: "排行榜视图",
      metricLabel: "指标",
      higherBetter: "越高越好",
      overallPerformanceTitle: "整体表现",
      scatterAria: "按模型比较平均主动意图恢复和任务完成表现的散点图",
      resourcesTitle: "资源",
      resourceCodeSub: "GitHub 仓库",
      resourceDataSub: "用户、episode、任务",
      citationTitle: "引用",
      footerText: "π-Bench 用于对主动式个人助理智能体进行受控评测。面向真实用户构建的系统应保留用户自主权、保护私人数据，并在决策具有现实影响时引入领域专家。",
      toTopAria: "回到顶部",
      rank: "#",
      model: "模型",
      proc: "Proc",
      comp: "Comp",
      avgProc: "平均 Proc",
      avgComp: "平均 Comp",
      allTasks: "全部任务",
      selectedDomain: "所选领域",
      tabOverall: "整体",
      loadingLeaderboard: "正在加载排行榜...",
      unableToLoadLeaderboard: "无法加载排行榜",
      formulaProc: "平均 Proc = 智能体完成的隐藏意图，或通过聚焦澄清引出的隐藏意图",
      formulaComp: "平均 Comp = 完整轨迹和产物中满足的可验证清单项",
      axisComp: "平均任务完成度，Comp (%)",
      axisProc: "平均主动意图恢复率，Proc (%)",
      leaderboardSummary: (metric, view) => `当前视图：按${metric}对${view}排序。`,
      tooltipOverall: (item) => `整体：Proc ${formatScore(item.proc)} ${formatError(item.procSd)}；Comp ${formatScore(item.comp)} ${formatError(item.compSd)}`.trim(),
      tooltipDomain: (name, proc, comp) => `${name}：Proc ${formatScore(proc)}；Comp ${formatScore(comp)}`,
      domainPerformanceAria: (name) => `${name}领域表现`,
      scatterPointAria: (item) => `${item.name}：平均 Proc ${formatScore(item.proc)}，平均 Comp ${formatScore(item.comp)}`,
      domains: {
        researcher: "研究员",
        marketer: "市场营销",
        pharmacist: "药剂师",
        law_trainee: "法律实习生",
        financier: "金融从业者"
      }
    }
  };

  const state = {
    data: null,
    sort: "proc",
    view: "overall"
  };

  let language = "en";

  function getCopy() {
    return copy[language] || copy.en;
  }

  function getSavedLanguage() {
    return localStorage.getItem("pibench-language") === "zh" ? "zh" : "en";
  }

  function setMetaContent(selector, content) {
    const node = document.querySelector(selector);
    if (node) node.setAttribute("content", content);
  }

  function applyStaticTranslations() {
    const strings = getCopy();
    root.lang = strings.htmlLang;
    document.title = strings.title;
    setMetaContent('meta[name="description"]', strings.metaDescription);
    setMetaContent('meta[property="og:title"]', strings.ogTitle);
    setMetaContent('meta[property="og:description"]', strings.ogDescription);

    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const value = strings[node.dataset.i18n];
      if (typeof value === "string") node.textContent = value;
    });
    document.querySelectorAll("[data-i18n-html]").forEach((node) => {
      const value = strings[node.dataset.i18nHtml];
      if (typeof value === "string") node.innerHTML = value;
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
      const value = strings[node.dataset.i18nAria];
      if (typeof value === "string") node.setAttribute("aria-label", value);
    });
    document.querySelectorAll("[data-i18n-alt]").forEach((node) => {
      const value = strings[node.dataset.i18nAlt];
      if (typeof value === "string") node.setAttribute("alt", value);
    });

    if (languageLabel) languageLabel.textContent = strings.languageLabel;
    if (languageToggle) languageToggle.setAttribute("aria-label", strings.languageToggleAria);
    updateThemeLabel();
  }

  function setLanguage(nextLanguage, options = {}) {
    language = nextLanguage === "zh" ? "zh" : "en";
    if (options.persist !== false) {
      localStorage.setItem("pibench-language", language);
    }
    applyStaticTranslations();
    renderSortButtons();
    if (state.data) {
      renderLeaderboard();
      initOverallScatter(state.data.models);
    } else if (leaderboardStatus) {
      leaderboardStatus.textContent = getCopy().loadingLeaderboard;
    }
  }

  function getSavedTheme() {
    return localStorage.getItem("pibench-theme") || "light";
  }

  function updateThemeLabel() {
    if (!themeLabel) return;
    const theme = root.dataset.theme || "light";
    const strings = getCopy();
    themeLabel.textContent = theme === "dark" ? strings.themeLight : strings.themeDark;
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
          domain.id,
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

  function getDomainLabel(id, fallback) {
    return getCopy().domains[id] || fallback || getCopy().selectedDomain;
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
    if (!state.data || view === "overall") return getCopy().allTasks;
    const domain = state.data.domains.find((item) => item.id === view);
    return domain ? getDomainLabel(domain.id, domain.label) : getCopy().selectedDomain;
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
    const tabs = [
      { id: "overall", label: getCopy().tabOverall },
      ...state.data.domains.map((domain) => ({
        id: domain.id,
        label: getDomainLabel(domain.id, domain.label)
      }))
    ];

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
      button.textContent = button.dataset.sort === "proc" ? getCopy().avgProc : getCopy().avgComp;
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
    const strings = getCopy();
    const procLabel = state.view === "overall" ? strings.avgProc : strings.proc;
    const compLabel = state.view === "overall" ? strings.avgComp : strings.comp;

    [strings.rank, strings.model, procLabel, compLabel].forEach((label) => {
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
      const metric = state.sort === "proc" ? getCopy().avgProc : getCopy().avgComp;
      leaderboardSummary.textContent = getCopy().leaderboardSummary(metric, getViewLabel(state.view));
    }
    if (leaderboardFormula) {
      leaderboardFormula.textContent = state.sort === "proc" ? getCopy().formulaProc : getCopy().formulaComp;
    }
  }

  function setLeaderboardError(error) {
    if (leaderboardTableWrap) {
      leaderboardTableWrap.hidden = true;
      leaderboardTableWrap.replaceChildren();
    }
    if (leaderboardStatus) {
      leaderboardStatus.hidden = false;
      leaderboardStatus.textContent = `${getCopy().unableToLoadLeaderboard}: ${error.message}`;
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
      [getCopy().avgProc, item.proc, item.procSd],
      [getCopy().avgComp, item.comp, item.compSd]
    ].forEach(([label, value, sd]) => {
      const box = document.createElement("div");
      box.append(
        createNode("span", "", label),
        createNode("span", "overall-score-value", `${formatScore(value)} ${formatError(sd)}`.trim())
      );
      overallGrid.appendChild(box);
    });

    const domainList = createNode("div", "domain-score-list");
    domainList.setAttribute("aria-label", getCopy().domainPerformanceAria(item.name));
    item.domains.forEach(([id, fallbackName, proc, comp]) => {
      const name = getDomainLabel(id, fallbackName);
      const row = createNode("div", "domain-score-row");
      const values = createNode("div", "domain-score-values");
      values.append(
        createNode("span", "", `${getCopy().proc}: ${formatScore(proc)}`),
        createNode("span", "", `${getCopy().comp}: ${formatScore(comp)}`)
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
    xLabel.textContent = getCopy().axisComp;
    svg.appendChild(xLabel);

    const yLabel = createSvgNode("text", {
      class: "scatter-axis-label",
      x: -margin.top - plotHeight / 2,
      y: 30,
      transform: "rotate(-90)",
      "text-anchor": "middle"
    });
    yLabel.textContent = getCopy().axisProc;
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
        { dx: 50, dy: -14, anchor: "end", leader: false, priority: -80 }
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
      appendTooltipLine(tooltip, getCopy().tooltipOverall(item));
      item.domains.forEach(([id, fallbackName, proc, comp]) => {
        appendTooltipLine(tooltip, getCopy().tooltipDomain(getDomainLabel(id, fallbackName), proc, comp));
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
        "aria-label": getCopy().scatterPointAria(item),
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
        leaderboardStatus.textContent = getCopy().loadingLeaderboard;
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

  if (languageToggle) {
    languageToggle.addEventListener("click", () => {
      setLanguage(language === "zh" ? "en" : "zh");
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

  setLanguage(getSavedLanguage(), { persist: false });
  setTheme(getSavedTheme());
  loadLeaderboard();
  updateProgress();
}());
