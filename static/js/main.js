document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const algorithmSelect = document.getElementById('algorithm-select');
    const imperfectionSlider = document.getElementById('imperfection-slider');
    const gridContainer = document.getElementById('grid-container');
    const startBtn = document.getElementById('start-btn');
    const resetBtn = document.getElementById('reset-btn');
    const mazeBtn = document.getElementById('maze-btn');
    const speedSlider = document.getElementById('speed-slider');
    const storyLog = document.getElementById('story-log');
    const pathCostDisplay = document.getElementById('path-cost-display');

    // --- Grid & State Configuration ---
    const NUM_COLS = 50;
    const NUM_ROWS = 25;
    let terrainGrid = [];
    let startNode = { row: 12, col: 10 };
    let endNode = { row: 12, col: 40 };
    let animationSpeed = 50;
    let isMouseDown = false, isDraggingStart = false, isDraggingEnd = false, isVisualizing = false;

    // --- Story Log Functions ---
    function clearLog() {
        storyLog.innerHTML = '';
        pathCostDisplay.textContent = '';
    }

    function addToLog(message) {
        storyLog.innerHTML += `<p>${message}</p>`;
        storyLog.scrollTop = storyLog.scrollHeight;
    }

    // --- Grid Initialization ---
    function createGrid() {
        gridContainer.innerHTML = '';
        terrainGrid = Array(NUM_ROWS).fill(null).map(() => Array(NUM_COLS).fill(0));
        gridContainer.style.gridTemplateColumns = `repeat(${NUM_COLS}, 1fr)`;

        for (let row = 0; row < NUM_ROWS; row++) {
            for (let col = 0; col < NUM_COLS; col++) {
                const cellElement = document.createElement('div');
                cellElement.className = 'cell';
                cellElement.dataset.row = row;
                cellElement.dataset.col = col;
                cellElement.addEventListener('mousedown', () => handleMouseDown(row, col));
                cellElement.addEventListener('mouseover', () => handleMouseOver(row, col));
                cellElement.addEventListener('mouseup', handleMouseUp);
                gridContainer.appendChild(cellElement);
            }
        }
        gridContainer.addEventListener('mouseleave', handleMouseUp);
        updateNodeDisplay();
    }

    // --- UI Display ---
    function updateNodeDisplay() {
        document.querySelectorAll('.cell').forEach(cell => {
            const row = parseInt(cell.dataset.row);
            const col = parseInt(cell.dataset.col);
            cell.className = 'cell';
            const terrainType = terrainGrid[row][col];
            if (terrainType === 1) cell.classList.add('wall');
            else if (terrainType === 2) cell.classList.add('water');
            else if (terrainType === 3) cell.classList.add('mud');
            else cell.classList.add('plains');

            cell.innerHTML = `<span class="score g-score"></span><span class="score h-score"></span><span class="score f-score"></span>`;
            if (row === startNode.row && col === startNode.col) {
                cell.classList.add('start');
                cell.innerHTML = '🚀';
            }
            if (row === endNode.row && col === endNode.col) {
                cell.classList.add('end');
                cell.innerHTML = '🏁';
            }
        });
    }

    // --- Event Handlers ---
    function handleMouseDown(row, col) {
        if (isVisualizing) return;
        isMouseDown = true;
        if (row === startNode.row && col === startNode.col) isDraggingStart = true;
        else if (row === endNode.row && col === endNode.col) isDraggingEnd = true;
    }

    function handleMouseOver(row, col) {
        if (isVisualizing) return;
        if (isDraggingStart) {
            if (terrainGrid[row][col] !== 1 && !(row === endNode.row && col === endNode.col)) {
                startNode = { row, col }; updateNodeDisplay();
            }
        } else if (isDraggingEnd) {
            if (terrainGrid[row][col] !== 1 && !(row === startNode.row && col === startNode.col)) {
                endNode = { row, col }; updateNodeDisplay();
            }
        }
    }

    function handleMouseUp() {
        isMouseDown = false; isDraggingStart = false; isDraggingEnd = false;
    }

    // --- Core Visualization Logic ---
    async function visualize() {
        if (isVisualizing) return;
        isVisualizing = true;
        toggleButtons(false);
        clearLog();
        
        const selectedAlgorithm = algorithmSelect.value;
        const algoName = algorithmSelect.options[algorithmSelect.selectedIndex].text;
        addToLog(`▶️ Starting ${algoName}...`);
        
        // --- THIS IS THE CORRECTED SECTION ---
        // It now safely clears previous animation states and scores.
        document.querySelectorAll('.cell').forEach(c => {
            c.classList.remove('open', 'closed', 'path');
            
            // Find score elements first. They might be null in start/end nodes.
            const gScoreEl = c.querySelector('.g-score');
            const hScoreEl = c.querySelector('.h-score');
            const fScoreEl = c.querySelector('.f-score');

            // Only clear textContent if the elements actually exist.
            if (gScoreEl) gScoreEl.textContent = '';
            if (hScoreEl) hScoreEl.textContent = '';
            if (fScoreEl) fScoreEl.textContent = '';
        });
        // --- END OF CORRECTION ---

        updateNodeDisplay();
        
        const payload = { 
            grid: terrainGrid, 
            start: [startNode.row, startNode.col], 
            end: [endNode.row, endNode.col],
            algorithm: selectedAlgorithm
        };

        try {
            const response = await fetch('/solve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const data = await response.json();
            await animateSearch(data.visited_nodes, selectedAlgorithm);
            
            if (data.path.length > 0) {
                const finalNode = data.visited_nodes.find(n => n.pos[0] === endNode.row && n.pos[1] === endNode.col) || data.visited_nodes[data.visited_nodes.length - 1];
                const totalCost = finalNode.g;
                pathCostDisplay.textContent = `Path Found! Cost: ${totalCost} | Nodes: ${data.visited_nodes.length} | Time: ${data.execution_time_ms}ms`;
                addToLog(`🏁 Path Found! Total cost is <span class="highlight">${totalCost}</span>.`);
                addToLog(`📊 Stats: Explored <span class="highlight">${data.visited_nodes.length}</span> nodes in <span class="highlight">${data.execution_time_ms}ms</span>.`);
                await animatePath(data.path);
            } else {
                pathCostDisplay.textContent = "No Path Found!";
                addToLog(`❌ No path could be found. Explored <span class="highlight">${data.visited_nodes.length}</span> nodes.`);
            }
        } catch (error) {
            console.error("Error during visualization:", error);
            addToLog(`🛑 An error occurred: ${error.message}`);
        } finally {
            isVisualizing = false;
            toggleButtons(true);
        }
    }

    // --- Animation & Storytelling ---
    async function animateSearch(visitedNodes, algorithm) {
        const terrainNames = { 0: "Plain", 1: "Wall", 2: "Water", 3: "Mud" };
        for (const nodeData of visitedNodes) {
            const [row, col] = nodeData.pos;
            const cellElement = document.querySelector(`[data-row='${row}'][data-col='${col}']`);
            const isStartNode = (row === startNode.row && col === startNode.col);
            const isEndNode = (row === endNode.row && col === endNode.col);

            if (!isStartNode && !isEndNode) {
                cellElement.classList.add('closed');
                if(algorithm === 'astar' || algorithm === 'dijkstra') {
                    cellElement.querySelector('.g-score').textContent = nodeData.g;
                    cellElement.querySelector('.h-score').textContent = nodeData.h.toFixed(0);
                    cellElement.querySelector('.f-score').textContent = nodeData.f.toFixed(0);
                } else {
                    cellElement.querySelector('.g-score').textContent = nodeData.g;
                }
            }
            
            let logMessage;
            if (algorithm === 'bfs') {
                logMessage = `Visiting [${row}, ${col}], steps: <span class="highlight">${nodeData.g}</span>.`;
            } else {
                logMessage = `Evaluating [${row}, ${col}]. G: <span class="highlight">${nodeData.g}</span>, F: <span class="highlight">${nodeData.f.toFixed(0)}</span>.`;
            }
            addToLog(logMessage);
            await new Promise(resolve => setTimeout(resolve, animationSpeed / 5));
        }
    }

    async function animatePath(path) {
        addToLog("Tracing the optimal path back to the start...");
        for (const pos of path) {
            const [row, col] = pos;
            const cellElement = document.querySelector(`[data-row='${row}'][data-col='${col}']`);
            cellElement.classList.remove('closed');
            cellElement.classList.add('path');
            await new Promise(resolve => setTimeout(resolve, animationSpeed));
        }
    }

    // --- Maze and Terrain Generation ---
    function getNeighbors(row, col, distance) {
        const neighbors = [];
        if (row - distance >= 0) neighbors.push({ row: row - distance, col });
        if (row + distance < NUM_ROWS) neighbors.push({ row: row + distance, col });
        if (col - distance >= 0) neighbors.push({ row, col: col - distance });
        if (col + distance < NUM_COLS) neighbors.push({ row, col: col + distance });
        return neighbors;
    }
    
    function makeMazeImperfect(numToRemove) {
        const candidateWalls = [];
        for (let r = 1; r < NUM_ROWS - 1; r++) {
            for (let c = 1; c < NUM_COLS - 1; c++) {
                if (terrainGrid[r][c] === 1) {
                    if (terrainGrid[r][c - 1] === 0 && terrainGrid[r][c + 1] === 0) candidateWalls.push({ row: r, col: c });
                    else if (terrainGrid[r - 1][c] === 0 && terrainGrid[r + 1][c] === 0) candidateWalls.push({ row: r, col: c });
                }
            }
        }
        for (let i = candidateWalls.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [candidateWalls[i], candidateWalls[j]] = [candidateWalls[j], candidateWalls[i]];
        }
        let removedCount = 0;
        for (let i = 0; i < numToRemove && i < candidateWalls.length; i++) {
            const wall = candidateWalls[i];
            terrainGrid[wall.row][wall.col] = 0;
            removedCount++;
        }
        addToLog(`Carved <span class="highlight">${removedCount}</span> extra paths to create loops.`);
    }

    function addTerrainFeatures() {
        const terrainConfig = [{ type: 2, count: 4, maxSize: 50 }, { type: 3, count: 6, maxSize: 30 }];
        for (const feature of terrainConfig) {
            for (let i = 0; i < feature.count; i++) {
                let startRow, startCol;
                do {
                    startRow = Math.floor(Math.random() * NUM_ROWS);
                    startCol = Math.floor(Math.random() * NUM_COLS);
                } while (terrainGrid[startRow][startCol] !== 0);
                let currentRow = startRow, currentCol = startCol;
                for (let j = 0; j < feature.maxSize; j++) {
                    if (terrainGrid[currentRow][currentCol] !== 0) break;
                    terrainGrid[currentRow][currentCol] = feature.type;
                    const neighbors = getNeighbors(currentRow, currentCol, 1).filter(n => terrainGrid[n.row][n.col] === 0);
                    if (neighbors.length === 0) break;
                    const nextCell = neighbors[Math.floor(Math.random() * neighbors.length)];
                    currentRow = nextCell.row;
                    currentCol = nextCell.col;
                }
            }
        }
    }

    function generateMazeWithTerrains() {
        if (isVisualizing) return;
        resetBoard();
        clearLog();
        addToLog("Generating a new, imperfect maze...");
        for (let r = 0; r < NUM_ROWS; r++) {
            for (let c = 0; c < NUM_COLS; c++) {
                terrainGrid[r][c] = 1;
            }
        }
        const startR = Math.floor(Math.random() * (NUM_ROWS / 2)) * 2;
        const startC = Math.floor(Math.random() * (NUM_COLS / 2)) * 2;
        terrainGrid[startR][startC] = 0;
        const frontier = getNeighbors(startR, startC, 2);
        while (frontier.length > 0) {
            const randIndex = Math.floor(Math.random() * frontier.length);
            const { row, col } = frontier.splice(randIndex, 1)[0];
            const neighbors = getNeighbors(row, col, 2).filter(n => terrainGrid[n.row][n.col] === 0);
            if (neighbors.length > 0) {
                const neighbor = neighbors[Math.floor(Math.random() * neighbors.length)];
                const inBetweenRow = (row + neighbor.row) / 2;
                const inBetweenCol = (col + neighbor.col) / 2;
                terrainGrid[row][col] = 0;
                terrainGrid[inBetweenRow][inBetweenCol] = 0;
            }
            getNeighbors(row, col, 2).forEach(f => {
                if (terrainGrid[f.row][f.col] === 1 && !frontier.some(cell => cell.row === f.row && cell.col === f.col)) {
                    frontier.push(f);
                }
            });
        }
        const numExtraPaths = parseInt(imperfectionSlider.value);
        if (numExtraPaths > 0) makeMazeImperfect(numExtraPaths);
        addTerrainFeatures();
        terrainGrid[startNode.row][startNode.col] = 0;
        terrainGrid[endNode.row][endNode.col] = 0;
        updateNodeDisplay();
        addToLog("Maze generated! You can now visualize the path.");
    }

    // --- Control Functions ---
    function resetBoard() {
        isVisualizing = false;
        createGrid();
        toggleButtons(true);
        clearLog();
        addToLog("Board has been reset. Create a maze or start visualizing!");
    }

    function toggleButtons(enabled) {
        startBtn.disabled = !enabled;
        mazeBtn.disabled = !enabled;
        resetBtn.disabled = !enabled;
    }

    // --- Initial Setup ---
    createGrid();
    addToLog("Welcome! Select an algorithm and click 'Generate Maze'.");
    startBtn.addEventListener('click', visualize);
    resetBtn.addEventListener('click', resetBoard);
    mazeBtn.addEventListener('click', generateMazeWithTerrains);
    speedSlider.addEventListener('input', (e) => { animationSpeed = 201 - e.target.value; });
});