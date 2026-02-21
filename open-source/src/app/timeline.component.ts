import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from './api.service';
import { Post } from './models';
import { PostCardComponent } from './post-card.component';
import { MOCK_POSTS } from './mocks/posts';

const USE_CONTENT_API = false;

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule, PostCardComponent],
  template: `
    <section>
      <h2>Timeline</h2>

      <p *ngIf="loading">Loading timeline...</p>
      <p class="error" *ngIf="error">{{ error }}</p>

      <div *ngIf="!loading && posts.length === 0">No posts yet — be the first!</div>

      <app-post-card
        *ngFor="let post of posts; trackBy: trackById"
        [post]="post">
      </app-post-card>
    </section>
  `
})
export class TimelineComponent implements OnInit {
  posts: Post[] = [];        // initialize empty
  loading = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    if (USE_CONTENT_API) {
      this.load();
    } else {
      // Use the shared mock array (no extra nesting)
      this.posts = MOCK_POSTS.slice(); // defensive copy
      this.loading = false;
    }
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.getTimeline(50).subscribe({
      next: (res) => {
        if (res?.data?.length) {
          this.posts = res.data;
        } else {
          this.posts = [];
        }
      },
      error: (err) => {
        // Keep mock posts if backend is unavailable.
        console.error('Timeline load error', err);
        this.error = 'Unable to load timeline — showing local demo posts.';
        this.posts = MOCK_POSTS.slice();
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }

  // trackBy helps ngFor perform better when list changes
  trackById(index: number, item: Post) {
    return item.id;
  }
}