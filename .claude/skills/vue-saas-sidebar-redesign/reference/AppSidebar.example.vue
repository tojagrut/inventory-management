<!--
  Reference sidebar for the SaaS redesign skill.
  The PARENT shell owns `collapsed` and passes translated labels (navLabel, expandLabel,
  collapseLabel) as props. Choose a phone (< 768px) mode:
  - Drawer (default, supported by this file): the parent owns `drawerOpen`, renders the backdrop,
    handles Escape and route-change closing, shows a hamburger, calls `focusFirstItem()` on open,
    restores focus to the hamburger on close and sets `inert` on the main column while open.
  - Icons-only rail: the parent passes collapsed=true below 768px (e.g. a computed
    `effectiveCollapsed = collapsed || isMobile`, so the saved desktop preference is not
    overwritten), never sets `drawerOpen`, keeps the sidebar in the grid, and replaces the
    drawer `@media (max-width: 767px)` block below with `.collapse-toggle { display: none }`.
-->
<template>
  <aside
    id="app-sidebar"
    ref="rootEl"
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-open': drawerOpen }"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <span class="brand-name">{{ brand }}</span>
    </div>

    <nav class="sidebar-nav" :aria-label="navLabel">
      <router-link
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :exact-active-class="item.to === '/' ? 'is-active' : ''"
        :active-class="item.to === '/' ? '' : 'is-active'"
        :title="collapsed ? item.label : undefined"
        :aria-label="collapsed ? item.label : undefined"
        @click="$emit('navigate')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path :d="item.icon" />
        </svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" />
      <button
        type="button"
        class="collapse-toggle"
        :aria-label="collapsed ? expandLabel : collapseLabel"
        :aria-expanded="!collapsed"
        @click="$emit('toggle-collapse')"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" :class="{ flipped: collapsed }">
          <path d="M15 6l-6 6 6 6" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  brand: { type: String, required: true },
  items: { type: Array, required: true },
  collapsed: { type: Boolean, default: false },
  drawerOpen: { type: Boolean, default: false },
  // Translated strings passed from the parent.
  navLabel: { type: String, default: 'Main' },
  expandLabel: { type: String, default: 'Expand sidebar' },
  collapseLabel: { type: String, default: 'Collapse sidebar' }
})

defineEmits(['toggle-collapse', 'navigate'])

const rootEl = ref(null)

// The parent calls this when the drawer opens so keyboard focus moves into it.
defineExpose({
  focusFirstItem: () => rootEl.value?.querySelector('.nav-item')?.focus()
})

const brandInitial = computed(() => (props.brand || '').charAt(0).toUpperCase())
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  height: 100dvh; /* mobile browsers: 100vh includes the collapsing URL bar */
  display: flex;
  flex-direction: column;
  background: var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  padding: var(--space-4) var(--space-3);
  gap: var(--space-4);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) var(--space-2) var(--space-3);
  min-height: 40px;
}
.brand-mark {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
}
.brand-name {
  color: var(--color-sidebar-text-active);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: inherit;
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: 500;
  transition: background var(--transition-fast), color var(--transition-fast);
}
.nav-item:hover { background: var(--color-sidebar-item-hover); color: var(--color-sidebar-text-active); }
.nav-item.is-active { background: var(--color-sidebar-item-active); color: var(--color-sidebar-text-active); }
.nav-icon, .collapse-toggle svg {
  flex: none;
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer { display: flex; flex-direction: column; gap: var(--space-2); }
.collapse-toggle {
  align-self: flex-end;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: inherit;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.collapse-toggle:hover { background: var(--color-sidebar-item-hover); }
.collapse-toggle svg.flipped { transform: rotate(180deg); }

/* Visually hidden but still announced by screen readers. */
@media (min-width: 768px) {
  .is-collapsed .nav-label,
  .is-collapsed .brand-name {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .is-collapsed .nav-item { justify-content: center; padding: 0; }
  .is-collapsed .sidebar-brand { justify-content: center; padding-inline: 0; }
  .is-collapsed .collapse-toggle { align-self: center; }
}

/* Mobile: off-canvas drawer. The parent renders the backdrop and toggles `drawerOpen`. */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    z-index: 50;
    transform: translateX(-100%);
    /* Hide after the slide-out finishes so closed-drawer links cannot take focus. */
    visibility: hidden;
    transition: transform var(--transition-fast), visibility 0s linear 150ms;
  }
  .sidebar.is-open {
    transform: translateX(0);
    visibility: visible;
    transition: transform var(--transition-fast), visibility 0s;
  }
  .collapse-toggle { display: none; }
}
</style>
