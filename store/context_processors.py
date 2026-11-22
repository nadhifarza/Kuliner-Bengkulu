from django.conf import settings
from .models import BusinessProfile

def site_context(request):
    try: profile=BusinessProfile.objects.first()
    except Exception: profile=None
    unread=0
    if request.user.is_authenticated:
        try: unread=request.user.notifications.filter(is_read=False).count()
        except Exception: pass
    return {'business_profile':profile,'unread_notifications':unread,'payment_gateway_name':settings.PAYMENT_GATEWAY_NAME}
