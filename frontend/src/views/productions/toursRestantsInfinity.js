/** Minuscules, sans accents, espaces normalisés (pour reconnaître « infini », « l’infini », etc.). */
export function normalizeInfinityText(s) {
  return String(s)
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(/['']/g, "")
    .replace(/\s+/g, " ");
}

/** True si la chaîne ressemble à « infini » (distance ≤ 2, longueur raisonnable). */
export function levenshtein1ToInfini(s) {
  const target = "infini";
  if (s === target) return true;
  if (s.includes("infini")) return true;
  if (s.length < 4 || s.length > 9) return false;
  const a = target;
  const b = s;
  const rows = a.length + 1;
  const cols = b.length + 1;
  const dp = Array.from({ length: rows }, () => Array.from({ length: cols }, () => 0));
  for (let i = 0; i < rows; i++) dp[i][0] = i;
  for (let j = 0; j < cols; j++) dp[0][j] = j;
  for (let i = 1; i < rows; i++) {
    for (let j = 1; j < cols; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost);
    }
  }
  return dp[a.length][b.length] <= 2;
}

/**
 * Texte interprété comme « illimité » : vide, symbole ∞, ou formulations proches de infini / synonymes.
 */
export function textMeansInfinity(raw) {
  const t = String(raw ?? "").trim();
  if (t === "") return true;
  if (t === "∞" || t === "\u221e") return true;

  const n = normalizeInfinityText(t);

  if (n === "inf" || n === "infinity") return true;

  const patterns = [
    /^infini$/,
    /^infinie$/,
    /^infinis$/,
    /^infinit$/,
    /^l infini$/,
    /^linfini$/,
    /infini/,
    /infin\b/,
    /illimit/,
    /sans limite/,
    /sans fin/,
    /pour toujours/,
    /a vie$/,
    /etern/,
    /toujours/,
    /unlimited/,
    /unendlich/,
    /jamais fin/,
  ];
  if (patterns.some((re) => re.test(n))) return true;

  if (n.length >= 4 && n.length <= 12 && levenshtein1ToInfini(n)) return true;

  return false;
}
