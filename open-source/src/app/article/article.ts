// src/app/article.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Post, SourceTweet } from '../models';
import { ApiService } from '../api.service';
import { catchError, finalize, of, timeout } from 'rxjs';
import { MOCK_POSTS } from '../mocks/posts';

@Component({
  selector: 'app-article',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './article.html',
  styleUrls: ['./article.css'],
})
export class Article implements OnInit {
  post?: Post;
  loading = false;
  error = '';
  tweets: SourceTweet[] = [];
  regenerating = false;
  regenError = '';
  selectedTweetIds = new Set<number>();

  constructor(private route: ActivatedRoute, private api: ApiService) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.post = undefined;
      return;
    }

    const navPost = (history.state?.post as Post | undefined) || undefined;
    if (navPost && navPost.id === id) {
      this.post = navPost;
      this.loading = false;
    } else {
      this.loading = true;
    }

    this.error = '';
    this.api
      .getPostById(id)
      .pipe(
        timeout(3000),
        catchError(() => of(this.post || (MOCK_POSTS.find((p) => p.id === id) as Post | undefined))),
        finalize(() => {
          this.loading = false;
        })
      )
      .subscribe({
        next: (post) => {
          this.post = post;
          if (!post) this.error = 'Post not found.';
          this.loadTweets(id);
        }
      });
  }

  private loadTweets(postId: number): void {
    this.api
      .getPostTweets(postId)
      .pipe(timeout(3000), catchError(() => of({ data: [] as SourceTweet[] })))
      .subscribe((res) => {
        this.tweets = res.data || [];
      });
  }

  toggleTweetSelection(tweetId: number, checked: boolean): void {
    if (checked) {
      this.selectedTweetIds.add(tweetId);
    } else {
      this.selectedTweetIds.delete(tweetId);
    }
  }

  regenerateSummary(): void {
    if (!this.post || this.selectedTweetIds.size === 0 || this.regenerating) return;
    this.regenerating = true;
    this.regenError = '';
    const removeIds = Array.from(this.selectedTweetIds);

    this.api.regeneratePost(this.post.id, removeIds).subscribe({
      next: (res) => {
        this.post = res.post;
        this.tweets = res.tweets || [];
        this.selectedTweetIds.clear();
      },
      error: (err) => {
        this.regenError = err?.error?.error || 'Could not regenerate summary.';
      },
      complete: () => {
        this.regenerating = false;
      }
    });
  }
}
