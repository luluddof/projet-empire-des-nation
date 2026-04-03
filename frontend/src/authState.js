import { ref } from "vue";

/** État partagé pour le garde de navigation (mis à jour par App.vue après /api/auth/me). */
export const authState = ref({ authenticated: false, user: null });
export const authLoading = ref(true);

/** À appeler à la déconnexion : sinon « Voir comme » reste sur l’ancienne préférence (ex. global). */
export function clearMjViewLocalStorage() {
  try {
    localStorage.removeItem("mj_view_choice_uid");
    localStorage.removeItem("mj_view_choice");
  } catch {
    // ignore
  }
}
