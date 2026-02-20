import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Post } from './models';

@Component({
  selector: 'app-post-card',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <article class="card post">
      <div class="post-head">
        <a
          *ngIf="post.author?.username; else fallbackUser"
          [routerLink]="['/u', post.author?.username]"
          class="username"
        >
          {{ post.author?.display_name || post.author?.username }}
        </a>
        <ng-template #fallbackUser>
          <span class="username">User #{{ post.user_id }}</span>
        </ng-template>
        <small>{{ post.created_at | date: 'short' }}</small>
      </div>

      <p>{{ post.content }}</p>

      <div class="row">
        <small>{{ post.likes_count || 0 }} likes</small>
      </div>
    </article>
  `
})
export class PostCardComponent {
  @Input({ required: true }) post!: Post;
}
