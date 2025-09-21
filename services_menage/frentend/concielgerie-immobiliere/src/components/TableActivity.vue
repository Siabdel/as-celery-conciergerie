<template>
  <div class="card">
    <div class="card-body">
      <h5 class="card-title">Résumé de l'activité</h5>

      <div class="table-responsive">
        <table class="table table-hover align-middle">
          <thead class="table-light">
            <tr>
              <th v-for="column in columns" :key="column.key">{{ column.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in data" :key="index">
              <td v-for="column in columns" :key="column.key">
                <template v-if="column.key === 'check_in_date' || column.key === 'check_out_date'">
                  {{ formatDate(row[column.key]) }}
                </template>
                <template
                  v-else-if="
                    [
                      'service_fee',
                      'cleaning_fee',
                      'linens_fee',
                      'gross_amount',
                      'net_revenue',
                    ].includes(column.key)
                  "
                >
                  {{ formatCurrency(row[column.key]) }}
                </template>
                <template
                  v-else-if="
                    ['concierge_commission_rate', 'rbnb_commission_rate'].includes(column.key)
                  "
                >
                  {{ row[column.key].toFixed(0) }}%
                </template>
                <template v-else>
                  {{ row[column.key] }}
                </template>
              </td>
            </tr>
          </tbody>
          <tfoot class="table-light">
            <tr>
              <th colspan="7">Total</th>
              <th>{{ formatCurrency(totalGross) }}</th>
              <th></th>
              <th></th>
              <th>{{ formatCurrency(totalNet) }}</th>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { formatDate, formatCurrency } from '../utils/helpers'

export default {
  name: 'TableActivity',
  props: {
    data: {
      type: Array,
      required: true,
    },
    columns: {
      type: Array,
      required: true,
    },
  },
  methods: {
    formatDate,
    formatCurrency,
  },
  computed: {
    totalGross() {
      return this.data.reduce((sum, item) => sum + item.gross_amount, 0)
    },
    totalNet() {
      return this.data.reduce((sum, item) => sum + item.net_revenue, 0)
    },
  },
}
</script>

<style scoped>
th {
  text-align: center;
}
</style>
