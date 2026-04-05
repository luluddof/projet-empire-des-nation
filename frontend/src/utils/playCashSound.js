import cashSoundUrl from "../../ressources/cashSound.mp3?url";

let audio;

/**
 * Retour joué après un achat / vente réussi (nécessite un geste utilisateur pour éviter le blocage navigateur).
 */
export function playCashSound() {
  try {
    if (!audio) {
      audio = new Audio(cashSoundUrl);
      audio.volume = 0.45;
    }
    audio.currentTime = 0;
    void audio.play();
  } catch {
    /* autoplay / fichier manquant */
  }
}
