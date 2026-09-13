import { loadPyodide } from "pyodide";

/** @import { Payload } from "./form.js" */

/** @typedef {{ report: (payload: string) => string }} RoofWeb */

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
 * Every module the page copies into Pyodide. A new module under `src/roof/`
 * has to be added here; `tests/test_web.py` checks the list against the tree.
 *
 * @type {readonly `roof/${string}.py`[]}
 */
const MODULES = [
  "roof/__init__.py",
  "roof/web.py",
  "roof/core/__init__.py",
  "roof/core/specs.py",
  "roof/core/roof.py",
  "roof/core/attic.py",
  "roof/core/sweep.py",
  "roof/core/validate.py",
  "roof/core/views.py",
  "roof/interpreters/__init__.py",
  "roof/interpreters/sk.py",
  "roof/interpreters/to_svg.py",
  "roof/interpreters/to_text.py",
  "roof/interpreters/to_csv.py",
  "roof/interpreters/to_html.py",
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
      `roof.web.report returned an unexpected shape: ${text.slice(0, SHAPE_ERROR_EXCERPT)}`,
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

  /** @type {RoofWeb} */
  const roofWeb = pyodide.pyimport("roof.web");

  return (payload) => asReport(roofWeb.report(JSON.stringify(payload)));
};

export { boot };
