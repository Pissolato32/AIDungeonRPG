// static/js/game.js

/**
 * Game UI Manager - Handles all UI updates and interactions
 */
class GameUIManager {
    constructor() {
        this.API_ENDPOINT = '/api/action';
        this.RESET_ENDPOINT = '/api/reset';
        this.initializeEventListeners();
        this.updateProgressBars();
        this.isProcessing = false;
        this.addAttackButton();
    }

    /**
     * Initialize all event listeners
     */
    initializeEventListeners() {
        // Set up MutationObservers to watch for changes
        this.setupMutationObservers();
        
        // Set up form submission handler
        this.setupActionForm();
        
        // Set up combat buttons
        this.setupCombatButtons();
        
        // Set up rest button
        this.setupRestButton();
        
        // Set up use item buttons
        this.setupUseItemButtons();
        
        // Set up reset game button
        this.setupResetGameButton();
    }

    /**
     * Add attack button to the UI
     */
    addAttackButton() {
        const actionTypeSelect = document.getElementById('actionType');
        if (actionTypeSelect) {
            // Check if attack option already exists
            let attackExists = false;
            for (let i = 0; i < actionTypeSelect.options.length; i++) {
                if (actionTypeSelect.options[i].value === 'attack') {
                    attackExists = true;
                    break;
                }
            }
            
            // Add attack option if it doesn't exist
            if (!attackExists) {
                const attackOption = document.createElement('option');
                attackOption.value = 'attack';
                attackOption.textContent = 'Attack';
                actionTypeSelect.appendChild(attackOption);
            }
        }
    }

    /**
     * Update all progress bars on the page
     */
    updateProgressBars() {
        this.updateEnemyHpBar();
        this.updateCharacterBars();
    }

    /**
     * Update enemy HP bar based on current values
     */
    updateEnemyHpBar() {
        const enemyHpBar = document.getElementById('enemyHpBar');
        const enemyHp = document.getElementById('enemyHp');
        const enemyMaxHp = document.getElementById('enemyMaxHp');
        
        if (enemyHpBar && enemyHp && enemyMaxHp) {
            const currentHp = parseInt(enemyHp.textContent) || 0;
            const maxHp = parseInt(enemyMaxHp.textContent) || 1;
            
            if (maxHp > 0) {
                const percentage = (currentHp / maxHp * 100).toFixed(1);
                enemyHpBar.style.width = percentage + '%';
            } else {
                enemyHpBar.style.width = '0%';
            }
        }
    }

    /**
     * Update all character progress bars based on data attributes
     */
    updateCharacterBars() {
        // Update all bars that have data-width attribute
        const progressBars = {
            exp: document.querySelector('.progress-bar.bg-info'),
            hp: document.getElementById('hpBar'),
            stamina: document.getElementById('staminaBar'),
            hunger: document.getElementById('hungerBar'),
            thirst: document.getElementById('thirstBar')
        };
        
        for (const [key, bar] of Object.entries(progressBars)) {
            if (bar?.dataset.width) {
                bar.style.width = bar.dataset.width + '%';
            }
        }
    }

    /**
     * Set up mutation observers to watch for dynamic content changes
     */
    setupMutationObservers() {
        const enemyHp = document.getElementById('enemyHp');
        if (enemyHp) {
            const observer = new MutationObserver(() => this.updateEnemyHpBar());
            observer.observe(enemyHp, { childList: true, characterData: true, subtree: true });
        }
    }

    /**
     * Set up the action form submission handler
     */
    setupActionForm() {
        const actionForm = document.getElementById('actionForm');
        if (!actionForm) return;
        
        actionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            if (this.isProcessing) return; // Prevent multiple submissions
            
            const actionTypeElement = document.querySelector('#actionType');
            if (!actionTypeElement) {
                console.error('Action type element not found');
                return;
            }
            
            const actionType = actionTypeElement.value;
            const actionDetailsElement = document.getElementById('actionDetails');
            const actionDetails = actionDetailsElement.value;
            
            if (!actionDetails.trim()) {
                alert('Please enter details for your action');
                return;
            }
            
            // Show loading state
            this.isProcessing = true;
            const submitButton = actionForm.querySelector('button[type="submit"]');
            const originalButtonContent = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
            
            // Add player's action to the message container
            this.addPlayerMessage(`${actionType}: ${actionDetails}`);
            
            // Show "thinking" indicator
            this.showThinkingIndicator();
            
            // Send action to server
            this.sendGameAction(
                actionType, 
                actionDetails,
                (data) => {
                    // Remove thinking indicator
                    this.removeThinkingIndicator();
                    
                    // Reset form
                    actionDetailsElement.value = '';
                    
                    // Reset button state
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonContent;
                    this.isProcessing = false;
                    
                    // Handle the response
                    this.handleActionResponse(data);
                },
                (error) => {
                    // Remove thinking indicator
                    this.removeThinkingIndicator();
                    
                    // Reset button state
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonContent;
                    this.isProcessing = false;
                    
                    // Display error message
                    this.displayErrorMessage('An error occurred while processing your action. Please try again.');
                }
            );
        });
    }

    /**
     * Add player's message to the chat
     * @param {string} message - The player's action message
     */
    addPlayerMessage(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message player-message';
        messageDiv.innerHTML = `<strong>You:</strong> ${message}`;
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to the bottom of the messages container
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Show "thinking" indicator in the chat
     */
    showThinkingIndicator() {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message thinking-indicator';
        thinkingDiv.innerHTML = '<strong>Game Master:</strong> <span class="thinking-dots">...</span>';
        thinkingDiv.id = 'thinkingIndicator';
        messagesContainer.appendChild(thinkingDiv);
        
        // Animate the dots
        const dots = thinkingDiv.querySelector('.thinking-dots');
        let count = 0;
        this.thinkingInterval = setInterval(() => {
            count = (count + 1) % 4;
            dots.textContent = '.'.repeat(count || 3);
        }, 500);
        
        // Scroll to the bottom of the messages container
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Remove "thinking" indicator from the chat
     */
    removeThinkingIndicator() {
        clearInterval(this.thinkingInterval);
        const thinkingIndicator = document.getElementById('thinkingIndicator');
        if (thinkingIndicator) {
            thinkingIndicator.remove();
        }
    }

    /**
     * Set up combat button event listeners
     */
    setupCombatButtons() {
        const combatButtons = document.querySelectorAll('#attackBasic, #attackLight, #attackHeavy, #fleeButton');
        combatButtons.forEach(button => {
            button.addEventListener('click', () => {
                const action = button.id === 'fleeButton' ? 'flee' : 'attack';
                const details = button.id === 'attackBasic' ? 'basic' : 
                               button.id === 'attackLight' ? 'light' : 
                               button.id === 'attackHeavy' ? 'heavy' : '';
                
                // Add player's action to the message container
                this.addPlayerMessage(`${action}: ${details}`);
                
                // Show "thinking" indicator
                this.showThinkingIndicator();
                
                // Disable all combat buttons
                combatButtons.forEach(btn => btn.disabled = true);
                
                // Send action to server
                this.sendGameAction(
                    action, 
                    details,
                    () => {
                        // Remove thinking indicator
                        this.removeThinkingIndicator();
                        
                        // Reload page to update game state
                        window.location.reload();
                    },
                    () => {
                        // Remove thinking indicator
                        this.removeThinkingIndicator();
                        
                        // Re-enable combat buttons
                        combatButtons.forEach(btn => btn.disabled = false);
                    }
                );
            });
        });
    }

    /**
     * Set up rest button event listener
     */
    setupRestButton() {
        const restButton = document.getElementById('restButton');
        if (!restButton) return;
        
        restButton.addEventListener('click', () => {
            // Add player's action to the message container
            this.addPlayerMessage('rest');
            
            // Show "thinking" indicator
            this.showThinkingIndicator();
            
            // Disable button
            restButton.disabled = true;
            
            // Send rest action to server
            this.sendGameAction(
                'rest', 
                '',
                () => {
                    // Remove thinking indicator
                    this.removeThinkingIndicator();
                    
                    // Reload page to update game state
                    window.location.reload();
                },
                () => {
                    // Remove thinking indicator
                    this.removeThinkingIndicator();
                    
                    // Re-enable button
                    restButton.disabled = false;
                }
            );
        });
    }

    /**
     * Set up use item button event listeners
     */
    setupUseItemButtons() {
        const useItemButtons = document.querySelectorAll('.use-item-btn');
        useItemButtons.forEach(button => {
            button.addEventListener('click', () => {
                const item = button.getAttribute('data-item');
                
                // Add player's action to the message container
                this.addPlayerMessage(`use item: ${item}`);
                
                // Show "thinking" indicator
                this.showThinkingIndicator();
                
                // Disable all use item buttons
                useItemButtons.forEach(btn => btn.disabled = true);
                
                // Send use item action to server
                this.sendGameAction(
                    'use_item', 
                    item,
                    () => {
                        // Remove thinking indicator
                        this.removeThinkingIndicator();
                        
                        // Reload page to update game state
                        window.location.reload();
                    },
                    () => {
                        // Remove thinking indicator
                        this.removeThinkingIndicator();
                        
                        // Re-enable use item buttons
                        useItemButtons.forEach(btn => btn.disabled = false);
                    }
                );
            });
        });
    }

    /**
     * Set up reset game button event listeners
     */
    setupResetGameButton() {
        const resetGameBtn = document.getElementById('resetGameBtn');
        const confirmResetBtn = document.getElementById('confirmResetBtn');
        
        if (!resetGameBtn || !confirmResetBtn) return;
        
        resetGameBtn.addEventListener('click', () => {
            // Show confirmation modal
            const resetModal = new bootstrap.Modal(document.getElementById('resetGameModal'));
            resetModal.show();
        });
        
        confirmResetBtn.addEventListener('click', () => {
            // Disable button
            confirmResetBtn.disabled = true;
            confirmResetBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Resetting...';
            
            // Send reset action to server
            fetch(this.RESET_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(() => {
                // Redirect to character creation
                window.location.href = '/character';
            })
            .catch(error => {
                console.error('Error:', error);
                // Re-enable button
                confirmResetBtn.disabled = false;
                confirmResetBtn.innerHTML = 'Reset Game';
                
                // Show error message
                alert('An error occurred while resetting the game. Please try again.');
            });
        });
    }

    /**
     * Send a game action to the server
     * @param {string} action - The action to perform
     * @param {string} details - Additional details for the action
     * @param {Function} onSuccess - Callback function on successful response
     * @param {Function} onError - Callback function on error
     */
    sendGameAction(action, details, onSuccess, onError) {
        const requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                action: action,
                details: details
            })
        };
        
        fetch(this.API_ENDPOINT, requestOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (onSuccess) onSuccess(data);
            })
            .catch(error => {
                console.error('Error:', error);
                this.displayErrorMessage('An error occurred while processing your action. Please try again.');
                if (onError) onError(error);
            });
    }

    /**
     * Handle the response from an action API call
     * @param {Object} data - The response data
     */
    handleActionResponse(data) {
        // Check if the response is a JSON string that wasn't properly parsed
        if (typeof data === 'string' && data.startsWith('{') && data.endsWith('}')) {
            try {
                data = JSON.parse(data);
            } catch (e) {
                console.error('Failed to parse JSON string:', e);
            }
        }
        
        // Check if the message is a JSON string
        if (data.message && typeof data.message === 'string') {
            if (data.message.startsWith('{') && data.message.endsWith('}')) {
                try {
                    const jsonData = JSON.parse(data.message);
                    if (jsonData.message) {
                        data.message = jsonData.message;
                    }
                } catch (e) {
                    // Not valid JSON, keep original message
                }
            }
        }
        
        if (data.success) {
            // Add the message to the messages container
            if (data.message) {
                this.addMessage(data.message);
            }
            
            // Update scene description if it changed
            if (data.description) {
                this.updateSceneDescription(data.description);
            }
            
            // Update location if it changed
            if (data.new_location) {
                this.updateLocation(data.new_location);
            }
            
            // Update NPCs if they changed
            if (data.npcs) {
                this.updateNPCs(data.npcs);
            }
            
            // Update events if they changed
            if (data.events) {
                this.updateEvents(data.events);
            }
            
            // Handle combat state
            if (data.combat) {
                // Reload page to show combat interface
                window.location.reload();
            }
        } else {
            // Display error message
            if (data.message) {
                this.displayErrorMessage(data.message);
            }
        }
    }

    /**
     * Add a message to the messages container
     * @param {string} message - The message to add
     * @param {boolean} isError - Whether this is an error message
     */
    addMessage(message, isError = false) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;
        
        // Highlight dice rolls with regex pattern
        const diceRollPattern = /rolagem (de \w+\s)?foi de (\d+)|roll(ed)? (a )?(\d+)|rolled (\d+)|rolagem: (\d+)|roll: (\d+)|rolou (\d+)/gi;
        const highlightedMessage = message.replace(diceRollPattern, match => {
            // Extract the number from the match
            const numberMatch = match.match(/\d+/);
            if (numberMatch) {
                const number = numberMatch[0];
                return match.replace(number, `<span class="dice-roll">${number}</span>`);
            }
            return match;
        });
        
        const messageDiv = document.createElement('div');
        messageDiv.className = isError ? 'message text-danger' : 'message';
        messageDiv.innerHTML = `<strong>Game Master:</strong> ${highlightedMessage}`;
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to the bottom of the messages container
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Display an error message
     * @param {string} message - The error message to display
     */
    displayErrorMessage(message) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            this.addMessage(message, true);
        } else {
            alert(message);
        }
    }

    /**
     * Update the scene description
     * @param {string} description - The new scene description
     */
    updateSceneDescription(description) {
        const sceneDescription = document.querySelector('.scene-description');
        if (sceneDescription) {
            sceneDescription.textContent = description;
        }
    }

    /**
     * Update the location display
     * @param {string} location - The new location name
     */
    updateLocation(location) {
        const locationElement = document.querySelector('.card-header h5');
        if (locationElement) {
            locationElement.innerHTML = `<i class="bi bi-compass me-2"></i>${location}`;
        }
    }

    /**
     * Update the NPCs display
     * @param {Array} npcs - Array of NPC names
     */
    updateNPCs(npcs) {
        let npcsElement = document.querySelector('.npcs-present');
        
        if (npcs.length > 0) {
            if (npcsElement) {
                // Update existing element
                npcsElement.innerHTML = `<strong>NPCs Present:</strong> ${npcs.join(', ')}`;
                npcsElement.style.display = 'block';
            } else {
                // Create new element
                const gameOutput = document.getElementById('gameOutput');
                if (gameOutput) {
                    npcsElement = document.createElement('div');
                    npcsElement.className = 'npcs-present mb-3';
                    npcsElement.innerHTML = `<strong>NPCs Present:</strong> ${npcs.join(', ')}`;
                    gameOutput.insertBefore(npcsElement, document.getElementById('messagesContainer'));
                }
            }
        } else if (npcsElement) {
            // Hide if no NPCs
            npcsElement.style.display = 'none';
        }
    }

    /**
     * Update the events display
     * @param {Array} events - Array of event descriptions
     */
    updateEvents(events) {
        let eventsElement = document.querySelector('.events');
        
        if (events.length > 0) {
            if (eventsElement) {
                // Update existing element
                eventsElement.innerHTML = `<strong>Events:</strong> ${events.join(', ')}`;
                eventsElement.style.display = 'block';
            } else {
                // Create new element
                const gameOutput = document.getElementById('gameOutput');
                if (gameOutput) {
                    eventsElement = document.createElement('div');
                    eventsElement.className = 'events mb-3';
                    eventsElement.innerHTML = `<strong>Events:</strong> ${events.join(', ')}`;
                    gameOutput.insertBefore(eventsElement, document.getElementById('messagesContainer'));
                }
            }
        } else if (eventsElement) {
            // Hide if no events
            eventsElement.style.display = 'none';
        }
    }
}

// Initialize the game UI when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const gameUI = new GameUIManager();
});