import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <h2>Login</h2>

    <form (ngSubmit)="submit()" #f="ngForm" class="card">
      <label>
        Username
        <input name="username" [(ngModel)]="username" required />
      </label>

      <label>
        Password
        <input name="password" type="password" [(ngModel)]="password" required />
      </label>

      <button type="submit" [disabled]="f.invalid || loading">Sign in</button>
      <p class="error" *ngIf="error">{{ error }}</p>
    </form>

    <p>New here? <a routerLink="/auth/register">Create an account</a>.</p>
  `
})
export class LoginComponent {
  username = '';
  password = '';
  loading = false;
  error = '';

  constructor(private api: ApiService, private auth: AuthService, private router: Router) {}

  submit(): void {
    this.error = '';
    this.loading = true;

    this.api.login({ username: this.username, password: this.password }).subscribe({
      next: (res) => {
        if (!res.ok) {
          this.error = 'Login failed.';
          return;
        }
        this.auth.markLoggedIn(res.user?.username || this.username);
        this.router.navigateByUrl('/timeline');
      },
      error: (err: HttpErrorResponse) => {
        const backendMessage = err.error?.message;
        const details = err.error?.errors?.__all__?.[0];
        this.error = backendMessage || details || 'Login failed.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
