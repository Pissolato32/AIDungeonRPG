# WebChatRPG Game Data Directory

This directory stores the game data files for WebChatRPG, including:

- Character data files (`character_[user_id].json`)
- Game state files (`game_state_[user_id].json`)

## Data Structure

### Character Data
Character data is stored in JSON format with the following structure:
```json
{
  "name": "Character Name",
  "class": "Warrior",
  "race": "Human",
  "strength": 10,
  "dexterity": 10,
  "constitution": 10,
  "intelligence": 10,
  "wisdom": 10,
  "charisma": 10,
  "max_hp": 20,
  "current_hp": 20,
  "max_stamina": 10,
  "current_stamina": 10,
  "inventory": ["Basic Sword", "Health Potion"],
  "gold": 50,
  "experience": 0,
  "level": 1,
  "last_updated": "2023-08-01T12:00:00.000Z"
}
