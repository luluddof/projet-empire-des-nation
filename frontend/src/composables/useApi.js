/** Vide = même origine (proxy Vite /api → backend). Sinon URL absolue ex. prod. */
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export function useApi() {
  async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error ?? `Erreur HTTP ${res.status}`);
    }
    return res.json();
  }

  const get = (path) => request(path);
  const post = (path, data) => request(path, { method: "POST", body: JSON.stringify(data) });
  const put = (path, data) => request(path, { method: "PUT", body: JSON.stringify(data) });
  const patch = (path, data) => request(path, { method: "PATCH", body: JSON.stringify(data) });
  const del = (path) => request(path, { method: "DELETE" });

  return { get, post, put, patch, del };
}

/** Nom API / seed de la ressource monnaie (unité = 1 ƒ). */
export const FLORINS_NOM = "Florins";

const intlEntier = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

/**
 * Grand nombre lisible : milliers (k), millions (M), milliards (Md), sans symbole monétaire.
 */
export function formatCompactNombre(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  const sign = n < 0 ? "−" : "";
  const abs = Math.abs(n);
  if (abs < 1000) {
    return sign + intlEntier.format(Math.round(abs));
  }
  if (abs < 1_000_000) {
    const x = abs / 1000;
    const maxFrac = x >= 100 ? 0 : x >= 10 ? 1 : 2;
    const txt = new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: maxFrac,
      minimumFractionDigits: 0,
    }).format(x);
    return sign + txt + " k";
  }
  if (abs < 1_000_000_000) {
    const x = abs / 1_000_000;
    const maxFrac = x >= 100 ? 0 : 1;
    const txt = new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: maxFrac,
      minimumFractionDigits: 0,
    }).format(x);
    return sign + txt + " M";
  }
  const x = abs / 1_000_000_000;
  const maxFrac = x >= 100 ? 0 : 1;
  const txt = new Intl.NumberFormat("fr-FR", {
    maximumFractionDigits: maxFrac,
    minimumFractionDigits: 0,
  }).format(x);
  return sign + txt + " Md";
}

/**
 * Montant en florins (abrégé : k / M / Md). Valeur exacte pour infobulle : {@link formatFlorinExact}.
 */
export function formatFlorin(value) {
  if (value == null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  return formatCompactNombre(n) + " ƒ";
}

/** Florins en notation complète (infobulle, détail). */
export function formatFlorinExact(value) {
  if (value == null) return "";
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return "";
  const sign = n < 0 ? "−" : "";
  return sign + intlEntier.format(Math.abs(n)) + " ƒ";
}

/**
 * Quantité de ressource physique (ordre de grandeur ≤ milliers) : entiers groupés, sans suffixe k/M.
 */
export function formatQuantiteRessource(value) {
  if (value == null || value === "") return "—";
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return "—";
  return intlEntier.format(n);
}
