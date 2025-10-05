import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { SidebarComponent } from '../sidebar/sidebar.component';

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

interface ChatResponse {
  success: boolean;
  response?: string;
  session_id?: string;
  sessionId?: string;
  timestamp: string;
  error?: string;
}

interface SessionResponse {
  success: boolean;
  sessionId: string;
  createdAt: string;
  message?: string;
}

@Component({
  selector: 'app-agent',
  standalone: true,
  imports: [CommonModule, FormsModule, SidebarComponent],
  templateUrl: './agent.component.html',
  styleUrl: './agent.component.css'
})
export class AgentComponent implements OnInit, OnDestroy {
  private apiUrl = 'http://localhost:5000/api';
  
  messages: Message[] = [];
  userInput: string = '';
  isLoading: boolean = false;
  sessionId: string | null = null;
  error: string | null = null;
  
  // Suggested prompts
  suggestedPrompts = [
   
    'Comment la stéganographie protège-t-elle mes images ?',
    'Comment puis-je détecter si mon image a été altérée ?'
  ];

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.initializeSession();
    this.addWelcomeMessage();
  }

  ngOnDestroy() {
    // Optionally clear session on component destroy
    if (this.sessionId) {
      this.clearSession();
    }
  }

  private initializeSession() {
    this.http.post<SessionResponse>(`${this.apiUrl}/agent/session`, {})
      .pipe(
        catchError((error: HttpErrorResponse) => {
          console.error('Erreur lors de la création de la session:', error);
          this.error = 'Échec de l\'initialisation de la session de chat';
          return of(null);
        })
      )
      .subscribe(response => {
        if (response && response.success) {
          this.sessionId = response.sessionId;
          console.log('Session créée:', this.sessionId);
        }
      });
  }

  private addWelcomeMessage() {
    const welcomeMessage: Message = {
      id: this.generateId(),
      role: 'agent',
      content: `Bonjour ! Je suis votre expert en stéganographie et filigrane numérique. Je peux vous aider à comprendre :

• Les techniques de filigrane numérique
• Les méthodes de stéganographie et les meilleures pratiques
• Les stratégies de protection d'images
• La vérification et la détection de filigranes
• Les recommandations de sécurité pour vos images

Comment puis-je vous aider aujourd'hui ?`,
      timestamp: new Date()
    };
    this.messages.push(welcomeMessage);
  }

  sendMessage() {
    if (!this.userInput.trim() || this.isLoading) {
      return;
    }

    if (!this.sessionId) {
      this.error = 'Aucune session active. Veuillez actualiser la page.';
      return;
    }

    // Add user message to chat
    const userMessage: Message = {
      id: this.generateId(),
      role: 'user',
      content: this.userInput,
      timestamp: new Date()
    };
    this.messages.push(userMessage);

    const messageText = this.userInput;
    this.userInput = '';
    this.isLoading = true;
    this.error = null;

    // Send to backend
    this.http.post<ChatResponse>(`${this.apiUrl}/agent/chat`, {
      message: messageText,
      sessionId: this.sessionId,
      context: {}
    })
    .pipe(
      catchError((error: HttpErrorResponse) => {
        console.error('Erreur lors de l\'envoi du message:', error);
        this.isLoading = false;
        
        const errorMessage: Message = {
          id: this.generateId(),
          role: 'agent',
          content: 'Désolé, j\'ai rencontré une erreur lors du traitement de votre demande. Veuillez réessayer.',
          timestamp: new Date()
        };
        this.messages.push(errorMessage);
        
        return of(null);
      })
    )
    .subscribe(response => {
      this.isLoading = false;
      
      if (response && response.success && response.response) {
        const agentMessage: Message = {
          id: this.generateId(),
          role: 'agent',
          content: response.response,
          timestamp: new Date()
        };
        this.messages.push(agentMessage);
        
        // Auto-scroll to bottom
        setTimeout(() => this.scrollToBottom(), 100);
      }
    });
  }

  useSuggestedPrompt(prompt: string) {
    this.userInput = prompt;
    this.sendMessage();
  }

  clearChat() {
    if (confirm('Êtes-vous sûr de vouloir effacer l\'historique du chat ?')) {
      this.messages = [];
      this.addWelcomeMessage();
      
      if (this.sessionId) {
        this.http.delete(`${this.apiUrl}/agent/session/${this.sessionId}`)
          .pipe(
            catchError(error => {
              console.error('Erreur lors de l\'effacement de la session:', error);
              return of(null);
            })
          )
          .subscribe(() => {
            // Reinitialize session
            this.initializeSession();
          });
      }
    }
  }

  private clearSession() {
    if (this.sessionId) {
      this.http.delete(`${this.apiUrl}/agent/session/${this.sessionId}`)
        .pipe(
          catchError(error => {
            console.error('Erreur lors de l\'effacement de la session:', error);
            return of(null);
          })
        )
        .subscribe();
    }
  }

  private scrollToBottom() {
    const chatMessages = document.querySelector('.chat-messages');
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  private generateId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}