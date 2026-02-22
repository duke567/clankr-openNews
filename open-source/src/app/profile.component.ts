import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from './api.service';
import { Post, User } from './models';
import { PostCardComponent } from './post-card.component';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, RouterLink, PostCardComponent],
  template: `
    <section>
      <p><a routerLink="/timeline">← Back to timeline</a></p>

      <h2 *ngIf="user">{{ user.display_name || user.username }}</h2>
      <p *ngIf="user" class="muted">@{{ user.username }}</p>

      <p *ngIf="loading">Loading profile...</p>
      <p class="error" *ngIf="error">{{ error }}</p>

      <app-post-card *ngFor="let post of posts" [post]="post"></app-post-card>
    </section>
  `
})
export class ProfileComponent implements OnInit {
  user: User | null = null;
  posts: Post[] = [];
  loading = false;
  error = '';

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const username = params.get('username');
      if (!username) return;
      this.load(username);
    });
  }

  private load(username: string): void {
    this.loading = true;
    this.error = '';
    this.api.getUserProfile(username).subscribe({
      next: (res) => {
        this.user = res.user;
        this.posts = res.posts || [];
      },
      error: () => {
        this.error = 'Could not load profile.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
