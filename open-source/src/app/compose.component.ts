import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api.service';
import { Post } from './models';

@Component({
  selector: 'app-compose',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <form (ngSubmit)="submit()" #f="ngForm" class="card">
      <textarea
        name="content"
        [(ngModel)]="content"
        required
        maxlength="280"
        rows="3"
        placeholder="What's happening?"
      ></textarea>
      <div class="row">
        <small>{{ content.length }}/280</small>
        <button type="submit" [disabled]="f.invalid || loading">Post</button>
      </div>
    </form>
  `
})
export class ComposeComponent {
  @Output() posted = new EventEmitter<Post>();

  content = '';
  loading = false;

  constructor(private api: ApiService) {}

  submit(): void {
    const text = this.content.trim();
    if (!text) return;

    this.loading = true;
    this.api.createPost(text).subscribe({
      next: (post) => {
        this.content = '';
        this.posted.emit(post);
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
}
