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
    const comparisonTableBody = document.querySelector("#comparison-table tbody");
    const clearComparisonBtn = document.getElementById('clear-comparison-btn');
    const stepForwardBtn = document.getElementById('step-forward-btn');
    const resumeBtn = document.getElementById('resume-btn');
    // const stepBackwardBtn = document.getElementById('step-backward-btn');

    // --- Grid & State Configuration ---
    const NUM_COLS = 50;
    const NUM_ROWS = 25;
    let terrainGrid = [];
    let comparisonStats = []; // For comparison table
    let startNode = { row: 12, col: 10 };
    let endNode = { row: 12, col: 40 };
    let animationSpeed = 50;
    let isMouseDown = false, isDraggingStart = false, isDraggingEnd = false, isVisualizing = false;
    let isPaused = false;
    let currentStepIndex = 0;
    let visitedNodesCache = [];
    let pathCache = [];
    let currentPhase = 'search'; // 'search' or 'path'

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
        // const tableBody = document.querySelector("#comparison-table tbody"); // Cached as comparisonTableBody
        if (!comparisonTableBody) return; // Guard clause if table doesn't exist
        comparisonTableBody.innerHTML = ''; // Clear existing rows
        comparisonStats.forEach(stat => {
            const row = comparisonTableBody.insertRow();
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
            else if (terrainType === 4) cell.classList.add('forest'); // Added Forest
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
    let fullVisualizationData = {}; // To store data for finalizeVisualization when stepping

    async function visualize() {
        if (isVisualizing) return; // Already running or paused
        
        isVisualizing = true; // Master flag for ongoing visualization
        isPaused = false;
        currentStepIndex = 0;
        visitedNodesCache = [];
        pathCache = [];
        currentPhase = 'search';
        fullVisualizationData = {}; // Reset

        clearLog();
        const selectedAlgorithm = algorithmSelect.value;
        const algoName = algorithmSelect.options[algorithmSelect.selectedIndex].text;
        addToLog(`▶️ Initializing ${algoName} for stepping or animation...`);

        // Clear previous visual states
        // It now safely clears previous animation states and scores.
        document.querySelectorAll('.cell').forEach(c => {
            c.classList.remove('open', 'closed', 'path');
            const gScoreEl = c.querySelector('.g-score');
            const hScoreEl = c.querySelector('.h-score');
            const fScoreEl = c.querySelector('.f-score');
            if (gScoreEl) gScoreEl.textContent = '';
            if (hScoreEl) hScoreEl.textContent = '';
            if (fScoreEl) fScoreEl.textContent = '';
        });
        updateNodeDisplay(); // Redraw start/end nodes and terrain

        toggleButtons(false); // Disables main buttons, enables step buttons via updateStepButtonStates if paused

        const payload = {
            grid: terrainGrid,
            start: [startNode.row, startNode.col],
            end: [endNode.row, endNode.col],
            algorithm: selectedAlgorithm
        };

        try {
            const response = await fetch('/solve', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            visitedNodesCache = data.visited_nodes;
            pathCache = data.path;
            fullVisualizationData = data; // Store for finalizeVisualization

            isPaused = true; // Start in paused state
            currentStepIndex = 0;
            currentPhase = 'search';

            addToLog("Data loaded. Click 'Step Forward' or 'Resume Animation'.");
            handleStep(); // Show the first step
            updateStepButtonStates(); // Update buttons based on new state

            // Original animation and finalize logic is now predominantly in handleStep and resume,
            // or directly in finalizeVisualization if stepping through everything.

        } catch (error) {
            console.error("Error during visualization setup:", error);
            addToLog(`🛑 An error occurred: ${error.message}`);
            isVisualizing = false;
            isPaused = false;
            toggleButtons(true);
            updateStepButtonStates();
        }
    }

    // dataForFinalize now directly uses fullVisualizationData
    function finalizeVisualization(pathFoundSuccess, algoNameForFinalize, selectedAlgorithmForFinalize) {
        const dataToUse = fullVisualizationData; // Use the stored full data

        let currentCost = "N/A";
        if (pathFoundSuccess) {
            if (dataToUse.path_cost !== undefined) { // Changed dataForFinalize to dataToUse
                currentCost = dataToUse.path_cost;    // Changed dataForFinalize to dataToUse
            } else if (selectedAlgorithmForFinalize === 'bfs') {
                const endNodeData = dataToUse.visited_nodes.find(n => n.pos[0] === endNode.row && n.pos[1] === endNode.col); // Changed dataForFinalize to dataToUse
                if (endNodeData) {
                    currentCost = endNodeData.g;
                } else if (dataToUse.path.length > 0) { // Changed dataForFinalize to dataToUse
                    const lastPathNodePos = dataToUse.path[dataToUse.path.length - 1]; // Changed dataForFinalize to dataToUse
                    const lastPathNodeData = dataToUse.visited_nodes.find(n => n.pos[0] === lastPathNodePos[0] && n.pos[1] === lastPathNodePos[1]); // Changed dataForFinalize to dataToUse
                    if (lastPathNodeData) currentCost = lastPathNodeData.g;
                }
            } else { // For A*, Dijkstra, GBFS
                const finalPathNode = dataToUse.visited_nodes.find(n => n.pos[0] === endNode.row && n.pos[1] === endNode.col); // Changed dataForFinalize to dataToUse
                if (finalPathNode) {
                    currentCost = finalPathNode.g;
                } else if (dataToUse.path.length > 0) { // Changed dataForFinalize to dataToUse
                    const lastNodeInPath = dataToUse.path[dataToUse.path.length - 1]; // Changed dataForFinalize to dataToUse
                    const lastNodeData = dataToUse.visited_nodes.find(n => n.pos[0] === lastNodeInPath[0] && n.pos[1] === lastNodeInPath[1]); // Changed dataForFinalize to dataToUse
                    if (lastNodeData) currentCost = lastNodeData.g;
                }
            }
            pathCostDisplay.textContent = `Result: Path Found! Cost: ${currentCost} | Length: ${dataToUse.path.length} steps | Explored: ${dataToUse.visited_nodes.length} nodes | Time: ${dataToUse.execution_time_ms}ms`; // Changed dataForFinalize to dataToUse
            addToLog(`🏁 Path Found! Total cost: <span class="highlight">${currentCost}</span>, Steps: <span class="highlight">${dataToUse.path.length}</span>.`); // Changed dataForFinalize to dataToUse
            addToLog(`📊 Stats: Explored <span class="highlight">${dataToUse.visited_nodes.length}</span> nodes in <span class="highlight">${dataToUse.execution_time_ms}ms</span>.`); // Changed dataForFinalize to dataToUse
        } else {
            pathCostDisplay.textContent = `Result: No Path Found. Explored: ${dataToUse.visited_nodes.length} nodes | Time: ${dataToUse.execution_time_ms}ms`; // Changed dataForFinalize to dataToUse
            addToLog(`❌ No path could be found. Explored <span class="highlight">${dataToUse.visited_nodes.length}</span> nodes in <span class="highlight">${dataToUse.execution_time_ms}ms</span>.`); // Changed dataForFinalize to dataToUse
        }

        comparisonStats.push({
            algorithmName: algoNameForFinalize,
            pathCost: pathFoundSuccess ? currentCost : "N/A",
            pathLength: pathFoundSuccess ? dataToUse.path.length : "N/A", // Changed dataForFinalize to dataToUse
            nodesExplored: dataToUse.visited_nodes.length, // Changed dataForFinalize to dataToUse
            executionTimeMs: dataToUse.execution_time_ms, // Changed dataForFinalize to dataToUse
            pathFound: pathFoundSuccess
        });
        renderComparisonTable();

        isVisualizing = false;
        isPaused = false; // Ensure pause is reset
        toggleButtons(true); // Re-enable main controls, this will also call updateStepButtonStates
    }

    // --- Animation & Storytelling ---
    // --- Core Visualization Logic ---
    // (visualize function is above this)
    // (finalizeVisualization function is above this)

    async function handleStep() {
        if (!isPaused) return;

        const selectedAlgorithm = algorithmSelect.value;
        const algoName = algorithmSelect.options[algorithmSelect.selectedIndex].text;

        if (currentPhase === 'search') {
            if (currentStepIndex < visitedNodesCache.length) {
                const nodeData = visitedNodesCache[currentStepIndex];
                renderNodeState(nodeData, selectedAlgorithm);
                currentStepIndex++;
                if (currentStepIndex >= visitedNodesCache.length) {
                    currentPhase = 'path';
                    currentStepIndex = 0;
                    if (pathCache.length === 0) {
                        isPaused = false;
                        // Use fullVisualizationData which contains the original execution time
                        finalizeVisualization(false, algoName, selectedAlgorithm);
                    } else {
                        addToLog("Search complete. Path found. Step through path or resume.");
                    }
                }
            }
        } else if (currentPhase === 'path') {
            if (currentStepIndex < pathCache.length) {
                if (currentStepIndex === 0) {
                    addToLog("Tracing the optimal path back to the start...");
                }
                const pos = pathCache[currentStepIndex];
                renderPathStep(pos);
                currentStepIndex++;
                if (currentStepIndex >= pathCache.length) {
                    isPaused = false;
                    // Use fullVisualizationData
                    finalizeVisualization(true, algoName, selectedAlgorithm);
                }
            }
        }
        updateStepButtonStates();
    }

    // --- Animation & Storytelling ---

    // Renders a single node's state (extracted from animateSearch)
    function renderNodeState(nodeData, algorithm) {
        const [row, col] = nodeData.pos;
        const cellElement = document.querySelector(`[data-row='${row}'][data-col='${col}']`);
        if (!cellElement) return; // Should not happen

        const isStartNode = (row === startNode.row && col === startNode.col);
        const isEndNode = (row === endNode.row && col === endNode.col);

        if (!isStartNode && !isEndNode) {
            cellElement.classList.add('closed');
            // Display G, H, and F scores
            if (algorithm === 'astar' || algorithm === 'dijkstra' || algorithm === 'gbfs' || algorithm === 'bidirectional_astar') {
                cellElement.querySelector('.g-score').textContent = nodeData.g;
                cellElement.querySelector('.h-score').textContent = nodeData.h.toFixed(0);
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
            const direction = nodeData.dir === 'fwd' ? 'Fwd' : (nodeData.dir === 'bwd' ? 'Bwd' : 'Dir?');
            logMessage = `Evaluating [${row}, ${col}] (Bi-A* ${direction}). G: <span class="highlight">${nodeData.g}</span>, H: <span class="highlight">${nodeData.h.toFixed(0)}</span>, F: <span class="highlight">${nodeData.f.toFixed(0)}</span>.`;
        } else { // A* and Dijkstra
            logMessage = `Evaluating [${row}, ${col}]. G: <span class="highlight">${nodeData.g}</span>, H: <span class="highlight">${nodeData.h.toFixed(0)}</span>, F: <span class="highlight">${nodeData.f.toFixed(0)}</span>.`;
        }
        addToLog(logMessage);
    }

    // Renders a single path step (extracted from animatePath)
    function renderPathStep(pos) {
        const [row, col] = pos;
        const cellElement = document.querySelector(`[data-row='${row}'][data-col='${col}']`);
        if (!cellElement) return; // Should not happen

        cellElement.classList.remove('closed'); // In case it was marked closed
        cellElement.classList.add('path');
    }

    async function animateSearch(visitedNodes, algorithm) {
        // const terrainNames = { 0: "Plain", 1: "Wall", 2: "Water", 3: "Mud", 4: "Forest" }; // No longer needed here
        while (currentStepIndex < visitedNodes.length && !isPaused) {
            const nodeData = visitedNodes[currentStepIndex];
            renderNodeState(nodeData, algorithm);
            currentStepIndex++;
            await new Promise(resolve => setTimeout(resolve, animationSpeed / 5));
        }
        // If loop finishes (not paused), it means search animation is complete.
        // Transition to path or finalize is handled by resumeBtn logic or handleStep.
    }

    async function animatePath(path) {
        // addToLog("Tracing the optimal path back to the start..."); // Moved to where animatePath is called
        while (currentStepIndex < path.length && !isPaused) {
            const pos = path[currentStepIndex];
            renderPathStep(pos);
            currentStepIndex++;
            await new Promise(resolve => setTimeout(resolve, animationSpeed));
        }
        // If loop finishes (not paused), path animation is complete.
        // Finalization is handled by resumeBtn logic or handleStep.
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
        const terrainConfig = [
            { type: 2, count: 4, maxSize: 50 }, // Water
            { type: 3, count: 6, maxSize: 30 }, // Mud
            { type: 4, count: 5, maxSize: 40 }  // Forest (new)
        ];
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
        isPaused = false; // Reset pause state
        currentStepIndex = 0;
        visitedNodesCache = [];
        pathCache = [];
        currentPhase = 'search';
        fullVisualizationData = {};

        createGrid(); // This also calls updateNodeDisplay
        clearLog();
        comparisonStats = [];
        renderComparisonTable();

        toggleButtons(true); // This will call updateStepButtonStates
        addToLog("Board has been reset. Create a maze or start visualizing!");
    }

    function toggleButtons(enabled) {
        startBtn.disabled = isVisualizing || !enabled; // Disable if visualizing or general disable
        mazeBtn.disabled = isVisualizing || !enabled;
        resetBtn.disabled = isVisualizing || !enabled;
        algorithmSelect.disabled = isVisualizing || !enabled;

        // Step buttons are handled by updateStepButtonStates
        updateStepButtonStates();
    }

    function updateStepButtonStates() {
        if (!stepForwardBtn || !resumeBtn) return; // Buttons might not exist in all test environments

        const canStepForward = isPaused &&
                               ( (currentPhase === 'search' && currentStepIndex < visitedNodesCache.length) ||
                                 (currentPhase === 'path' && currentStepIndex < pathCache.length) );

        stepForwardBtn.disabled = !canStepForward;
        resumeBtn.disabled = !isPaused;

        // Adjust main control buttons based on isPaused and isVisualizing
        // isVisualizing is the master flag for an ongoing visualization process (paused or not)
        startBtn.disabled = isVisualizing;
        mazeBtn.disabled = isVisualizing;
        resetBtn.disabled = isVisualizing;
        algorithmSelect.disabled = isVisualizing;
    }

    // --- Initial Setup ---
    createGrid();
    renderComparisonTable(); // Initial render of the (empty) comparison table
    addToLog("Welcome! Select an algorithm and click 'Generate Maze'.");

    // const clearComparisonBtn = document.getElementById('clear-comparison-btn'); // Cached
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

    stepForwardBtn.addEventListener('click', () => {
        if (isPaused) {
            // Log is handled by renderNodeState or start of path rendering in handleStep
            handleStep();
        }
    });

    resumeBtn.addEventListener('click', async () => {
        if (isPaused) {
            isPaused = false;
            updateStepButtonStates(); // Disable step/resume, re-evaluate main buttons

            const selectedAlgorithm = algorithmSelect.value;
            const algoName = algorithmSelect.options[algorithmSelect.selectedIndex].text;

            if (currentPhase === 'search') {
                addToLog("▶️ Resuming search animation...");
                await animateSearch(visitedNodesCache, selectedAlgorithm);

                // After animateSearch completes (or is interrupted by pause)
                if (!isPaused) { // If not paused again during animation
                    if (currentStepIndex >= visitedNodesCache.length) { // Search fully completed
                        currentPhase = 'path';
                        currentStepIndex = 0;
                        if (pathCache.length > 0) {
                            addToLog("▶️ Resuming path animation...");
                            await animatePath(pathCache);
                            if (!isPaused && currentStepIndex >= pathCache.length) { // Path fully completed
                                finalizeVisualization(true, algoName, selectedAlgorithm);
                            } else if (isPaused) {
                                // Was paused during path animation
                                addToLog("Animation paused during path tracing.");
                            }
                        } else { // No path found after search
                            finalizeVisualization(false, algoName, selectedAlgorithm);
                        }
                    } else {
                         // Was paused during search animation
                         addToLog("Animation paused during search.");
                    }
                } else {
                     addToLog("Animation paused during search.");
                }
            } else if (currentPhase === 'path') {
                addToLog("▶️ Resuming path animation...");
                await animatePath(pathCache);
                if (!isPaused && currentStepIndex >= pathCache.length) { // Path fully completed
                    finalizeVisualization(true, algoName, selectedAlgorithm);
                } else if (isPaused) {
                    // Was paused during path animation
                    addToLog("Animation paused during path tracing.");
                }
            }
             updateStepButtonStates(); // Final check on button states
        }
    });
});