import random
import ssl

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.core.mail import send_mail, EmailMessage, mail_admins, BadHeaderError
from django.core.validators import EmailValidator
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.template.loader import get_template, render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.csrf import csrf_exempt
from sendgrid import Mail, SendGridAPIClient

from .forms import UserRegisterForm, CustomAuthenticationForm, UserUpdateForm, CustomPassChangeForm, ContactForm, \
    SubscriberForm

from django.contrib.auth.models import User

from .mixins import CartMixin
from .models import Item, OrderItem, Order, Customer, Subscriber
from django.views.generic import (
    View,
    ListView,
    DetailView,
)
from django import forms

ssl._create_default_https_context = ssl._create_unverified_context


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm


class ItemDetailView(CartMixin, DetailView):
    model = Item

    def get(self, request, slug, *args, **kwargs):
        item = Item.objects.get(slug=slug)
        context = {
            'object': item,
            'order': self.order
        }
        return render(request, 'product.html', context)


def home(request, *args, **kwargs):
    # paginate_by = 10
    # template_name = "home.html"
    try:
        customer = request.user.customer
        print("1")

    except:
        print("2")

        try:
            device = request.COOKIES['device']
            print("3")

            customer, created = Customer.objects.get_or_create(device=device)
            print("4")

        except:
            print("5")

            context = {
                'products': Item.objects.all(),
            }

            return render(request, 'home.html', context)

    qs = Order.objects.filter(customer=customer, ordered=False)
    if qs.exists():
        order = qs[0]
    else:
        order = False
    context = {
        'products': Item.objects.all(),
        'order': order,
        'form': SubscriberForm
    }
    return render(request, 'home.html', context)


class AboutView(CartMixin, ListView):
    model = Item
    template_name = "about.html"

    def get(self, request, *args, **kwargs):
        context = {'order': self.order}
        return render(request, 'about.html', context)


class ContactsView(CartMixin, ListView):
    model = Item
    template_name = "contacts.html"

    def get(self, request, *args, **kwargs):
        context = {'order': self.order}
        return render(request, 'contacts.html', context)


class RulesView(CartMixin, ListView):
    model = Item
    template_name = "rules.html"

    def get(self, request, *args, **kwargs):
        context = {'order': self.order}
        return render(request, 'rules.html', context)


def add_to_cart(request, slug):
    try:
        customer = request.user.customer
    except:
        try:
            device = request.COOKIES['device']
            customer, created = Customer.objects.get_or_create(device=device)
        except:
            return render(request, '403_csrf.html')

    # customer, created = Customer.objects.get_or_create(user=request.user)
    customer.save()
    item = get_object_or_404(Item, slug=slug)

    order_qs = Order.objects.filter(customer=customer, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order_item, created = OrderItem.objects.get_or_create(item=item, order=order, ordered=False)

        if created:
            order_item.quantity = 1
            order_item.save()
            order.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("toys:order-summary")
        else:
            order_item.quantity += 1
            order_item.save()
            order.save()
            messages.info(request, "This item was added to your cart.")
            return redirect("toys:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(customer=customer, ordered_date=ordered_date)
        order_item, created = OrderItem.objects.get_or_create(
            item=item,
            order=order,
            ordered=False
        )
        order_item.quantity = 1
        order_item.save()
        order.save()
        messages.info(request, "This item was added to your cart.")
        return redirect("toys:order-summary")


def remove_from_cart(request, slug):
    try:
        customer = request.user.customer
    except:
        try:
            device = request.COOKIES['device']
            customer, created = Customer.objects.get_or_create(device=device)
        except:
            return render(request, '403_csrf.html')

    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(customer=customer, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        orderitems = order.orderitem_set.all()

        if orderitems.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                order=order,
                ordered=False
            )[0]
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("toys:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("toys:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("toys:product", slug=slug)


def remove_single_item_from_cart(request, slug):
    try:
        customer = request.user.customer
    except:
        try:
            device = request.COOKIES['device']
            customer, created = Customer.objects.get_or_create(device=device)
        except:
            return render(request, '403_csrf.html')

    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        customer=customer,
        ordered=False
    )

    if order_qs.exists():
        order = order_qs[0]
        orderitems = order.orderitem_set.all()

        if orderitems.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                order=order,
                ordered=False
            )[0]

            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()

            messages.info(request, "This item quantity was updated.")
            return redirect("toys:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("toys:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("toys:product", slug=slug)


class OrderSummaryView(CartMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            try:
                customer = request.user.customer
            except:
                try:
                    device = request.COOKIES['device']
                    customer, created = Customer.objects.get_or_create(device=device)
                except:
                    return render(request, '403_csrf.html')

            order = Order.objects.get(customer=customer, ordered=False)

            context = {'object': order,
                       'order': self.order
                       }
            return render(self.request, 'order_summary.html', context)

            context = {'order': self.order}
            return render(request, 'about.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class CheckoutForm(forms.Form):
    phone = forms.CharField(required=False)
    email = forms.EmailField(required=True)
    username = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ['phone', 'email', 'username']


def is_email(value):
    try:
        EmailValidator()(value)
    except ValidationError:
        return False
    else:
        return True


# def sendmail(customer, order):
#     eemail = customer.email
#     ctx = {
#         'user': customer.username,
#         'order': order
#     }
#     message = get_template('email.html').render(ctx)
#     msg = EmailMessage(
#         'Subject',
#         message,
#         'vp7007@gmail.com',
#         [eemail],
#     )
#     msg.content_subtype = "html"  # Main content is now text/html
#     msg.send()




def sendmail1(customer, order):
    # Order confirmation to customer email
    subject = 'Order confirmation'
    eemail = customer.email
    html_message = render_to_string('email.html', {'user': customer.username,
                                                   'order': order,
                                                   'phone': customer.phone,
                                                   'email': eemail})
    plain_message = strip_tags(html_message)
    from_email = 'From <vp7007@gmail.com>'
    to = eemail

    mail.send_mail(subject, plain_message, from_email, [to], fail_silently=False, html_message=html_message)



def sendmail_admin(customer, order):
    # New order notification to admins
    subject = 'New order notification'
    eemail = customer.email
    html_message = render_to_string('email_admins.html', {'user': customer.username,
                                                   'order': order,
                                                   'phone': customer.phone,
                                                   'email': eemail})
    plain_message = strip_tags(html_message)
    mail_admins(subject, plain_message, fail_silently=False, connection=None,  html_message=html_message)


class CheckoutView(View):
    def get(self, request, *args, **kwargs):
        try:
            try:
                customer = request.user.customer
            except:
                device = request.COOKIES['device']
                customer, created = Customer.objects.get_or_create(device=device)

            order = Order.objects.get(customer=customer, ordered=False)

            form = CheckoutForm()
            context = {
                'form': form,
                'order': order,
                'customer': customer
            }
            order.save()
            return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("toys:checkout")

    def post(self, request, *args, **kwargs):

        try:
            customer = request.user.customer
        except:
            device = request.COOKIES['device']
            customer, created = Customer.objects.get_or_create(device=device)

        order = Order.objects.get(customer=customer, ordered=False)
        form = CheckoutForm(self.request.POST)
        if form.is_valid():
            customer.username = form.cleaned_data.get('username')
            customer.phone = form.cleaned_data.get('phone')
            customer.email = form.cleaned_data.get('email')
            customer.save()

            order.ordered = True
            order.save()

            orderitems = order.orderitem_set.all()
            for item in orderitems:
                item.ordered = True
                item.save()
            sendmail1(customer, order)
            sendmail_admin(customer, order)

            messages.info(self.request, "Подтверждение заказа отправлено на вашу почту")
            # mail_admins("subject", "message", fail_silently=False, connection=None, html_message=None)

        else:
            for error in form.errors:
                if error == 'email':
                    messages.info(
                        self.request, "fill in Email")
                if error == 'username':
                    messages.info(
                        self.request, "Please fill in User")

            return redirect("toys:checkout")
        return redirect("toys:home")


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, f'Your account has been created! You are now able to log in')
            return redirect('toys:login')
    else:
        form = UserRegisterForm()
    return render(request, 'register.html', {'form': form})


def logout(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user.customer)
        if u_form.is_valid():
            user = request.user
            user.password = request.POST.get('password')
            u_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user.customer)
    customer=request.user.customer
    qs = Order.objects.filter(customer=customer, ordered=False)
    orders=Order.objects.filter(customer=customer, ordered=True)
    if qs.exists():
        order = qs[0]
    else:
        order = False
    context = {
        'u_form': u_form,
        'order': order,
        'orders': orders
    }

    return render(request, 'profile.html', context)


def password_change(request):
    if request.method == 'POST':
        form = CustomPassChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('toys:home')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomPassChangeForm(request.user)
    return render(request, 'password_change.html', {
        'form': form
    })


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            body = {
                'name': form.cleaned_data['name'],
                'from_email': form.cleaned_data['from_email'],
                'message': form.cleaned_data['message'],
            }
            message = "\n".join(body.values())
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['from_email']
            try:
                send_mail(subject, message, from_email, ['vp7007@gmail.com'])
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect("toys:home")

    form = ContactForm()
    return render(request, "contact.html", {'form': form})


def random_digits():
    return "%0.12d" % random.randint(0, 999999999999)


@csrf_exempt
def new(request):
    # New subscriber
    if request.method == 'POST':
        email_signup_qs = Subscriber.objects.filter(email=request.POST['email'])
        if email_signup_qs.exists():
            messages.info(request, "You are already subscribed")
            return redirect("toys:home")

        else:
            sub = Subscriber(email=request.POST['email'], conf_num=random_digits())
            sub.save()
            message = Mail(
                from_email=settings.FROM_EMAIL,
                to_emails=sub.email,
                subject='Newsletter Confirmation',
                html_content='Thank you for signing up for my email newsletter! \
                    Please complete the process by \
                    <a href="{}?email={}&conf_num={}"> clicking here to \
                    confirm your registration</a>.'.format(request.build_absolute_uri('/confirm/'),
                                                        sub.email,
                                                        sub.conf_num))
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return render(request, 'home.html', {'email': sub.email, 'action': 'added', 'form': SubscriberForm()})
    else:
        return render(request, 'home.html', {'form': SubscriberForm()})


def confirm(request):
    # email confirmation
    sub = Subscriber.objects.get(email=request.GET['email'])
    if sub.conf_num == request.GET['conf_num']:
        sub.confirmed = True
        sub.save()
        return render(request, 'home.html', {'email': sub.email, 'action': 'confirmed'})
    else:
        return render(request, 'home.html', {'email': sub.email, 'action': 'denied'})


def delete(request):
    # Subscription remove
    sub = Subscriber.objects.get(email=request.GET['email'])
    if sub.conf_num == request.GET['conf_num']:
        sub.delete()
        return render(request, 'home.html', {'email': sub.email, 'action': 'unsubscribed'})
    else:
        return render(request, 'home.html', {'email': sub.email, 'action': 'denied'})