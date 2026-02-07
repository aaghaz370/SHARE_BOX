const API_BASE = '/api';
const urlParams = new URLSearchParams(window.location.search);
const userId = urlParams.get('u');

// State
let allLinks = [];
let categories = new Set();
let currentFilter = 'all';
let currentSort = 'date-desc';

// Elements
const linksGrid = document.getElementById('links-grid');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const categorySelect = document.getElementById('category-select');

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (!userId) {
        linksGrid.innerHTML = '<div class="loader">⚠️ Error: Missing User ID</div>';
        return;
    }
    fetchStats();
    fetchLinks();
});

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/stats?u=${userId}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        document.getElementById('username').innerText = data.username;
        document.getElementById('plan-badge').innerText = data.plan; // || 'FREE';

        if (data.bot_username) window.bot_username = data.bot_username;

        animateValue('total-links', data.total_links);
        animateValue('total-views', data.total_views);

    } catch (e) {
        console.error('Stats Error:', e);
    }
}

async function fetchLinks() {
    try {
        linksGrid.innerHTML = '<div class="loader">Loading...</div>';
        const res = await fetch(`${API_BASE}/links?u=${userId}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        allLinks = data.links;

        // Extract Categories
        categories.clear();
        allLinks.forEach(l => {
            if (l.category) categories.add(l.category);
        });
        updateCategoryDropdown();

        applyFilters(); // Initial Render

    } catch (e) {
        linksGrid.innerHTML = `<div class="loader">❌ Error: ${e.message}</div>`;
    }
}

function updateCategoryDropdown() {
    categorySelect.innerHTML = '<option value="all">All Categories</option>';
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat;
        option.innerText = cat;
        categorySelect.appendChild(option);
    });
}

function applyFilters() {
    const term = searchInput.value.toLowerCase();
    const cat = categorySelect.value;
    const sort = sortSelect.value;

    // Filter
    let filtered = allLinks.filter(l => {
        const matchSearch = (l.name && l.name.toLowerCase().includes(term)) ||
            (l.link_id && l.link_id.toLowerCase().includes(term));
        const matchCat = cat === 'all' || l.category === cat;
        return matchSearch && matchCat;
    });

    // Sort
    filtered.sort((a, b) => {
        switch (sort) {
            case 'date-desc': return new Date(b.created_at || 0) - new Date(a.created_at || 0);
            case 'date-asc': return new Date(a.created_at || 0) - new Date(b.created_at || 0);
            case 'name-asc': return (a.name || '').localeCompare(b.name || '');
            case 'name-desc': return (b.name || '').localeCompare(a.name || '');
            case 'views-desc': return (b.views || 0) - (a.views || 0);
            default: return 0;
        }
    });

    renderLinks(filtered);
}

function renderLinks(links) {
    if (links.length === 0) {
        linksGrid.innerHTML = '<div class="loader">No links found matching criteria.</div>';
        return;
    }

    const baseOrigin = window.location.origin;
    const botUser = window.bot_username || 'SHAREBOXBOT';

    linksGrid.innerHTML = links.map(link => {
        const shareUrl = `${baseOrigin}/share/${link.link_id}`;

        return `
        <div class="link-card glass">
            <div class="link-header">
                <div class="link-info-top">
                   <h4>${link.name || 'Untitled Link'}</h4>
                   <span class="category-tag">${link.category || 'Uncategorized'}</span>
                </div>
                <!-- Action Buttons -->
                <div class="actions-top">
                    <button class="copy-btn" onclick="copyLink('${shareUrl}')" title="Copy Link">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                    <a href="${shareUrl}" target="_blank" class="copy-btn open-link-btn" title="Open">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    </a>
                </div>
            </div>
            
            <div class="link-details">
                <div class="meta-item">
                    <i class="fa-solid fa-file"></i>
                    <span>${link.file_count || 0} Files</span>
                </div>
                <div class="meta-item">
                    <i class="fa-solid fa-eye"></i>
                    <span>${link.views || 0} Views</span>
                </div>
            </div>
            
            <div class="link-footer">
                <span class="date">${formatDate(link.created_at)}</span>
                <span class="id-badge">#${link.link_id}</span>
            </div>
        </div>
        `;
    }).join('');
}

function filterCategory(cat) {
    // For sidebar clicks
    categorySelect.value = cat === 'Favorites' ? 'all' : cat; // Handle favorites later?
    if (cat === 'all') categorySelect.value = 'all';
    applyFilters();
    // Close mobile menu if we had one?
}

function copyLink(url) {
    navigator.clipboard.writeText(url).then(() => {
        showToast();
    });
}

function showToast() {
    const toast = document.getElementById('toast');
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function formatDate(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function animateValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value;
}
