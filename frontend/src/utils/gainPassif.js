/**
 * Variation nette de stock au prochain tour pour une ressource,
 * en appliquant les règles actives dans l’ordre des id (aligné backend).
 */
export function deltaNetProchainTour(stockQuantite, gainsPourRessource) {
  const list = (gainsPourRessource || [])
    .filter((g) => g.actif)
    .sort((a, b) => (a.id ?? 0) - (b.id ?? 0));
  let cur = Number(stockQuantite) || 0;
  let total = 0;
  for (const g of list) {
    const mode = g.mode_production || "fixe";
    const d =
      mode === "pourcentage"
        ? Math.trunc((cur * g.quantite_par_tour) / 100)
        : g.quantite_par_tour;
    cur += d;
    total += d;
  }
  return total;
}

export const BALISE_LABELS = {
  science: "Science",
  politique: "Politique",
  evenement: "Événement",
  autre: "Autre",
};

export function libelleBalise(b) {
  return BALISE_LABELS[b] ?? BALISE_LABELS.autre;
}

export function formatEffetProduction(g) {
  const mode = g.mode_production || "fixe";
  const q = g.quantite_par_tour;
  if (mode === "pourcentage") {
    const s = q > 0 ? `+${q}` : String(q);
    return `${s} % du stock`;
  }
  const s = q > 0 ? `+${q}` : String(q);
  return `${s} unités`;
}
