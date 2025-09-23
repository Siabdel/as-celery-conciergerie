<template>
  <div class="app">
    <!-- En-tête -->
    <h2>app immo</h2>
    <header class="header text-center py-4">
      <div class="container">
        <h1 class="mb-0">Concierge Immobilière</h1>
        <p class="mb-0">Suivi des réservations et activité</p>
      </div>
    </header>

    <div class="container my-4">
      <!-- Section de filtrage -->
      <div class="card">
        <div class="card-body">
          <h5 class="card-title">Filtres de recherche</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <label for="startDate" class="form-label">Date de début</label>
              <input
                type="date"
                class="form-control"
                id="startDate"
                v-model="filters.startDate"
                @change="loadData"
              />
            </div>
            <div class="col-md-6">
              <label for="endDate" class="form-label">Date de fin</label>
              <input
                type="date"
                class="form-control"
                id="endDate"
                v-model="filters.endDate"
                @change="loadData"
              />
            </div>
          </div>

          <!-- Bouton de recherche -->
          <button class="btn btn-primary w-100" @click="loadData" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status"></span>
            {{ loading ? 'Chargement...' : 'Charger les données' }}
          </button>
        </div>
      </div>

      <!-- Message d'erreur -->
      <div v-if="error" class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
        {{ error }}
        <button type="button" class="btn-close" @click="error = null"></button>
      </div>

      <!-- Bouton d'export -->
      <div class="d-flex gap-2 mb-3" v-if="activityData.length > 0">
        <button class="btn btn-export" @click="exportToPDF" :disabled="loading">
          <i class="bi bi-file-earmark-pdf"></i> Exporter en PDF
        </button>
        <button class="btn btn-secondary" @click="exportToICal" :disabled="loading">
          <i class="bi bi-calendar2-event"></i> Exporter iCal
        </button>
      </div>

      <!-- Section de résultat -->
      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
      </div>

      <table-activity v-else-if="activityData.length > 0" :data="activityData" :columns="columns" />

      <!-- Message quand aucune donnée -->
      <div v-else class="alert alert-info text-center mt-4">
        Aucune donnée disponible. Choisissez une période et chargez les données.
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import TableActivity from './components/TableActivity.vue'
import apiService from './services/api'
import { transformData, generatePdf, exportToICal } from './utils/helpers'

export default {
  name: 'App',
  components: {
    TableActivity,
  },
  data() {
    return {
      filters: {
        startDate: '',
        endDate: '',
      },
      activityData: [],
      loading: false,
      error: null,
      columns: [
        { key: 'check_in_date', label: 'Début' },
        { key: 'check_out_date', label: 'Fin' },
        { key: 'nights', label: 'Nb nuitées' },
        { key: 'client_name', label: 'Client' },
        { key: 'service_fee', label: 'Frais service' },
        { key: 'cleaning_fee', label: 'Frais ménage' },
        { key: 'linens_fee', label: 'Frais linge' },
        { key: 'gross_amount', label: 'Montant Brut' },
        { key: 'concierge_commission_rate', label: 'Comm. Conciergerie (%)' },
        { key: 'rbnb_commission_rate', label: 'Comm. Rbnb (%)' },
        { key: 'net_revenue', label: 'Revenu Net Client' },
      ],
    }
  },
  created() {
    // Définir la période par défaut (mois courant)
    const today = new Date()
    const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate())

    this.filters.startDate = lastMonth.toISOString().split('T')[0]
    this.filters.endDate = today.toISOString().split('T')[0]
  },
  methods: {
    async loadData_test() {
      // c'est mmieux de utiliser interceptor axios
      // Interceptor pour ajouter le token à chaque requête
      // on traite err 403 ou 401
      axios.interceptors.request.use(
        config => {
          const token = localStorage.getItem('accessToken');
          if (token) {
            config.headers['Authorization'] = 'Bearer ' + token;
          }
          return config;
        },
        error => {
          return Promise.reject(error);
        }
      );


      // appel  load axios
      //const URL = 'https://conciergerie.netatlass.com/api/'
      const URL_LOCAL = 'http://localhost:8000/api/'
      this.loading = true
      this.error = null

      // recuperer le token dans de connexion
      axios.post('http://localhost:8000/api/token/', {
        username: 'admin',
        password: 'grutil001'
      })
      .then(response => {
        const accessToken = response.data.access;      // Token court 5 min
        const refreshToken = response.data.refresh;    // Token long 1 jour
        console.log('Access Token:', accessToken);
        console.log('Refresh Token:', refreshToken);
        // Stocke le token, par exemple dans localStorage
        localStorage.setItem('accessToken', accessToken);
      })
      .catch(error => {
        // Gère l’erreur
      });
      // rafraîchir la page pour voir le token dans localStorage

      // charger le token
      const accessToken = localStorage.getItem('accessToken');
      console.log('Access Token from localStorage:', accessToken);
      // Utiliser le token dans les en-têtes des requêtes
      axios.get(`${URL_LOCAL}property/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        })
        .then(response => {
          console.log('Données chargées avec succès:', response.data);
          this.activityData = response.data; // Mettre à jour les données avec la réponse
        })
        .catch(error => {
          console.error('!!! - Erreur lors du chargement des données:', error);
          console.log(' !!! - Erreur lors du chargement des données:', error);
          this.error = 'Erreur lors du chargement des données. Veuillez réessayer.';
        }).finally(
          this.loading = false
        );
    },
    async loadData() {
      this.loading = true
      this.error = null

      try {
        // Validation des dates
        if (!this.filters.startDate || !this.filters.endDate) {
          throw new Error('Veuillez sélectionner une période de temps.')
        }

        // Récupération des données
        const [reservationsResponse, propertiesResponse, expensesResponse] = await Promise.all([
          apiService.getReservations({
            check_in__gte: this.filters.startDate,
            check_in__lte: this.filters.endDate,
            ordering: '-check_in',
          }),
          apiService.getProperties(),
          apiService.getAdditionalExpenses(1),
        ])

        // Transformation des données
        const transformedData = transformData(
          reservationsResponse.data.results,
          propertiesResponse.data.results,
          expensesResponse.data.results,
        )

        this.activityData = transformedData
      } catch (err) {
        console.error('Erreur lors du chargement des données:', err)
        this.error = 'Erreur lors du chargement des données. Veuillez réessayer.'
      } finally {
        this.loading = false
      }
    },

    async exportToPDF() {
      this.loading = true
      try {
        await generatePdf(this.activityData, {
          startDate: this.filters.startDate,
          endDate: this.filters.endDate,
        })
      } catch (error) {
        console.error('Erreur export PDF:', error)
        this.error = "Erreur lors de l'export PDF."
      } finally {
        this.loading = false
      }
    },

    exportToICal() {
      try {
        // On utilise simplement les données des réservations pour l'export iCal
        exportToICal(
          this.activityData.slice(0, 5),
          () => {
            alert('Export iCalendar terminé.')
          },
          (error) => {
            this.error = "Erreur lors de l'export iCalendar: " + error.message
          },
        )
      } catch (error) {
        this.error = "Erreur lors de l'export iCalendar: " + error.message
      }
    },
  },
}
</script>

<style scoped>
.btn-export {
  background-color: #28a745;
  border: none;
}

.btn-export:hover {
  background-color: #218838;
}
</style>
