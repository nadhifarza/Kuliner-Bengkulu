from django import forms
from django.contrib.auth import authenticate
from .models import User,Address,Product,Category,BusinessProfile,Banner


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Minimal 8 karakter'}
        ),
        min_length=8
    )

    address = forms.CharField(
        label='Alamat pertama',
        widget=forms.Textarea(attrs={'rows': 3})
    )

    class Meta:
        model = User
        fields = ['first_name', 'email', 'phone']
        labels = {
            'first_name': 'Nama lengkap',
            'email': 'Email',
            'phone': 'Nomor telepon'
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Email sudah terdaftar. Silakan gunakan email lain.'
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email'].strip().lower()
        user.username = user.email
        user.role = 'CUSTOMER'
        user.set_password(self.cleaned_data['password'])
        user.email_verified = True

        if commit:
            user.save()

            Address.objects.create(
                user=user,
                recipient=user.first_name,
                phone=user.phone,
                address=self.cleaned_data['address'],
                is_default=True
            )

        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password'
    )
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.user = None
    def clean(self):
        data = super().clean()
        email = data.get('email')
        password = data.get('password')
        if email and password:
            user_record = User.objects.filter(
                email__iexact=email.strip()
            ).first()
            if user_record is None:
                raise forms.ValidationError(
                    'Email atau password tidak sesuai.'
                )
            self.user = authenticate(
                self.request,
                username=user_record.username,
                password=password
            )
            if self.user is None:
                raise forms.ValidationError(
                    'Email atau password tidak sesuai.'
                )
        return data

class AddressForm(forms.ModelForm):
    class Meta:
        model=Address; fields=['label','recipient','phone','address','is_default']
        widgets={'address':forms.Textarea(attrs={'rows':3})}

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product; fields=['name','category','price','description','composition','history','image','stock','is_active']
        widgets={'description':forms.Textarea(attrs={'rows':3}),'composition':forms.Textarea(attrs={'rows':2}),'history':forms.Textarea(attrs={'rows':2})}

class CategoryForm(forms.ModelForm):
    class Meta: model=Category; fields=['name','slug','description']

class BusinessProfileForm(forms.ModelForm):
    class Meta: model=BusinessProfile; fields=['name','tagline','description','history','address','phone','opening_hours','instagram','facebook','tiktok']

class BannerForm(forms.ModelForm):
    class Meta: model=Banner; fields=['title','subtitle','image','is_active']

class EmployeeForm(forms.Form):
    name=forms.CharField(label='Nama pegawai')
    email=forms.EmailField()
    phone=forms.CharField(required=False)
    password=forms.CharField(widget=forms.PasswordInput,min_length=8)
