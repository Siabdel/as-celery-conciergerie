
export default {
    name: 'PropertyDetails',
    props: {
        property: Object,
    },
    template: `
        <section class="property-details-section">
            <div class="row">
                <div class="col-lg-12">
                     <h3 class="section-title">Description</h3>
                     <p class="description-text">{{ property.description }}</p>
                </div>
            </div>
            <div class="row mt-5">
                <div class="col-lg-12">
                    <h3 class="section-title">Prestations et équipements</h3>
                    <div class="amenities-grid">
                        <div v-for="amenity in property.amenities" :key="amenity.name" class="amenity-item">
                            <i :class="['amenity-icon', amenity.icon]"></i>
                            <span class="amenity-name">{{ amenity.name }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `
};
