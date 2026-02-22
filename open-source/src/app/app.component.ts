import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { AuthService } from './auth.service';
import { TimelineRefreshService } from './timeline-refresh.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  template: `
    <header class="topbar">
      <button type="button" class="brand nav-link-btn" (click)="goTimeline()">OpenNews</button>
      <nav class="nav">
        <button type="button" class="nav-link-btn" (click)="goTimeline()">Timeline</button>
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
  authReady = false;

  constructor(
    public auth: AuthService,
    private router: Router,
    private timelineRefresh: TimelineRefreshService
  ) {}

  ngOnInit(): void {
    this.auth.bootstrapSession().subscribe(() => {
      this.authReady = true;
    });
  }

  goTimeline(): void {
    if (this.router.url.startsWith('/timeline')) {
      this.timelineRefresh.trigger();
      return;
    }
    this.router.navigate(['/timeline']);
  }
}
