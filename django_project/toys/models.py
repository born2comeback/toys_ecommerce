from django.conf import settings
from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User
from sendgrid import SendGridAPIClient, Mail


class Customer (models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=200, null=True, default="dell", verbose_name = "имя")
    phone = models.CharField(max_length=200, null=True, verbose_name = "телефон")
    email = models.CharField(max_length=200, null=True)
    device = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        if self.username:
            name = self.username or ""
        else:
            name = self.device
        return str(name)


class Item(models.Model):
    name = models.CharField(max_length=150)
    price = models.IntegerField()
    description = models.TextField()
    discount_price = models.IntegerField(blank=True, null=True)

    image1 = models.ImageField(default='default.jpg', upload_to='images')
    image2 = models.ImageField(default='default.jpg', upload_to='images')
    image3 = models.ImageField(default='default.jpg', upload_to='images')
    image4 = models.ImageField(default='default.jpg', upload_to='images')
    image5 = models.ImageField(default='default.jpg', upload_to='images')
    slug = models.SlugField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("toys:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("toys:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("toys:remove-from-cart", kwargs={
            'slug': self.slug
        })


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(null=True)
    ordered = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    def get_total(self):
        total = 0
        orderitems = self.orderitem_set.all()
        for item in orderitems:
            total += item.get_total_item_price()
        return total

    @property
    def cart_count(request, *args, **kwargs):
        try:
            customer = request.user.customer
        except:
            device = request.COOKIES['device']
            customer, created = Customer.objects.get_or_create(device=device)

        qs = Order.objects.filter(customer=customer, ordered=False)
        if qs.exists():
            order = qs[0]
            orderitems = order.orderitem_set.all()
            return orderitems.count()
        return 0


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.name}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    conf_num = models.CharField(max_length=15)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.email + " (" + str(self.confirmed) + ")"

    class Meta:
        ordering = ("conf_num", "confirmed", "email" )


class Newsletter(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subject = models.CharField(max_length=150)
    contents = models.FileField(upload_to='media/')

    def __str__(self):
        return self.subject + " " + self.created_at.strftime("%B %d, %Y")

    def send(self, request):
        contents = self.contents.read().decode('utf-8')
        subscribers = Subscriber.objects.filter(confirmed=True)
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        for sub in subscribers:
            print(sub.email)
            message = Mail(
                from_email=settings.FROM_EMAIL,
                to_emails=sub.email,
                subject=self.subject,
                html_content=contents + '<br><a href="{}?email={}&conf_num={}">Unsubscribe</a>.'.format(request.build_absolute_uri('/delete/'),
                                                       sub.email,
                                                       sub.conf_num))
            sg.send(message)