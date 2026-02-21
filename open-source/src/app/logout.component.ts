import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-logout',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <section class="card">
      <h2>Thank You</h2>
      <p>You have been logged out.</p>
      <p><a routerLink="/auth/login">Back to login</a></p>
    </section>
  `
})
export class LogoutComponent implements OnInit {
  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    this.auth.logout();
  }
}
