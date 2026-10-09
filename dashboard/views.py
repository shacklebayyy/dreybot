from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import UserProfile
from catalog.models import Product, Category, Country, Region
from orders.models import Order, PaymentStatus, OrderStatus
from payments.models import Payment
from verification.models import VerificationRequest, VerificationService, VerificationProvider
from coupons.models import Coupon
from support.models import SupportTicket, SupportMessage
from audit.models import AuditLog
from core.models import SystemSetting
from notifications.services import dispatch_notification

@staff_member_required
def dashboard_home(request):
    total_customers = UserProfile.objects.filter(role='CUSTOMER').count()
    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(payment_status='PAID').count()
    total_revenue = Order.objects.filter(payment_status='PAID').aggregate(Sum('total'))['total__sum'] or 0.00
    pending_orders = Order.objects.filter(payment_status='PENDING').count()

    total_verifications = VerificationRequest.objects.count()
    completed_verifications = VerificationRequest.objects.filter(status='COMPLETED').count()
    failed_verifications = VerificationRequest.objects.filter(status='FAILED').count()

    recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
    recent_verifications = VerificationRequest.objects.select_related('customer', 'service').order_by('-created_at')[:5]

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'total_revenue': total_revenue,
        'pending_orders': pending_orders,
        'total_verifications': total_verifications,
        'completed_verifications': completed_verifications,
        'failed_verifications': failed_verifications,
        'recent_orders': recent_orders,
        'recent_verifications': recent_verifications,
    }
    return render(request, 'dashboard/home.html', context)

# Product Management
@staff_member_required
def product_list(request):
    products = Product.objects.select_related('category', 'country', 'state').all()
    return render(request, 'dashboard/products/list.html', {'products': products})

@staff_member_required
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        country_id = request.POST.get('country')
        state_id = request.POST.get('state')
        price = request.POST.get('price', 12.00)
        description = request.POST.get('description', '')
        file_type = request.POST.get('file_type', 'PSD')
        file_size = request.POST.get('file_size', '15 MB')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'

        preview_image = request.FILES.get('preview_image')
        downloadable_file = request.FILES.get('downloadable_file')

        category = get_object_or_404(Category, id=category_id)
        country = Country.objects.filter(id=country_id).first() if country_id else None
        state = Region.objects.filter(id=state_id).first() if state_id else None

        product = Product.objects.create(
            name=name,
            category=category,
            country=country,
            state=state,
            price=price,
            description=description,
            file_type=file_type,
            file_size=file_size,
            is_active=is_active,
            is_featured=is_featured,
            preview_image=preview_image,
            downloadable_file=downloadable_file
        )
        messages.success(request, f"Product '{product.name}' created successfully!")
        return redirect('dashboard:product_list')

    categories = Category.objects.filter(active=True)
    countries = Country.objects.filter(active=True)
    states = Region.objects.filter(active=True)
    return render(request, 'dashboard/products/form.html', {
        'categories': categories,
        'countries': countries,
        'states': states
    })

# Categories, Countries, States
@staff_member_required
def category_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            messages.success(request, f"Category '{name}' created!")
            return redirect('dashboard:category_list')
    categories = Category.objects.all()
    return render(request, 'dashboard/categories/list.html', {'categories': categories})

@staff_member_required
def country_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        iso = request.POST.get('iso_code')
        flag = request.POST.get('flag_emoji', '')
        if name and iso:
            Country.objects.create(name=name, iso_code=iso, flag_emoji=flag)
            messages.success(request, f"Country '{name}' added!")
            return redirect('dashboard:country_list')
    countries = Country.objects.all()
    return render(request, 'dashboard/countries/list.html', {'countries': countries})

@staff_member_required
def state_list(request):
    if request.method == 'POST':
        country_id = request.POST.get('country')
        name = request.POST.get('name')
        code = request.POST.get('code', '')
        country = get_object_or_404(Country, id=country_id)
        if name:
            Region.objects.create(country=country, name=name, code=code)
            messages.success(request, f"State/Region '{name}' added!")
            return redirect('dashboard:state_list')
    states = Region.objects.select_related('country').all()
    countries = Country.objects.filter(active=True)
    return render(request, 'dashboard/states/list.html', {'states': states, 'countries': countries})

# Order & Customer Management
@staff_member_required
def order_list(request):
    orders = Order.objects.select_related('customer').order_by('-created_at')
    return render(request, 'dashboard/orders/list.html', {'orders': orders})

@staff_member_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upload_doc':
            doc_file = request.FILES.get('custom_document')
            if doc_file:
                order.custom_document = doc_file
                order.payment_status = PaymentStatus.PAID
                order.order_status = OrderStatus.COMPLETED
                order.paid_at = timezone.now()
                order.completed_at = timezone.now()
                order.save()

                from downloads.services import generate_download_tokens_for_order
                tokens = generate_download_tokens_for_order(order)
                token_obj = tokens[0] if tokens else order.download_tokens.first()
                dl_url = f"http://{request.get_host()}/download/{token_obj.token}/" if token_obj else "Available in menu"

                from notifications.services import dispatch_notification, send_telegram_document_file
                file_sent = send_telegram_document_file(
                    order.customer.telegram_user_id,
                    order.custom_document,
                    caption=f"🎉 Completed Document File for Order #{order.order_number}"
                )
                msg = (
                    f"🎉 *YOUR ORDER HAS BEEN COMPLETED!*\n\n"
                    f"📋 *Order:* `{order.order_number}`\n"
                    f"Status: *COMPLETED / PAID*\n\n"
                    f"Your requested document has been prepared and uploaded by Admin.\n\n"
                    f"📥 [CLICK HERE TO DOWNLOAD YOUR FILE]({dl_url})"
                )
                dispatch_notification(order.customer, msg, title="Order Completed")
                if file_sent:
                    messages.success(request, f"Document file attached & dispatched directly to {order.customer.full_name}'s Telegram!")
                else:
                    messages.success(request, f"Document saved and download link dispatched to {order.customer.full_name}'s Telegram!")

        elif action == 'mark_paid':
            order.payment_status = PaymentStatus.PAID
            order.order_status = OrderStatus.COMPLETED
            order.paid_at = timezone.now()
            order.completed_at = timezone.now()
            order.save()

            from downloads.services import generate_download_tokens_for_order
            tokens = generate_download_tokens_for_order(order)
            token_obj = tokens[0] if tokens else order.download_tokens.first()
            dl_url = f"http://{request.get_host()}/download/{token_obj.token}/" if token_obj else "Available in menu"

            msg = (
                f"✅ *PAYMENT CONFIRMED & ORDER COMPLETED*\n\n"
                f"📋 *Order:* `{order.order_number}`\n"
                f"💰 *Total:* `${order.total}` {order.currency}\n\n"
                f"📥 [CLICK HERE TO DOWNLOAD YOUR FILE]({dl_url})"
            )
            dispatch_notification(order.customer, msg, title="Payment Confirmed")
            messages.success(request, f"Order {order.order_number} marked as PAID and notification sent to customer.")
        elif action == 'cancel':
            order.order_status = OrderStatus.CANCELLED
            order.payment_status = PaymentStatus.CANCELLED
            order.save()
            messages.success(request, f"Order {order.order_number} cancelled.")
        elif action == 'send_custom_message':
            msg_text = request.POST.get('custom_message', '').strip()
            if msg_text:
                msg = f"💬 *MESSAGE FROM DREYDOCS ADMIN (Order #{order.order_number})*\n\n{msg_text}"
                dispatch_notification(order.customer, msg, title=f"Message for Order #{order.order_number}")
                AuditLog.objects.create(
                    user_profile=request.user.userprofile if hasattr(request.user, 'userprofile') else None,
                    action='ADMIN_MESSAGE_SENT',
                    object_type='Order',
                    object_id=str(order.id),
                    metadata={'details': f"Sent custom message for order {order.order_number}"}
                )
                messages.success(request, f"Custom message sent to {order.customer.full_name}'s Telegram!")
        return redirect('dashboard:order_detail', order_id=order.id)
    return render(request, 'dashboard/orders/detail.html', {'order': order})

@staff_member_required
def customer_list(request):
    customers = UserProfile.objects.annotate(order_count=Count('orders')).order_by('-joined_at')
    return render(request, 'dashboard/customers/list.html', {'customers': customers})

@staff_member_required
def customer_detail(request, customer_id):
    customer = get_object_or_404(UserProfile, id=customer_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_block':
            customer.is_blocked = not customer.is_blocked
            customer.save()
            msg = "blocked" if customer.is_blocked else "unblocked"
            messages.success(request, f"Customer {customer.full_name} has been {msg}.")
        elif action == 'send_notify':
            msg_text = request.POST.get('message', '')
            if msg_text:
                dispatch_notification(customer, msg_text, "Notification from DreyDocs Support")
                messages.success(request, f"Telegram notification sent to {customer.full_name}.")
        elif action == 'credit_balance':
            amount = request.POST.get('amount', '0')
            bonus_amount = request.POST.get('bonus_amount', '0')
            customer.credit_balance(amount, bonus_amount)
            msg = (
                f"🎉 *BALANCE CREDITED BY ADMIN*\n\n"
                f"💰 *Amount Added:* `${amount} USD`\n"
                f"🎁 *Bonus Added:* `${bonus_amount} USD`\n"
                f"👛 *Current Available Balance:* `${customer.total_available_balance} USD`"
            )
            dispatch_notification(customer, msg, title="Balance Credited")
            messages.success(request, f"Credited ${amount} (+${bonus_amount} bonus) to {customer.full_name}'s account!")
        elif action == 'deduct_balance':
            amount = request.POST.get('amount', '0')
            customer.deduct_balance(amount)
            msg = (
                f"ℹ️ *BALANCE ADJUSTMENT BY ADMIN*\n\n"
                f"💸 *Amount Deducted:* `${amount} USD`\n"
                f"👛 *Current Available Balance:* `${customer.total_available_balance} USD`"
            )
            dispatch_notification(customer, msg, title="Balance Adjusted")
            messages.success(request, f"Deducted ${amount} from {customer.full_name}'s balance.")
        return redirect('dashboard:customer_detail', customer_id=customer.id)
    return render(request, 'dashboard/customers/detail.html', {'customer': customer})


# Support Tickets Management
@staff_member_required
def ticket_list(request):
    tickets = SupportTicket.objects.select_related('customer').annotate(msg_count=Count('messages')).order_by('-updated_at')
    return render(request, 'dashboard/tickets/list.html', {'tickets': tickets})

@staff_member_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send_reply':
            reply_text = request.POST.get('reply_message', '').strip()
            new_status = request.POST.get('status', ticket.status)
            if reply_text:
                admin_profile = UserProfile.objects.filter(user=request.user).first()
                SupportMessage.objects.create(
                    ticket=ticket,
                    sender=admin_profile or ticket.customer,
                    is_admin_reply=True,
                    message=reply_text
                )
                ticket.status = new_status
                ticket.save()

                telegram_msg = (
                    f"💬 *SUPPORT REPLY - TICKET #{ticket.ticket_number}*\n\n"
                    f"{reply_text}\n\n"
                    f"Status: *{ticket.status}*\n\n"
                    f"_You can reply directly to this chat if you have further questions._"
                )
                dispatch_notification(ticket.customer, telegram_msg, title="Support Ticket Reply")
                messages.success(request, f"Reply dispatched to customer {ticket.customer.full_name}'s Telegram!")
        elif action == 'update_status':
            ticket.status = request.POST.get('status', ticket.status)
            ticket.save()
            messages.success(request, f"Ticket #{ticket.ticket_number} status updated to {ticket.status}.")
        return redirect('dashboard:ticket_detail', ticket_id=ticket.id)
    
    msg_list = ticket.messages.select_related('sender').order_by('created_at')
    return render(request, 'dashboard/tickets/detail.html', {'ticket': ticket, 'messages_list': msg_list})

# Verification Management

@staff_member_required
def verification_list(request):
    requests_list = VerificationRequest.objects.select_related('customer', 'service').order_by('-created_at')
    return render(request, 'dashboard/verification/list.html', {'requests': requests_list})

@staff_member_required
def provider_list(request):
    providers = VerificationProvider.objects.all()
    return render(request, 'dashboard/verification/providers.html', {'providers': providers})

# Audit Logs & Settings
@staff_member_required
def audit_list(request):
    logs = AuditLog.objects.select_related('user_profile').order_by('-timestamp')[:100]
    return render(request, 'dashboard/audit/list.html', {'logs': logs})

@staff_member_required
def settings_view(request):
    keys = ['site_name', 'currency', 'telegram_bot_token', 'site_announcement']
    if request.method == 'POST':
        for key in keys:
            val = request.POST.get(key, '')
            SystemSetting.set_setting(key, val)
        messages.success(request, "General System Settings updated successfully!")
        return redirect('dashboard:settings')
    
    settings_dict = {key: SystemSetting.get_setting(key, '') for key in keys}
    if not settings_dict['site_name']: settings_dict['site_name'] = 'DreyDocs'
    if not settings_dict['currency']: settings_dict['currency'] = 'USD'
    return render(request, 'dashboard/settings/list.html', {'settings': settings_dict})

@staff_member_required
def payment_settings_view(request):
    toggle_keys = ['enable_crypto', 'enable_stripe', 'enable_paystack', 'enable_mpesa', 'enable_wallet']
    text_keys = [
        'btc_address', 'btc_network',
        'ltc_address', 'ltc_network',
        'trx_address', 'trx_network',
        'eth_address', 'eth_network',
        'usdt_address', 'usdt_network',
        'stripe_public_key', 'stripe_secret_key',
        'paystack_public_key', 'paystack_secret_key',
        'mpesa_shortcode', 'mpesa_consumer_key', 'mpesa_consumer_secret',
        'min_topup_amount', 'topup_bonus_threshold', 'topup_bonus_amount', 'payment_instructions'
    ]

    if request.method == 'POST':
        for key in toggle_keys:
            is_enabled = request.POST.get(key) in ['on', 'true', '1']
            SystemSetting.set_setting(key, 'true' if is_enabled else 'false')
        
        for key in text_keys:
            val = request.POST.get(key, '')
            SystemSetting.set_setting(key, val)

        messages.success(request, "Payment Gateways & Wallet Settings updated successfully!")
        return redirect('dashboard:payment_settings')

    all_keys = toggle_keys + text_keys
    settings_dict = {key: SystemSetting.get_setting(key, '') for key in all_keys}

    if not settings_dict['enable_crypto']: settings_dict['enable_crypto'] = 'true'
    if not settings_dict['enable_wallet']: settings_dict['enable_wallet'] = 'true'
    if not settings_dict['btc_address']: settings_dict['btc_address'] = 'bc1q0h7ql9m8zr3dk3f2f4vvjrgmz4kdt8v3daw2xm0pjr24efgde4ksh4skq6'
    if not settings_dict['btc_network']: settings_dict['btc_network'] = 'Bitcoin Mainnet'
    if not settings_dict['ltc_address']: settings_dict['ltc_address'] = 'ltc1qydca6ls4qs7wu7rhnm7fh9gpzfz200t5ecukfkqts26ulaelh29sm3pc04'
    if not settings_dict['ltc_network']: settings_dict['ltc_network'] = 'Litecoin Mainnet'
    if not settings_dict['trx_address']: settings_dict['trx_address'] = 'TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7'
    if not settings_dict['trx_network']: settings_dict['trx_network'] = 'TRON (TRC20)'
    if not settings_dict['eth_address']: settings_dict['eth_address'] = '0x3d33a1641a61af1b3b499a1f6a236176bd1820b4'
    if not settings_dict['eth_network']: settings_dict['eth_network'] = 'Ethereum (ERC20)'
    if not settings_dict['usdt_address']: settings_dict['usdt_address'] = 'TEq2LD3ZRq53ScffRx9qvJmMatutkQeCV7'
    if not settings_dict['usdt_network']: settings_dict['usdt_network'] = 'TRC20 / ERC20'
    if not settings_dict['min_topup_amount']: settings_dict['min_topup_amount'] = '7.00'

    if not settings_dict['topup_bonus_threshold']: settings_dict['topup_bonus_threshold'] = '50.00'
    if not settings_dict['topup_bonus_amount']: settings_dict['topup_bonus_amount'] = '5.00'

    return render(request, 'dashboard/settings/payments.html', {'settings': settings_dict})

# Top Up Requests & Crediting Area
from payments.models import TopUpRequest, TopUpStatus

@staff_member_required
def topup_request_list(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        topup_id = request.POST.get('topup_id')
        topup = get_object_or_404(TopUpRequest, id=topup_id)

        if action == 'approve' and topup.status != TopUpStatus.APPROVED:
            customer = topup.customer
            customer.credit_balance(topup.amount, topup.bonus_amount)
            topup.status = TopUpStatus.APPROVED
            topup.approved_at = timezone.now()
            topup.save()

            msg = (
                f"🎉 *YOUR TOP UP HAS BEEN APPROVED & CREDITED!*\n\n"
                f"📋 *Reference:* `{topup.reference}`\n"
                f"💰 *Amount Credited:* `${topup.amount} USD`\n"
                f"{'🎁 *Bonus Reward Credited:* $' + str(topup.bonus_amount) + ' USD' if topup.bonus_amount > 0 else ''}\n"
                f"👛 *Total Available Balance:* `${customer.total_available_balance} USD`\n\n"
                f"Thank you for your payment! You can now use your wallet balance to place orders instantly."
            )
            dispatch_notification(customer, msg, title="Top Up Approved")
            AuditLog.objects.create(
                user_profile=request.user.userprofile if hasattr(request.user, 'userprofile') else None,
                action='TOPUP_APPROVED',
                object_type='TopUpRequest',
                object_id=str(topup.id),
                metadata={'details': f"Approved top up {topup.reference} (${topup.amount}) for {customer.full_name}"}
            )
            messages.success(request, f"Approved & credited ${topup.amount} (+${topup.bonus_amount} bonus) to {customer.full_name}'s account!")

        elif action == 'reject' and topup.status != TopUpStatus.REJECTED:
            reason = request.POST.get('reason', 'Transaction hash/proof could not be verified.')
            topup.status = TopUpStatus.REJECTED
            topup.save()

            msg = (
                f"❌ *TOP UP REQUEST REJECTED*\n\n"
                f"📋 *Reference:* `{topup.reference}`\n"
                f"💰 *Amount:* `${topup.amount} USD`\n"
                f"⚠️ *Reason:* {reason}\n\n"
                f"If you believe this is an error, please contact support with your payment receipt."
            )
            dispatch_notification(customer, msg, title="Top Up Rejected")
            messages.warning(request, f"Top up {topup.reference} rejected.")

        return redirect('dashboard:topup_request_list')

    topup_requests = TopUpRequest.objects.select_related('customer').order_by('-created_at')
    pending_count = TopUpRequest.objects.filter(status=TopUpStatus.PENDING).count()
    approved_total = TopUpRequest.objects.filter(status=TopUpStatus.APPROVED).aggregate(Sum('amount'))['amount__sum'] or 0.00

    context = {
        'topup_requests': topup_requests,
        'pending_count': pending_count,
        'approved_total': approved_total,
    }
    return render(request, 'dashboard/topups/list.html', context)



