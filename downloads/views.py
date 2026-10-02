import os
from django.http import HttpResponse, FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import DownloadToken
from audit.utils import log_audit

def download_file_view(request, token_str):
    token_obj = get_object_or_404(DownloadToken, token=token_str)

    if not token_obj.is_valid:
        return render(request, 'downloads/download_error.html', {
            'error': 'This download link is invalid, expired, or has reached its download limit.'
        }, status=403)

    product = token_obj.product
    if not product.downloadable_file:
        content = (
            f"====================================================\n"
            f"               DREYDOCS EDUCATIONAL TEMPLATE         \n"
            f"====================================================\n"
            f"Product: {product.name}\n"
            f"Category: {product.category.name}\n"
            f"File Type: {product.file_type}\n"
            f"Order Number: {token_obj.order.order_number}\n"
            f"Issued To: Telegram ID #{token_obj.order.customer.telegram_user_id}\n"
            f"----------------------------------------------------\n"
            f"DISCLAIMER & COMPLIANCE WARNING:\n"
            f"THIS FILE IS AN EDUCATIONAL DESIGN TEMPLATE ONLY.\n"
            f"SAMPLE TEMPLATE - NOT A GOVERNMENT DOCUMENT.\n"
            f"NOT VALID FOR IDENTIFICATION OR REAL-WORLD USE.\n"
            f"====================================================\n"
        ).encode('utf-8')

        token_obj.download_count += 1
        token_obj.save()

        log_audit(
            user_profile=token_obj.order.customer,
            action='DOWNLOAD_PRODUCT',
            object_type='Product',
            object_id=str(product.id),
            metadata={'token': token_str, 'order_number': token_obj.order.order_number}
        )

        response = HttpResponse(content, content_type='text/plain')
        filename = f"{product.slug}_EDUCATIONAL_TEMPLATE.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    file_path = product.downloadable_file.path
    if not os.path.exists(file_path):
        raise Http404("Requested file does not exist on storage.")

    token_obj.download_count += 1
    token_obj.save()

    log_audit(
        user_profile=token_obj.order.customer,
        action='DOWNLOAD_PRODUCT',
        object_type='Product',
        object_id=str(product.id),
        metadata={'token': token_str, 'order_number': token_obj.order.order_number}
    )

    response = FileResponse(open(file_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response
