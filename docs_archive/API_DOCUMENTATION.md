# MagMon API Documentation

## Authentication

### Register User
- **POST** `/api/register`
- **Body**: `{ "username": string, "email": string, "password": string }`
- **Response**: `{ "message": string, "user": { "id": number, "username": string, "email": string } }`

### Login
- **POST** `/api/auth/login`
- **Body**: `{ "username": string, "password": string }`
- **Response**: `{ "access_token": string, "refresh_token": string }`

## Users

### List Users
- **GET** `/api/users`
- **Response**: List of users with basic info and stats
```json
[
  {
    "id": number,
    "username": string,
    "avatar_url": string,
    "stats": {
      "total_wins": number
    }
  }
]
```

### Get User Profile
- **GET** `/api/users/<user_id>`
- **Response**: User's public profile
```json
{
  "id": number,
  "username": string,
  "avatar_url": string,
  "favorite_color": string,
  "retirement_plane": string,
  "stats": {
    "total_wins": number
  }
}
```

### Get User's Decks
- **GET** `/api/users/<user_id>/decks`
- **Response**: List of user's decks
```json
[
  {
    "id": number,
    "name": string,
    "commander": string,
    "colors": string,
    "last_updated": string
  }
]
```

## Profile

### Get Own Profile
- **GET** `/api/profile`
- **Auth**: Required
- **Response**: Full profile details
```json
{
  "id": number,
  "username": string,
  "email": string,
  "avatar_url": string,
  "favorite_color": string,
  "retirement_plane": string,
  "registered_on": string
}
```

### Update Profile
- **PATCH** `/api/profile`
- **Auth**: Required
- **Body**: `{ "favorite_color"?: string, "retirement_plane"?: string }`
- **Response**: Updated profile details

### Upload Avatar
- **POST** `/api/profile/avatar`
- **Auth**: Required
- **Body**: Form data with 'avatar' file
- **Response**: `{ "message": string, "avatar_url": string }`

## Games

### List Games
- **GET** `/api/games`
- **Query Params**:
  - `status`: Filter by game status
  - `date`: Filter by date (YYYY-MM-DD)
- **Response**: List of games with details

### Create Game
- **POST** `/api/games`
- **Auth**: Required
- **Body**:
```json
{
  "game_date": string,
  "is_pauper": boolean,
  "details": string
}
```

### Get Game Details
- **GET** `/api/games/<game_id>`
- **Response**: Full game details with registrations

### Update Game
- **PATCH** `/api/games/<game_id>`
- **Auth**: Admin required
- **Body**: Game update fields

### Delete Game
- **DELETE** `/api/games/<game_id>`
- **Auth**: Admin required

## Decks

### List Decks
- **GET** `/api/decks`
- **Response**: List of all decks

### Create Deck
- **POST** `/api/decks`
- **Auth**: Required
- **Body**:
```json
{
  "name": string,
  "commander": string,
  "colors": string
}
```

### Get Deck Details
- **GET** `/api/decks/<deck_id>`
- **Response**: Full deck details with version history

### Update Deck
- **PATCH** `/api/decks/<deck_id>`
- **Auth**: Required (must be owner)
- **Body**: Deck update fields

### Delete Deck
- **DELETE** `/api/decks/<deck_id>`
- **Auth**: Required (must be owner)

## Error Responses

All endpoints may return the following error responses:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side error

Error response format:
```json
{
  "error": string
}