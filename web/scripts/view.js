import { ui } from "./ui.js";

/** @import { Report } from "./runtime.js" */

/** @typedef {"report" | "table" | "csv"} Pane */

/** @param {string | undefined} value @returns {Pane | null} */
const asPane = (value) =>
  value === "report" || value === "table" || value === "csv" ? value : null;

/** @returns {Pane} */
const selected = () => {
  for (const tab of ui.tabs) {
    const pane = asPane(tab.dataset.view);

    if (pane && tab.getAttribute("aria-selected") === "true") {
      return pane;
    }
  }

  throw new Error("no tab is selected");
};

/** @returns {boolean} */
const refused = () => !ui.problems.classList.contains("hidden");

/** @returns {void} */
const renderPanes = () => {
  const pane = selected();
  const blocked = refused();

  for (const [name, node] of /** @type {const} */ ([
    ["report", ui.report],
    ["table", ui.table],
    ["csv", ui.csv],
  ])) {
    node.classList.toggle("hidden", blocked || name !== pane);
  }
};

/** @param {string[]} problems @returns {HTMLUListElement} */
const problemList = (problems) => {
  const list = document.createElement("ul");

  for (const problem of problems) {
    const item = document.createElement("li");
    item.textContent = problem;
    list.append(item);
  }

  return list;
};

/** @param {string[]} problems @returns {void} */
const renderProblems = (problems) => {
  ui.problems.classList.toggle("hidden", problems.length === 0);
  ui.problems.textContent = "";

  if (problems.length === 0) {
    return;
  }

  ui.problems.append(problemList(problems));
};

/** @param {string[]} problems @returns {void} */
const showProblems = (problems) => {
  renderProblems(problems);
  renderPanes();
};

/** @param {Report} report @returns {void} */
const showReport = (report) => {
  if (report.problems.length === 0) {
    ui.report.srcdoc = report.html;
    ui.table.textContent = report.table;
    ui.csv.textContent = report.csv;
    ui.downloadCsv.disabled = false;
    ui.downloadHtml.disabled = false;
  }

  showProblems(report.problems);
};

/** @param {string} name @param {string} text @param {string} type @returns {void} */
const download = (name, text, type) => {
  const url = URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
};

/** @param {HTMLButtonElement} tab @returns {void} */
const selectPane = (tab) => {
  for (const other of ui.tabs) {
    other.setAttribute("aria-selected", String(other === tab));
  }

  renderPanes();
};

/** @returns {void} */
const downloadCsv = () => download("sweep.csv", ui.csv.textContent ?? "", "text/csv");

/** @returns {void} */
const downloadHtml = () => download("roof.html", ui.report.srcdoc, "text/html");

export { downloadCsv, downloadHtml, selectPane, showProblems, showReport };
