from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app_membres.models import Member
from django.shortcuts import render, redirect

@csrf_exempt
def block_member(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user_id = request.session.get('client', {}).get('id')
            member_id = request.POST.get('member_id')
            if not user_id or not member_id:
                return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=401)
            user = Member.objects.get(id=user_id)
            to_block = Member.objects.get(id=member_id)
            user.blocked_members.add(to_block)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@csrf_exempt
def unblock_member(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            user_id = request.session.get('client', {}).get('id')
            member_id = request.POST.get('member_id')
            if not user_id or not member_id:
                return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=401)
            user = Member.objects.get(id=user_id)
            to_unblock = Member.objects.get(id=member_id)
            user.blocked_members.remove(to_unblock)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

def blocked_members_list(request):
    if not request.session.get("client"):
        return redirect('aff_login')
    user = Member.objects.get(id=request.session["client"]["id"])
    blocked_members = user.blocked_members.all()
    return render(request, "blocked_members.html", {"blocked_members": blocked_members})
