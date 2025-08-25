import { Injectable } from '@angular/core';
import { Auth, createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut, onAuthStateChanged,
  User,
  GoogleAuthProvider,
  GithubAuthProvider,
  signInWithPopup } from '@angular/fire/auth';
import { from, Observable } from 'rxjs';


@Injectable({ providedIn: 'root' })
export class AuthService {
  currentUser$: Observable<User | null>;

  constructor(private auth: Auth) {
    this.currentUser$ = new Observable(subscriber => {
      const unsubscribe = onAuthStateChanged(this.auth, user => subscriber.next(user));
      return unsubscribe;
    });
  }

  login(email: string, password: string) {
    return from(signInWithEmailAndPassword(this.auth, email, password));
  }

  register(email: string, password: string) {
    return from(createUserWithEmailAndPassword(this.auth, email, password));
  }

  logout() {
    return from(signOut(this.auth));
  }

  loginWithGoogle() {
    const provider = new GoogleAuthProvider();
    return from(signInWithPopup(this.auth, provider));
  }

   loginWithGitHub() {
    const provider = new GithubAuthProvider();
    return from(signInWithPopup(this.auth, provider));
  }
}
