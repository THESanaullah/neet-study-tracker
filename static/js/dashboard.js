// Dashboard interactions and chapter progress management

document.addEventListener('DOMContentLoaded', function() {
  initializeChapterCheckboxes();
  initializeRevisionButtons();
  initializeMobileMenu();
});

// Handle chapter progress checkbox updates
function initializeChapterCheckboxes() {
  const checkboxes = document.querySelectorAll('.chapter-checkbox');
  
  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      const chapterId = this.dataset.chapterId;
      const checkboxType = this.dataset.type;
      const isChecked = this.checked;
      
      updateChapterProgress(chapterId, checkboxType, isChecked);
    });
  });
}

// Send chapter progress update to server
function updateChapterProgress(chapterId, checkboxType, isChecked) {
  const data = {};
  data[checkboxType] = isChecked;
  
  fetch(`/update_chapter/${chapterId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Update UI if needed
      if (data.revision_count) {
        updateRevisionCount(chapterId, data.revision_count);
      }
      
      // Show success indicator
      showSuccessToast('Progress updated!');
      
      // Reload page to update progress percentages
      setTimeout(() => {
        location.reload();
      }, 500);
    }
  })
  .catch(err => {
    console.error('Error updating chapter:', err);
    showErrorToast('Failed to update progress. Please try again.');
  });
}

// Initialize revision logging buttons
function initializeRevisionButtons() {
  const revisionBtns = document.querySelectorAll('.log-revision-btn');
  
  revisionBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const chapterId = this.dataset.chapterId;
      const chapterName = this.dataset.chapterName;
      
      logRevision(chapterId, chapterName);
    });
  });
}

// Log a chapter revision
function logRevision(chapterId, chapterName) {
  const notes = prompt(`Logging revision for: ${chapterName}\n\nOptional notes (press OK to skip):`);
  const confidence = prompt('Confidence level (1-5, or leave blank):');
  
  const data = {
    notes: notes || '',
    confidence_level: confidence ? parseInt(confidence) : null
  };
  
  fetch(`/log_revision/${chapterId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showSuccessToast('Revision logged successfully!');
      updateRevisionCount(chapterId, data.revision_count);
      
      // Reload to update stats
      setTimeout(() => {
        location.reload();
      }, 500);
    }
  })
  .catch(err => {
    console.error('Error logging revision:', err);
    showErrorToast('Failed to log revision. Please try again.');
  });
}

// Update revision count badge in UI
function updateRevisionCount(chapterId, count) {
  const badge = document.querySelector(`[data-chapter-id="${chapterId}"] .revision-badge`);
  if (badge) {
    badge.textContent = `${count}× revised`;
  }
}

// Toast notification system
function showSuccessToast(message) {
  showToast(message, 'success');
}

function showErrorToast(message) {
  showToast(message, 'error');
}

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    background-color: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    z-index: 9999;
    animation: slideIn 0.3s ease-out;
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-in';
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOut {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Mobile menu toggle
function initializeMobileMenu() {
  const toggle = document.querySelector('.navbar-toggle');
  const menu = document.querySelector('.navbar-menu');
  
  if (toggle && menu) {
    toggle.addEventListener('click', function() {
      menu.classList.toggle('active');
    });
  }
}

// Subject filter for chapter list
function filterChapters(subject) {
  const chapters = document.querySelectorAll('.chapter-item');
  
  chapters.forEach(chapter => {
    if (subject === 'all' || chapter.dataset.subject === subject) {
      chapter.style.display = '';
    } else {
      chapter.style.display = 'none';
    }
  });
}

// Export study data (future enhancement)
function exportStudyData() {
  // This can be implemented to export user data as CSV/PDF
  alert('Export feature coming soon!');
}
