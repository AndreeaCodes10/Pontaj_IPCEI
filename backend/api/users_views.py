'''
Views related to user and lab management, such as listing lab members, adding/removing users from labs, and listing all users.

FUNCTIONS:
----------
lab_members(request, lab_id): 
    Lists members of a lab. Accessible by admin and lab members.
add_user_to_lab(request, lab_id, user_id): 
    Adds a user to a lab. Accessible by admin and lab directors.
remove_user_from_lab(request, lab_id, user_id): 
    Removes a user from a lab. Accessible by admin and lab directors.
all_users(request): 
    Lists all users. Accessible by admin and lab directors.
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
        }
        for m in memberships
    ]

    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["POST"])
def add_user_to_lab(request, lab_id, user_id):
    '''Endpoint to add a user to a lab. Only admin or lab director can perform this action.'''
    lab = get_object_or_404(Lab, id=lab_id)
    user = get_object_or_404(User, id=user_id)

    profile = request.user.userprofile

    if profile.role != "admin" and not LabMembership.objects.filter(
        lab=lab, profile=profile, role="director"
    ).exists():
        return HttpResponseForbidden()

    LabMembership.objects.get_or_create(
        lab=lab,
        profile=user.userprofile,
        defaults={"role": "member"},
    )

    return JsonResponse({"status": "ok"})

@login_required
@require_http_methods(["DELETE"])
def remove_user_from_lab(request, lab_id, user_id):
    '''Endpoint to remove a user from a lab. Only admin or lab director can perform this action.'''
    lab = get_object_or_404(Lab, id=lab_id)
    target_user = get_object_or_404(User, id=user_id)

    requester = request.user.userprofile

    try:
        requester_membership = LabMembership.objects.get(
            lab=lab, profile=requester
        )
    except LabMembership.DoesNotExist:
        return HttpResponseForbidden()

    try:
        target_membership = LabMembership.objects.get(
            lab=lab, profile=target_user.userprofile
        )
    except LabMembership.DoesNotExist:
        return JsonResponse({"status": "not_member"})

    # admin can remove anyone
    if requester.role != "admin":
        if requester_membership.role != "director":
            return HttpResponseForbidden()

        if target_user == request.user:
            return HttpResponseForbidden()

        if target_membership.role == "director":
            return HttpResponseForbidden()

    target_membership.delete()
    return JsonResponse({"status": "ok"})

@login_required
def all_users(request):
    '''Endpoint to list all users, for admin and director use only'''
    profile = request.user.userprofile

    if profile.role == "admin":
        pass
    else:
        if not LabMembership.objects.filter(
            profile=profile, role="director"
        ).exists():
            return HttpResponseForbidden()

    users = User.objects.all()
    data = [{"id": u.id, "username": u.username} for u in users]
    return JsonResponse(data, safe=False)