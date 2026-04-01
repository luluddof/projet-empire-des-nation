<script setup>
import ResourcesPage from "./resources/ResourcesPage.vue";

defineProps({
  authState: { type: Object, required: true },
});
</script>

<template>
  <ResourcesPage :auth-state="authState" />
</template>
