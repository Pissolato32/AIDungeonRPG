// WebChatRPG Game Client
// Main JavaScript file for handling game UI interactions and API calls

document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements
    const gameOutput = document.getElementById('gameOutput');
    const messagesContainer = document.getElementById('messagesContainer');
    const actionForm = document.getElementById('actionForm');
    const actionType = document.getElementById('actionType');
    const actionDetails = document.getElementById('actionDetails');
    const combatInterface = document.getElementById('combatInterface');
    const combatLog = document.getElementById('combatLog');
    const enemyName = document.getElementById('enemyName');
    const enemyHp = document.getElementById('enemyHp');
    const enemyMaxHp = document.getElementById('enemyMaxHp');
    const enemyHpBar = document.getElementById('enemyHpBar');
    const enemyDescription = document.getElementById('enemyDescription');
    const resetGameBtn = document.getElementById('resetGameBtn');
    const confirmResetBtn = document.getElementById('confirmResetBtn');
    const resetGameModal = new bootstrap.Modal(document.getElementById('resetGameModal'));
    const hpDisplay = document.getElementById('hpDisplay');
    const hpBar = document.getElementById('hpBar');
    const staminaDisplay = document.getElementById('staminaDisplay');
    const staminaBar = document.getElementById('staminaBar');
    const inventoryList = document.getElementById('inventoryList');
    const restButton = document.getElementById('restButton');
    
    // Combat buttons
    const attackBasic = document.getElementById('attackBasic');
    const attackLight = document.getElementById('attackLight');
    const attackHeavy = document.getElementById('attackHeavy');
    const fleeButton = document.getElementById('fleeButton');
    
    // Game state variables
    let inCombat = combatInterface && !combatInterface.classList.contains('d-none');
    
    // Scroll messages to bottom on load
    scrollMessagesToBottom();
    
    // Event Listeners
    
    // Action Form Submission
    if (actionForm) {
        actionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const action = actionType.value;
            const details = actionDetails.value.trim();
            
            // Custom action handling
            if (action === 'custom' && details) {
                const [customAction, ...customDetails] = details.split(' ');
                performAction(customAction, customDetails.join(' '));
            } else if (details || action === 'search') {
                performAction(action, details);
            } else {
                addMessage("Please provide details for your action.");
            }
            
            // Clear input field
            actionDetails.value = '';
        });
    }
    
    // Use Item Buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('use-item-btn')) {
            const item = e.target.getAttribute('data-item');
            useItem(item);
        }
    });
    
    // Combat Attack Buttons
    if (attackBasic) {
        attackBasic.addEventListener('click', function() {
            performCombatAttack('basic');
        });
    }
    
    if (attackLight) {
        attackLight.addEventListener('click', function() {
            performCombatAttack('light');
        });
    }
    
    if (attackHeavy) {
        attackHeavy.addEventListener('click', function() {
            performCombatAttack('heavy');
        });
    }
    
    // Flee Button
    if (fleeButton) {
        fleeButton.addEventListener('click', function() {
            performAction('flee', '');
        });
    }
    
    // Rest Button
    if (restButton) {
        restButton.addEventListener('click', function() {
            rest();
        });
    }
    
    // Reset Game Button
    if (resetGameBtn) {
        resetGameBtn.addEventListener('click', function() {
            resetGameModal.show();
        });
    }
    
    // Confirm Reset Button
    if (confirmResetBtn) {
        confirmResetBtn.addEventListener('click', function() {
            resetGame();
            resetGameModal.hide();
        });
    }
    
    // API Functions
    
    /**
     * Perform a game action via API
     * @param {string} action - The type of action to perform
     * @param {string} details - Additional details for the action
     */
    function performAction(action, details) {
        // Show loading state
        addMessage(`<em>Performing action: ${action} ${details}...</em>`, true);
        
        fetch('/api/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: action,
                details: details
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading message
            removeLastMessage();
            
            // Handle response based on action success
            if (data.success) {
                // Add the message from the response
                addMessage(data.message);
                
                // Check if combat was initiated
                if (data.combat_started) {
                    startCombat(data.enemy);
                }
                
                // Update character stats if they changed
                updateCharacterStats();
                
                // Update inventory if needed
                if (data.effects && (data.effects.items_gained || data.effects.items_lost)) {
                    updateInventory();
                }
            } else {
                // Show error message
                addMessage(`<span class="text-warning">${data.message}</span>`);
            }
            
            // Scroll messages to bottom
            scrollMessagesToBottom();
        })
        .catch(error => {
            console.error('Error performing action:', error);
            removeLastMessage();
            addMessage(`<span class="text-danger">Error: Could not perform action. ${error.message}</span>`);
            scrollMessagesToBottom();
        });
    }
    
    /**
     * Perform a combat attack
     * @param {string} attackType - The type of attack (basic, light, heavy)
     */
    function performCombatAttack(attackType) {
        if (!inCombat) return;
        
        // Disable attack buttons during the request
        setAttackButtonsEnabled(false);
        
        fetch('/api/combat/attack', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                attack_type: attackType
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update combat log
                addCombatLogEntry(data.message);
                
                // Update enemy HP
                updateEnemyHealth(data.enemy_hp_after, data.enemy_hp_before);
                
                // Handle enemy counter-attack
                if (data.enemy_attack) {
                    addCombatLogEntry(data.enemy_attack);
                }
                
                // Update player HP and stamina
                updateCharacterStats();
                
                // Check if combat is over
                if (data.combat_over) {
                    if (data.victory) {
                        // Player won the combat
                        handleCombatVictory(data);
                    } else {
                        // Player lost the combat
                        handleCombatDefeat();
                    }
                }
            } else {
                // Attack failed (e.g., not enough stamina)
                addCombatLogEntry(`<span class="text-warning">${data.message}</span>`);
            }
            
            // Re-enable attack buttons
            setAttackButtonsEnabled(true);
        })
        .catch(error => {
            console.error('Error performing attack:', error);
            addCombatLogEntry(`<span class="text-danger">Error: Could not perform attack. ${error.message}</span>`);
            setAttackButtonsEnabled(true);
        });
    }
    
    /**
     * Use an item from inventory
     * @param {string} item - The name of the item to use
     */
    function useItem(item) {
        fetch('/api/use-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item: item
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Show message
                if (inCombat) {
                    addCombatLogEntry(data.message);
                } else {
                    addMessage(data.message);
                }
                
                // Update character stats
                updateCharacterStats();
                
                // Update inventory (item was consumed)
                updateInventory();
            } else {
                // Use failed
                const errorMessage = `<span class="text-warning">${data.message}</span>`;
                if (inCombat) {
                    addCombatLogEntry(errorMessage);
                } else {
                    addMessage(errorMessage);
                }
            }
        })
        .catch(error => {
            console.error('Error using item:', error);
            const errorMessage = `<span class="text-danger">Error: Could not use item. ${error.message}</span>`;
            if (inCombat) {
                addCombatLogEntry(errorMessage);
            } else {
                addMessage(errorMessage);
            }
        });
    }
    
    /**
     * Rest to recover HP and stamina
     */
    function rest() {
        if (inCombat) {
            addMessage("<span class='text-warning'>You cannot rest while in combat!</span>");
            return;
        }
        
        fetch('/api/rest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Show message
                addMessage(data.message);
                
                // Update character stats
                updateCharacterStats();
            } else {
                // Rest failed
                addMessage(`<span class="text-warning">${data.message}</span>`);
            }
        })
        .catch(error => {
            console.error('Error resting:', error);
            addMessage(`<span class="text-danger">Error: Could not rest. ${error.message}</span>`);
        });
    }
    
    /**
     * Reset the game (delete character and game state)
     */
    function resetGame() {
        fetch('/api/reset-game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Redirect to character creation
                window.location.href = '/character';
            } else {
                addMessage(`<span class="text-warning">${data.message}</span>`);
            }
        })
        .catch(error => {
            console.error('Error resetting game:', error);
            addMessage(`<span class="text-danger">Error: Could not reset game. ${error.message}</span>`);
        });
    }
    
    /**
     * Get updated character stats
     */
    function updateCharacterStats() {
        fetch('/character', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.redirected) {
                // If redirected, character might be missing, reload the page
                window.location.reload();
                return null;
            }
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.character) {
                // Update HP display and bar
                const character = data.character;
                if (hpDisplay && hpBar) {
                    const hpPercent = (character.current_hp / character.max_hp) * 100;
                    hpDisplay.textContent = `${character.current_hp} / ${character.max_hp}`;
                    hpBar.style.width = `${hpPercent}%`;
                    hpBar.setAttribute('aria-valuenow', character.current_hp);
                    hpBar.setAttribute('aria-valuemax', character.max_hp);
                }
                
                // Update stamina display and bar
                if (staminaDisplay && staminaBar) {
                    const staminaPercent = (character.current_stamina / character.max_stamina) * 100;
                    staminaDisplay.textContent = `${character.current_stamina} / ${character.max_stamina}`;
                    staminaBar.style.width = `${staminaPercent}%`;
                    staminaBar.setAttribute('aria-valuenow', character.current_stamina);
                    staminaBar.setAttribute('aria-valuemax', character.max_stamina);
                }
            }
        })
        .catch(error => {
            console.error('Error updating character stats:', error);
        });
    }
    
    /**
     * Update inventory display
     */
    function updateInventory() {
        if (!inventoryList) return;
        
        fetch('/character', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data && data.character && data.character.inventory) {
                // Clear current inventory
                inventoryList.innerHTML = '';
                
                // Add each item
                data.character.inventory.forEach(item => {
                    const itemElement = document.createElement('div');
                    itemElement.className = 'list-group-item d-flex justify-content-between align-items-center';
                    itemElement.innerHTML = `
                        <span>${item}</span>
                        <button class="btn btn-sm btn-outline-primary use-item-btn" data-item="${item}">Use</button>
                    `;
                    inventoryList.appendChild(itemElement);
                });
                
                // If inventory is empty
                if (data.character.inventory.length === 0) {
                    inventoryList.innerHTML = `
                        <div class="text-center text-secondary p-3">
                            <i class="bi bi-inbox-fill fs-4"></i>
                            <p class="mt-2">Your inventory is empty</p>
                        </div>
                    `;
                }
                
                // Update gold display
                const goldDisplays = document.querySelectorAll('.gold-display');
                goldDisplays.forEach(display => {
                    display.textContent = data.character.gold;
                });
            }
        })
        .catch(error => {
            console.error('Error updating inventory:', error);
        });
    }
    
    // Helper Functions
    
    /**
     * Add a message to the game output
     * @param {string} message - The message to display
     * @param {boolean} isTemp - Whether this is a temporary message
     */
    function addMessage(message, isTemp = false) {
        if (!messagesContainer) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = 'message';
        if (isTemp) messageEl.className += ' temp-message';
        messageEl.innerHTML = message;
        messagesContainer.appendChild(messageEl);
        scrollMessagesToBottom();
    }
    
    /**
     * Remove the last message (used for loading indicators)
     */
    function removeLastMessage() {
        if (!messagesContainer) return;
        
        const tempMessages = messagesContainer.querySelectorAll('.temp-message');
        if (tempMessages.length > 0) {
            tempMessages[tempMessages.length - 1].remove();
        }
    }
    
    /**
     * Add an entry to the combat log
     * @param {string} entry - The log entry to add
     */
    function addCombatLogEntry(entry) {
        if (!combatLog) return;
        
        const logEntry = document.createElement('div');
        logEntry.innerHTML = entry;
        combatLog.appendChild(logEntry);
        combatLog.scrollTop = combatLog.scrollHeight;
    }
    
    /**
     * Start combat with a new enemy
     * @param {Object} enemy - The enemy data
     */
    function startCombat(enemy) {
        if (!combatInterface || !actionForm) return;
        
        inCombat = true;
        
        // Update enemy display
        if (enemyName) enemyName.textContent = enemy.name;
        if (enemyHp) enemyHp.textContent = enemy.current_hp;
        if (enemyMaxHp) enemyMaxHp.textContent = enemy.max_hp;
        if (enemyDescription) enemyDescription.textContent = enemy.description;
        
        // Update HP bar
        if (enemyHpBar) {
            const hpPercent = (enemy.current_hp / enemy.max_hp) * 100;
            enemyHpBar.style.width = `${hpPercent}%`;
            enemyHpBar.setAttribute('aria-valuenow', enemy.current_hp);
            enemyHpBar.setAttribute('aria-valuemax', enemy.max_hp);
        }
        
        // Show combat interface, hide action form
        combatInterface.classList.remove('d-none');
        actionForm.classList.add('d-none');
        
        // Clear previous combat log
        if (combatLog) combatLog.innerHTML = '';
        
        // Add initial combat message
        addCombatLogEntry(`Combat started with ${enemy.name}!`);
    }
    
    /**
     * Update enemy health display
     * @param {number} newHp - The new HP value
     * @param {number} oldHp - The previous HP value
     */
    function updateEnemyHealth(newHp, oldHp) {
        if (!enemyHp || !enemyHpBar || !enemyName) return;
        
        // Animate HP reduction
        const hpReduction = oldHp - newHp;
        if (hpReduction > 0) {
            // Create damage number
            const damageEl = document.createElement('span');
            damageEl.className = 'damage-number';
            damageEl.textContent = `-${hpReduction}`;
            enemyName.parentNode.appendChild(damageEl);
            
            // Remove after animation
            setTimeout(() => {
                damageEl.remove();
            }, 1000);
        }
        
        // Update HP text
        enemyHp.textContent = newHp;
        
        // Update HP bar
        if (enemyMaxHp) {
            const maxHp = parseInt(enemyMaxHp.textContent);
            const hpPercent = (newHp / maxHp) * 100;
            enemyHpBar.style.width = `${hpPercent}%`;
            enemyHpBar.setAttribute('aria-valuenow', newHp);
        }
    }
    
    /**
     * Handle victory in combat
     * @param {Object} data - Combat result data
     */
    function handleCombatVictory(data) {
        if (!combatInterface || !actionForm) return;
        
        // End combat mode
        inCombat = false;
        
        // Hide combat interface, show action form
        setTimeout(() => {
            combatInterface.classList.add('d-none');
            actionForm.classList.remove('d-none');
        }, 1500);
        
        // Display rewards
        if (data.rewards) {
            let rewardMessage = "<strong>Combat Rewards:</strong><br>";
            
            if (data.rewards.experience) {
                rewardMessage += `+${data.rewards.experience} XP<br>`;
            }
            
            if (data.rewards.gold) {
                rewardMessage += `+${data.rewards.gold} Gold<br>`;
            }
            
            if (data.rewards.loot && data.rewards.loot.length > 0) {
                rewardMessage += `Items: ${data.rewards.loot.join(', ')}<br>`;
            }
            
            if (data.rewards.level_up) {
                rewardMessage += `<strong class="text-success">You leveled up!</strong><br>`;
            }
            
            addMessage(rewardMessage);
        }
    }
    
    /**
     * Handle defeat in combat
     */
    function handleCombatDefeat() {
        if (!combatInterface || !actionForm) return;
        
        // End combat mode
        inCombat = false;
        
        // Hide combat interface, show action form
        setTimeout(() => {
            combatInterface.classList.add('d-none');
            actionForm.classList.remove('d-none');
        }, 1500);
        
        // Display defeat message
        addMessage('<span class="text-danger"><strong>You were defeated!</strong> You have been revived with a portion of your health.</span>');
    }
    
    /**
     * Enable or disable attack buttons
     * @param {boolean} enabled - Whether the buttons should be enabled
     */
    function setAttackButtonsEnabled(enabled) {
        if (attackBasic) attackBasic.disabled = !enabled;
        if (attackLight) attackLight.disabled = !enabled;
        if (attackHeavy) attackHeavy.disabled = !enabled;
        if (fleeButton) fleeButton.disabled = !enabled;
    }
    
    /**
     * Scroll the messages container to the bottom
     */
    function scrollMessagesToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    // Initialize the game by checking for important elements
    function initializeGame() {
        // Add some CSS for damage numbers
        const style = document.createElement('style');
        style.textContent = `
            .damage-number {
                position: absolute;
                color: #ff4444;
                font-weight: bold;
                animation: damage-float 1s ease-out;
                opacity: 0;
            }
            
            @keyframes damage-float {
                0% { transform: translateY(0); opacity: 1; }
                100% { transform: translateY(-20px); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
        
        // Check if we need to update character stats and inventory on load
        if (hpDisplay && staminaDisplay) {
            updateCharacterStats();
        }
        
        if (inventoryList) {
            updateInventory();
        }
    }
    
    // Initialize the game
    initializeGame();
});
