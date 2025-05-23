import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { catchError } from 'rxjs/operators';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css'],
  standalone: true,
  imports: [FormsModule, CommonModule, HttpClientModule]
})
export class HomeComponent implements OnInit {
  // Image handling properties
  selectedFile: File | null = null;
  imagePreviewUrl: string | null = null;
  resultImageUrl: string | null = null;
  isDragging: boolean = false;
  isProcessing: boolean = false;

  // Digital watermark options
  watermarkType: string = 'invisible';
  watermarkStrength: number = 50;
  watermarkText: string = '';
  watermarkPattern: string = 'random';
  
  // Hash for content verification
  imageHash: string | null = null;

  // API endpoint
  private apiUrl = 'http://localhost:5000/api/images/watermark'; // Updated endpoint name

  constructor(private http: HttpClient) { }

  ngOnInit(): void {
    // Initialization code if needed
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
      if (file.size <= 10 * 1024 * 1024) { // 10MB limit (increased from 5MB)
        this.selectedFile = file;
        const reader = new FileReader();
        reader.onload = () => {
          this.imagePreviewUrl = reader.result as string;
          
          // Generate a basic hash of the image for verification
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
    // Simple hash function for demonstration
    // In production, use a proper crypto library
    let hash = 0;
    for (let i = 0; i < imageData.length; i++) {
      const char = imageData.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
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
  }

  /**
   * Apply digital watermark to the image
   */
  watermarkImage(): void {
    if (!this.selectedFile) return;

    this.isProcessing = true;
    const formData = new FormData();
    formData.append('image', this.selectedFile);
    formData.append('type', this.watermarkType);
    formData.append('strength', this.watermarkStrength.toString());
    formData.append('text', this.watermarkText);
    formData.append('pattern', this.watermarkPattern);

    this.http.post<any>(this.apiUrl, formData)
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
        
        if (response) {
          // Handle the response from the backend
          if (response.watermarkedImageUrl) {
            this.resultImageUrl = response.watermarkedImageUrl;
          } else if (response.base64Image) {
            // If the backend returns a base64 image
            this.resultImageUrl = 'data:image/jpeg;base64,' + response.base64Image;
          }
          
          // If the backend returns a verification code or hash
          if (response.verificationHash) {
            this.imageHash = response.verificationHash;
          }
        }
      });
  }

  /**
   * Apply client-side watermark (for demonstration purposes)
   * This is a simplified example and would not be as robust as server-side processing
   */
  applyClientSideWatermark(): void {
    if (!this.selectedFile || !this.imagePreviewUrl) return;
    
    // Create an image element to work with
    const img = new Image();
    img.src = this.imagePreviewUrl;
    
    img.onload = () => {
      // Create a canvas to manipulate the image
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      canvas.width = img.width;
      canvas.height = img.height;
      
      // Draw the original image
      ctx.drawImage(img, 0, 0);
      
      // Get image data to manipulate pixels
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const pixels = imageData.data;
      
      // Apply LSB (Least Significant Bit) watermarking
      // This is a very basic implementation - real world would be more sophisticated
      const message = this.watermarkText || "Protected Image";
      const messageBytes = this.textToBytes(message);
      
      // Encode message length first (4 bytes)
      const messageLength = messageBytes.length;
      this.encodeInteger(pixels, 0, messageLength);
      
      // Encode the message bytes
      for (let i = 0; i < messageBytes.length; i++) {
        this.encodeByte(pixels, (i + 4) * 8, messageBytes[i]);
      }
      
      // Put the modified image data back
      ctx.putImageData(imageData, 0, 0);
      
      // Convert to base64 and display
      this.resultImageUrl = canvas.toDataURL('image/png');
      this.isProcessing = false;
    };
    
    img.onerror = () => {
      alert('Error processing image');
      this.isProcessing = false;
    };
  }
  
  /**
   * Utility function to convert text to byte array
   */
  private textToBytes(text: string): Uint8Array {
    const encoder = new TextEncoder();
    return encoder.encode(text);
  }
  
  /**
   * Encode an integer in the first 32 pixels (4 bytes)
   */
  private encodeInteger(pixels: Uint8ClampedArray, startPixel: number, value: number): void {
    for (let i = 0; i < 32; i++) {
      // Get the bit to encode
      const bit = (value >> i) & 1;
      
      // Calculate pixel position (each pixel has 4 values: R,G,B,A)
      const pixelPos = (startPixel + i) * 4;
      
      // Modify the LSB of the red channel
      if (pixelPos < pixels.length) {
        // Clear the LSB and set it to our bit
        pixels[pixelPos] = (pixels[pixelPos] & 0xFE) | bit;
      }
    }
  }
  
  /**
   * Encode a byte in 8 pixels
   */
  private encodeByte(pixels: Uint8ClampedArray, startPixel: number, value: number): void {
    for (let i = 0; i < 8; i++) {
      // Get the bit to encode
      const bit = (value >> i) & 1;
      
      // Calculate pixel position
      const pixelPos = (startPixel + i) * 4;
      
      // Modify the LSB of the red channel
      if (pixelPos < pixels.length) {
        pixels[pixelPos] = (pixels[pixelPos] & 0xFE) | bit;
      }
    }
  }

  /**
   * Download the watermarked image
   */
  downloadImage(): void {
    if (!this.resultImageUrl) return;

    // Create a temporary link element
    const link = document.createElement('a');
    
    // If the image is a base64 string
    if (this.resultImageUrl.startsWith('data:')) {
      link.href = this.resultImageUrl;
    } else {
      // If the image is a URL
      link.href = this.resultImageUrl;
    }
    
    // Generate a filename with timestamp and hash
    const hashPart = this.imageHash ? `_${this.imageHash}` : '';
    const filename = `protected_image${hashPart}_${new Date().getTime()}.png`;
    link.download = filename;
    
    // Append to the document, click and remove
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  /**
   * Verify if an image contains our watermark
   * This would typically be a separate utility, included here for completeness
   */
  verifyWatermark(): void {
    if (!this.selectedFile) return;

    this.isProcessing = true;
    const formData = new FormData();
    formData.append('image', this.selectedFile);

    this.http.post<any>('http://localhost:5000/api/images/verify', formData)
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
        console.log(response)
        if (response) {
          if (response.hasWatermark) {
            alert(`Watermark detected! Message: ${response.extractedMessage || 'N/A'}`);
          } else {
            alert('No watermark detected in this image.');
          }
        }
      });
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
  }
}