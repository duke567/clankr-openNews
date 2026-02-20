import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from './api.service';
import { Post } from './models';
import { PostCardComponent } from './post-card.component';

const MOCK_POSTS: Post[] = [
  {
    id: 1001,
    user_id: 1,
    content: 'Ship fast, iterate faster. Hackathon mode is ON.',
    created_at: '2026-02-20T16:05:00Z',
    likes_count: 12,
    liked_by_me: false,
    author: { id: 1, username: 'demo', display_name: 'Demo Dev' }
  },
  {
    id: 1002,
    user_id: 2,
    content: 'Built a Django API + Angular frontend in one afternoon. Coffee carried.',
    created_at: '2026-02-20T15:10:00Z',
    likes_count: 27,
    liked_by_me: false,
    author: { id: 2, username: 'alice', display_name: 'Alice' }
  },
  {
    id: 1003,
    user_id: 3,
    content: 'If it works in prod, it was always the plan.',
    created_at: '2026-02-20T14:35:00Z',
    likes_count: 41,
    liked_by_me: false,
    author: { id: 3, username: 'bob', display_name: 'Bob' }
  }
];

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule, PostCardComponent],
  template: `
    <section>
      <h2>Timeline</h2>

      <p *ngIf="loading">Loading timeline...</p>
      <p class="error" *ngIf="error">{{ error }}</p>

      <app-post-card *ngFor="let post of posts" [post]="post"></app-post-card>
    </section>
  `
})
export class TimelineComponent implements OnInit {
  posts: Post[] = [...MOCK_POSTS];
  loading = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.getTimeline(50).subscribe({
      next: (res) => {
        if (res.data?.length) {
          this.posts = res.data;
        }
      },
      error: () => {
        // Keep mock posts if backend is unavailable.
        this.error = '';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
