import { loadPyodide } from "pyodide";

/** @import { Payload } from "./form.js" */

/** @typedef {{ report: (payload: string) => string }} HouseWeb */

/**
 * @typedef {object} Report
 * @property {string[]} problems
 * @property {string} table
 * @property {string} csv
 * @property {string} html
 */

/** @typedef {(payload: Payload) => Report} Sweep */

const SHAPE_ERROR_EXCERPT = 200;

/**
 * Every module the page copies into Pyodide. A new module under `src/house/`
 * has to be added here; `tests/test_web.py` checks the list against the tree.
 *
 * @type {readonly `house/${string}.py`[]}
 */
const MODULES = [
  "house/__init__.py",
  "house/web.py",
  "house/core/__init__.py",
  "house/core/specs.py",
  "house/core/roof.py",
  "house/core/attic.py",
  "house/core/sweep.py",
  "house/core/validate.py",
  "house/core/views.py",
  "house/interpreters/__init__.py",
  "house/interpreters/sk.py",
  "house/interpreters/to_svg.py",
  "house/interpreters/to_text.py",
  "house/interpreters/to_csv.py",
  "house/interpreters/to_html.py",
];

/** @param {string} text @returns {Report} */
const asReport = (text) => {
  const { problems, table, csv, html } = JSON.parse(text);

  if (
    !Array.isArray(problems) ||
    problems.some((problem) => typeof problem !== "string") ||
    typeof table !== "string" ||
    typeof csv !== "string" ||
    typeof html !== "string"
  ) {
    throw new TypeError(
      `house.web.report returned an unexpected shape: ${text.slice(0, SHAPE_ERROR_EXCERPT)}`,
    );
  }

  return { problems, table, csv, html };
};

/**
 * @returns {Promise<Sweep>}
 */
const boot = async () => {
  const pyodide = await loadPyodide();
  await Promise.all(
    MODULES.map(async (name) => {
      // Uses `no-store` so a reload picks up edits under src/.
      const response = await fetch(`../src/${name}`, { cache: "no-store" });

      if (!response.ok) {
        throw new Error(`../src/${name}: ${response.status}`);
      }

      pyodide.FS.mkdirTree(`/lib/${name.split("/").slice(0, -1).join("/")}`);
      pyodide.FS.writeFile(`/lib/${name}`, await response.text());
    }),
  );

  pyodide.runPython(`import sys; sys.path.insert(0, "/lib")`);

  /** @type {HouseWeb} */
  const houseWeb = pyodide.pyimport("house.web");

  return (payload) => asReport(houseWeb.report(JSON.stringify(payload)));
};

export { boot };
