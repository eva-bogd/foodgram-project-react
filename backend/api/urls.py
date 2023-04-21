from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (TagViewSet, IngredientViewSet,
                       RecipeViewSet, FavoriteViewSet,
                       ShoppingCartViewSet, SubscribeViewSet,
                       CustomUserViewSet)

router_api_v1 = DefaultRouter()

router_api_v1.register(r'^users', CustomUserViewSet, basename='users')
# router_api_v1.register(r'^users/me', CustomUserViewSet)
# router_api_v1.register(r'^users/auth', CustomUserViewSet, basename='auth')


router_api_v1.register(r'^tags', TagViewSet, basename='tags')
router_api_v1.register(r'^recipes', RecipeViewSet, basename='recipes')
router_api_v1.register(r'^ingredients',
                       IngredientViewSet,
                       basename='ingredients')
router_api_v1.register(r'^recipes/download_shopping_cart',  # ???
                       ShoppingCartViewSet,
                       basename='download_shopping_cart')
router_api_v1.register(r'^recipes/(?P<recipe_id>\d+)/shopping_cart',
                       ShoppingCartViewSet,
                       basename='shopping_cart')
router_api_v1.register(r'^recipes/(?P<recipe_id>\d+)/favorite',
                       FavoriteViewSet,
                       basename='favorite')
router_api_v1.register(r'^users/subscriptions',
                       SubscribeViewSet,
                       basename='subscriptions')
router_api_v1.register(r'^users/(?P<user_id>\d+)/subscribe',
                       SubscribeViewSet,
                       basename='subscribe')


urlpatterns = [
    path('', include(router_api_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),  # .authtoken


    # path('auth/token/login/', CustomUserViewSet.as_view()),
    # path('auth/token/logout/', CustomUserViewSet.as_view()) ,
    # path('auth/password/', include('djoser.urls')),
    # path('auth/password/reset/confirm/<str:uid>/<str:token>/', include('djoser.urls')),
]
