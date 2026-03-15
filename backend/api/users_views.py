'''
Views related to user and lab management, such as listing lab members, adding/removing users from labs, and listing all users.

FUNCTIONS:
----------
lab_members(request, lab_id): 
    Lists members of a lab. Accessible by admin and lab members.
update_monthly_hour_limit(request, lab_id, user_id):
    Updates monthly_hour_limit for a lab member. Accessible by admin and lab directors.
'''
import json
from django.http import JsonResponse, HttpResponseForbidden 
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Lab, User, LabMembership

@login_required
def lab_members(request, lab_id):
    '''Endpoint to list active members of a lab. Only admin or lab members can access this endpoint.'''
    lab = get_object_or_404(Lab, id=lab_id)

    profile = request.user.userprofile

    # check membership or admin
    if profile.role != "admin" and not LabMembership.objects.filter(
        lab=lab, profile=profile
    ).exists():
        return HttpResponseForbidden()

    memberships = LabMembership.objects.filter(lab=lab).select_related("profile__user")

    data = [
        {
            "id": m.profile.user.id,
            "username": m.profile.user.username,
            "role": m.role,
            "monthly_hour_limit": m.monthly_hour_limit,
        }
        for m in memberships
    ]

    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["PATCH", "POST"])
def update_monthly_hour_limit(request, lab_id, user_id):
    """Update monthly_hour_limit for a user within a lab.

    Permissions:
    - Admins can update any lab membership.
    - Lab directors can update membership limits for their lab.
    """

    lab = get_object_or_404(Lab, id=lab_id)
    target_user = get_object_or_404(User, id=user_id)

    requester_profile = request.user.userprofile

    is_admin = requester_profile.role == "admin"
    is_director_in_lab = LabMembership.objects.filter(
        lab=lab, profile=requester_profile, role="director"
    ).exists()

    if not (is_admin or is_director_in_lab):
        return HttpResponseForbidden()

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    if "monthly_hour_limit" not in payload:
        return JsonResponse(
            {"status": "error", "message": "monthly_hour_limit is required"},
            status=400,
        )

    try:
        new_limit = int(payload["monthly_hour_limit"])
    except (TypeError, ValueError):
        return JsonResponse(
            {"status": "error", "message": "monthly_hour_limit must be an integer"},
            status=400,
        )

    if new_limit < 0 or new_limit > 1000:
        return JsonResponse(
            {"status": "error", "message": "monthly_hour_limit out of range"},
            status=400,
        )

    membership = get_object_or_404(
        LabMembership, lab=lab, profile=target_user.userprofile
    )
    membership.monthly_hour_limit = new_limit
    membership.save(update_fields=["monthly_hour_limit"])

    return JsonResponse({"status": "ok", "monthly_hour_limit": membership.monthly_hour_limit})
