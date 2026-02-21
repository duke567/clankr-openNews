// src/app/article.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Post } from '../models';
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

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) {
      this.post = undefined;
      return;
    }
    // use the shared mock array
    this.post = MOCK_POSTS.find(p => p.id === id);
  }
}