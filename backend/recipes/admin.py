from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Subscribe, Tag)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'total_favorites')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-empty-'

    def total_favorites(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    empty_value_display = '-empty-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientInRecipe)
admin.site.register(Tag)
admin.site.register(Subscribe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
