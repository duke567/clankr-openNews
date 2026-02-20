import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { User } from './models';

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private userSubject = new BehaviorSubject<User | null>(this.readUser());
  user$ = this.userSubject.asObservable();

  get token(): string | null {
    return this.storageGet(TOKEN_KEY);
  }

  get user(): User | null {
    return this.userSubject.value;
  }

  isLoggedIn(): boolean {
    return !!this.token;
  }

  setSession(token: string, user: User): void {
    this.storageSet(TOKEN_KEY, token);
    this.storageSet(USER_KEY, JSON.stringify(user));
    this.userSubject.next(user);
  }

  setUser(user: User): void {
    this.storageSet(USER_KEY, JSON.stringify(user));
    this.userSubject.next(user);
  }

  logout(): void {
    this.storageRemove(TOKEN_KEY);
    this.storageRemove(USER_KEY);
    this.userSubject.next(null);
  }

  private readUser(): User | null {
    const raw = this.storageGet(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  private storageGet(key: string): string | null {
    return typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
  }

  private storageSet(key: string, value: string): void {
    if (typeof localStorage !== 'undefined') localStorage.setItem(key, value);
  }

  private storageRemove(key: string): void {
    if (typeof localStorage !== 'undefined') localStorage.removeItem(key);
  }
}
