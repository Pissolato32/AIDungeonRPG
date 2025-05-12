import json
import os
from datetime import datetime

class Character:
    """Character model representing player character attributes and methods"""
    
    def __init__(self, name, character_class, race, 
                 strength=10, dexterity=10, constitution=10, 
                 intelligence=10, wisdom=10, charisma=10,
                 max_hp=20, current_hp=20, max_stamina=10, current_stamina=10,
                 max_hunger=100, current_hunger=100, max_thirst=100, current_thirst=100,
                 inventory=None, gold=50, experience=0, level=1):
        
        self.name = name
        self.character_class = character_class
        self.race = race
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelligence = intelligence
        self.wisdom = wisdom
        self.charisma = charisma
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.max_stamina = max_stamina
        self.current_stamina = current_stamina
        self.inventory = inventory or ["Basic Sword", "Health Potion"]
        self.max_hunger = max_hunger
        self.current_hunger = current_hunger
        self.max_thirst = max_thirst
        self.current_thirst = current_thirst
        self.gold = gold
        self.experience = experience
        self.level = level
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert character to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "class": self.character_class,
            "race": self.race,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "constitution": self.constitution,
            "intelligence": self.intelligence,
            "wisdom": self.wisdom,
            "charisma": self.charisma,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "max_stamina": self.max_stamina,
            "current_stamina": self.current_stamina,
            "max_hunger": self.max_hunger,
            "current_hunger": self.current_hunger,
            "max_thirst": self.max_thirst,
            "current_thirst": self.current_thirst,
            "inventory": self.inventory,
            "gold": self.gold,
            "experience": self.experience,
            "level": self.level,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create character from dictionary"""
        if not data:
            return None
            
        character = cls(
            name=data.get("name", "Unknown"),
            character_class=data.get("class", "Fighter"),
            race=data.get("race", "Human"),
            strength=data.get("strength", 10),
            dexterity=data.get("dexterity", 10),
            constitution=data.get("constitution", 10),
            intelligence=data.get("intelligence", 10),
            wisdom=data.get("wisdom", 10),
            charisma=data.get("charisma", 10),
            max_hp=data.get("max_hp", 20),
            current_hp=data.get("current_hp", 20),
            max_stamina=data.get("max_stamina", 10),
            current_stamina=data.get("current_stamina", 10),
            inventory=data.get("inventory", ["Basic Sword", "Health Potion"]),
            gold=data.get("gold", 50),
            experience=data.get("experience", 0),
            level=data.get("level", 1)
        )
        
        character.last_updated = data.get("last_updated", datetime.now().isoformat())
        return character
    
    def take_damage(self, amount):
        """Apply damage to character"""
        self.current_hp = max(0, self.current_hp - amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_hp
    
    def heal(self, amount):
        """Heal character"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_hp
    
    def use_stamina(self, amount):
        """Use stamina for actions"""
        if self.current_stamina < amount:
            return False
        
        self.current_stamina -= amount
        self.last_updated = datetime.now().isoformat()
        return True
    
    def recover_stamina(self, amount):
        """Recover stamina"""
        self.current_stamina = min(self.max_stamina, self.current_stamina + amount)
        self.last_updated = datetime.now().isoformat()
        return self.current_stamina
    
    def add_to_inventory(self, item):
        """Add item to inventory"""
        self.inventory.append(item)
        self.last_updated = datetime.now().isoformat()
    
    def remove_from_inventory(self, item):
        """Remove item from inventory"""
        if item in self.inventory:
            self.inventory.remove(item)
            self.last_updated = datetime.now().isoformat()
            return True
        return False
    
    def add_experience(self, amount):
        """Add experience points and handle level up"""
        self.experience += amount
        
        # Simple leveling logic: 100 * current level = XP needed for next level
        xp_for_next_level = 100 * self.level
        
        if self.experience >= xp_for_next_level:
            self.level_up()
        
        self.last_updated = datetime.now().isoformat()
    
    def level_up(self):
        """Level up character, increasing stats"""
        self.level += 1
        
        # Increase HP and stamina
        hp_increase = 5 + (self.constitution // 3)
        stamina_increase = 2 + (self.constitution // 5)
        
        self.max_hp += hp_increase
        self.current_hp = self.max_hp
        self.max_stamina += stamina_increase
        self.current_stamina = self.max_stamina
        
        self.last_updated = datetime.now().isoformat()
        return {
            "new_level": self.level,
            "hp_increase": hp_increase,
            "stamina_increase": stamina_increase
        }

class Enemy:
    """Enemy model representing NPCs and monsters in combat"""
    
    def __init__(self, name, description, level=1, max_hp=10, current_hp=10, 
                 attack_damage=(1, 6), defense=0, experience_reward=25, 
                 gold_reward=(5, 15), loot_table=None):
        
        self.name = name
        self.description = description
        self.level = level
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.attack_damage = attack_damage  # Tuple of (min_damage, max_damage)
        self.defense = defense
        self.experience_reward = experience_reward
        self.gold_reward = gold_reward  # Tuple of (min_gold, max_gold)
        self.loot_table = loot_table or []
    
    def to_dict(self):
        """Convert enemy to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "max_hp": self.max_hp,
            "current_hp": self.current_hp,
            "attack_damage": self.attack_damage,
            "defense": self.defense,
            "experience_reward": self.experience_reward,
            "gold_reward": self.gold_reward,
            "loot_table": self.loot_table
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create enemy from dictionary"""
        if not data:
            return None
            
        return cls(
            name=data.get("name", "Unknown Enemy"),
            description=data.get("description", "A mysterious creature"),
            level=data.get("level", 1),
            max_hp=data.get("max_hp", 10),
            current_hp=data.get("current_hp", 10),
            attack_damage=data.get("attack_damage", (1, 6)),
            defense=data.get("defense", 0),
            experience_reward=data.get("experience_reward", 25),
            gold_reward=data.get("gold_reward", (5, 15)),
            loot_table=data.get("loot_table", [])
        )
    
    def take_damage(self, amount):
        """Apply damage to enemy"""
        damage_after_defense = max(1, amount - self.defense)
        self.current_hp = max(0, self.current_hp - damage_after_defense)
        return self.current_hp, damage_after_defense
    
    def is_defeated(self):
        """Check if enemy is defeated"""
        return self.current_hp <= 0
