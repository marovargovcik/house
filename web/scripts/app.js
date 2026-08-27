import { malformed, readPayload } from "./form.js";
import { boot } from "./runtime.js";
import { ui } from "./ui.js";
import {
  downloadCsv,
  downloadHtml,
  selectPane,
  showProblems,
  showReport,
} from "./view.js";

/** @import { Sweep } from "./runtime.js" */

for (const tab of ui.tabs) {
  tab.addEventListener("click", () => selectPane(tab));
}
ui.downloadCsv.addEventListener("click", downloadCsv);
ui.downloadHtml.addEventListener("click", downloadHtml);

/** @returns {Promise<Sweep>} */
const bootOrExplain = async () => {
  try {
    return await boot();
  } catch (error) {
    ui.status.textContent = "nepodarilo sa načítať";
    showProblems([String(error)]);
    throw error;
  }
};

const sweep = await bootOrExplain();

ui.run.disabled = false;
ui.status.textContent = "pripravené";

ui.form.addEventListener("submit", (event) => {
  event.preventDefault();

  const payload = readPayload();
  const bad = malformed(payload);

  if (bad.length > 0) {
    return showProblems(bad);
  }

  ui.status.textContent = "počítam…";

  setTimeout(() => {
    const started = performance.now();

    try {
      const result = sweep(payload);
      showReport(result);
      ui.status.textContent = `hotovo za ${Math.round(performance.now() - started)} ms`;
    } catch (error) {
      showProblems([String(error)]);
      ui.status.textContent = "chyba";
    }
  }, 0);
});

ui.form.requestSubmit();
