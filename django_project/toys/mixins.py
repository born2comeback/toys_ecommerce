from django.views.generic import View

from .models import Customer, Order, Item


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        try:
            customer = request.user.customer
        except:
            try:
                device = request.COOKIES['device']
                customer, created = Customer.objects.get_or_create(device=device)
            except:
                # return HttpResponse("Для корректной работы сайта включите cookies")
                order = False
                self.order = order
                return super().dispatch(request, *args, **kwargs)

        qs = Order.objects.filter(customer=customer, ordered=False)
        if qs.exists():
            order = qs[0]
        # context = {
        #     'products': Item.objects.all(),
        #     'order': order
        # }
        else:
            order = False
        self.order = order
        return super().dispatch(request, *args, **kwargs)
