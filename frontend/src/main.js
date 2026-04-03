import { createApp } from "vue";
import App from "./App.vue";
import { authLoading, authState } from "./authState.js";
import { router } from "./router/index.js";
import "./style.css";

function waitAuthReady() {
  return new Promise((resolve) => {
    const tick = () => {
      if (!authLoading.value) {
        resolve();
        return;
      }
      requestAnimationFrame(tick);
    };
    tick();
  });
}

router.beforeEach(async (to, from, next) => {
  if (!to.meta.requiresAuth) {
    next();
    return;
  }
  await waitAuthReady();
  if (!authState.value.authenticated) {
    next({ path: "/", replace: true });
  } else {
    next();
  }
});

createApp(App).use(router).mount("#app");
