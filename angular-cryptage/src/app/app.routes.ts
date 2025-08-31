import { Routes } from '@angular/router';
 import { HomeComponent } from './home/home.component';
import { LoginComponent } from './login/login.component';
import { ExtractMessageComponent } from './extract-message/extract-message.component';

export const routes: Routes = [
   { path: 'home', component: HomeComponent },
  { path: 'login', component: LoginComponent },
  {path:'extract',component:ExtractMessageComponent},
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/login' } // Catch-all route for any undefined routes
];