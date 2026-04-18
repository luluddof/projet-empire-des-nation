export const VOIR_TOUTES_KEY = "stocks_voir_toutes_ressources";

export function readVoirToutesPref() {
  try {
    return typeof localStorage !== "undefined" && localStorage.getItem(VOIR_TOUTES_KEY) === "1";
  } catch {
    return false;
  }
}

export function persistVoirToutes(v) {
  try {
    localStorage.setItem(VOIR_TOUTES_KEY, v ? "1" : "0");
  } catch {
    /* ignore */
  }
}
