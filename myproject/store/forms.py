from django import forms
from django.contrib.auth.models import User, Group
from .models import Product, VeggiePlotBooking

class QuantumUserEditForm(forms.ModelForm):
    # ดึงรายชื่อกลุ่ม (Groups) มาแสดงเป็น Checkbox
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'quantum-checkbox'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'groups']
        widgets = {
            field: forms.TextInput(attrs={'class': 'quantum-input'}) 
            for field in ['username', 'email', 'first_name', 'last_name']
        }

class QuantumProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'category', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'quantum-input'}),
            'price': forms.NumberInput(attrs={'class': 'quantum-input'}),
            'category': forms.TextInput(attrs={'class': 'quantum-input'}),
            'description': forms.Textarea(attrs={'class': 'quantum-input', 'rows': 4}),
        }

class QuantumPlotForm(forms.ModelForm):
    class Meta:
        model = VeggiePlotBooking
        fields = ['plot_name', 'status'] # ลบ booking_date ออกเพราะแก้ไขไม่ได้
        widgets = {
            'plot_name': forms.TextInput(attrs={'class': 'quantum-input'}),
            'status': forms.Select(attrs={'class': 'quantum-input'}),
        }