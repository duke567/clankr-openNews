import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Post, SourceTweet, User } from './models';
import { Observable, switchMap } from 'rxjs';

// Keep '' when frontend and Django API share origin.
// If API is elsewhere, set e.g. 'https://api.example.com'
const API_BASE = '';

@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(private http: HttpClient) {}

  register(payload: { username: string; password1: string; password2: string }): Observable<{ ok: boolean }> {
    return this.ensureCsrf().pipe(
      switchMap(() => this.http.post<{ ok: boolean }>(`${API_BASE}/api/auth/register/`, payload))
    );
  }

  login(payload: { username: string; password: string }): Observable<{ ok: boolean; user?: { username: string } }> {
    return this.ensureCsrf().pipe(
      switchMap(() =>
        this.http.post<{ ok: boolean; user?: { username: string } }>(`${API_BASE}/api/auth/login/`, payload)
      )
    );
  }

  getTimeline(limit = 50): Observable<{ data: Post[] }> {
    return this.http.get<{ data: Post[] }>(`${API_BASE}/api/v1/posts/timeline`, {
      params: { limit, t: Date.now() }
    });
  }

  getPostById(postId: number): Observable<Post> {
    return this.http.get<Post>(`${API_BASE}/api/v1/posts/${postId}`);
  }

  getPostTweets(postId: number): Observable<{ data: SourceTweet[] }> {
    return this.http.get<{ data: SourceTweet[] }>(`${API_BASE}/api/v1/posts/${postId}/tweets`);
  }

  regeneratePost(postId: number, removeIds: number[]): Observable<{ post: Post; tweets: SourceTweet[] }> {
    return this.http.post<{ post: Post; tweets: SourceTweet[] }>(`${API_BASE}/api/v1/posts/${postId}/regenerate`, {
      remove_ids: removeIds
    });
  }

  createPost(content: string): Observable<Post> {
    return this.http.post<Post>(`${API_BASE}/api/v1/posts`, { content });
  }

  likePost(postId: number): Observable<void> {
    return this.http.post<void>(`${API_BASE}/api/v1/posts/${postId}/like`, {});
  }

  unlikePost(postId: number): Observable<void> {
    return this.http.delete<void>(`${API_BASE}/api/v1/posts/${postId}/like`);
  }

  getUserProfile(username: string): Observable<{ user: User; posts: Post[] }> {
    return this.http.get<{ user: User; posts: Post[] }>(`${API_BASE}/api/v1/users/${username}`);
  }

  private ensureCsrf(): Observable<string> {
    return this.http.get(`${API_BASE}/api/auth/csrf/`, { responseType: 'text', withCredentials: true });
  }
}
