from django.shortcuts import render

def landing_page(request):
    return render(request, 'landing.html')

def about_page(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')

def faq_page(request):
    return render(request, 'faq.html')

def terms_page(request):
    return render(request, 'terms.html')

def privacy_page(request):
    return render(request, 'privacy.html')