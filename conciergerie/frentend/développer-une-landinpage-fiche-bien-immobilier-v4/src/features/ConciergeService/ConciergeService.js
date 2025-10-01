
export default {
    name: 'ConciergeService',
    data() {
        return {
            services: [
                { icon: 'bi-key', title: 'Gestion des Clés', description: 'Remise et récupération sécurisées pour vos invités ou prestataires.' },
                { icon: 'bi-box-seam', title: 'Réception Colis', description: 'Nous réceptionnons et stockons vos colis en toute sécurité.' },
                { icon: 'bi-calendar-check', title: 'Prise de RDV', description: 'Organisation de vos rendez-vous (ménage, réparations...).' },
                { icon: 'bi-house-heart', title: 'Intendance', description: 'Surveillance et entretien de votre bien pendant votre absence.' },
            ]
        };
    },
    template: `
        <section class="concierge-section">
            <div class="container text-center">
                <h2 class="section-title">Nos Services de Conciergerie</h2>
                <p class="lead mb-5 mw-75 mx-auto">Vivez l'esprit tranquille, nous nous occupons de tout. Découvrez nos services exclusifs inclus avec votre bien.</p>
                <div class="row g-4">
                    <div v-for="service in services" :key="service.title" class="col-lg-3 col-md-6">
                        <div class="concierge-card">
                            <i :class="['concierge-icon', service.icon]"></i>
                            <h4>{{ service.title }}</h4>
                            <p>{{ service.description }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    `
};
