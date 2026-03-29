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

export function formatFlorin(value) {
  if (value == null) return "—";
  return new Intl.NumberFormat("fr-FR").format(value) + " ƒ";
}
