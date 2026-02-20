import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Post } from '../models';

@Component({
  selector: 'app-article',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './article.html',
  styleUrls: ['./article.css'],
})
export class Article implements OnInit {

  post?: Post;

  // Mock data matching your interface exactly
  private posts: Post[] = [
    {
      id: 1001,
      user_id: 1,
      title: 'First Article',
      subtitle: 'An introduction',
      created_at: new Date().toISOString(),
      views_count: 10,
      content: `This is the full content of the first article.

Multiple paragraphs supported.`
    },
    {
      id: 1002,
      user_id: 2,
      title: 'Second Article',
      created_at: new Date().toISOString(),
      content: `Another article without subtitle or views.`
    }
  ];

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.post = this.posts.find(p => p.id === id);
  }
}