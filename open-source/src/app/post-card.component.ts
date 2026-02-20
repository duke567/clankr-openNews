import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Post } from './models';

@Component({
  selector: 'app-post-card',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <a class="post-link" [routerLink]="['/posts', post.id]">
      <article class="card post">
        <h2><b>{{ post.title }}</b></h2>
        <p>{{ post.subtitle }}</p>

        <div class="row">
          <small>{{ post.created_at | date: 'short' }}</small>
          <small>{{ post.views_count || 0 }} views</small>
        </div>
      </article>
    </a>
  `
})

export class PostCardComponent {
  @Input({ required: true }) post!: Post;
}
