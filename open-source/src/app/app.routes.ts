import { Routes } from '@angular/router';
import { TimelineComponent } from './timeline.component';
import { ProfileComponent } from './profile.component';
import { Article } from './article/article';

export const appRoutes: Routes = [
  { path: '', component: TimelineComponent },
  { path: 'u/:username', component: ProfileComponent },
  { path: 'posts/:id', component: Article},
  { path: '**', redirectTo: '' }
];
