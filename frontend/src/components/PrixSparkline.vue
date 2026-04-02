<script setup>
import { computed } from "vue";

const props = defineProps({
  points: { type: Array, default: () => [] },
  label: { type: String, default: "Évolution du prix d’achat catalogue (ƒ)" },
  /** Champ à tracer dans les points: 'prix_achat' (achat) ou 'prix_modifie' (revente). */
  valueKey: { type: String, default: "prix_achat" },
});

const W = 340;
const H = 112;
const PAD = 10;

const pathD = computed(() => {
  const pts = props.points;
  if (!pts.length) return "";
  const key = props.valueKey || "prix_achat";
  const vals = pts.map((p) => Number(p?.[key]) || 0);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const n = pts.length;
  return pts
    .map((p, i) => {
      const v = Number(p?.[key]) || 0;
      const x = PAD + (n === 1 ? (W - 2 * PAD) / 2 : (i / (n - 1)) * (W - 2 * PAD));
      const y = PAD + (1 - (v - min) / span) * (H - 2 * PAD);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join("");
});

/** Un seul point : afficher un segment minimal pour que le trait soit visible. */
const pathDLine = computed(() => {
  if (props.points.length !== 1 || !pathD.value) return pathD.value;
  const pts = props.points;
  const key = props.valueKey || "prix_achat";
  const vals = pts.map((p) => Number(p?.[key]) || 0);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const span = max - min || 1;
  const v = Number(pts[0]?.[key]) || 0;
  const x = PAD + (W - 2 * PAD) / 2;
  const y = PAD + (1 - (v - min) / span) * (H - 2 * PAD);
  return `M${(x - 20).toFixed(1)},${y.toFixed(1)} L${(x + 20).toFixed(1)},${y.toFixed(1)}`;
});
</script>

<template>
  <div class="sparkline-wrap">
    <div class="sparkline-label">{{ label }}</div>
    <svg
      v-if="points.length"
      class="sparkline-svg"
      :viewBox="`0 0 ${W} ${H}`"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#5865f2" stop-opacity="0.22" />
          <stop offset="100%" stop-color="#5865f2" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path
        v-if="pathD && points.length > 1"
        :d="`${pathD} L${W - PAD},${H - PAD} L${PAD},${H - PAD} Z`"
        fill="url(#sparkFill)"
      />
      <path
        v-if="pathD && points.length > 1"
        :d="pathD"
        fill="none"
        stroke="#a5b4fc"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <path
        v-if="points.length === 1 && pathDLine"
        :d="pathDLine"
        fill="none"
        stroke="#a5b4fc"
        stroke-width="2"
        stroke-linecap="round"
      />
    </svg>
    <p v-else class="sparkline-empty">
      Pas encore d’historique : les points s’ajoutent lorsque le MJ modifie les prix du marché.
    </p>
  </div>
</template>

<style scoped>
.sparkline-wrap {
  margin: 12px 0 4px;
}
.sparkline-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 6px;
}
.sparkline-svg {
  width: 100%;
  max-width: 100%;
  height: auto;
  display: block;
  border-radius: 8px;
  background: #0f172a;
  border: 1px solid #334155;
}
.sparkline-empty {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  padding: 12px;
  background: #0f172a;
  border-radius: 8px;
  border: 1px dashed #334155;
}
</style>
