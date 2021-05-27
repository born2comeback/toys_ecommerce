from django.contrib import admin

from .models import Item, OrderItem, Order, Customer, Subscriber, Newsletter

admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Customer)


def send_newsletter(modeladmin, request, queryset):
    for newsletter in queryset:
        newsletter.send(request)


send_newsletter.short_description = "Send selected Newsletters to all subscribers"


class NewsletterAdmin(admin.ModelAdmin):
    actions = [send_newsletter]


admin.site.register(Newsletter, NewsletterAdmin)


@admin.register(Subscriber)
class SubsAdmin(admin.ModelAdmin):
    list_display = ("email", "conf_num", "confirmed")


