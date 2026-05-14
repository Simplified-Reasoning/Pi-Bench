(function () {
  const root = document.documentElement;
  const languageButtons = document.querySelectorAll("[data-lang]");
  const i18nNodes = document.querySelectorAll("[data-i18n-en]");
  const themeToggle = document.getElementById("themeToggle");
  const themeLabel = document.getElementById("themeLabel");
  const progressBar = document.getElementById("progressBar");
  const toTop = document.getElementById("toTop");

  function getSavedLanguage() {
    return localStorage.getItem("pibench-lang") || "en";
  }

  function setLanguage(lang) {
    const key = lang === "zh" ? "i18nZh" : "i18nEn";
    root.lang = lang === "zh" ? "zh-CN" : "en";
    i18nNodes.forEach((node) => {
      if (node.dataset[key]) {
        node.textContent = node.dataset[key];
      }
    });
    languageButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.lang === lang);
      button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
    });
    localStorage.setItem("pibench-lang", lang);
    updateThemeLabel();
  }

  function getSavedTheme() {
    return localStorage.getItem("pibench-theme") || "light";
  }

  function updateThemeLabel() {
    if (!themeLabel) return;
    const lang = getSavedLanguage();
    const theme = root.dataset.theme || "light";
    if (lang === "zh") {
      themeLabel.textContent = theme === "dark" ? "浅色" : "深色";
    } else {
      themeLabel.textContent = theme === "dark" ? "Light" : "Dark";
    }
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

  function copyText(button) {
    const text = button.dataset.copy;
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      const lang = getSavedLanguage();
      const previous = button.textContent;
      button.textContent = lang === "zh" ? "已复制" : "Copied";
      setTimeout(() => {
        button.textContent = previous;
      }, 1400);
    }).catch(() => {
      const lang = getSavedLanguage();
      button.textContent = lang === "zh" ? "复制失败" : "Copy failed";
    });
  }

  languageButtons.forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.lang));
  });

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      setTheme(root.dataset.theme === "dark" ? "light" : "dark");
    });
  }

  document.querySelectorAll(".copy-button").forEach((button) => {
    button.addEventListener("click", () => copyText(button));
  });

  if (toTop) {
    toTop.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  window.addEventListener("scroll", updateProgress, { passive: true });
  window.addEventListener("resize", updateProgress);

  setTheme(getSavedTheme());
  setLanguage(getSavedLanguage());
  updateProgress();
}());
