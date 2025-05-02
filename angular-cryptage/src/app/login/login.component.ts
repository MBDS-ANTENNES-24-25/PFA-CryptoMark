import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule]
})
export class LoginComponent implements OnInit {
  isLoginMode = true;
  showPassword = false;
  loginForm: FormGroup = new FormGroup({});
  registerForm: FormGroup = new FormGroup({});
  loginError: string | null = null;

  constructor(
    private fb: FormBuilder,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.initForms();
  }

  initForms(): void {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      rememberMe: [false]
    });

    this.registerForm = this.fb.group({
      fullName: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', Validators.required],
      termsAccepted: [false, Validators.requiredTrue]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
    const password = control.get('password');
    const confirmPassword = control.get('confirmPassword');
    if (password && confirmPassword && password.value !== confirmPassword.value) {
      confirmPassword.setErrors({ notMatched: true });
      return { notMatched: true };
    }
   
    return null;
  }

  switchMode(isLogin: boolean): void {
    this.isLoginMode = isLogin;
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    if (this.isLoginMode) {
      if (this.loginForm.valid) {
        this.login();
      } else {
        this.markFormGroupTouched(this.loginForm);
      }
    } else {
      if (this.registerForm.valid) {
        this.register();
      } else {
        this.markFormGroupTouched(this.registerForm);
      }
    }
  }

  markFormGroupTouched(formGroup: FormGroup): void {
    Object.keys(formGroup.controls).forEach(key => {
      const control = formGroup.get(key);
      if (control) {
        control.markAsTouched();
       
        if (control instanceof FormGroup) {
          this.markFormGroupTouched(control);
        }
      }
     
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  login(): void {
    this.loginError = null;
    const { email, password } = this.loginForm.value;
    console.log('Login attempt:', { email, password });
    
    // Check for admin credentials
    if (email === 'admin@admin.ma' && password === 'admin123') {
      console.log('Admin login successful');
      this.router.navigate(['/home']);
      return;
    }
    
    // Regular user login logic
    // Here you would typically call an authentication service
    // For demonstration purposes, we're just redirecting after a delay
    setTimeout(() => {
      // You can add actual authentication logic here
      // If login fails, you could set the loginError message
      this.router.navigate(['/dashboard']);
    }, 1000);
  }

  register(): void {
    const userData = {
      fullName: this.registerForm.value.fullName,
      email: this.registerForm.value.email,
      password: this.registerForm.value.password
    };
   
    console.log('Registration data:', userData);
   
    setTimeout(() => {
      this.isLoginMode = true;
      this.loginForm.patchValue({
        email: userData.email
      });
     
      console.log('Registration successful! Please login.');
    }, 1000);
  }

  uploadAndProtectImage(image: File): void {
    console.log('Processing image for cryptographic signature:', image.name);
  }
}