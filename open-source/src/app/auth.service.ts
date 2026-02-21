import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, map, Observable, tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private loggedInSubject = new BehaviorSubject<boolean>(false);
  isLoggedIn$ = this.loggedInSubject.asObservable();
  private usernameSubject = new BehaviorSubject<string | null>(null);
  username$ = this.usernameSubject.asObservable();

  constructor(private http: HttpClient) {}

  isLoggedIn(): boolean {
    return this.loggedInSubject.value;
  }

  get username(): string | null {
    return this.usernameSubject.value;
  }

  markLoggedIn(username: string): void {
    this.usernameSubject.next(username);
    this.loggedInSubject.next(true);
  }

  logout(): void {
    // Local logout state only until backend logout is needed.
    this.usernameSubject.next(null);
    this.loggedInSubject.next(false);
  }

  checkSession(): Observable<boolean> {
    return this.http
      .get<{ authenticated: boolean; user: { username: string } | null }>('/api/auth/me/')
      .pipe(
        tap((res) => {
          this.loggedInSubject.next(res.authenticated);
          this.usernameSubject.next(res.user?.username ?? null);
        }),
        map((res) => res.authenticated)
      );
  }
}
