from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

# --- เพิ่มด้านล่างนี้ครับ ---

def shop(request):
    return render(request, 'shop.html')

def veggie_plots(request):
    return render(request, 'veggie_plots.html') # ชื่อไฟล์ต้องตรงกับใน templates

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')