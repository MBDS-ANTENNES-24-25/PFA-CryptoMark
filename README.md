## PS : Code est sur la branche master


# PFA-CryptoMark

# 🛡️ ImageProtector

**Système Avancé de Filigrane Numérique pour la Protection des Droits d'Auteur d'Images**

ImageProtector est une solution de filigrane robuste et cryptographiquement sécurisée qui intègre des signatures de propriété invisibles dans vos images. Protégez vos actifs numériques avec un chiffrement de niveau militaire et plusieurs techniques d'intégration conçues pour survivre à l'édition, la compression et la distribution non autorisée.

---

## 🌟 Fonctionnalités Principales

### Sécurité Multi-Couches
- **Clés Secrètes Spécifiques à l'Utilisateur**: Chaque utilisateur obtient une clé cryptographique unique pour ses filigranes
- **Chiffrement AES**: Toutes les données du filigrane sont chiffrées avant l'intégration
- **Aléatoire Déterministe**: Votre clé génère le même motif d'extraction à chaque fois
- **Vérification du Hash de Clé**: Confirme que vous utilisez la bonne clé lors de l'extraction

### Quatre Méthodes de Filigrane

1. **Filigrane Invisible (Stéganographie LSB)**
   - Intègre les données dans les bits les moins significatifs des pixels
   - Complètement invisible à l'œil humain
   - Rapide et efficace pour un usage quotidien

2. **Stéganographie Avancée avec Redondance**
   - Intègre chaque bit plusieurs fois pour la correction d'erreurs
   - Résiste à la compression d'image et aux modifications mineures
   - Utilise un vote majoritaire pour une extraction robuste

3. **Filigrane dans le Domaine Fréquentiel**
   - Fonctionne dans l'espace DCT (Transformée en Cosinus Discrète)
   - Résiste à la compression JPEG et aux conversions de format
   - Protection de qualité professionnelle

4. **Filigrane Métadonnées**
   - Intègre les informations de copyright dans les balises EXIF/métadonnées
   - Documentation légale et flux de travail professionnels
   - Facile à vérifier avec des outils standard

### Niveau de Protection Ajustable
- Niveaux de force de 1 à 100
- Force plus élevée = filigrane plus robuste
- Équilibre entre invisibilité et résilience



## 🔒 Comment Ça Fonctionne

### Processus d'Intégration
```
Votre Texte → Métadonnées JSON → Chiffrement AES → Données Binaires → Graine de Clé Utilisateur → Motif de Pixels Aléatoire → Intégration dans l'Image
```

### Processus d'Extraction
```
Image Protégée → Graine de Clé Utilisateur → Même Motif Aléatoire → Extraction Binaire → Déchiffrement AES → Filigrane Original
```

### Modèle de Sécurité
- **Sans votre clé utilisateur**: Impossible de savoir quels pixels contiennent des données
- **Sans clé de chiffrement**: Les données extraites sont du charabia chiffré
- **Avec les deux clés**: Extraction parfaite du filigrane original

---

## 📊 Comparaison des Méthodes

| Caractéristique | LSB | Redondance | Fréquentiel | Métadonnées |
|-----------------|-----|------------|-------------|-------------|
| **Invisibilité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Robustesse** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Vitesse** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Résiste au JPEG** | ❌ | ✅ | ✅✅ | ✅✅ |
| **Résiste à l'Édition** | ❌ | ✅ | ✅✅ | ✅✅ |
| **Difficile à Retirer** | ✅✅ | ✅✅✅ | ✅✅✅✅ | ❌ |

---

## 🎯 Cas d'Usage

### Pour les Photographes
- Protéger les images de portfolio contre le vol
- Tracer l'utilisation non autorisée en ligne
- Prouver la propriété dans les litiges de droits d'auteur

### Pour les Créateurs de Contenu
- Filigraner invisiblement le contenu des réseaux sociaux
- Protéger les mèmes et graphiques contre le repostage
- Maintenir la qualité visuelle tout en sécurisant les droits

### Pour les Entreprises
- Protection de marque sur les canaux numériques
- Suivre la distribution et les fuites d'actifs
- Gestion des droits d'image corporate

### Pour les Artistes
- Protéger les œuvres numériques avant la vente
- Soumissions de galerie avec signatures intégrées
- Authentification NFT et provenance

---

## 🔐 Fonctionnalités de Sécurité

### Composants Cryptographiques
- **Hachage SHA-256** pour la dérivation de clés
- **Chiffrement AES** pour les données du filigrane
- **PRNG déterministe** pour des motifs reproductibles
- **Stockage de hash de clé partiel** pour la vérification

### Résistance aux Attaques
- ✅ Résistant à l'inspection visuelle
- ✅ Résistant à l'analyse statistique (sans clé)
- ✅ Résistant à la compression (modes fréquentiel & redondance)
- ✅ Résistant au recadrage (intégration distribuée)
- ✅ Résistant à la conversion de format

### Protection de la Vie Privée
- Les clés utilisateur ne sont jamais stockées dans les images
- Seulement un hash de clé partiel pour la vérification
- Données de propriété complètes chiffrées
- Aucun suivi ni dépendance externe


## ⚙️ Configuration Avancée

### Directives de Force
- **1-25**: Protection légère, invisibilité maximale
- **26-50**: Équilibré (recommandé pour la plupart des cas)
- **51-75**: Protection forte, résiste à l'édition modérée
- **76-100**: Robustesse maximale, peut introduire des artefacts mineurs

### Choisir une Méthode
- **LSB**: Protection rapide pour distribution non modifiée
- **Redondance**: Réseaux sociaux, sites web, pièces jointes email
- **Fréquentiel**: Photographie professionnelle, documentation légale
- **Métadonnées**: Protection supplémentaire, dissuasion visible


## ⚠️ Notes Importantes

### Gestion des Clés
- **NE PERDEZ JAMAIS votre clé utilisateur** - il est impossible d'extraire les filigranes sans elle
- Stockez les clés en toute sécurité (gestionnaire de mots de passe, coffre-fort chiffré)
- Clés différentes pour différents projets/clients
- Sauvegardez les clés dans plusieurs emplacements sécurisés

### Limitations
- Les filigranes n'empêchent pas les captures d'écran ou photos d'écran
- Les modifications d'image extrêmes peuvent détruire les données intégrées
- Ne remplace pas l'enregistrement légal du droit d'auteur
- Les filigranes de métadonnées sont facilement supprimables par des utilisateurs malveillants

### Bonnes Pratiques
- Utilisez les méthodes de redondance ou fréquentielles pour les images partagées en ligne
- Combinez les méthodes (ex: fréquentiel + métadonnées) pour une protection maximale
- Testez l'extraction sur les versions compressées avant distribution
- Conservez les originaux non filigranés dans un stockage sécurisé

---

**Protégez votre travail. Prouvez votre propriété. Préservez vos droits.**

*CryptoMark - Parce que vos images méritent mieux qu'un filigrane visible.*

# Demo : https://youtu.be/3JVu9oQEQpo
# Team : Asri Mohamed Amine , Baddredine Boufangha , Ayoub Benabdoulwahid , Rzama Hamza
