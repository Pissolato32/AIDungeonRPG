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
            gridSize: 7,
            showCoordinates: false
        }, options);
        
        this.locations = {};
        this.playerPosition = { x: 0, y: 0 };
        
        this.initializeMap();
    }
    
    initializeMap() {
        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.options.tileSize * this.options.gridSize;
        this.canvas.height = this.options.tileSize * this.options.gridSize;
        this.canvas.className = 'game-map-canvas';
        this.container.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        
        // Add legend
        const legend = document.createElement('div');
        legend.className = 'map-legend';
        legend.innerHTML = `
            <div class="legend-item"><span class="legend-color" style="background-color: #4CAF50;"></span> Current Location</div>
            <div class="legend-item"><span class="legend-color" style="background-color: #2196F3;"></span> Visited</div>
            <div class="legend-item"><span class="legend-color" style="background-color: #9E9E9E;"></span> Discovered</div>
        `;
        this.container.appendChild(legend);
        
        // Initial render
        this.render();
    }
    
    updateData(worldData, playerPosition) {
        if (!worldData || !worldData.locations) return;
        
        this.locations = worldData.locations;
        this.playerPosition = playerPosition || { x: 0, y: 0 };
        
        // Center the map on player
        this.options.centerX = this.playerPosition.x;
        this.options.centerY = this.playerPosition.y;
        
        this.render();
    }
    
    render() {
        const { tileSize, centerX, centerY, gridSize } = this.options;
        const halfGrid = Math.floor(gridSize / 2);
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
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
        
        // Draw locations
        for (const locId in this.locations) {
            const location = this.locations[locId];
            const coords = location.coordinates || { x: 0, y: 0 };
            
            // Calculate position on grid
            const gridX = halfGrid + (coords.x - centerX);
            const gridY = halfGrid - (coords.y - centerY); // Y is inverted in canvas
            
            // Skip if outside visible grid
            if (gridX < 0 || gridX >= gridSize || gridY < 0 || gridY >= gridSize) continue;
            
            // Calculate pixel position
            const x = gridX * tileSize;
            const y = gridY * tileSize;
            
            // Determine color based on status
            let color = '#9E9E9E'; // Default: discovered
            if (coords.x === this.playerPosition.x && coords.y === this.playerPosition.y) {
                color = '#4CAF50'; // Current location
            } else if (location.visited) {
                color = '#2196F3'; // Visited
            }
            
            // Draw location tile
            this.ctx.fillStyle = color;
            this.ctx.fillRect(x + 2, y + 2, tileSize - 4, tileSize - 4);
            
            // Draw location type icon
            this.drawLocationIcon(location.type, x + tileSize/2, y + tileSize/2);
            
            // Draw coordinates if enabled
            if (this.options.showCoordinates) {
                this.ctx.fillStyle = '#fff';
                this.ctx.font = '8px Arial';
                this.ctx.textAlign = 'center';
                this.ctx.fillText(`${coords.x},${coords.y}`, x + tileSize/2, y + tileSize - 5);
            }
        }
        
        // Draw connections between locations
        for (const locId in this.locations) {
            const location = this.locations[locId];
            const coords = location.coordinates || { x: 0, y: 0 };
            const connections = location.connections || {};
            
            // Calculate position on grid
            const gridX = halfGrid + (coords.x - centerX);
            const gridY = halfGrid - (coords.y - centerY); // Y is inverted in canvas
            
            // Skip if outside visible grid
            if (gridX < 0 || gridX >= gridSize || gridY < 0 || gridY >= gridSize) continue;
            
            // Calculate pixel position (center of tile)
            const x = gridX * tileSize + tileSize/2;
            const y = gridY * tileSize + tileSize/2;
            
            // Draw connections
            for (const direction in connections) {
                const targetId = connections[direction];
                const targetLoc = this.locations[targetId];
                if (!targetLoc) continue;
                
                const targetCoords = targetLoc.coordinates || { x: 0, y: 0 };
                const targetGridX = halfGrid + (targetCoords.x - centerX);
                const targetGridY = halfGrid - (targetCoords.y - centerY);
                
                // Skip if target is outside visible grid
                if (targetGridX < 0 || targetGridX >= gridSize || targetGridY < 0 || targetGridY >= gridSize) continue;
                
                // Calculate target pixel position
                const targetX = targetGridX * tileSize + tileSize/2;
                const targetY = targetGridY * tileSize + tileSize/2;
                
                // Draw connection line
                this.ctx.strokeStyle = '#666';
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.moveTo(x, y);
                this.ctx.lineTo(targetX, targetY);
                this.ctx.stroke();
            }
        }
    }
    
    drawLocationIcon(locationType, x, y) {
        this.ctx.fillStyle = '#fff';
        this.ctx.font = '12px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        let icon = '•'; // Default
        
        // Set icon based on location type
        switch(locationType) {
            case 'aldeia':
            case 'vila':
                icon = '◊';
                break;
            case 'cidade':
                icon = '■';
                break;
            case 'fortaleza':
                icon = '▲';
                break;
            case 'floresta':
                icon = '♣';
                break;
            case 'montanha':
                icon = '▲';
                break;
            case 'caverna':
                icon = '○';
                break;
            case 'ruínas':
                icon = '†';
                break;
            default:
                icon = '•';
        }
        
        this.ctx.fillText(icon, x, y);
    }
}

// Initialize map when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if map container exists
    const mapContainer = document.getElementById('mapContainer');
    if (!mapContainer) return;
    
    // Create map instance
    const gameMap = new GameMap('mapContainer', {
        tileSize: 40,
        gridSize: 5,
        showCoordinates: true
    });
    
    // Fetch world data
    fetch('/api/world_map')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                gameMap.updateData(data.world_map, data.player_position);
            }
        })
        .catch(error => console.error('Error fetching world map:', error));
});