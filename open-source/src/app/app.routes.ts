import { Routes } from '@angular/router';
import { TimelineComponent } from './timeline.component';
import { ProfileComponent } from './profile.component';

export const appRoutes: Routes = [
  { path: '', component: TimelineComponent },
  { path: 'u/:username', component: ProfileComponent },
  { path: '**', redirectTo: '' }
];
