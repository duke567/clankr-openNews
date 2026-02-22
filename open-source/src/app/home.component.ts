import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <section class="card">
      <h2>OpenNews</h2>
      <p class="muted">Live event feed powered by your scrape pipeline.</p>
      <button type="button" routerLink="/timeline">Open Timeline</button>
    </section>
  `
})
export class HomeComponent {}
