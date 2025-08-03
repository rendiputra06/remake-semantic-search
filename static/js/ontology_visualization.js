let ontologyData = null;
let currentVisualization = null;
let selectedConcept = null;
let filteredData = null;

// Visualization filters
let visualizationFilters = {
    broader: true,
    narrower: true,
    related: true,
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('visualizationType').addEventListener('change', function() {
        updateVisualization();
    });
    
    document.getElementById('searchConcept').addEventListener('input', function() {
        searchConcepts(this.value);
    });
    
    // Filter checkboxes
    document.getElementById('filter-broader').addEventListener('change', function() {
        visualizationFilters.broader = this.checked;
        applyVisualizationFilters();
    });
    
    document.getElementById('filter-narrower').addEventListener('change', function() {
        visualizationFilters.narrower = this.checked;
        applyVisualizationFilters();
    });
    
    document.getElementById('filter-related').addEventListener('change', function() {
        visualizationFilters.related = this.checked;
        applyVisualizationFilters();
    });
    
    // Load initial data
    loadOntologyData();
});

function loadOntologyData() {
    showLoading(true);
    
    fetch('/api/ontology/admin/all')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                ontologyData = data.concepts;
                filteredData = [...ontologyData];
                updateStatistics();
                updateVisualization();
                showLoading(false);
            } else {
                showError('Gagal memuat data ontologi');
            }
        })
        .catch(error => {
            showError('Error: ' + error.message);
        });
}

function updateStatistics() {
    if (!ontologyData) return;
    
    const totalConcepts = ontologyData.length;
    let totalRelations = 0;
    let totalVerses = 0;
    
    ontologyData.forEach(concept => {
        totalRelations += (concept.broader?.length || 0) + 
                        (concept.narrower?.length || 0) + 
                        (concept.related?.length || 0);
        totalVerses += (concept.verses?.length || 0);
    });
    
    document.getElementById('totalConcepts').textContent = totalConcepts;
    document.getElementById('totalRelations').textContent = totalRelations;
    document.getElementById('totalVerses').textContent = totalVerses;
}

function updateVisualization() {
    const type = document.getElementById('visualizationType').value;
    const title = document.getElementById('visualizationType').options[
        document.getElementById('visualizationType').selectedIndex
    ].text;
    
    document.getElementById('visualizationTitle').textContent = title;
    
    switch(type) {
        case 'bubble':
            renderBubbleNetwork();
            break;
        case 'hierarchical':
            renderHierarchicalTree();
            break;
        case 'force':
            renderForceDirected();
            break;
        case 'table':
            renderTable();
            break;
        case 'cards':
            renderCards();
            break;
    }
}

function renderBubbleNetwork() {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = '';
    
    if (!filteredData || !filteredData.length) {
        container.innerHTML = '<div class="text-center py-5"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div>';
        return;
    }
    
    const graphData = createOntologyGraphData(filteredData);
    
    const options = {
        nodes: {
            shape: "circle",
            borderWidth: 2,
            shadow: true,
            font: { size: 12, color: "#ffffff" },
            scaling: { min: 15, max: 35 },
        },
        edges: {
            width: 2,
            shadow: true,
            smooth: { type: "curvedCW", roundness: 0.2 },
        },
        physics: {
            barnesHut: {
                gravitationalConstant: -2000,
                centralGravity: 0.3,
                springLength: 100,
                springConstant: 0.04,
            },
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
        }
    };
    
    currentVisualization = new vis.Network(container, graphData, options);
    
    // Add click event
    currentVisualization.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const concept = filteredData.find(c => c.id === nodeId);
            if (concept) {
                showConceptDetails(concept);
            }
        }
    });
    
    // Add hover effects
    currentVisualization.on('hoverNode', function(params) {
        const connectedNodes = currentVisualization.getConnectedNodes(params.node);
        currentVisualization.selectNodes([params.node, ...connectedNodes]);
    });
    
    currentVisualization.on('blurNode', function(params) {
        currentVisualization.unselectAll();
    });
}

function renderHierarchicalTree() {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = '';
    
    if (!filteredData || !filteredData.length) {
        container.innerHTML = '<div class="text-center py-5"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div>';
        return;
    }
    
    const treeData = createHierarchicalData(filteredData);
    
    const options = {
        nodes: {
            shape: "box",
            margin: 10,
            font: { size: 14 },
        },
        edges: {
            width: 2,
            smooth: { type: "cubicBezier" },
        },
        layout: {
            hierarchical: {
                enabled: true,
                direction: "UD",
                sortMethod: "directed",
            },
        },
        physics: false,
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
        }
    };
    
    currentVisualization = new vis.Network(container, treeData, options);
    
    // Add click event
    currentVisualization.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const concept = filteredData.find(c => c.id === nodeId);
            if (concept) {
                showConceptDetails(concept);
            }
        }
    });
}

function renderForceDirected() {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = '';
    
    if (!filteredData || !filteredData.length) {
        container.innerHTML = '<div class="text-center py-5"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div>';
        return;
    }
    
    const forceData = createOntologyGraphData(filteredData);
    
    const options = {
        nodes: {
            shape: "dot",
            size: 20,
            font: { size: 12 },
        },
        edges: {
            width: 1,
            smooth: { type: "continuous" },
        },
        physics: {
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 100,
                springConstant: 0.08,
            },
        },
        interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
        }
    };
    
    currentVisualization = new vis.Network(container, forceData, options);
    
    // Add click event
    currentVisualization.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const concept = filteredData.find(c => c.id === nodeId);
            if (concept) {
                showConceptDetails(concept);
            }
        }
    });
}

function renderTable() {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = '';
    
    if (!filteredData || !filteredData.length) {
        container.innerHTML = '<div class="text-center py-5"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div>';
        return;
    }
    
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-hover concept-table">
                <thead class="table-dark">
                    <tr>
                        <th>ID</th>
                        <th>Label</th>
                        <th>Sinonim</th>
                        <th>Broader</th>
                        <th>Narrower</th>
                        <th>Related</th>
                        <th>Ayat</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    filteredData.forEach(concept => {
        tableHtml += `
            <tr onclick="showConceptDetails('${concept.id}')">
                <td><strong>${concept.id}</strong></td>
                <td>${concept.label}</td>
                <td>${(concept.synonyms || []).map(syn => 
                    `<span class="badge bg-info me-1">${syn}</span>`
                ).join('')}</td>
                <td>${(concept.broader || []).map(b => 
                    `<span class="badge bg-secondary me-1">${b}</span>`
                ).join('')}</td>
                <td>${(concept.narrower || []).map(n => 
                    `<span class="badge bg-secondary me-1">${n}</span>`
                ).join('')}</td>
                <td>${(concept.related || []).map(r => 
                    `<span class="badge bg-warning text-dark me-1">${r}</span>`
                ).join('')}</td>
                <td>${(concept.verses || []).map(v => 
                    `<span class="badge bg-success me-1">${v}</span>`
                ).join('')}</td>
            </tr>
        `;
    });
    
    tableHtml += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = tableHtml;
}

function renderCards() {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = '';
    
    if (!filteredData || !filteredData.length) {
        container.innerHTML = '<div class="text-center py-5"><p class="text-muted">Tidak ada data untuk ditampilkan</p></div>';
        return;
    }
    
    let cardsHtml = '<div class="row">';
    
    filteredData.forEach(concept => {
        const relationCount = (concept.broader?.length || 0) + 
                            (concept.narrower?.length || 0) + 
                            (concept.related?.length || 0);
        
        cardsHtml += `
            <div class="col-md-4 col-lg-3 mb-3">
                <div class="card concept-card h-100" onclick="showConceptDetails('${concept.id}')">
                    <div class="card-header bg-primary text-white">
                        <h6 class="mb-0">${concept.label}</h6>
                    </div>
                    <div class="card-body">
                        <p class="card-text"><strong>ID:</strong> ${concept.id}</p>
                        <p class="card-text">
                            <strong>Sinonim:</strong><br>
                            ${(concept.synonyms || []).map(syn => 
                                `<span class="badge bg-info me-1 mb-1">${syn}</span>`
                            ).join('')}
                        </p>
                        <p class="card-text">
                            <strong>Relasi:</strong> ${relationCount}<br>
                            <small class="text-muted">
                                Broader: ${concept.broader?.length || 0} | 
                                Narrower: ${concept.narrower?.length || 0} | 
                                Related: ${concept.related?.length || 0}
                            </small>
                        </p>
                        <p class="card-text">
                            <strong>Ayat:</strong> ${concept.verses?.length || 0} ayat
                        </p>
                    </div>
                </div>
            </div>
        `;
    });
    
    cardsHtml += '</div>';
    container.innerHTML = cardsHtml;
}

function createOntologyGraphData(concepts) {
    const nodes = [];
    const edges = [];
    const nodeMap = new Map();

    // Create nodes for each concept
    concepts.forEach((concept, index) => {
        // Calculate node size based on number of relations
        const relationCount =
            (concept.synonyms?.length || 0) +
            (concept.broader?.length || 0) +
            (concept.narrower?.length || 0) +
            (concept.related?.length || 0);
        const nodeSize = Math.max(20, Math.min(35, 20 + relationCount * 2));

        // Determine node color based on concept type
        let nodeColor = "#007bff"; // Default blue
        if (concept.broader && concept.broader.length > 0) {
            nodeColor = "#28a745"; // Green for broader concepts
        } else if (concept.narrower && concept.narrower.length > 0) {
            nodeColor = "#ffc107"; // Yellow for narrower concepts
        } else if (concept.related && concept.related.length > 0) {
            nodeColor = "#dc3545"; // Red for related concepts
        }

        const node = {
            id: concept.id,
            label: concept.label,
            size: nodeSize,
            color: {
                background: nodeColor,
                border: "#ffffff",
                highlight: {
                    background: nodeColor,
                    border: "#ffffff",
                },
            },
            font: {
                size: Math.max(10, Math.min(16, 10 + relationCount)),
                color: "#ffffff",
                face: "Arial",
            },
            title: createNodeTooltip(concept),
            conceptId: concept.id,
        };

        nodes.push(node);
        nodeMap.set(concept.id, node);
    });

    // Create edges for relationships based on filters
    concepts.forEach((concept) => {
        // Broader relationships
        if (concept.broader && visualizationFilters.broader) {
            concept.broader.forEach((broaderId) => {
                if (nodeMap.has(broaderId)) {
                    edges.push({
                        from: concept.id,
                        to: broaderId,
                        color: {
                            color: "#28a745",
                            width: 2,
                        },
                        arrows: "to",
                        smooth: { type: "curvedCW", roundness: 0.2 },
                    });
                }
            });
        }

        // Narrower relationships
        if (concept.narrower && visualizationFilters.narrower) {
            concept.narrower.forEach((narrowerId) => {
                if (nodeMap.has(narrowerId)) {
                    edges.push({
                        from: concept.id,
                        to: narrowerId,
                        color: {
                            color: "#ffc107",
                            width: 2,
                        },
                        arrows: "to",
                        smooth: { type: "curvedCW", roundness: 0.2 },
                    });
                }
            });
        }

        // Related relationships
        if (concept.related && visualizationFilters.related) {
            concept.related.forEach((relatedId) => {
                if (nodeMap.has(relatedId)) {
                    edges.push({
                        from: concept.id,
                        to: relatedId,
                        color: {
                            color: "#dc3545",
                            width: 1,
                        },
                        smooth: { type: "curvedCW", roundness: 0.1 },
                    });
                }
            });
        }
    });

    return {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
    };
}

function createHierarchicalData(concepts) {
    const nodes = [];
    const edges = [];
    const nodeMap = new Map();

    // Create nodes
    concepts.forEach((concept) => {
        const node = {
            id: concept.id,
            label: concept.label,
            shape: "box",
            color: {
                background: "#007bff",
                border: "#ffffff",
            },
            font: { size: 14, color: "#ffffff" },
            title: createNodeTooltip(concept),
        };
        nodes.push(node);
        nodeMap.set(concept.id, node);
    });

    // Create hierarchical edges based on broader relationships
    concepts.forEach((concept) => {
        if (concept.broader && visualizationFilters.broader) {
            concept.broader.forEach((broaderId) => {
                if (nodeMap.has(broaderId)) {
                    edges.push({
                        from: concept.id,
                        to: broaderId,
                        color: { color: "#28a745", width: 2 },
                        arrows: "to",
                    });
                }
            });
        }
    });

    return {
        nodes: new vis.DataSet(nodes),
        edges: new vis.DataSet(edges),
    };
}

function createNodeTooltip(concept) {
    let tooltip = `<strong>${concept.label}</strong><br>`;
    tooltip += `ID: ${concept.id}<br>`;
    
    if (concept.synonyms && concept.synonyms.length > 0) {
        tooltip += `Sinonim: ${concept.synonyms.join(', ')}<br>`;
    }
    
    if (concept.broader && concept.broader.length > 0) {
        tooltip += `Broader: ${concept.broader.join(', ')}<br>`;
    }
    
    if (concept.narrower && concept.narrower.length > 0) {
        tooltip += `Narrower: ${concept.narrower.join(', ')}<br>`;
    }
    
    if (concept.related && concept.related.length > 0) {
        tooltip += `Related: ${concept.related.join(', ')}<br>`;
    }
    
    if (concept.verses && concept.verses.length > 0) {
        tooltip += `Ayat: ${concept.verses.join(', ')}`;
    }
    
    return tooltip;
}

function applyVisualizationFilters() {
    // Re-render current visualization with filters
    updateVisualization();
    
    // Show filter summary
    const activeFilters = Object.entries(visualizationFilters)
        .filter(([key, value]) => value)
        .map(([key]) => key)
        .join(", ");

    showToast(`Filter diterapkan: ${activeFilters || "Semua relasi"}`, "success");
}

function searchConcepts(query) {
    if (!query.trim()) {
        filteredData = [...ontologyData];
    } else {
        const searchTerm = query.toLowerCase();
        filteredData = ontologyData.filter(concept => 
            concept.label.toLowerCase().includes(searchTerm) ||
            concept.id.toLowerCase().includes(searchTerm) ||
            (concept.synonyms && concept.synonyms.some(syn => 
                syn.toLowerCase().includes(searchTerm)
            ))
        );
    }
    
    updateVisualization();
}

function showConceptDetails(conceptId) {
    // Handle both concept object and concept ID
    let concept;
    if (typeof conceptId === 'string') {
        concept = filteredData.find(c => c.id === conceptId);
    } else {
        concept = conceptId;
    }
    
    if (!concept) return;
    
    selectedConcept = concept;
    
    const modal = new bootstrap.Modal(document.getElementById('conceptModal'));
    document.getElementById('conceptModalTitle').textContent = concept.label;
    
    let bodyHtml = `
        <div class="row">
            <div class="col-md-6">
                <h6>Informasi Dasar</h6>
                <ul class="list-unstyled">
                    <li><strong>ID:</strong> ${concept.id}</li>
                    <li><strong>Label:</strong> ${concept.label}</li>
                    <li><strong>Jumlah Ayat:</strong> ${concept.verses?.length || 0}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Sinonim</h6>
                <div class="mb-3">
                    ${(concept.synonyms || []).map(syn => 
                        `<span class="badge bg-secondary me-1">${syn}</span>`
                    ).join('')}
                </div>
                
                <h6>Ayat Terkait</h6>
                <div class="mb-3">
                    ${(concept.verses || []).map(verse => 
                        `<span class="badge bg-info me-1">${verse}</span>`
                    ).join('')}
                </div>
            </div>
        </div>
    `;
    
    if (concept.broader && concept.broader.length > 0) {
        bodyHtml += `
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Konsep Lebih Luas (Broader)</h6>
                    <div class="mb-3">
                        ${concept.broader.map(broaderId => {
                            const broaderConcept = ontologyData.find(c => c.id === broaderId);
                            return broaderConcept ? 
                                `<span class="badge bg-primary me-1">${broaderConcept.label}</span>` : 
                                `<span class="badge bg-secondary me-1">${broaderId}</span>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    if (concept.narrower && concept.narrower.length > 0) {
        bodyHtml += `
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Konsep Lebih Spesifik (Narrower)</h6>
                    <div class="mb-3">
                        ${concept.narrower.map(narrowerId => {
                            const narrowerConcept = ontologyData.find(c => c.id === narrowerId);
                            return narrowerConcept ? 
                                `<span class="badge bg-success me-1">${narrowerConcept.label}</span>` : 
                                `<span class="badge bg-secondary me-1">${narrowerId}</span>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    if (concept.related && concept.related.length > 0) {
        bodyHtml += `
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Konsep Terkait</h6>
                    <div class="mb-3">
                        ${concept.related.map(relatedId => {
                            const relatedConcept = ontologyData.find(c => c.id === relatedId);
                            return relatedConcept ? 
                                `<span class="badge bg-warning me-1">${relatedConcept.label}</span>` : 
                                `<span class="badge bg-secondary me-1">${relatedId}</span>`;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    }
    
    document.getElementById('conceptModalBody').innerHTML = bodyHtml;
    modal.show();
}

function showRelatedConcepts() {
    if (!selectedConcept) return;
    
    // Filter data to show only related concepts
    const relatedIds = new Set([
        ...(selectedConcept.broader || []),
        ...(selectedConcept.narrower || []),
        ...(selectedConcept.related || []),
        selectedConcept.id
    ]);
    
    filteredData = ontologyData.filter(concept => 
        relatedIds.has(concept.id)
    );
    
    // Update visualization with filtered data
    updateVisualization();
    
    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('conceptModal')).hide();
}

function showLoading(show) {
    const spinner = document.getElementById('loadingSpinner');
    const area = document.getElementById('visualizationArea');
    
    if (show) {
        spinner.style.display = 'block';
        area.style.display = 'none';
    } else {
        spinner.style.display = 'none';
        area.style.display = 'block';
    }
}

function showError(message) {
    const container = document.getElementById('visualizationArea');
    container.innerHTML = `
        <div class="alert alert-danger m-3">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
}

function showToast(message, type = 'success') {
    // Create toast notification
    const toastContainer = document.createElement('div');
    toastContainer.className = 'position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = '1055';
    
    const color = type === 'success' ? 'bg-success' : type === 'danger' ? 'bg-danger' : 'bg-warning';
    
    toastContainer.innerHTML = `
        <div class="toast align-items-center text-white ${color} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toastContainer);
    const toastEl = toastContainer.querySelector('.toast');
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toastContainer);
    });
}

function resetView() {
    if (currentVisualization && currentVisualization.fit) {
        currentVisualization.fit();
    }
}

function zoomIn() {
    if (currentVisualization && currentVisualization.moveTo) {
        const scale = currentVisualization.getScale();
        currentVisualization.moveTo({ scale: scale * 1.2 });
    }
}

function zoomOut() {
    if (currentVisualization && currentVisualization.moveTo) {
        const scale = currentVisualization.getScale();
        currentVisualization.moveTo({ scale: scale * 0.8 });
    }
}

function fitView() {
    if (currentVisualization && currentVisualization.fit) {
        currentVisualization.fit();
    }
} 