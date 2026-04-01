import { ref } from "vue";
import { useApi } from "../../../composables/useApi.js";

export function useResourcesApiData() {
  const { get } = useApi();

  const ressources = ref([]);
  const categories = ref([]);
  const utilisateursListe = ref([]);
  const erreur = ref("");

  async function chargerCategories() {
    try {
      categories.value = await get("/api/categories");
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function chargerUtilisateurs({ enabled }) {
    if (!enabled) return;
    try {
      utilisateursListe.value = await get("/api/utilisateurs");
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function chargerRessources({ isMj, mjVueChoix }) {
    try {
      let q = "";
      if (isMj) {
        if (mjVueChoix === "global") q = "?global=1";
        else q = `?as_user_id=${encodeURIComponent(String(mjVueChoix).trim())}`;
      }
      ressources.value = await get(`/api/ressources${q}`);
    } catch (e) {
      erreur.value = e.message;
    }
  }

  async function chargerTout({ isMj, mjVueChoix }) {
    await Promise.all([
      chargerCategories(),
      chargerRessources({ isMj, mjVueChoix }),
      chargerUtilisateurs({ enabled: isMj }),
    ]);
  }

  return {
    ressources,
    categories,
    utilisateursListe,
    erreur,
    chargerCategories,
    chargerRessources,
    chargerUtilisateurs,
    chargerTout,
  };
}

