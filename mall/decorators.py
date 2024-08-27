import json
import functools
from django.http import HttpResponseForbidden, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from PaymentPractice import settings
from mall.models import OrderPayment


def deny_from_untrusted_hosts(allowed_ip_list):
    def get_client_ip(request: HttpRequest) -> str:
        client_ip = request.META.get("REMOTE_ADDR")
        return client_ip

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            client_ip = request.META.get("REMOTE_ADDR")
            if client_ip not in allowed_ip_list:
                return HttpResponseForbidden("허용되지 않은 IP에서의 요청입니다.")
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@require_POST
@csrf_exempt
@deny_from_untrusted_hosts(settings.ALLOWED_WEBHOOK_IPS)
def portone_webhook(request):
    # 요청의 IP 주소를 확인
    payload = json.loads(request.body)
    print(payload)
    merchant_uid = payload.get("data").get("paymentId")

    if not merchant_uid:
        return HttpResponse("merchant_uid 인자가 누락되었습니다.", status=400)

    payment = get_object_or_404(OrderPayment, uid=merchant_uid)
    payment.portone_check()
    print("payment.is_paid_ok", payment.is_paid_ok)
    return HttpResponse("ok")
