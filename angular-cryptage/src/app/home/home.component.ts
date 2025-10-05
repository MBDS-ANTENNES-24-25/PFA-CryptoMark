import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../sidebar/sidebar.component';

interface UserKey {
  keyId: string;
  secretKey: string;
  createdAt?: string;
}

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
  standalone: true,
  imports: [FormsModule, CommonModule, HttpClientModule,SidebarComponent]
})
export class HomeComponent implements OnInit {
  // Image handling properties
  selectedFile: File | null = null;
  imagePreviewUrl: string | null = null;
  resultImageUrl: string | null = null;
  isDragging: boolean = false;
  isProcessing: boolean = false;

  // Digital watermark options
  watermarkType: string = 'steganography';
  watermarkStrength: number = 50;
  watermarkText: string = '';
  watermarkPattern: string = 'random';
  
  // User key management
  userSecretKey: string = '';
  savedKeys: UserKey[] = [];
  showKeyModal: boolean = false;
  generatedKey: UserKey | null = null;
  verificationKey: string = '';
  keyHint: string | null = null;
  
  // Hash for content verification
  imageHash: string | null = null;

  // API endpoints
  private apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    // Load saved keys from localStorage (in production, use secure storage)
    this.loadSavedKeys();
    
    // Check if user has a default key
    const defaultKey = localStorage.getItem('defaultUserKey');
    if (defaultKey) {
      this.userSecretKey = defaultKey;
    }
  }

  /**
   * Generate a new user secret key
   */
  generateNewKey(): void {
    this.isProcessing = true;
    
    this.http.post<any>(`${this.apiUrl}/keys/generate`, {})
      .pipe(
        catchError(error => {
          console.error('Error generating key:', error);
          alert('Error generating key. Please try again.');
          this.isProcessing = false;
          return of(null);
        })
      )
      .subscribe(response => {
        this.isProcessing = false;
        
        if (response && response.success) {
          this.generatedKey = {
            keyId: response.keyId,
            secretKey: response.secretKey,
            createdAt: new Date().toISOString()
          };
          
          // Show the key to user
          this.showKeyModal = true;
          
          // Optionally set as current key
          this.userSecretKey = response.secretKey;
          
          // Save to local storage (in production, use secure storage)
          this.saveKey(this.generatedKey);
        }
      });
  }

  /**
   * Save a key to local storage
   */
  saveKey(key: UserKey): void {
    const keys = this.getSavedKeys();
    keys.push(key);
    localStorage.setItem('userKeys', JSON.stringify(keys));
    this.loadSavedKeys();
  }

  /**
   * Load saved keys from storage
   */
  loadSavedKeys(): void {
    this.savedKeys = this.getSavedKeys();
  }

  /**
   * Get saved keys from storage
   */
  getSavedKeys(): UserKey[] {
    const keysJson = localStorage.getItem('userKeys');
    return keysJson ? JSON.parse(keysJson) : [];
  }

  /**
   * Select a saved key to use
   */
  selectKey(key: UserKey): void {
    this.userSecretKey = key.secretKey;
    localStorage.setItem('defaultUserKey', key.secretKey);
    this.showKeyModal = false;
  }

  /**
   * Copy key to clipboard
   */
  copyKeyToClipboard(key: string): void {
    navigator.clipboard.writeText(key).then(() => {
      alert('Key copied to clipboard!');
    }).catch(err => {
      console.error('Could not copy key:', err);
      alert('Please manually copy the key');
    });
  }

  /**
   * Handle file selection from input
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.processSelectedFile(input.files[0]);
    }
  }

  /**
   * Handle drag over event
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  /**
   * Handle drag leave event
   */
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  /**
   * Handle drop event
   */
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (this.isValidImageFile(file)) {
        this.processSelectedFile(file);
      } else {
        alert('Please upload a valid image file (JPG, PNG, or WebP)');
      }
    }
  }

  /**
   * Process the selected file
   */
  private processSelectedFile(file: File): void {
    if (this.isValidImageFile(file)) {
      if (file.size <= 10 * 1024 * 1024) { // 10MB limit
        this.selectedFile = file;
        const reader = new FileReader();
        reader.onload = () => {
          this.imagePreviewUrl = reader.result as string;
          this.generateImageHash(reader.result as string);
        };
        reader.readAsDataURL(file);
      } else {
        alert('File size exceeds 10MB limit');
      }
    } else {
      alert('Please upload a valid image file (JPG, PNG, or WebP)');
    }
  }

  /**
   * Generate a hash of the image data for verification
   */
  private generateImageHash(imageData: string): void {
    let hash = 0;
    for (let i = 0; i < imageData.length; i++) {
      const char = imageData.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    this.imageHash = Math.abs(hash).toString(16).substring(0, 8);
  }

  /**
   * Check if file is a valid image
   */
  private isValidImageFile(file: File): boolean {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    return validTypes.includes(file.type);
  }

  /**
   * Remove the selected image
   */
  removeImage(): void {
    this.selectedFile = null;
    this.imagePreviewUrl = null;
    this.imageHash = null;
    this.resultImageUrl = null;
    this.keyHint = null;
  }

  /**
   * Apply digital watermark to the image
   */
  watermarkImage(): void {
    if (!this.selectedFile) return;

    // Check if user has a key
    if (!this.userSecretKey) {
      const useTemporary = confirm(
        'No secret key set. Would you like to:\n\n' +
        'OK - Generate a new permanent key (recommended)\n' +
        'Cancel - Use a temporary key (less secure)'
      );
      
      if (useTemporary) {
        this.generateNewKey();
        return;
      }
      // Continue with temporary key (backend will generate one)
    }

    this.isProcessing = true;
    const formData = new FormData();
    formData.append('image', this.selectedFile);
    formData.append('type', this.watermarkType);
    formData.append('strength', this.watermarkStrength.toString());
    formData.append('text', this.watermarkText || '© Protected Image');
    formData.append('pattern', this.watermarkPattern);
    
    if (this.userSecretKey) {
      formData.append('userKey', this.userSecretKey);
    }

    this.http.post<any>(`${this.apiUrl}/images/watermark`, formData)
      .pipe(
        catchError(error => {
          console.error('Error applying watermark:', error);
          alert('Error processing the image. Please try again.');
          this.isProcessing = false;
          return of(null);
        })
      )
      .subscribe(response => {
        this.isProcessing = false;
        
        if (response && response.success) {
          // Handle the response
          if (response.base64Image) {
            this.resultImageUrl = 'data:image/jpeg;base64,' + response.base64Image;
          }
          
          if (response.verificationHash) {
            this.imageHash = response.verificationHash;
          }
          
          if (response.keyHint) {
            this.keyHint = response.keyHint;
          }
          
          // If a temporary key was generated, save it
          if (response.temporaryKey) {
            this.userSecretKey = response.temporaryKey;
            const tempKey: UserKey = {
              keyId: 'temp_' + Date.now(),
              secretKey: response.temporaryKey,
              createdAt: new Date().toISOString()
            };
            this.saveKey(tempKey);
            alert(response.warning);
          }
        }
      });
  }

  /**
   * Verify if an image contains our watermark
   */
  verifyWatermark(): void {
    if (!this.selectedFile) {
      alert('Please select an image to verify');
      return;
    }

    // Ask for verification key if not already set
    if (!this.verificationKey && !this.userSecretKey) {
      this.verificationKey = prompt('Enter your secret key to verify the watermark:') || '';
      if (!this.verificationKey) {
        alert('Verification key is required');
        return;
      }
    }

    const keyToUse = this.verificationKey || this.userSecretKey;

    this.isProcessing = true;
    const formData = new FormData();
    formData.append('image', this.selectedFile);
    formData.append('userKey', keyToUse);
    formData.append('method', this.watermarkType);
    formData.append('strength', this.watermarkStrength.toString());

    this.http.post<any>(`${this.apiUrl}/images/verify`, formData)
      .pipe(
        catchError(error => {
          console.error('Error verifying watermark:', error);
          alert('Error during verification. Please try again.');
          this.isProcessing = false;
          return of(null);
        })
      )
      .subscribe(response => {
        this.isProcessing = false;
        console.log('Verification response:', response);
        
        if (response) {
          if (response.hasWatermark && response.isValidKey) {
            alert(
              `✅ Watermark verified successfully!\n\n` +
              `Message: ${response.extractedMessage || 'N/A'}\n` +
              `Method: ${response.method || 'Unknown'}\n` +
              `Timestamp: ${response.timestamp || 'Unknown'}`
            );
          } else if (response.hasWatermark && !response.isValidKey) {
            alert(
              `⚠️ Watermark detected but key doesn't match!\n\n` +
              `This image appears to be protected by someone else.`
            );
          } else {
            alert(
              `❌ No watermark found with your key.\n\n` +
              `Possible reasons:\n` +
              `• The image doesn't have a watermark\n` +
              `• The watermark was created with a different key\n` +
              `• The image was modified after watermarking`
            );
          }
        }
      });
  }

  /**
   * Download the watermarked image
   */
  downloadImage(): void {
    if (!this.resultImageUrl) return;

    const link = document.createElement('a');
    link.href = this.resultImageUrl;
    
    // Generate filename with key hint
    const keyPart = this.keyHint ? `_${this.keyHint}` : '';
    const hashPart = this.imageHash ? `_${this.imageHash.substring(0, 8)}` : '';
    const filename = `protected_image${keyPart}${hashPart}_${new Date().getTime()}.png`;
    link.download = filename;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Start a new image watermarking process
   */
  startNewImage(): void {
    this.selectedFile = null;
    this.imagePreviewUrl = null;
    this.resultImageUrl = null;
    this.watermarkType = 'invisible';
    this.watermarkStrength = 50;
    this.watermarkText = '';
    this.watermarkPattern = 'random';
    this.imageHash = null;
    this.keyHint = null;
    this.verificationKey = '';
  }

  /**
   * Show key management modal
   */
  showKeyManager(): void {
    this.showKeyModal = true;
  }

  /**
   * Delete a saved key
   */
  deleteKey(keyId: string): void {
    if (confirm('Are you sure you want to delete this key? This action cannot be undone.')) {
      const keys = this.getSavedKeys().filter(k => k.keyId !== keyId);
      localStorage.setItem('userKeys', JSON.stringify(keys));
      this.loadSavedKeys();
    }
  }
}