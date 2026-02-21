import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from './api.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <h2>Register</h2>

    <form (ngSubmit)="submit()" #f="ngForm" class="card">
      <label>
        Username
        <input name="username" [(ngModel)]="username" required />
      </label>

      <label>
        Password
        <input name="password1" type="password" [(ngModel)]="password1" required minlength="6" />
      </label>

      <label>
        Confirm Password
        <input name="password2" type="password" [(ngModel)]="password2" required minlength="6" />
      </label>

      <button type="submit" [disabled]="f.invalid || loading">Create account</button>
      <p class="error" *ngIf="error">{{ error }}</p>
    </form>

    <p>Already have an account? <a routerLink="/auth/login">Login</a>.</p>
  `
})
export class RegisterComponent {
  username = '';
  password1 = '';
  password2 = '';
  loading = false;
  error = '';

  constructor(private api: ApiService, private router: Router) {}

  submit(): void {
    this.error = '';
    if (this.password1 !== this.password2) {
      this.error = 'Passwords do not match.';
      return;
    }
    this.loading = true;

    this.api.register({ username: this.username, password1: this.password1, password2: this.password2 }).subscribe({
      next: (res) => {
        if (!res.ok) {
          this.error = 'Registration failed.';
          return;
        }
        this.router.navigateByUrl('/auth/login');
      },
      error: (err: HttpErrorResponse) => {
        const backendMessage = err.error?.message;
        const details =
          err.error?.errors?.username?.[0] ||
          err.error?.errors?.password2?.[0] ||
          err.error?.errors?.password1?.[0];
        this.error = backendMessage || details || 'Registration failed.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
