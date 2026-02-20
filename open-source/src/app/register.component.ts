import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
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
        Email
        <input name="email" type="email" [(ngModel)]="email" required />
      </label>

      <label>
        Password
        <input name="password" type="password" [(ngModel)]="password" required minlength="6" />
      </label>

      <button type="submit" [disabled]="f.invalid || loading">Create account</button>
      <p class="error" *ngIf="error">{{ error }}</p>
    </form>

    <p>Already have an account? <a routerLink="/login">Login</a>.</p>
  `
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  loading = false;
  error = '';

  constructor(private api: ApiService, private router: Router) {}

  submit(): void {
    this.error = '';
    this.loading = true;

    this.api.register({ username: this.username, email: this.email, password: this.password }).subscribe({
      next: () => this.router.navigateByUrl('/login'),
      error: () => {
        this.error = 'Registration failed.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
