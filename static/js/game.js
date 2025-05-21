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
        this.thinkingInterval = null; // Initialize thinkingInterval
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
     * Update all progress bars on the page
     */
    updateProgressBars() {
        this.updateEnemyHpBar();
        this.updateCharacterBars();
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
     * Set up the action form submission handler
     */
    setupActionForm() {
        const actionForm = document.getElementById('actionForm');
        if (!actionForm) return;

        actionForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (this.isProcessing) return; // Prevent multiple submissions

            const actionType = "interpret"; // Ação agora é sempre "interpret"
            const actionDetailsElement = document.getElementById('actionDetails');
            const actionDetails = actionDetailsElement ? actionDetailsElement.value : '';

            // Show loading state
            this.isProcessing = true;
            const submitButton = actionForm.querySelector('button[type="submit"]');
            const originalButtonContent = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';

            // Add player's action to the message container
            this.addPlayerMessage(actionDetails); // Apenas os detalhes, já que o tipo é implícito

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
                    if (actionDetailsElement) actionDetailsElement.value = '';

                    // Reset button state
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalButtonContent;
                    this.isProcessing = false;

                    // Handle the response
                    this.handleActionResponse(data);

                    // Update bars after response
                    this.updateProgressBars();
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
        messageDiv.className = 'message message-user'; // Changed from player-message for consistency
        messageDiv.innerHTML = `<strong>Você:</strong> ${message}`; // Changed from You:
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
        thinkingDiv.innerHTML = '<strong>Mestre:</strong> <span class="thinking-dots">...</span>'; // Changed from Game Master:
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

                this.handleButtonAction(action, details, combatButtons);
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
            this.handleButtonAction('rest', '', restButton);
        });
    }

    /**
     * Set up use item button event listeners
     */
    setupUseItemButtons() {
        // Use event delegation for dynamically added items
        const inventoryList = document.getElementById('inventoryList');
        if (inventoryList) {
            inventoryList.addEventListener('click', (event) => {
                if (event.target && event.target.classList.contains('use-item-btn')) {
                    const button = event.target;
                    const itemName = button.dataset.itemName; // Corrected: was getAttribute('data-item')
                    if (itemName) {
                        this.handleButtonAction('use_item', itemName, [button]); // Pass button as an array
                    }
                }
            });
        }
    }


    /**
     * Helper method to handle common button action flow
     * @param {string} action - The action to perform
     * @param {string} details - Additional details for the action
     * @param {NodeList|Array|HTMLElement} buttons - Buttons to disable during processing
     * @param {boolean} reloadOnSuccess - Whether to reload the page on success
     */
    handleButtonAction(action, details, buttons, reloadOnSuccess = true) {
        // Add player's action to the message container
        this.addPlayerMessage(`${action}${details ? ': ' + details : ''}`);

        // Show "thinking" indicator
        this.showThinkingIndicator();

        // Disable buttons
        const buttonArray = buttons instanceof NodeList || Array.isArray(buttons) ? Array.from(buttons) : [buttons];
        buttonArray.forEach(btn => { btn.disabled = true; });

        // Send action to server
        this.sendGameAction(
            action,
            details,
            (data) => {
                // Remove thinking indicator
                this.removeThinkingIndicator();

                // Handle the response
                this.handleActionResponse(data);

                // Reload page or continue
                if (reloadOnSuccess && data.success && (data.combat || data.new_location)) {
                    window.location.reload();
                } else {
                    // Re-enable buttons
                    buttonArray.forEach(btn => { btn.disabled = false; });
                }
            },
            (error) => {
                // Remove thinking indicator
                this.removeThinkingIndicator();

                // Re-enable buttons
                buttonArray.forEach(btn => { btn.disabled = false; });

                // Display error message
                this.displayErrorMessage('An error occurred while processing your action. Please try again.');
            }
        );
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
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const resetModal = new bootstrap.Modal(document.getElementById('resetGameModal'));
                resetModal.show();
            } else {
                alert('Bootstrap JS não carregado.');
            }
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
                    // Add CSRF token if you implement Flask-WTF
                    // 'X-CSRFToken': csrfToken 
                }
            })
                .then(response => response.json())
                .then(data => { // Changed from () to data
                    if (data.redirect_url) { // Check for redirect_url
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.href = '/character'; // Fallback
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    // Re-enable button
                    confirmResetBtn.disabled = false;
                    confirmResetBtn.innerHTML = 'Reset Game';
                    // Show error message
                    this.displayErrorMessage('An error occurred while resetting the game. Please try again.');
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
                // Add CSRF token if you implement Flask-WTF
                // 'X-CSRFToken': csrfToken 
            },
            body: JSON.stringify({ action, details })
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
                if (onError) onError(error);
            });
    }

    /**
     * Handle the response from an action API call
     * @param {Object} data - The response data
     */
    handleActionResponse(data) {
        if (data.success) {
            // Add the message to the messages container
            // Check if data.message is not null or undefined before passing
            this.addMessage(data.message || "", false, data.interactable_elements);


            // Update scene description if it changed
            if (data.scene_description_update) { // Prefer the new field
                this.updateSceneDescription(data.scene_description_update);
            } else if (data.description) { // Fallback to old field
                this.updateSceneDescription(data.description);
            }


            // Update location if it changed
            if (data.current_detailed_location) { // Prefer the new field
                this.updateLocation(data.current_detailed_location);
            } else if (data.new_location) { // Fallback to old field
                this.updateLocation(data.new_location);
            }


            // Update NPCs if they changed
            if (data.npcs_present) { // Prefer the new field (assuming it's an array of strings)
                this.updateNPCs(data.npcs_present);
            } else if (data.npcs) { // Fallback to old field
                this.updateNPCs(data.npcs);
            }

            // Update events if they changed
            if (data.events) {
                this.updateEvents(data.events);
            }

            // Update inventory if present in response (more robust than full reload)
            if (data.inventory) {
                this.updateInventory(data.inventory);
            }
            if (data.gold !== undefined) {
                this.updateGold(data.gold);
            }
            if (data.character_stats) { // For HP, Stamina, etc.
                this.updateCharacterStats(data.character_stats);
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
     * @param {Array<string>} [interactableElements=null] - Optional array of interactable element names
     */
    addMessage(message, isError = false, interactableElements = null) {
        const messagesContainer = document.getElementById('messagesContainer');
        if (!messagesContainer) return;

        // If the message is effectively empty and not an error, and no interactable elements, don't add an empty bubble
        if (!message && !isError && (!interactableElements || interactableElements.length === 0)) {
            return;
        }

        const diceRollPattern = /rolagem (de \w+\s)?foi de (\d+)|roll(ed)? (a )?(\d+)|rolled (\d+)|rolagem: (\d+)|roll: (\d+)|rolou (\d+)/gi;
        // CORRIGIDO: Usar 'message' em vez de 'displayMessage'
        const highlightedMessage = (typeof message === 'string' ? message : '').replace(diceRollPattern, match => {
            // Extract the number from the match
            const numberMatch = match.match(/\d+/);
            if (numberMatch) {
                const number = numberMatch[0];
                return match.replace(number, `<span class="dice-roll">${number}</span>`);
            }
            return match;
        });

        const messageDiv = document.createElement('div'); // Use the 'message' argument directly
        messageDiv.className = isError ? 'message text-danger' : 'message message-assistant';

        let fullMessageHTML = `<strong>${isError ? "Erro:" : "Mestre:"}</strong> ${highlightedMessage}`;
        // CORRIGIDO: Usar 'interactableElements' em vez de 'interactableElementsForDisplay'
        if (interactableElements && interactableElements.length > 0) {
            fullMessageHTML += `<div class="interactable-elements-inline mt-2"><strong>Você percebe:</strong>`;
            const listGroup = document.createElement('div');
            listGroup.className = 'list-group list-group-flush mt-1';

            interactableElements.forEach(elementName => { // Usar 'interactableElements'
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'list-group-item list-group-item-action list-group-item-secondary p-2 text-start'; // Added text-start for better alignment
                button.textContent = elementName;
                button.addEventListener('click', () => {
                    const actionDetailsInput = document.getElementById('actionDetails');
                    if (actionDetailsInput) {
                        actionDetailsInput.value = `Examinar ${elementName}`;
                        // Consider if you want to auto-submit or just fill the input
                        // document.getElementById('actionForm').requestSubmit(); 
                    }
                });
                listGroup.appendChild(button);
            });
            fullMessageHTML += listGroup.outerHTML + '</div>';
        }

        messageDiv.innerHTML = fullMessageHTML;
        messagesContainer.appendChild(messageDiv);

        // Scroll to the bottom of the messages container
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Display an error message
     * @param {string} message - The error message to display
     */
    displayErrorMessage(message) {
        this.addMessage(message, true);
    }

    /**
     * Update the scene description
     * @param {string} description - The new scene description
     */
    updateSceneDescription(description) {
        const sceneDescription = document.getElementById('sceneDescription'); // Changed from querySelector
        if (sceneDescription) {
            sceneDescription.textContent = description;
        }
    }

    /**
     * Update the location display
     * @param {string} location - The new location name
     */
    updateLocation(location) {
        const locationElement = document.getElementById('currentLocationDisplay'); // Changed from querySelector
        if (locationElement) {
            locationElement.innerHTML = `<i class="bi bi-compass me-2"></i>${location}`;
        }
    }

    /**
     * Update the NPCs display
     * @param {Array} npcs - Array of NPC names
     */
    updateNPCs(npcs) {
        const npcsContainer = document.getElementById('npcsPresent'); // The container div
        const npcListSpan = document.getElementById('npcList'); // The span for the list
        if (npcsContainer && npcListSpan) {
            if (npcs && npcs.length > 0) {
                npcListSpan.textContent = npcs.join(', ');
                npcsContainer.style.display = 'block'; // Or remove d-none if using Bootstrap visibility
            } else {
                npcListSpan.textContent = '';
                npcsContainer.style.display = 'none'; // Or add d-none
            }
        }
    }

    /**
     * Update the events display
     * @param {Array} events - Array of event descriptions
     */
    updateEvents(events) {
        const eventsContainer = document.getElementById('currentEvents'); // The container div
        const eventListSpan = document.getElementById('eventList'); // The span for the list
        if (eventsContainer && eventListSpan) {
            if (events && events.length > 0) {
                eventListSpan.textContent = events.join(', ');
                eventsContainer.style.display = 'block';
            } else {
                eventListSpan.textContent = '';
                eventsContainer.style.display = 'none';
            }
        }
    }

    /**
     * Update the inventory display
     * @param {Array<Object|string>} inventoryItems - Array of inventory items
     */
    updateInventory(inventoryItems) {
        const inventoryList = document.getElementById('inventoryList');
        const emptyMessage = document.getElementById('emptyInventoryMessage');

        if (!inventoryList) return;
        inventoryList.innerHTML = ''; // Clear existing items

        if (inventoryItems && inventoryItems.length > 0) {
            if (emptyMessage) emptyMessage.style.display = 'none';
            inventoryItems.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'list-group-item d-flex justify-content-between align-items-center';

                let itemName = '';
                let isEquipped = false; // You'll need logic to determine this from character.equipment
                let durability = null;
                let quantity = null;

                if (typeof item === 'string') {
                    itemName = item;
                } else if (typeof item === 'object' && item !== null && item.name) {
                    itemName = item.name;
                    durability = item.durability;
                    quantity = item.quantity;
                    // TODO: Check if item is equipped by comparing with initialCharacterData.equipment
                    // This requires initialCharacterData to be updated or a new field from backend
                } else {
                    itemName = 'Item Desconhecido';
                }

                let itemHTML = `<span>`;
                if (isEquipped) {
                    itemHTML += `<strong>${itemName}*</strong> <span class="badge bg-success ms-2">Equipado</span>`;
                } else {
                    itemHTML += itemName;
                }
                if (durability !== null && durability !== undefined) {
                    itemHTML += ` <span class="badge bg-secondary ms-2">Durabilidade: ${durability}</span>`;
                }
                if (quantity !== null && quantity !== undefined && quantity > 1) {
                    itemHTML += ` <span class="badge bg-info ms-2">x${quantity}</span>`;
                }
                itemHTML += `</span>`;
                itemHTML += `<button class="btn btn-sm btn-outline-primary use-item-btn" data-item-name="${itemName}">Usar</button>`;
                itemDiv.innerHTML = itemHTML;
                inventoryList.appendChild(itemDiv);
            });
        } else {
            if (emptyMessage) emptyMessage.style.display = 'block';
        }
    }

    /**
     * Update character gold display
     * @param {number} goldAmount 
     */
    updateGold(goldAmount) {
        const goldDisplay = document.getElementById('characterGold');
        if (goldDisplay) {
            goldDisplay.textContent = goldAmount;
        }
    }

    /**
     * Update character stats (HP, Stamina, etc.) and their bars
     * @param {Object} statsData - Object containing character stats like current_hp, max_hp, etc.
     */
    updateCharacterStats(statsData) {
        // HP
        const hpDisplay = document.getElementById('hpDisplay');
        const hpBar = document.getElementById('hpBar');
        if (hpDisplay && hpBar && statsData.current_hp !== undefined && statsData.max_hp !== undefined) {
            hpDisplay.textContent = `${statsData.current_hp} / ${statsData.max_hp}`;
            const hpPercent = statsData.max_hp > 0 ? (statsData.current_hp / statsData.max_hp * 100) : 0;
            hpBar.style.width = `${hpPercent.toFixed(1)}%`;
            hpBar.setAttribute('aria-valuenow', statsData.current_hp);
            hpBar.setAttribute('aria-valuemax', statsData.max_hp);
        }

        // Stamina
        const staminaDisplay = document.getElementById('staminaDisplay');
        const staminaBar = document.getElementById('staminaBar');
        if (staminaDisplay && staminaBar && statsData.current_stamina !== undefined && statsData.max_stamina !== undefined) {
            staminaDisplay.textContent = `${statsData.current_stamina} / ${statsData.max_stamina}`;
            const staminaPercent = statsData.max_stamina > 0 ? (statsData.current_stamina / statsData.max_stamina * 100) : 0;
            staminaBar.style.width = `${staminaPercent.toFixed(1)}%`;
            staminaBar.setAttribute('aria-valuenow', statsData.current_stamina);
            staminaBar.setAttribute('aria-valuemax', statsData.max_stamina);
        }

        // Hunger (assuming statsData might contain survival_stats directly or nested)
        const hungerData = statsData.survival_stats || statsData; // Adjust if survival_stats is nested
        const hungerDisplay = document.getElementById('hungerDisplay');
        const hungerBar = document.getElementById('hungerBar');
        if (hungerDisplay && hungerBar && hungerData.current_hunger !== undefined && hungerData.max_hunger !== undefined) {
            hungerDisplay.textContent = `${hungerData.current_hunger} / ${hungerData.max_hunger}`;
            const hungerPercent = hungerData.max_hunger > 0 ? (hungerData.current_hunger / hungerData.max_hunger * 100) : 0;
            hungerBar.style.width = `${hungerPercent.toFixed(1)}%`;
            hungerBar.setAttribute('aria-valuenow', hungerData.current_hunger);
            hungerBar.setAttribute('aria-valuemax', hungerData.max_hunger);
        }

        // Thirst
        const thirstData = statsData.survival_stats || statsData; // Adjust if survival_stats is nested
        const thirstDisplay = document.getElementById('thirstDisplay');
        const thirstBar = document.getElementById('thirstBar');
        if (thirstDisplay && thirstBar && thirstData.current_thirst !== undefined && thirstData.max_thirst !== undefined) {
            thirstDisplay.textContent = `${thirstData.current_thirst} / ${thirstData.max_thirst}`;
            const thirstPercent = thirstData.max_thirst > 0 ? (thirstData.current_thirst / thirstData.max_thirst * 100) : 0;
            thirstBar.style.width = `${thirstPercent.toFixed(1)}%`;
            thirstBar.setAttribute('aria-valuenow', thirstData.current_thirst);
            thirstBar.setAttribute('aria-valuemax', thirstData.max_thirst);
        }

        // Update attributes if they are part of statsData
        if (statsData.attributes) {
            for (const [attr, value] of Object.entries(statsData.attributes)) {
                const valueElement = document.getElementById(`${attr}Value`);
                if (valueElement) {
                    valueElement.textContent = value;
                }
            }
        }
        // Update navbar character info
        const navbarName = document.getElementById('navbarCharacterName');
        const navbarLevel = document.getElementById('navbarCharacterLevel');
        if (navbarName && statsData.name) navbarName.textContent = statsData.name;
        if (navbarLevel && statsData.level) navbarLevel.textContent = statsData.level;

    }
}

// Initialize the game UI when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new GameUIManager();
});
