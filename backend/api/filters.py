from django_filters import CharFilter, FilterSet
from django_filters import rest_framework as filters
from django_filters.widgets import BooleanWidget
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')
    author = filters.CharFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(
        widget=BooleanWidget(),
        method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        widget=BooleanWidget(),
        method='filter_shopping_cart')

    class Meta():
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_by_field(self, queryset, value, field):
        user = self.request.user
        if user.is_anonymous:
            return queryset.none()
        if value:
            return queryset.filter(**{field + '__user': user})
        else:
            return queryset.exclude(**{field + '__user': user})

    def filter_favorited(self, queryset, name, value):
        return self.filter_by_field(queryset, value, 'favorites')

    def filter_shopping_cart(self, queryset, name, value):
        return self.filter_by_field(queryset, value, 'shopping_cart')


class IngredientFilter(FilterSet):
    name = CharFilter(
        field_name='name',
        lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
