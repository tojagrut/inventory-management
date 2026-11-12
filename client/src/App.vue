<template>
  <!--
    Grid shell: [sidebar | main]. `minmax(0, 1fr)` (and min-width: 0 on .app-main) lets wide
    tables/charts shrink instead of stretching the page horizontally.
  -->
  <div class="app-shell" :class="{ 'is-collapsed': effectiveCollapsed }">
    <AppSidebar
      :brand="t('nav.companyName')"
      :items="navItems"
      :nav-label="t('nav.mainNavigation')"
      :expand-label="t('nav.expandSidebar')"
      :collapse-label="t('nav.collapseSidebar')"
      :collapsed="effectiveCollapsed"
      @toggle-collapse="toggleCollapse"
    />

    <div class="app-main">
      <AppTopbar
        :title="pageTitle"
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
      <!-- Sticks directly below the topbar. -->
      <div class="app-filterbar">
        <FilterBar />
      </div>
      <main class="app-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppTopbar from './components/layout/AppTopbar.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileDetailsModal,
    TasksModal,
    AppSidebar,
    AppTopbar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const route = useRoute()

    // Inline SVG path data (24x24 viewBox, stroke icons) for the sidebar.
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'M4 5h6v6H4zM14 5h6v6h-6zM4 15h6v4H4zM14 15h6v4h-6z' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'M21 8l-9-5-9 5 9 5 9-5zM3 8v8l9 5 9-5V8M12 13v8' },
      { to: '/orders', label: t('nav.orders'), icon: 'M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1zM8 6H6a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-2M9 12h6M9 16h6' },
      { to: '/spending', label: t('nav.finance'), icon: 'M12 3v18M16 7.5c-.8-1-2.2-1.5-4-1.5-2.2 0-4 1-4 2.8s1.6 2.4 4 3.2 4 1.2 4 3.2S14.2 18 12 18c-1.8 0-3.2-.6-4-1.6' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' },
      { to: '/reports', label: t('nav.reports'), icon: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6' }
    ])

    // Page title = label of the matching nav item (longest prefix wins; '/' only matches exactly).
    const pageTitle = computed(() => {
      const path = route.path
      const match = navItems.value.find(item =>
        item.to === '/' ? path === '/' : path === item.to || path.startsWith(item.to + '/')
      )
      return match ? match.label : t('nav.companyName')
    })

    // ---- Sidebar state (owned here, rendered by AppSidebar) ----
    const COLLAPSED_KEY = 'sidebar-collapsed'

    // localStorage can throw (private mode, blocked storage); never let that break the app.
    const readStoredCollapsed = () => {
      try {
        const v = localStorage.getItem(COLLAPSED_KEY)
        return v === 'true' ? true : v === 'false' ? false : null
      } catch (e) {
        return null
      }
    }
    const writeStoredCollapsed = (value) => {
      try {
        localStorage.setItem(COLLAPSED_KEY, String(value))
      } catch (e) {
        // ignore: the choice just won't persist
      }
    }

    // Breakpoints: >= 1024 expanded, 768-1023 icon-only, < 768 icons-only rail (see effectiveCollapsed).
    const desktopQuery = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(min-width: 1024px)') : null
    const mobileQuery = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(max-width: 767px)') : null

    // A saved user choice wins; otherwise default by viewport width.
    const storedCollapsed = readStoredCollapsed()
    const hasUserPreference = ref(storedCollapsed !== null)
    const collapsed = ref(storedCollapsed !== null ? storedCollapsed : (desktopQuery ? !desktopQuery.matches : false))
    // Below 768px the sidebar is always an icons-only rail. Derived (not written into `collapsed`)
    // so the user's saved desktop preference in localStorage is never overwritten, and so the
    // `collapsed` prop also drives the nav icons' title/aria-label (which CSS alone cannot do).
    const isMobile = ref(mobileQuery ? mobileQuery.matches : false)
    const effectiveCollapsed = computed(() => collapsed.value || isMobile.value)

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
      hasUserPreference.value = true
      writeStoredCollapsed(collapsed.value)
    }

    // Without a saved preference, keep following the viewport when it crosses 1024px.
    const onDesktopChange = (e) => {
      if (!hasUserPreference.value) collapsed.value = !e.matches
    }
    const onMobileChange = (e) => {
      isMobile.value = e.matches
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      if (desktopQuery) desktopQuery.addEventListener('change', onDesktopChange)
      if (mobileQuery) mobileQuery.addEventListener('change', onMobileChange)
    })

    onBeforeUnmount(() => {
      if (desktopQuery) desktopQuery.removeEventListener('change', onDesktopChange)
      if (mobileQuery) mobileQuery.removeEventListener('change', onMobileChange)
    })

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      navItems,
      pageTitle,
      effectiveCollapsed,
      toggleCollapse
    }
  }
}
</script>

<style>
/*
 * Design tokens. Colors are derived from the existing slate palette
 * (#0f172a / #64748b / #e2e8f0) and the original status colors.
 */
:root {
  /* Spacing: 4px scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-pill: 999px;

  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 16px;
  --text-lg: 20px;
  --text-xl: 24px;

  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-subtle: #f1f5f9;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;

  --color-sidebar-bg: #0f172a;
  --color-sidebar-text: #cbd5e1;
  --color-sidebar-text-active: #ffffff;
  --color-sidebar-item-hover: rgba(255, 255, 255, 0.06);
  --color-sidebar-item-active: rgba(255, 255, 255, 0.1);

  --color-accent: #2563eb;
  --color-focus-ring: rgba(37, 99, 235, 0.45);
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-fg: #065f46;
  --color-info: #2563eb;
  --color-info-bg: #dbeafe;
  --color-info-fg: #1e40af;
  --color-warning: #b45309;
  --color-warning-bg: #fef3c7;
  --color-warning-fg: #92400e;
  --color-danger: #dc2626;
  --color-danger-bg: #fee2e2;
  --color-danger-fg: #991b1b;

  --sidebar-width: 240px;
  --sidebar-width-collapsed: 68px;
  --topbar-height: 60px;
  --content-max-width: 1440px;

  --transition-fast: 150ms ease;
}

@media (prefers-reduced-motion: reduce) {
  :root { --transition-fast: 0ms; }
}

:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---- App shell ---- */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns var(--transition-fast);
}

.app-shell.is-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.app-main {
  display: flex;
  flex-direction: column;
  min-width: 0; /* grid items default to min-width: auto; this lets wide content shrink */
}

/* Sits under the sticky topbar. FilterBar's own `top: 70px` is a no-op inside this wrapper. */
.app-filterbar {
  position: sticky;
  top: var(--topbar-height);
  z-index: 30;
}

.app-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

/* Phones: the rail stays in the grid at the collapsed width (.is-collapsed above), so only the
   content padding tightens (307px of content at 375px wide). */
@media (max-width: 767px) {
  .app-content {
    padding: var(--space-3);
  }
}

/* ---- Shared page classes ---- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-info); }

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-md);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

/* Horizontal scroll stays inside the card instead of widening the page. */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-surface-subtle);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: #475569;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-surface-subtle);
  color: #334155;
  font-size: var(--text-base);
  font-variant-numeric: tabular-nums;
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-surface-subtle);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-bg);
  color: var(--color-success-fg);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning-fg);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-bg);
  color: var(--color-danger-fg);
}

.badge.info,
.badge.low {
  background: var(--color-info-bg);
  color: var(--color-info-fg);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-10);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: var(--color-danger-fg);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
