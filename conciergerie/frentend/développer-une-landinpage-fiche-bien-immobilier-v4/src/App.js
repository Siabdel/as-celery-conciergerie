
import Header from './components/Header/Header.js';
import Footer from './components/Footer/Footer.js';
import PropertyHero from './features/PropertyHero/PropertyHero.js';
import PropertyDetails from './features/PropertyDetails/PropertyDetails.js';
import LocationMap from './features/LocationMap/LocationMap.js';
import FloorPlan from './features/FloorPlan/FloorPlan.js';
import ConciergeService from './features/ConciergeService/ConciergeService.js';

export default {
  name: 'App',
  components: {
    Header,
    Footer,
    PropertyHero,
    PropertyDetails,
    LocationMap,
    FloorPlan,
    ConciergeService,
  },
  data() {
    return {
      property: null,
    };
  },
  async created() {
    try {
      const response = await fetch('/src/assets/data.json');
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      this.property = await response.json();
    } catch (error) {
      console.error("Failed to fetch property data:", error);
    }
  },
  template: `
    <div v-if="!property" class="loading-spinner">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    <div v-else class="App">
      <Header />
      <main>
        <PropertyHero :property="property" />
        <div class="container my-5">
           <PropertyDetails :property="property" />
        </div>
        <div class="container my-5">
           <FloorPlan :floorPlan="property.floorPlan" />
         </div>
        <div class="container my-5">
           <LocationMap :location="property.location" :address="property.address" />
        </div>
        <ConciergeService />
      </main>
      <Footer />
    </div>
  `
};
