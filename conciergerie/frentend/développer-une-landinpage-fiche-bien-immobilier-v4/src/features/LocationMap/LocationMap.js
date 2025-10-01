
export default {
  name: 'LocationMap',
  props: {
    location: Object,
    address: Object,
  },
  data() {
    return {
      mapInstance: null,
    };
  },
  mounted() {
    if (typeof L === 'undefined' || !this.$refs.mapContainer) {
      return;
    }

    if (this.mapInstance) {
      return;
    }

    const map = L.map(this.$refs.mapContainer).setView([this.location.lat, this.location.lng], 15);
    this.mapInstance = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const customIcon = L.divIcon({
        html: \`<i class="bi bi-geo-alt-fill" style="font-size: 2.5rem; color: var(--secondary-color);"></i>\`,
        className: 'custom-map-marker',
        iconSize: [40, 40],
        iconAnchor: [20, 40],
        popupAnchor: [0, -40]
    });

    L.marker([this.location.lat, this.location.lng], { icon: customIcon }).addTo(map)
      .bindPopup(\`<b>\${this.address.street}</b><br>\${this.address.city}, \${this.address.zip}\`)
      .openPopup();
  },
  beforeUnmount() {
    if (this.mapInstance) {
      this.mapInstance.remove();
      this.mapInstance = null;
    }
  },
  template: `
    <section>
        <h2 class="section-title">Localisation</h2>
        <div ref="mapContainer" class="map-container"></div>
    </section>
  `
};
