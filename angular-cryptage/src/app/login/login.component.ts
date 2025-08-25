import { Component, OnInit ,inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { AuthService } from '../auth.service';



@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css'],
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule]
})
export class LoginComponent  {
  isLoginMode = true;
  showPassword = false;
  loginForm: FormGroup = new FormGroup({});
  registerForm: FormGroup = new FormGroup({});
  authError: string | null = null;
  isLoading = false;
  authService: AuthService = inject(AuthService);

  constructor(
    private fb: FormBuilder,
    private router: Router,
   
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
      confirmPassword?.setErrors({ notMatched: true });
      return { notMatched: true };
    }
    return null;
  }

  switchMode(isLogin: boolean): void {
    this.isLoginMode = isLogin;
    this.authError = null; // Clear error when switching modes
  }

  togglePasswordVisibility(): void {
    this.showPassword = !this.showPassword;
  }

  onSubmit(): void {
    this.authError = null;
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
    Object.values(formGroup.controls).forEach(control => {
      control.markAsTouched();
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  login(): void {
    if (!this.loginForm.valid) return;
    this.isLoading = true;
    const { email, password } = this.loginForm.value;

    this.authService.login(email, password).subscribe({
      next: () => {
        this.isLoading = false;
        console.log('Login successful!');
        this.router.navigate(['/home']); // Navigate to a protected route
      },
      error: (err) => {
        this.isLoading = false;
        this.authError = this.getFirebaseErrorMessage(err.code);
        console.error('Login error:', err);
      }
    });
  }

  register(): void {
    if (!this.registerForm.valid) return;
    this.isLoading = true;
    const { email, password } = this.registerForm.value;

    this.authService.register(email, password).subscribe({
      next: () => {
        this.isLoading = false;
        console.log('Registration successful!');
        // Switch to login mode and pre-fill email for user convenience
        this.isLoginMode = true;
        this.loginForm.patchValue({ email: email });
        // You could also show a success message here
      },
      error: (err) => {
        this.isLoading = false;
        this.authError = this.getFirebaseErrorMessage(err.code);
        console.error('Registration error:', err);
      }
    });
  }

  googleLogin(): void {
    this.isLoading = true;
    this.authError = null;
    this.authService.loginWithGoogle().subscribe({
      next: () => {
        this.isLoading = false;
        console.log('Google login successful!');
        this.router.navigate(['/home']);
      },
      error: (err) => {
        this.isLoading = false;
        this.authError = this.getFirebaseErrorMessage(err.code);
        console.error('Google login error:', err);
      }
    });
  }

  githubLogin(): void {
    this.isLoading = true;
    this.authError = null;
    this.authService.loginWithGitHub().subscribe({
      next: () => {
        this.isLoading = false;
        console.log('GitHub login successful!');
        this.router.navigate(['/home']);
      },
      error: (err) => {
        this.isLoading = false;
        this.authError = this.getFirebaseErrorMessage(err.code);
        console.error('GitHub login error:', err);
      }
    });
  }

  /**
   * Converts Firebase error codes into user-friendly messages.
   * @param errorCode The error code from Firebase.
   * @returns A user-friendly error string.
   */
  private getFirebaseErrorMessage(errorCode: string): string {
    switch (errorCode) {
      case 'auth/invalid-email':
        return 'The email address is not valid.';
      case 'auth/user-disabled':
        return 'This user account has been disabled.';
      case 'auth/user-not-found':
      case 'auth/wrong-password':
      case 'auth/invalid-credential':
        return 'Invalid email or password. Please try again.';
      case 'auth/email-already-in-use':
        return 'This email address is already in use by another account.';
      case 'auth/weak-password':
        return 'The password is too weak. It must be at least 6 characters long.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }
}
