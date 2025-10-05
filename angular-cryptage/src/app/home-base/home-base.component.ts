import { Component } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-home-base',
  templateUrl: './home-base.component.html',
  styleUrls: ['./home-base.component.css'],
  standalone: true,
  imports: [RouterModule, CommonModule]
})
export class HomeBaseComponent {

}