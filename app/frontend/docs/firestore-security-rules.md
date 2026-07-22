# Firestore Security Rules for Dating App

## Overview
These security rules ensure that users can only access and modify their own dating profiles and preferences while allowing read access to public profile information for matching purposes.

## Rules Configuration

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Dating Profiles - public read, private write
    match /datingProfiles/{userId} {
      allow read: if true; // Allow anyone to read profiles for matching
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // User Preferences - private read/write
    match /userPreferences/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Matches - private to users involved
    match /matches/{matchId} {
      allow read, write: if request.auth != null && 
        (resource.data.user1 == request.auth.uid || 
         resource.data.user2 == request.auth.uid);
    }
    
    // Likes - write only, read for own likes
    match /likes/{likeId} {
      allow read: if request.auth != null && resource.data.fromUser == request.auth.uid;
      allow create: if request.auth != null && request.auth.uid == resource.data.fromUser;
      allow delete: if request.auth != null && request.auth.uid == resource.data.fromUser;
    }
    
    // Passes - write only, read for own passes
    match /passes/{passId} {
      allow read: if request.auth != null && resource.data.fromUser == request.auth.uid;
      allow create: if request.auth != null && request.auth.uid == resource.data.fromUser;
      allow delete: if request.auth != null && request.auth.uid == resource.data.fromUser;
    }
  }
}
```

## Collections Structure

### datingProfiles
```typescript
{
  uid: string;
  displayName: string;
  age: number;
  bio: string;
  location: string;
  interests: string[];
  lookingFor: 'friendship' | 'dating' | 'serious' | 'casual';
  genderIdentity: string;
  genderPreference: string[];
  photos: string[];
  verified: boolean;
  lastActive: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

### userPreferences
```typescript
{
  ageRange: { min: number; max: number };
  maxDistance: number;
  genderPreference: string[];
  lookingFor: string[];
}
```

### matches
```typescript
{
  user1: string;
  user2: string;
  matchedAt: Date;
  conversationId?: string;
}
```

### likes
```typescript
{
  fromUser: string;
  toUser: string;
  likedAt: Date;
}
```

### passes
```typescript
{
  fromUser: string;
  toUser: string;
  passedAt: Date;
}
```

## Installation Instructions

1. Go to the Firebase Console
2. Navigate to Firestore Database
3. Click on "Rules" tab
4. Replace the existing rules with the rules above
5. Click "Publish"

## Security Features

- **Profile Privacy**: Users can only edit their own profiles
- **Preference Privacy**: Only the user can see their own preferences
- **Match Privacy**: Only matched users can see their match data
- **Public Discovery**: All users can read basic profile info for matching
- **Audit Trail**: All likes and passes are tracked with timestamps
