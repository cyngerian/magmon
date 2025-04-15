# Deck Versioning Feature

## Overview

The deck versioning feature allows users to track changes to their decks over time. Each deck can have multiple versions, and each version represents a snapshot of the deck at a specific point in time. This is useful for tracking the evolution of a deck, as well as for preserving the exact state of a deck when it was used in a game.

## Key Concepts

- **Deck**: A deck represents a Magic: The Gathering Commander deck, with a name, commander, colors, and a decklist.
- **Deck Version**: A version of a deck, with a version number, decklist, and notes about the changes made in this version.
- **Current Version**: Each deck has a "current version" which is the most recent version of the deck.

## Database Schema

The following database tables are used to implement deck versioning:

- **decks**: Stores basic information about a deck, including a reference to the current version.
- **deck_versions**: Stores versions of a deck, including the decklist and notes for each version.
- **game_registrations**: Links a user, deck, and game, and now includes a reference to the specific version of the deck used.
- **match_players**: Records a player's participation in a match, and now includes a reference to the specific version of the deck used.

## API Endpoints

The following API endpoints are available for working with deck versions:

- `GET /decks/{deck_id}/versions`: Get a list of all versions for a deck.
- `GET /decks/{deck_id}/versions/{version_id}`: Get details for a specific version of a deck.
- `POST /decks/{deck_id}/versions`: Create a new version of a deck.

## Usage

### Creating a New Deck

When a new deck is created, an initial version (version 1) is automatically created with the same decklist as the deck.

### Creating a New Version

To create a new version of a deck, send a POST request to `/decks/{deck_id}/versions` with the following JSON body:

```json
{
  "decklist_text": "Updated decklist...",
  "notes": "Notes about the changes made in this version..."
}
```

The new version will be assigned the next available version number for the deck, and will become the current version.

### Registering for a Game

When registering for a game, you can optionally specify a specific version of the deck to use. If no version is specified, the current version will be used.

### Submitting Match Results

When submitting match results, the specific version of the deck used by each player is recorded. This allows for accurate tracking of which version of a deck was used in a particular match.

## Benefits

- **Historical Record**: Keep track of how your decks have evolved over time.
- **Game Integrity**: Ensure that the exact version of a deck used in a game is recorded, even if the deck is later modified.
- **Analysis**: Analyze the performance of different versions of a deck to identify effective changes.
