import { Routes } from '@angular/router';
import { TimelineComponent } from './timeline.component';
import { ProfileComponent } from './profile.component';
import { Article } from './article/article';
import { LoginComponent } from './login.component';
import { RegisterComponent } from './register.component';
import { LogoutComponent } from './logout.component';
import { authGuard, guestGuard } from './auth.guard';

export const appRoutes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'auth/login' },
  { path: 'auth/login', component: LoginComponent, canActivate: [guestGuard] },
  { path: 'auth/register', component: RegisterComponent, canActivate: [guestGuard] },
  { path: 'auth/logout', component: LogoutComponent },
  { path: 'timeline', component: TimelineComponent, canActivate: [authGuard] },
  { path: 'u/:username', component: ProfileComponent, canActivate: [authGuard] },
  { path: 'posts/:id', component: Article, canActivate: [authGuard] },
  { path: '**', redirectTo: 'auth/login' }
];
