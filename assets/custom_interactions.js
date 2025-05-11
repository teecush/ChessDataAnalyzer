// Custom interactions for chess analytics dashboard

// Function to handle right-click on treemap segments
function setupTreemapRightClick() {
  // Select all treemap segments (plotly SVG elements)
  const treemapSegments = document.querySelectorAll('.treemap-container .main-svg .trace');
  
  treemapSegments.forEach(segment => {
    // Add context menu event listener
    segment.addEventListener('contextmenu', function(e) {
      e.preventDefault(); // Prevent default context menu
      
      // Get the opening name from the data attribute
      const openingName = e.target.getAttribute('data-opening');
      if (!openingName) return;
      
      // Create and show custom context menu
      showContextMenu(e.pageX, e.pageY, openingName);
    });
    
    // Add long press for mobile
    let timer;
    let longPressDuration = 500; // ms
    
    segment.addEventListener('touchstart', function(e) {
      timer = setTimeout(() => {
        const openingName = e.target.getAttribute('data-opening');
        if (openingName) {
          e.preventDefault();
          showContextMenu(e.touches[0].pageX, e.touches[0].pageY, openingName);
        }
      }, longPressDuration);
    });
    
    segment.addEventListener('touchend', function() {
      clearTimeout(timer);
    });
    
    segment.addEventListener('touchmove', function() {
      clearTimeout(timer);
    });
  });
  
  // Close context menu on click outside
  document.addEventListener('click', function() {
    const menu = document.getElementById('custom-context-menu');
    if (menu) menu.remove();
  });
}

// Function to create and show the context menu
function showContextMenu(x, y, openingName) {
  // Remove any existing context menu
  const existingMenu = document.getElementById('custom-context-menu');
  if (existingMenu) existingMenu.remove();
  
  // Create new context menu
  const menu = document.createElement('div');
  menu.id = 'custom-context-menu';
  menu.style.position = 'absolute';
  menu.style.left = `${x}px`;
  menu.style.top = `${y}px`;
  menu.style.backgroundColor = '#fff';
  menu.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
  menu.style.borderRadius = '4px';
  menu.style.padding = '5px 0';
  menu.style.zIndex = '1000';
  
  // Add menu item
  const searchYouTube = document.createElement('div');
  searchYouTube.textContent = '🎬 Search YouTube for this opening';
  searchYouTube.style.padding = '8px 12px';
  searchYouTube.style.cursor = 'pointer';
  searchYouTube.style.hover = 'background-color: #f0f0f0';
  
  searchYouTube.addEventListener('click', function() {
    const searchQuery = encodeURIComponent(`chess opening ${openingName}`);
    window.open(`https://www.youtube.com/results?search_query=${searchQuery}`, '_blank');
    menu.remove();
  });
  
  menu.appendChild(searchYouTube);
  document.body.appendChild(menu);
  
  // Handle clicking outside to close
  document.addEventListener('click', function closeMenu(e) {
    if (!menu.contains(e.target)) {
      menu.remove();
      document.removeEventListener('click', closeMenu);
    }
  });
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
  setupTreemapRightClick();
  
  // Re-setup on Streamlit render events
  const observer = new MutationObserver(function(mutations) {
    for (const mutation of mutations) {
      if (mutation.addedNodes && mutation.addedNodes.length > 0) {
        // Check if treemap was rendered
        if (document.querySelector('.treemap-container')) {
          setupTreemapRightClick();
        }
      }
    }
  });
  
  observer.observe(document.body, { childList: true, subtree: true });
});