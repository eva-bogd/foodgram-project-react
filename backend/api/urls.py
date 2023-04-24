from django.urls import include, path
from rest_framework.routers import DefaultRouter


from api.views import (TagViewSet, IngredientViewSet,
                       RecipeViewSet,
                       CustomUserViewSet,)

router_api_v1 = DefaultRouter()

router_api_v1.register(r'^users', CustomUserViewSet, basename='users')


# router_api_v1.register(r'^users', CustomUserViewSet, basename='users')
# router_api_v1.register(r'^users/subscriptions',
#                        SubscribeViewSet,
#                        basename='subscriptions')
# router_api_v1.register(r'^users/(?P<user_id>\d+)/subscribe',
#                        SubscribeViewSet,
#                        basename='subscribe')

router_api_v1.register(
    r'^tags', TagViewSet, basename='tags')
router_api_v1.register(
    r'^ingredients', IngredientViewSet, basename='ingredients')
router_api_v1.register(
    r'^recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('', include(router_api_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
