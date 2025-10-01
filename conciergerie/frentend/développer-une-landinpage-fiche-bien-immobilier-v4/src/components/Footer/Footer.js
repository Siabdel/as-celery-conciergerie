
export default {
    name: 'Footer',
    computed: {
        currentYear() {
            return new Date().getFullYear();
        }
    },
    template: `
        <footer class="footer">
            <div class="container">
                <div class="row">
                    <div class="col-md-6 mb-3 mb-md-0">
                        <a href="#" class="footer-brand">Conciergerie<span>Royale</span></a>
                        <p class="footer-text">Votre partenaire de confiance pour une vie sans soucis.</p>
                        <div class="footer-social-links">
                            <a href="#"><i class="bi bi-twitter-x"></i></a>
                            <a href="#"><i class="bi bi-facebook"></i></a>
                            <a href="#"><i class="bi bi-instagram"></i></a>
                            <a href="#"><i class="bi bi-linkedin"></i></a>
                        </div>
                    </div>
                    <div class="col-md-3 col-6">
                        <h5>Explorer</h5>
                        <ul class="list-unstyled">
                            <li><a href="#" class="text-white-50 text-decoration-none">Nos Biens</a></li>
                            <li><a href="#" class="text-white-50 text-decoration-none">Services</a></li>
                            <li><a href="#" class="text-white-50 text-decoration-none">À Propos</a></li>
                        </ul>
                    </div>
                     <div class="col-md-3 col-6">
                        <h5>Contact</h5>
                        <ul class="list-unstyled">
                            <li><a href="#" class="text-white-50 text-decoration-none">Nous Contacter</a></li>
                            <li><a href="#" class="text-white-50 text-decoration-none">Support</a></li>
                        </ul>
                    </div>
                </div>
                <div class="footer-bottom">
                    &copy; {{ currentYear }} Conciergerie Royale. Tous droits réservés.
                </div>
            </div>
        </footer>
    `
};
