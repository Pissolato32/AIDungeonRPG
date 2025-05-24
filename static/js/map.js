/**
 * Map visualization for the RPG game
 */

class GameMap {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container with ID ${containerId} not found`);
            return;
        }

        this.options = Object.assign({
            tileSize: 40,
            centerX: 0,
            centerY: 0,
            gridSize: 11,
            showCoordinates: false
        }, options);

        this.worldMap = {
            locations: {},
            discovered: {}
        };
        this.playerPosition = { x: 0, y: 0 };

        // Map icons
        this.icons = {
            city: '🏙️',
            village: '🏘️',
            town: '🏠',
            dungeon: '🏛️',
            cave: '🕳️',
            forest: '🌲',
            mountain: '⛰️',
            castle: '🏰',
            ruins: '🗿',
            temple: '⛩️',
            quest: '❗',
            shop: '🛒',
            tavern: '🍺',
            player: '🧙'
        };

        this.initializeMap();
        this.loadMapData();
    }

    initializeMap() {
        // Clear container
        this.container.innerHTML = '';

        // Create map wrapper
        this.mapWrapper = document.createElement('div');
        this.mapWrapper.className = 'map-wrapper';
        this.mapWrapper.style.position = 'relative';
        this.container.appendChild(this.mapWrapper);

        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.options.tileSize * this.options.gridSize;
        this.canvas.height = this.options.tileSize * this.options.gridSize;
        this.canvas.className = 'game-map-canvas';
        this.mapWrapper.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d');

        // Add legend
        const legend = document.createElement('div');
        legend.className = 'map-legend';
        legend.innerHTML = `
            <div class="legend-item"><span class="legend-color" style="background-color: #4CAF50;"></span> Localização Atual</div>
            <div class="legend-item"><span class="legend-color" style="background-color: #2196F3;"></span> Visitado</div>
            <div class="legend-item"><span class="legend-color" style="background-color: #9E9E9E;"></span> Descoberto</div>
        `;
        this.container.appendChild(legend);

        // Add controls
        const controls = document.createElement('div');
        controls.className = 'map-controls';
        controls.innerHTML = `
            <button id="mapZoomIn">+</button>
            <button id="mapZoomOut">-</button>
        `;
        this.container.appendChild(controls);

        // Set up event listeners
        document.getElementById('mapZoomIn').addEventListener('click', () => this.zoom(1));
        document.getElementById('mapZoomOut').addEventListener('click', () => this.zoom(-1));

        // Initial render
        this.render();
    }

    zoom(direction) {
        const newSize = this.options.tileSize + (direction * 5);
        if (newSize >= 20 && newSize <= 60) {
            this.options.tileSize = newSize;
            this.render();
        }
    }

    loadMapData() {
        fetch('/api/world_map')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.updateData(data.world_map, data.player_position);
                } else {
                    console.error('Failed to load map data:', data.message);
                    // Create empty map if no data
                    this.createEmptyMap();
                }
            })
            .catch(error => {
                console.error('Error fetching world map:', error);
                this.createEmptyMap();
            });
    }

    createEmptyMap() {
        // Create a basic empty map with just the starting location
        this.worldMap = {
            locations: {
                "start": {
                    id: "start",
                    name: "Ponto de Partida",
                    type: "village",
                    coordinates: { x: 0, y: 0 },
                    visited: true,
                    discovered: true
                }
            },
            discovered: {
                "0,0": "start"
            }
        };

        this.playerPosition = { x: 0, y: 0 };
        this.render();
    }

    updateData(worldMap, playerPosition) {
        if (worldMap && worldMap.locations) {
            this.worldMap = worldMap;
        }

        if (playerPosition) {
            this.playerPosition = playerPosition;
        }

        // Center the map on player
        this.options.centerX = this.playerPosition.x;
        this.options.centerY = this.playerPosition.y;

        this.render();
    }

    /**
     * Reloads map data from the server and re-renders the map.
     */
    refreshMapData() {
        console.log("Map.js: Refreshing map data...");
        this.loadMapData(); // This already fetches and calls render
    }

    render() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);

        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update canvas size
        this.canvas.width = tileSize * gridSize;
        this.canvas.height = tileSize * gridSize;

        // Draw background grid
        this.drawGrid();

        // Draw discovered tiles
        this.drawDiscoveredTiles();

        // Draw location connections
        this.drawConnections();

        // Draw locations
        this.drawLocations();

        // Draw player position
        this.drawPlayer();
    }

    drawGrid() {
        const { tileSize, gridSize } = this.options;

        // Draw grid
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1;

        for (let i = 0; i <= gridSize; i++) {
            // Vertical lines
            this.ctx.beginPath();
            this.ctx.moveTo(i * tileSize, 0);
            this.ctx.lineTo(i * tileSize, gridSize * tileSize);
            this.ctx.stroke();

            // Horizontal lines
            this.ctx.beginPath();
            this.ctx.moveTo(0, i * tileSize);
            this.ctx.lineTo(gridSize * tileSize, i * tileSize);
            this.ctx.stroke();
        }

        // Draw coordinate labels if enabled
        if (this.options.showCoordinates) {
            const { centerX, centerY } = this.options;
            const halfGrid = Math.floor(gridSize / 2);

            this.ctx.fillStyle = '#666';
            this.ctx.font = '10px Arial';
            this.ctx.textAlign = 'center';

            for (let i = 0; i < gridSize; i++) {
                const x = centerX - halfGrid + i;
                const y = centerY + halfGrid - i;

                // X coordinates at bottom
                this.ctx.fillText(x.toString(), (i + 0.5) * tileSize, gridSize * tileSize - 2);

                // Y coordinates at left
                this.ctx.fillText(y.toString(), 10, (i + 0.5) * tileSize);
            }
        }
    }

    drawDiscoveredTiles() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);

        // Draw discovered areas
        if (this.worldMap.discovered) {
            this.ctx.fillStyle = '#333';

            for (const coordKey in this.worldMap.discovered) {
                const [x, y] = coordKey.split(',').map(Number);

                // Calculate position on grid
                const gridX = halfGrid + (x - centerX);
                const gridY = halfGrid - (y - centerY); // Y is inverted in canvas

                // Skip if outside visible grid
                if (gridX < 0 || gridX >= gridSize || gridY < 0 || gridY >= gridSize) continue;

                // Draw discovered tile
                this.ctx.fillRect(gridX * tileSize, gridY * tileSize, tileSize, tileSize);
            }
        }
    }

    drawConnections() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);

        // Draw connections between locations
        if (this.worldMap.locations) {
            this.ctx.strokeStyle = '#666';
            this.ctx.lineWidth = 2;

            for (const locId in this.worldMap.locations) {
                const location = this.worldMap.locations[locId];
                if (!location.coordinates) continue;

                const { x, y } = location.coordinates;
                const connections = location.connections || {};

                // Calculate position on grid
                const gridX = halfGrid + (x - centerX);
                const gridY = halfGrid - (y - centerY); // Y is inverted in canvas

                // Skip if outside visible grid
                if (gridX < 0 || gridX >= gridSize || gridY < 0 || gridY >= gridSize) continue;

                // Calculate pixel position (center of tile)
                const startX = gridX * tileSize + tileSize / 2;
                const startY = gridY * tileSize + tileSize / 2;

                // Draw connections
                for (const direction in connections) {
                    const targetId = connections[direction];
                    const targetLoc = this.worldMap.locations[targetId];
                    if (!targetLoc || !targetLoc.coordinates) continue;

                    const targetX = targetLoc.coordinates.x;
                    const targetY = targetLoc.coordinates.y;

                    const targetGridX = halfGrid + (targetX - centerX);
                    const targetGridY = halfGrid - (targetY - centerY);

                    // Skip if target is outside visible grid
                    if (targetGridX < 0 || targetGridX >= gridSize || targetGridY < 0 || targetGridY >= gridSize) continue;

                    // Calculate target pixel position
                    const endX = targetGridX * tileSize + tileSize / 2;
                    const endY = targetGridY * tileSize + tileSize / 2;

                    // Draw connection line
                    this.ctx.beginPath();
                    this.ctx.moveTo(startX, startY);
                    this.ctx.lineTo(endX, endY);
                    this.ctx.stroke();
                }
            }
        }
    }

    drawLocations() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);

        // Remove existing location icons
        const existingIcons = this.mapWrapper.querySelectorAll('.map-icon:not(.map-icon-player)');
        existingIcons.forEach(icon => icon.remove());

        // Draw locations
        if (this.worldMap.locations) {
            for (const locId in this.worldMap.locations) {
                const location = this.worldMap.locations[locId];
                if (!location.coordinates) continue;

                const { x, y } = location.coordinates;

                // Calculate position on grid
                const gridX = halfGrid + (x - centerX);
                const gridY = halfGrid - (y - centerY); // Y is inverted in canvas

                // Skip if outside visible grid
                if (gridX < 0 || gridX >= gridSize || gridY < 0 || gridY >= gridSize) continue;

                // Calculate pixel position
                const pixelX = gridX * tileSize + tileSize / 2;
                const pixelY = gridY * tileSize + tileSize / 2;

                // Determine color based on status
                let color = '#9E9E9E'; // Default: discovered
                if (x === this.playerPosition.x && y === this.playerPosition.y) {
                    color = '#4CAF50'; // Current location
                } else if (location.visited) {
                    color = '#2196F3'; // Visited
                }

                // Draw location tile
                this.ctx.fillStyle = color;
                this.ctx.fillRect(gridX * tileSize + 2, gridY * tileSize + 2, tileSize - 4, tileSize - 4);

                // Add location icon as HTML element for better rendering
                this.addLocationIcon(location, pixelX, pixelY);

                // Draw location name if zoomed in enough
                if (tileSize >= 40) {
                    this.ctx.fillStyle = '#fff';
                    this.ctx.font = '9px Arial';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(
                        location.name.substring(0, 10) + (location.name.length > 10 ? '...' : ''),
                        pixelX,
                        gridY * tileSize + tileSize - 5
                    );
                }
            }
        }
    }

    drawPlayer() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);

        // Calculate position on grid
        const gridX = halfGrid; // Player is always at center
        const gridY = halfGrid;

        // Calculate pixel position
        const pixelX = gridX * tileSize + tileSize / 2;
        const pixelY = gridY * tileSize + tileSize / 2;

        // Remove existing player icon
        const existingPlayer = this.mapWrapper.querySelector('.map-icon-player');
        if (existingPlayer) {
            existingPlayer.remove();
        }

        // Add player icon
        const playerIcon = document.createElement('div');
        playerIcon.className = 'map-icon map-icon-player';
        playerIcon.style.left = `${pixelX}px`;
        playerIcon.style.top = `${pixelY}px`;
        playerIcon.textContent = this.icons.player;
        playerIcon.title = 'Você está aqui';
        this.mapWrapper.appendChild(playerIcon);
    }

    addLocationIcon(location, x, y) {
        const type = location.type || 'unknown';
        let icon = this.icons[type] || '📍';

        // Create icon element
        const iconElement = document.createElement('div');
        iconElement.className = `map-icon map-icon-${type}`;
        iconElement.style.left = `${x}px`;
        iconElement.style.top = `${y}px`;
        iconElement.textContent = icon;
        iconElement.title = location.name;

        // Add quest indicator if location has quests
        if (location.quests && location.quests.length > 0) {
            iconElement.classList.add('has-quest');
            iconElement.title += ' (Quest disponível)';
        }

        this.mapWrapper.appendChild(iconElement);
    }
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Check if map container exists
    const mapContainer = document.getElementById('gameMap');
    if (!mapContainer) return;

    // Create map instance
    window.gameMap = new GameMap('gameMap', { // Assign to window for global access
        tileSize: 40,
        gridSize: 11,
        showCoordinates: true
    });
});