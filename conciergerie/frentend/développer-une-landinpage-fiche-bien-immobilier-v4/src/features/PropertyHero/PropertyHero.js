
import Carousel from '../../components/Carousel/Carousel.js';

export default {
  name: 'PropertyHero',
  components: {
    Carousel,
  },
  props: {
    property: Object,
  },
  computed: {
    fullAddress() {
      if (!this.property || !this.property.address) return '';
      return `${this.property.address.street}, ${this.property.address.zip} ${this.property.address.city}`;
    }
  },
  template: `
    <section class="hero-section">
      <div class="container">
        <div class="row align-items-center g-5">
          <div class="col-lg-7">
            <Carousel :images="property.images" />
          </div>
          <div class="col-lg-5">
            <h1 class="hero-title">{{ property.name }}</h1>
            <p class="hero-address">
              <i class="bi bi-geo-alt-fill me-2 text-muted"></i>
              {{ fullAddress }}
            </p>
            <div class="hero-price">
              {{ property.price }}
            </div>
            
            <p class="hero-owner">
                Vendu par: <strong class="ms-1">{{ property.owner.name }}</strong> 
                <i class="bi bi-patch-check-fill ms-2 hero-owner-icon" title="Vendeur certifié"></i>
            </p>

            <div class="d-grid gap-2 d-md-flex">
                 <button class="btn btn-primary btn-lg px-4 me-md-2" type="button">
                    <i class="bi bi-calendar-event me-2"></i>
                    Planifier une visite
                </button>
                <button class="btn btn-outline-secondary btn-lg px-4" type="button">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    Recevoir la brochure
                </button>
            </div>
           
          </div>
        </div>
      </div>
    </section>
  `
};
