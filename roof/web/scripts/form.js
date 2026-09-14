import { ui } from "./ui.js";

/**
 * The inputs `uv run cli` takes as flags.
 *
 * @typedef {object} Payload
 * @property {number[]} widths
 * @property {number[]} pitches_deg
 * @property {number} length
 * @property {number} overhang_eave
 * @property {number} overhang_gable
 * @property {number} h_min
 * @property {number} roof_buildup
 * @property {number} floor_buildup
 * @property {number} knee_height
 * @property {number | null} collar_above_wall_top
 * @property {number} eur_per_m2
 */

const NOT_A_NUMBER = "nie je číslo";
const NOTHING_GIVEN = "zadaj aspoň jednu hodnotu";

/** @param {string} text @returns {number[]} */
const numberList = (text) =>
  text
    .split(/[\s,]+/u)
    .filter(Boolean)
    .map(Number);

/** @param {string} name @returns {string} */
const field = (name) => {
  // Avoids `ui.form.elements[name]`, where `length` shadows the field.
  const found = ui.form.elements.namedItem(name);
  if (!(found instanceof HTMLInputElement)) {
    throw new Error(`no input named ${name}`);
  }
  return found.value.trim();
};

/** @returns {Payload} */
const readPayload = () => {
  const collar = field("collar_above_wall_top");
  return {
    widths: numberList(field("widths")),
    pitches_deg: numberList(field("pitches_deg")),
    length: Number(field("length")),
    overhang_eave: Number(field("overhang_eave")),
    overhang_gable: Number(field("overhang_gable")),
    h_min: Number(field("h_min")),
    roof_buildup: Number(field("roof_buildup")),
    floor_buildup: Number(field("floor_buildup")),
    knee_height: Number(field("knee_height")),
    // Empty means no collar tie (`--collar 0` on the CLI).
    collar_above_wall_top: collar === "" ? null : Number(collar),
    eur_per_m2: Number(field("eur_per_m2")),
  };
};

/** @param {string} key @param {number | number[] | null} value @returns {string[]} */
const fieldProblems = (key, value) => {
  if (value === null) {
    return [];
  }
  if (!Array.isArray(value)) {
    if (Number.isNaN(value)) {
      return [`${key}: ${NOT_A_NUMBER}`];
    }
    return [];
  }
  if (value.length === 0) {
    return [`${key}: ${NOTHING_GIVEN}`];
  }
  if (value.some(Number.isNaN)) {
    return [`${key}: ${NOT_A_NUMBER}`];
  }
  return [];
};

/** @param {Payload} payload @returns {string[]} */
const malformed = (payload) =>
  Object.entries(payload).flatMap(([key, value]) => fieldProblems(key, value));

export { malformed, readPayload };
