import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

interface ExtractionResult {
  hasWatermark: boolean;
  isValidKey: boolean;
  extractedMessage?: string;
  timestamp?: string;
  method?: string;
  details?: any;
  message: string;
  possibleReasons?: string[];
}

interface SavedKey {
  keyId: string;
  secretKey: string;
  createdAt?: string;
}

@Component({
  selector: 'app-extract-message',
  standalone: true,
  imports: [FormsModule, CommonModule, HttpClientModule],
  templateUrl: './extract-message.component.html',
  styleUrl: './extract-message.component.css'
})
export class ExtractMessageComponent implements OnInit {
  // Image handling
  selectedFile: File | null = null;
  imagePreviewUrl: string | null = null;
  isDragging: boolean = false;
  isProcessing: boolean = false;
  
  // Extraction parameters
  userSecretKey: string = '';
  extractionMethod: string = 'auto';
  strength: number = 50;
  
  // Results
  extractionResult: ExtractionResult | null = null;
  showResult: boolean = false;
  extractionSuccess: boolean = false;
  
  // Key management
  savedKeys: SavedKey[] = [];
  selectedKeyId: string = '';
  showKeyInput: boolean = false;
  
  // API endpoint
  private apiUrl = 'http://localhost:5000/api';
  
  constructor(private http: HttpClient) { }
  
  ngOnInit(): void {
    this.loadSavedKeys();
    
    // Check for default key
    const defaultKey = localStorage.getItem('defaultUserKey');
    if (defaultKey) {
      this.userSecretKey = defaultKey;
    }
  }
  
  /**
   * Load saved keys from localStorage
   */
  loadSavedKeys(): void {
    const keysJson = localStorage.getItem('userKeys');
    this.savedKeys = keysJson ? JSON.parse(keysJson) : [];
  }
  
  /**
   * Handle key selection from dropdown
   */
  onKeySelect(): void {
    if (this.selectedKeyId === 'manual') {
      this.showKeyInput = true;
      this.userSecretKey = '';
    } else if (this.selectedKeyId) {
      const selectedKey = this.savedKeys.find(k => k.keyId === this.selectedKeyId);
      if (selectedKey) {
        this.userSecretKey = selectedKey.secretKey;
        this.showKeyInput = false;
      }
    }
  }
  
  /**
   * Handle file selection
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
   * Process selected file
   */
  private processSelectedFile(file: File): void {
    if (this.isValidImageFile(file)) {
      if (file.size <= 10 * 1024 * 1024) { // 10MB limit
        this.selectedFile = file;
        const reader = new FileReader();
        reader.onload = () => {
          this.imagePreviewUrl = reader.result as string;
          this.extractionResult = null;
          this.showResult = false;
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
   * Check if file is valid image
   */
  private isValidImageFile(file: File): boolean {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
    return validTypes.includes(file.type);
  }
  
  /**
   * Remove selected image
   */
  removeImage(): void {
    this.selectedFile = null;
    this.imagePreviewUrl = null;
    this.extractionResult = null;
    this.showResult = false;
  }
  
  /**
   * Extract watermark from image
   */
  extractWatermark(): void {
    if (!this.selectedFile) {
      alert('Please select an image first');
      return;
    }
    
    if (!this.userSecretKey) {
      alert('Please enter or select your secret key');
      return;
    }
    
    this.isProcessing = true;
    this.showResult = false;
    
    const formData = new FormData();
    formData.append('image', this.selectedFile);
    formData.append('userKey', this.userSecretKey);
    
    // Set method based on selection
    if (this.extractionMethod !== 'auto') {
      formData.append('method', this.extractionMethod);
    }
    
    formData.append('strength', this.strength.toString());
    
    this.http.post<ExtractionResult>(`${this.apiUrl}/images/verify`, formData)
      .pipe(
        catchError(error => {
          console.error('Error extracting watermark:', error);
          alert('Error during extraction. Please try again.');
          this.isProcessing = false;
          return of(null);
        })
      )
      .subscribe(response => {
        this.isProcessing = false;
        
        if (response) {
          this.extractionResult = response;
          this.showResult = true;
          this.extractionSuccess = response.hasWatermark && response.isValidKey;
          
          // Auto-scroll to results
          setTimeout(() => {
            const resultElement = document.querySelector('.result-section');
            if (resultElement) {
              resultElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }, 100);
        }
      });
  }
  
  /**
   * Try all extraction methods
   */
  tryAllMethods(): void {
    if (!this.selectedFile || !this.userSecretKey) {
      alert('Please select an image and enter your key first');
      return;
    }
    
    this.isProcessing = true;
    this.showResult = false;
    
    const methods = ['invisible', 'steganography', 'frequency', 'metadata'];
    let successfulMethod: string | null = null;
    let attemptCount = 0;
    
    // Try each method sequentially
    const tryNextMethod = () => {
      if (attemptCount >= methods.length) {
        this.isProcessing = false;
        if (!successfulMethod) {
          this.extractionResult = {
            hasWatermark: false,
            isValidKey: false,
            message: 'No watermark found with any method',
            possibleReasons: [
              'The image may not have a watermark',
              'The watermark was created with a different key',
              'The image was modified after watermarking'
            ]
          };
          this.showResult = true;
          this.extractionSuccess = false;
        }
        return;
      }
      
      const currentMethod = methods[attemptCount];
      const formData = new FormData();
      formData.append('image', this.selectedFile!);
      formData.append('userKey', this.userSecretKey);
      formData.append('method', currentMethod);
      formData.append('strength', this.strength.toString());
      
      this.http.post<ExtractionResult>(`${this.apiUrl}/images/verify`, formData)
        .pipe(
          catchError(error => {
            console.error(`Error with method ${currentMethod}:`, error);
            return of(null);
          })
        )
        .subscribe(response => {
          if (response && response.hasWatermark && response.isValidKey) {
            // Success! Stop trying other methods
            this.extractionResult = response;
            this.showResult = true;
            this.extractionSuccess = true;
            this.isProcessing = false;
            successfulMethod = currentMethod;
          } else {
            // Try next method
            attemptCount++;
            tryNextMethod();
          }
        });
    };
    
    tryNextMethod();
  }
  
  /**
   * Copy text to clipboard
   */
  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      // Show temporary success message
      const button = event?.target as HTMLElement;
      if (button) {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => {
          button.textContent = originalText;
        }, 2000);
      }
    }).catch(err => {
      console.error('Could not copy text:', err);
      alert('Please manually copy the text');
    });
  }
  
  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string | undefined): string {
    if (!timestamp) return 'Unknown';
    
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  }
  
  /**
   * Get method display name
   */
  getMethodDisplayName(method: string | undefined): string {
    if (!method) return 'Unknown';
    
    const methodNames: { [key: string]: string } = {
      'invisible': 'Invisible Watermark (AI-Resistant)',
      'steganography': 'Steganographic Data Hiding',
      'frequency': 'Frequency Domain Watermark',
      'metadata': 'Metadata Embedding',
      'auto': 'Auto-Detect'
    };
    
    return methodNames[method] || method;
  }
  
  /**
   * Start new extraction
   */
  startNewExtraction(): void {
    this.selectedFile = null;
    this.imagePreviewUrl = null;
    this.extractionResult = null;
    this.showResult = false;
    this.extractionSuccess = false;
  }
}