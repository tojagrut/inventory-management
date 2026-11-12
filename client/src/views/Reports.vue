<template>
  <div class="reports">
    <div class="page-header">
      <h2>{{ t('reports.title') }}</h2>
      <p>{{ t('reports.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.quarterly.title') }}</h3>
        </div>
        <div v-if="quarterlyData.length === 0" class="no-data">{{ t('reports.noData') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('reports.quarterly.quarter') }}</th>
                <th>{{ t('reports.quarterly.totalOrders') }}</th>
                <th>{{ t('reports.quarterly.totalRevenue') }}</th>
                <th>{{ t('reports.quarterly.avgOrderValue') }}</th>
                <th>{{ t('reports.quarterly.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <td><strong>{{ q.quarter }}</strong></td>
                <td>{{ q.total_orders }}</td>
                <td>{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                <td>{{ formatCurrency(q.avg_order_value, currentCurrency) }}</td>
                <td>
                  <span :class="['badge', getFulfillmentClass(q.fulfillment_rate)]">
                    {{ q.fulfillment_rate }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Monthly Trends Chart -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.trend.title') }}</h3>
        </div>
        <div v-if="monthlyRows.length === 0" class="no-data">{{ t('reports.noData') }}</div>
        <div v-else class="chart-container">
          <div class="bar-chart" role="group" :aria-label="t('reports.trend.chartLabel')">
            <div v-for="row in monthlyRows" :key="row.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  role="img"
                  :style="{ height: getBarHeight(row.revenue) + 'px' }"
                  :title="formatCurrency(row.revenue, currentCurrency)"
                  :aria-label="`${row.label}: ${formatCurrency(row.revenue, currentCurrency)}`"
                ></div>
              </div>
              <div class="bar-label" aria-hidden="true">{{ row.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month-over-Month Comparison -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.mom.title') }}</h3>
        </div>
        <div v-if="monthlyRows.length === 0" class="no-data">{{ t('reports.noData') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('reports.mom.month') }}</th>
                <th>{{ t('reports.mom.orders') }}</th>
                <th>{{ t('reports.mom.revenue') }}</th>
                <th>{{ t('reports.mom.change') }}</th>
                <th>{{ t('reports.mom.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthlyRows" :key="row.month">
                <td><strong>{{ row.label }}</strong></td>
                <td>{{ row.order_count }}</td>
                <td>{{ formatCurrency(row.revenue, currentCurrency) }}</td>
                <td>
                  <span v-if="row.change !== null" :class="getChangeClass(row.change)">
                    {{ formatChange(row.change) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td>
                  <span v-if="row.change !== null" :class="getChangeClass(row.change)">
                    {{ formatGrowthRate(row.growthRate) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.totalOrders') }}</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.stats.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

// Order matches months.* locale keys; index 0 = January.
const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
const MAX_BAR_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    // Guards against out-of-order responses when filters change quickly:
    // only the most recent request may write to state.
    let latestRequestId = 0

    const loadData = async () => {
      const requestId = ++latestRequestId
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReports(filters),
          api.getMonthlyTrends(filters)
        ])
        if (requestId !== latestRequestId) return
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        if (requestId !== latestRequestId) return
        error.value = t('reports.loadError')
        console.error('Failed to load reports:', err)
      } finally {
        if (requestId === latestRequestId) loading.value = false
      }
    }

    // Convert 'YYYY-MM' to a translated label. Malformed input falls back
    // to the raw string (or a dash when empty) instead of throwing.
    const formatMonth = (monthStr) => {
      if (typeof monthStr !== 'string' || monthStr === '') return '-'
      const match = /^(\d{4})-(\d{2})$/.exec(monthStr)
      if (!match) return monthStr
      const monthIndex = Number(match[2]) - 1
      if (monthIndex < 0 || monthIndex > 11) return monthStr
      const name = t(`months.${MONTH_KEYS[monthIndex]}`)
      // Japanese month names are "N月", so the year goes first with the year marker.
      return currentLocale.value === 'ja' ? `${match[1]}年${name}` : `${name} ${match[1]}`
    }

    // Monthly rows with label and month-over-month change precomputed, so the
    // template needs no index lookups. Sorted chronologically ('YYYY-MM' sorts lexically).
    const monthlyRows = computed(() => {
      const sorted = [...monthlyData.value].sort((a, b) => String(a.month).localeCompare(String(b.month)))
      return sorted.map((row, i) => {
        const prev = i > 0 ? sorted[i - 1] : null
        const change = prev ? row.revenue - prev.revenue : null
        // growthRate is null when there is no previous month or it had zero revenue
        const growthRate = prev && prev.revenue !== 0 ? (change / prev.revenue) * 100 : null
        return { ...row, label: formatMonth(row.month), change, growthRate }
      })
    })

    // Summary stats derived from the data
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.revenue, 0)
    )
    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )
    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + m.order_count, 0)
    )
    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (q.total_revenue > 0 && (best === null || q.total_revenue > best.total_revenue)) best = q
      }
      return best ? best.quarter : '-'
    })

    // Max revenue computed once, not per bar
    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, m.revenue), 0)
    )

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * MAX_BAR_HEIGHT
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'success'
      if (rate >= 75) return 'warning'
      return 'danger'
    }

    const getChangeClass = (change) => {
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    // Sign followed by the formatted absolute value (formatCurrency handles currency conversion)
    const formatChange = (change) => {
      const amount = formatCurrency(Math.abs(change), currentCurrency.value)
      if (change > 0) return '+' + amount
      if (change < 0) return '-' + amount
      return amount
    }

    const formatGrowthRate = (rate) => {
      if (rate === null) return t('reports.mom.notAvailable')
      return (rate > 0 ? '+' : '') + rate.toFixed(1) + '%'
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      formatCurrency,
      loading,
      error,
      quarterlyData,
      monthlyRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      getChangeClass,
      formatChange,
      formatGrowthRate
    }
  }
}
</script>

<style scoped>
/* Card, table, badge, stat and loading/error styles come from App.vue. */

.no-data {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.chart-container {
  padding: var(--space-8) var(--space-4);
  min-height: 300px;
  /* On narrow screens scroll the chart inside the card instead of widening the page. */
  overflow-x: auto;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 250px;
  gap: var(--space-2);
  min-width: 520px; /* keeps bars readable; the container scrolls below this width */
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-width: 80px;
}

.bar-container {
  height: 200px;
  display: flex;
  align-items: flex-end;
  width: 100%;
}

.bar {
  width: 100%;
  background: var(--color-info);
  border-radius: 4px 4px 0 0;
  transition: opacity var(--transition-fast);
  cursor: pointer;
}

.bar:hover {
  opacity: 0.8;
}

.bar-label {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
  margin-top: var(--space-6);
}

.positive-change {
  color: var(--color-success);
  font-weight: 600;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
