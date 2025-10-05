import { Routes } from '@angular/router';
 import { HomeComponent } from './home/home.component';
import { LoginComponent } from './login/login.component';
import { ExtractMessageComponent } from './extract-message/extract-message.component';
import { HomeBaseComponent } from './home-base/home-base.component';
import { AboutUsComponent } from './about-us/about-us.component';
import { AgentComponent } from './agent/agent.component';

export const routes: Routes = [
   { path: 'home', component: HomeComponent },
   
  {path:'first-page',component:ExtractMessageComponent},
  { path: 'login', component: LoginComponent },
  {path:'extract',component:ExtractMessageComponent},
  {path:'home-base',component:HomeBaseComponent},
  {path:'about-us',component: AboutUsComponent},
  {path:'agent',component:AgentComponent},
  { path: '', redirectTo: '/home-base', pathMatch: 'full' },
  { path: '**', redirectTo: '/home-base' }
];