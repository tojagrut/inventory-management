<template>
  <header class="topbar">
    <h1 class="topbar-title">{{ title }}</h1>

    <div class="topbar-actions">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </header>
</template>

<script setup>
import LanguageSwitcher from '../LanguageSwitcher.vue'
import ProfileMenu from '../ProfileMenu.vue'

defineProps({
  title: { type: String, default: '' }
})

defineEmits(['show-profile-details', 'show-tasks'])
</script>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  /* Above the sticky filter bar so the profile/language dropdowns overlay it. */
  z-index: 40;
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-8);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.topbar-title {
  flex: 1;
  min-width: 0;
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex: none;
}

@media (max-width: 767px) {
  .topbar { padding: 0 var(--space-3); }
  .topbar-actions { gap: var(--space-2); }

  /* Slim down the (unmodified) child widgets so nothing clips at 375px.
     Keep the avatar, drop the name and chevron. */
  .topbar-actions :deep(.profile-name),
  .topbar-actions :deep(.profile-button .chevron) { display: none; }
  .topbar-actions :deep(.profile-button),
  .topbar-actions :deep(.language-button) {
    padding: var(--space-2);
    gap: var(--space-1);
  }
}

/* Very narrow phones: the globe icon alone is enough. */
@media (max-width: 479px) {
  .topbar-actions :deep(.language-label) { display: none; }
}
</style>
