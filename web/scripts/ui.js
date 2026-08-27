/**
 * @template {new (...args: never[]) => HTMLElement} T
 * @param {string} id
 * @param {T} kind
 * @returns {InstanceType<T>}
 */
const element = (id, kind) => {
  const found = document.getElementById(id);

  if (!(found instanceof kind)) {
    throw new Error(`#${id} is missing or is not a ${kind.name}`);
  }

  return /** @type {InstanceType<T>} */ (found);
};

/**
 * @template {new (...args: never[]) => HTMLElement} T
 * @param {string} selector
 * @param {T} kind
 * @returns {InstanceType<T>[]}
 */
const elements = (selector, kind) => {
  const found = [...document.querySelectorAll(selector)];

  if (found.length === 0) {
    throw new Error(`${selector} matches nothing`);
  }

  for (const node of found) {
    if (!(node instanceof kind)) {
      throw new Error(`${selector} matched something that is not a ${kind.name}`);
    }
  }

  return /** @type {InstanceType<T>[]} */ (found);
};

const ui = {
  form: element("form", HTMLFormElement),
  status: element("status", HTMLElement),
  problems: element("problems", HTMLDivElement),
  report: element("report", HTMLIFrameElement),
  table: element("table", HTMLPreElement),
  csv: element("csv", HTMLPreElement),
  run: element("run", HTMLButtonElement),
  downloadCsv: element("download-csv", HTMLButtonElement),
  downloadHtml: element("download-html", HTMLButtonElement),
  tabs: elements("button.tab", HTMLButtonElement),
};

export { ui };
