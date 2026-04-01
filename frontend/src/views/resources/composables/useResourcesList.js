import { computed, reactive } from "vue";

export function useResourcesList({ ressourcesRef, categoriesRef, rechercheRef, filtreCategorieIdRef }) {
  const sort = reactive({ key: "nom", dir: "asc" });

  const ressourcesFiltrees = computed(() => {
    return (ressourcesRef.value || []).filter((r) => {
      const okNom = String(r.nom || "").toLowerCase().includes(String(rechercheRef.value || "").toLowerCase());
      const okCat =
        !filtreCategorieIdRef.value ||
        (r.categorie_ids || []).includes(Number(filtreCategorieIdRef.value));
      return okNom && okCat;
    });
  });

  function categorieSortKey(r) {
    const cats = r.categories || [];
    return cats.map((c) => c.nom).sort().join(", ") || "zzz";
  }

  function sortedList(list) {
    const key = sort.key;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...list].sort((a, b) => {
      let va;
      let vb;
      switch (key) {
        case "nom":
          va = a.nom.toLowerCase();
          vb = b.nom.toLowerCase();
          break;
        case "type":
          va = a.type;
          vb = b.type;
          break;
        case "prix_base":
          va = a.prix_base;
          vb = b.prix_base;
          break;
        case "modificateur_pct":
          va = a.modificateur_pct;
          vb = b.modificateur_pct;
          break;
        case "facteur_prix":
          va = a.facteur_prix;
          vb = b.facteur_prix;
          break;
        case "prix_modifie":
          va = a.prix_modifie;
          vb = b.prix_modifie;
          break;
        case "prix_achat":
          va = a.prix_achat;
          vb = b.prix_achat;
          break;
        case "prix_lointain":
          va = a.prix_lointain;
          vb = b.prix_lointain;
          break;
        case "categories":
          va = categorieSortKey(a);
          vb = categorieSortKey(b);
          break;
        default:
          va = a.nom;
          vb = b.nom;
      }
      if (typeof va === "string") return va < vb ? -dir : va > vb ? dir : 0;
      return va === vb ? 0 : va < vb ? -dir : dir;
    });
  }

  const listePremiere = computed(() =>
    sortedList(ressourcesFiltrees.value.filter((r) => r.type === "Première")),
  );
  const listeManufacture = computed(() =>
    sortedList(ressourcesFiltrees.value.filter((r) => r.type === "Manufacturé")),
  );

  function toggleSort(key) {
    if (sort.key === key) sort.dir = sort.dir === "asc" ? "desc" : "asc";
    else {
      sort.key = key;
      sort.dir = "asc";
    }
  }

  function sortLabel(key) {
    if (sort.key !== key) return "";
    return sort.dir === "asc" ? " ▲" : " ▼";
  }

  // utilisé pour l'aperçu dans la modale ressource
  function previewPrix(prixBase, facteur) {
    const m = Number(facteur) || 1;
    const pb = Number(prixBase) || 0;
    const pm = Math.round(pb * m);
    return {
      prix_modifie: pm,
      prix_achat: Math.round(pm * 1.2),
      prix_lointain: Math.round(pm * 2.5),
    };
  }

  function getCategorieById(id) {
    return (categoriesRef.value || []).find((x) => x.id === id);
  }

  return {
    sort,
    ressourcesFiltrees,
    listePremiere,
    listeManufacture,
    toggleSort,
    sortLabel,
    previewPrix,
    getCategorieById,
  };
}

