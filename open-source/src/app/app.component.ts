import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink],
  template: `
    <header class="topbar">
      <a routerLink="/" class="brand">OpenNews</a>
      <nav class="nav">
        <a routerLink="/">Timeline</a>
      </nav>
    </header>

    <main class="container">
      <router-outlet></router-outlet>
    </main>
  `
})
export class AppComponent {}
