from . import views
from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    ItemDetailView,
    CheckoutView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart, RulesView, AboutView, ContactsView, CustomLoginView,
)

app_name = "toys"

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path("contact", views.contact, name="contact"),
    path('email-list-signup/', views.new, name='email-list-signup'),
    path('confirm/', views.confirm, name='confirm'),
    path('delete/', views.delete, name='delete'),
    path('about/', AboutView.as_view(), name='about'),
    path('rules/', RulesView.as_view(), name='rules'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),

]

