from django import template
from ..models import Order
register = template.Library()


@register.filter
def cart_item_count(self):
    print("444")

    qs = Order.objects.filter(customer=self, ordered=False)
    print(qs)
    if qs.exists():
        order = qs[0]
        orderitems = order.orderitem_set.all()

        return orderitems.count()
    print("333")

    return 0
