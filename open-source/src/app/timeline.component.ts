import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from './api.service';
import { Post } from './models';
import { PostCardComponent } from './post-card.component';
import { SpotlightComponent } from './spotlight.component';
import { interval, Subject, takeUntil, timeout, catchError, of, finalize } from 'rxjs';
import { TimelineRefreshService } from './timeline-refresh.service';

@Component({
  selector: 'app-timeline',
  standalone: true,
  imports: [CommonModule, PostCardComponent, SpotlightComponent],
  template: `
    <div class="row">
      <!-- Spotlight: first post only -->
      <section class="section" *ngIf="posts.length">
        <h2>Spotlight</h2>
        <app-spotlight [post]="posts[0]"></app-spotlight>
      </section>

      <section class="section timeline">
        <div class="row timeline-head">
          <h2>Happening Now</h2>
          <button type="button" (click)="refresh()" [disabled]="loading">Refresh</button>
        </div>
        <hr/>

        <p *ngIf="loading">Loading timeline...</p>
        <p class="error" *ngIf="error">{{ error }}</p>
        <p class="muted" *ngIf="!loading && !error && posts.length === 0">No posts in DB yet.</p>

        <app-post-card *ngFor="let post of posts" [post]="post"></app-post-card>
      </section>
    </div>
  `
})
export class TimelineComponent implements OnInit, OnDestroy {
  posts: Post[] = [];        // initialize empty
  loading = false;
  error = '';
  private destroy$ = new Subject<void>();
  private loadSeq = 0;

  constructor(private api: ApiService, private timelineRefresh: TimelineRefreshService) {}

  ngOnInit(): void {
    this.load();
    this.timelineRefresh.refresh$
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.load(true));

    interval(10000)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (!this.loading) this.load(false);
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  load(showLoading = true): void {
    const seq = ++this.loadSeq;
    if (showLoading) this.loading = true;
    this.error = '';

    // Hard safety: never leave the page in endless loading state.
    setTimeout(() => {
      if (this.loading && this.loadSeq === seq) {
        this.loading = false;
        this.error = 'Timeline request timed out. Try Refresh.';
      }
    }, 6000);

    this.api.getTimeline(50).pipe(
      timeout(5000),
      catchError((err) => {
        console.error('Timeline load error', err);
        this.error = 'Unable to load timeline from backend.';
        return of({ data: [] as Post[] });
      }),
      finalize(() => {
        if (showLoading && this.loadSeq === seq) this.loading = false;
      })
    ).subscribe({
      next: (res) => {
        if (res?.data?.length) {
          this.posts = res.data;
        } else {
          this.posts = [];
        }
      }
    });
  }

  refresh(): void {
    this.load(true);
  }

  // trackBy helps ngFor perform better when list changes
  trackById(index: number, item: Post) {
    return item.id;
  }
}
