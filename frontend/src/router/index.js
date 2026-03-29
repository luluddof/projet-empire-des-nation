import { createRouter, createWebHistory } from "vue-router";

import EarningsView from "../views/EarningsView.vue";
import HomeView from "../views/HomeView.vue";
import MjJoueursView from "../views/MjJoueursView.vue";
import ProductionsView from "../views/ProductionsView.vue";
import ResourcesView from "../views/ResourcesView.vue";
import StocksView from "../views/StocksView.vue";

const routes = [
  { path: "/", name: "home", component: HomeView },
  {
    path: "/ressources",
    name: "ressources",
    component: ResourcesView,
    meta: { requiresAuth: true },
  },
  {
    path: "/stocks",
    name: "stocks",
    component: StocksView,
    meta: { requiresAuth: true },
  },
  {
    path: "/productions",
    name: "productions",
    component: ProductionsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/gains",
    name: "gains",
    component: EarningsView,
    meta: { requiresAuth: true },
  },
  {
    path: "/mj/joueurs",
    name: "mj-joueurs",
    component: MjJoueursView,
    meta: { requiresAuth: true },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
