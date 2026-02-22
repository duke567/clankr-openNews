import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, catchError, map, Observable, of, switchMap, tap } from 'rxjs';

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
    this.http
      .get('/api/auth/csrf/', { responseType: 'text', withCredentials: true })
      .pipe(switchMap(() => this.http.post('/api/auth/logout/', {}, { withCredentials: true })))
      .subscribe({ error: () => void 0 });
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

  bootstrapSession(): Observable<boolean> {
    return this.checkSession().pipe(catchError(() => of(false)));
  }
}
