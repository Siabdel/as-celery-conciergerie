/**
 * Service pour consommer les API REST DRF
 */
import axios from 'axios'

//const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000/api'
//const API_BASE_URL = 'http://localhost:8000/api/'
const API_BASE_URL = 'https://conciergerie.netatlass.com/api/'
//if (process.env.NODE_ENV === 'development') { ... }

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})
// recuperer le token dans de connexion
axios.post('http://conciergerie.netatlass.com/api/token/', {
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
  console.log('Erreur post token :', error);
});
// rafraîchir la page pour voir le token dans localStorage

// charger le token
const accessToken = localStorage.getItem('accessToken');
console.log('Access Token from localStorage:', accessToken);

// Intercepteur pour ajouter les tokens JWT
apiClient.interceptors.request.use(
  (config) => {
    // Ajout du token JWT si disponible
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

// Intercepteur pour gérer les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirection vers la page de login si token invalide
      localStorage.removeItem('authToken')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export const apiService = {
  /**
   * Récupération des réservations pour une période donnée
   * @param {Object} params - Paramètres de filtrage
   * @returns {Promise} - Promesse avec les données
   */
  getReservations(params = {}) {
    return apiClient.get('/reservations/', { params })
  },

  /**
   * Récupération des biens
   * @returns {Promise} - Promesse avec les données
   */
  getProperties() {
    return apiClient.get('/property-depenses/1')
  },

  /**
   * Récupération des frais supplémentaires
   * @param {number} propertyId - ID du bien
   * @returns {Promise} - Promesse avec les données
   */
  getAdditionalExpenses(propertyId) {
    return apiClient.get(`/property-depenses/?property=${propertyId}`)
  },
}

export default apiService
