import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ExtractMessageComponent } from './extract-message.component';

describe('ExtractMessageComponent', () => {
  let component: ExtractMessageComponent;
  let fixture: ComponentFixture<ExtractMessageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExtractMessageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ExtractMessageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
