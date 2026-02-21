import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  template: `
    <header class="topbar">
      <a routerLink="/timeline" class="brand">OpenNews</a>
      <nav class="nav">
        <a routerLink="/timeline">Timeline</a>
        <a *ngIf="auth.username" [routerLink]="['/u', auth.username]">Profile</a>
        <a *ngIf="!auth.isLoggedIn()" routerLink="/auth/login">Login</a>
        <a *ngIf="!auth.isLoggedIn()" routerLink="/auth/register">Register</a>
        <a *ngIf="auth.isLoggedIn()" routerLink="/auth/logout">Logout</a>
      </nav>
    </header>

    <main class="container">
      <router-outlet></router-outlet>
    </main>
  `
})
export class AppComponent {
  constructor(public auth: AuthService) {}
}
