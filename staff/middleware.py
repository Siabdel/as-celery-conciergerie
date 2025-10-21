# core/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Force la connexion sur toutes les pages,
    sauf les URLs explicitement autorisées (whitelist).
    """

    PUBLIC_PATHS = [
        reverse("home_public"),
        reverse("admin:login"),  # optionnel
        "/api/auth/token/",       # endpoints d'authentification
        "/api/auth/login/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # autoriser les URLs publiques
        if any(request.path.startswith(path) for path in self.PUBLIC_PATHS):
            return self.get_response(request)

        # si pas connecté → rediriger vers login
        if not request.user.is_authenticated:
            return redirect("home_public")

        return self.get_response(request)
