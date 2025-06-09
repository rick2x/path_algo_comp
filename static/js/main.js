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
    let comparisonStats = []; // For comparison table
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

    // --- Comparison Table ---
    function renderComparisonTable() {
        const tableBody = document.querySelector("#comparison-table tbody");
        if (!tableBody) return; // Guard clause if table doesn't exist
        tableBody.innerHTML = ''; // Clear existing rows
        comparisonStats.forEach(stat => {
            const row = tableBody.insertRow();
            row.insertCell().textContent = stat.algorithmName;
            row.insertCell().textContent = stat.pathCost;
            row.insertCell().textContent = stat.pathLength;
            row.insertCell().textContent = stat.nodesExplored;
            row.insertCell().textContent = stat.executionTimeMs;
            row.insertCell().textContent = stat.pathFound ? 'Yes' : 'No';
        });
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
            
            const pathFound = data.path.length > 0;
            let currentCost = "N/A";

            if (pathFound) {
                if (data.path_cost !== undefined) { // Backend sent total_cost (e.g., Bi-A*)
                    currentCost = data.path_cost;
                } else if (selectedAlgorithm === 'bfs') {
                    // BFS path cost is specifically calculated by backend and stored in g of end node
                    const endNodeData = data.visited_nodes.find(n => n.pos[0] === endNode.row && n.pos[1] === endNode.col);
                    if (endNodeData) {
                        currentCost = endNodeData.g;
                    } else if (data.path.length > 0) { // Fallback for BFS if end node not in visited_nodes
                        const lastPathNodePos = data.path[data.path.length-1];
                        const lastPathNodeData = data.visited_nodes.find(n => n.pos[0] === lastPathNodePos[0] && n.pos[1] === lastPathNodePos[1]);
                        if(lastPathNodeData) currentCost = lastPathNodeData.g;
                    }
                } else { // For A*, Dijkstra, GBFS
                    const finalPathNode = data.visited_nodes.find(n => n.pos[0] === endNode.row && n.pos[1] === endNode.col);
                    if (finalPathNode) {
                        currentCost = finalPathNode.g;
                    } else { // If end node not in visited for some reason, take last node of path
                         const lastNodeInPath = data.path[data.path.length -1];
                         const lastNodeData = data.visited_nodes.find(n => n.pos[0] === lastNodeInPath[0] && n.pos[1] === lastNodeInPath[1]);
                         if(lastNodeData) currentCost = lastNodeData.g;
                    }
                }
                // Refined pathCostDisplay content
                pathCostDisplay.textContent = `Result: Path Found! Cost: ${currentCost} | Length: ${data.path.length} steps | Explored: ${data.visited_nodes.length} nodes | Time: ${data.execution_time_ms}ms`;
                addToLog(`🏁 Path Found! Total cost: <span class="highlight">${currentCost}</span>, Steps: <span class="highlight">${data.path.length}</span>.`);
                addToLog(`📊 Stats: Explored <span class="highlight">${data.visited_nodes.length}</span> nodes in <span class="highlight">${data.execution_time_ms}ms</span>.`);
                await animatePath(data.path);
            } else {
                // Refined pathCostDisplay content for no path found
                pathCostDisplay.textContent = `Result: No Path Found. Explored: ${data.visited_nodes.length} nodes | Time: ${data.execution_time_ms}ms`;
                addToLog(`❌ No path could be found. Explored <span class="highlight">${data.visited_nodes.length}</span> nodes in <span class="highlight">${data.execution_time_ms}ms</span>.`);
            }

            comparisonStats.push({
              algorithmName: algoName,
              pathCost: pathFound ? currentCost : "N/A",
              pathLength: pathFound ? data.path.length : "N/A",
              nodesExplored: data.visited_nodes.length,
              executionTimeMs: data.execution_time_ms,
              pathFound: pathFound
            });
            renderComparisonTable();

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
                // Display G, H, and F scores for A*, Dijkstra, GBFS, and Bidirectional A*
                if(algorithm === 'astar' || algorithm === 'dijkstra' || algorithm === 'gbfs' || algorithm === 'bidirectional_astar') {
                    cellElement.querySelector('.g-score').textContent = nodeData.g;
                    cellElement.querySelector('.h-score').textContent = nodeData.h.toFixed(0);
                    // F-score for GBFS might be just H, or G+H depending on Python implementation.
                    // For Bidirectional A*, f, g, h are from the perspective of its respective search direction.
                    cellElement.querySelector('.f-score').textContent = nodeData.f.toFixed(0); 
                } else { // BFS
                    cellElement.querySelector('.g-score').textContent = nodeData.g;
                }
            }
            
            let logMessage;
            if (algorithm === 'bfs') {
                logMessage = `Visiting [${row}, ${col}], steps: <span class="highlight">${nodeData.g}</span>.`;
            } else if (algorithm === 'gbfs') {
                logMessage = `Evaluating [${row}, ${col}] based on heuristic. H: <span class="highlight">${nodeData.h.toFixed(0)}</span>, G: <span class="highlight">${nodeData.g}</span>.`;
            } else if (algorithm === 'bidirectional_astar') {
                // The 'dir' field could be used here: nodeData.dir === 'fwd' ? '(Fwd)' : '(Bwd)'
                logMessage = `Evaluating [${row}, ${col}] (Bi-A*). G: <span class="highlight">${nodeData.g}</span>, H: <span class="highlight">${nodeData.h.toFixed(0)}</span>, F: <span class="highlight">${nodeData.f.toFixed(0)}</span>.`;
            }
            else { // A* and Dijkstra
                logMessage = `Evaluating [${row}, ${col}]. G: <span class="highlight">${nodeData.g}</span>, H: <span class="highlight">${nodeData.h.toFixed(0)}</span>, F: <span class="highlight">${nodeData.f.toFixed(0)}</span>.`;
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
        // Clear comparison stats when generating a new maze
        comparisonStats = [];
        renderComparisonTable();
        
        resetBoard(); // resetBoard also clears log and calls addToLog
        // clearLog(); // Already called by resetBoard
        addToLog("Generating a new, imperfect maze..."); // This will be after resetBoard's message
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
        // Clear comparison stats when resetting the board
        comparisonStats = []; 
        renderComparisonTable();
        addToLog("Board has been reset. Create a maze or start visualizing!");
    }

    function toggleButtons(enabled) {
        startBtn.disabled = !enabled;
        mazeBtn.disabled = !enabled;
        resetBtn.disabled = !enabled;
    }

    // --- Initial Setup ---
    createGrid();
    renderComparisonTable(); // Initial render of the (empty) comparison table
    addToLog("Welcome! Select an algorithm and click 'Generate Maze'.");

    const clearComparisonBtn = document.getElementById('clear-comparison-btn');
    if (clearComparisonBtn) { // Ensure button exists before adding listener
        clearComparisonBtn.addEventListener('click', () => {
            comparisonStats = [];
            renderComparisonTable();
            addToLog("Comparison data cleared.");
        });
    }

    startBtn.addEventListener('click', visualize);
    resetBtn.addEventListener('click', resetBoard);
    mazeBtn.addEventListener('click', generateMazeWithTerrains);
    speedSlider.addEventListener('input', (e) => { animationSpeed = 201 - e.target.value; });
});