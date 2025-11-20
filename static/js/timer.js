// Pomodoro Timer Implementation for NEET Study Tracker
class PomodoroTimer {
  constructor() {
    // Timer settings (in minutes)
    this.workMinutes = 25;
    this.shortBreak = 5;
    this.longBreak = 15;
    this.cyclesBeforeLongBreak = 4;
    
    // Timer state
    this.currentCycle = 0;
    this.isRunning = false;
    this.isBreak = false;
    this.timeRemaining = this.workMinutes * 60; // Convert to seconds
    this.timerInterval = null;
    
    // Initialize
    this.initializeElements();
    this.attachEventListeners();
    this.updateDisplay();
    this.updateStatus();
  }
  
  initializeElements() {
    // Get DOM elements
    this.display = document.getElementById('timer-display');
    this.startBtn = document.getElementById('start-btn');
    this.pauseBtn = document.getElementById('pause-btn');
    this.resetBtn = document.getElementById('reset-btn');
    this.statusText = document.getElementById('timer-status');
    this.cycleCount = document.getElementById('cycle-count');
    this.todayCount = document.getElementById('today-count');
  }
  
  attachEventListeners() {
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => this.start());
    }
    if (this.pauseBtn) {
      this.pauseBtn.addEventListener('click', () => this.pause());
    }
    if (this.resetBtn) {
      this.resetBtn.addEventListener('click', () => this.reset());
    }
  }
  
  start() {
    if (!this.isRunning) {
      this.isRunning = true;
      
      // Update button states
      if (this.startBtn) this.startBtn.disabled = true;
      if (this.pauseBtn) this.pauseBtn.disabled = false;
      
      // Start the countdown
      this.timerInterval = setInterval(() => {
        this.tick();
      }, 1000);
      
      // Send start event to server
      this.sendTimerEvent('start');
    }
  }
  
  pause() {
    if (this.isRunning) {
      this.isRunning = false;
      
      // Update button states
      if (this.startBtn) this.startBtn.disabled = false;
      if (this.pauseBtn) this.pauseBtn.disabled = true;
      
      // Stop the countdown
      clearInterval(this.timerInterval);
    }
  }
  
  reset() {
    // Stop timer
    this.pause();
    
    // Reset to work session
    this.isBreak = false;
    this.timeRemaining = this.workMinutes * 60;
    
    // Update UI
    this.updateDisplay();
    this.updateStatus();
  }
  
  tick() {
    // Decrement time
    this.timeRemaining--;
    
    // Check if timer completed
    if (this.timeRemaining <= 0) {
      this.complete();
    }
    
    // Update display
    this.updateDisplay();
  }
  
  complete() {
    // Stop the timer
    this.pause();
    
    // Play notification sound
    this.playNotificationSound();
    
    if (!this.isBreak) {
      // Work session completed
      this.currentCycle++;
      this.sendCompletedSession();
      
      // Show browser notification
      this.showNotification('Pomodoro Complete!', 'Great work! Time for a break.');
      
      // Determine break type
      if (this.currentCycle % this.cyclesBeforeLongBreak === 0) {
        // Long break
        this.timeRemaining = this.longBreak * 60;
        alert('Amazing! ' + this.currentCycle + ' Pomodoros completed. Take a ' + this.longBreak + ' minute long break!');
      } else {
        // Short break
        this.timeRemaining = this.shortBreak * 60;
        alert('Pomodoro complete! Take a ' + this.shortBreak + ' minute break.');
      }
      
      this.isBreak = true;
    } else {
      // Break completed
      this.timeRemaining = this.workMinutes * 60;
      this.isBreak = false;
      this.showNotification('Break Over!', 'Ready for another Pomodoro?');
      alert('Break over! Ready for another focused session?');
    }
    
    // Update UI
    this.updateDisplay();
    this.updateStatus();
    this.updateCycleCount();
  }
  
  updateDisplay() {
    const minutes = Math.floor(this.timeRemaining / 60);
    const seconds = this.timeRemaining % 60;
    
    const display = String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
    
    if (this.display) {
      this.display.textContent = display;
    }
  }
  
  updateStatus() {
    if (this.statusText) {
      if (this.isBreak) {
        this.statusText.textContent = 'Break Time';
        this.statusText.className = 'timer-status text-success';
      } else {
        this.statusText.textContent = 'Focus Time';
        this.statusText.className = 'timer-status text-primary';
      }
    }
  }
  
  updateCycleCount() {
    if (this.cycleCount) {
      this.cycleCount.textContent = this.currentCycle;
    }
  }
  
  playNotificationSound() {
    try {
      // Create a simple beep sound using Web Audio API
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (err) {
      console.log('Audio notification not supported:', err);
    }
  }
  
  showNotification(title, body) {
    // Check if browser supports notifications
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification(title, {
          body: body,
          icon: '/static/images/icon.png',
          badge: '/static/images/badge.png'
        });
      } catch (err) {
        console.log('Notification error:', err);
      }
    }
  }
  
  sendTimerEvent(eventType) {
    const subjectSelect = document.getElementById('timer-subject');
    const subject = subjectSelect ? subjectSelect.value : null;
    
    fetch('/pomodoro/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        event: eventType,
        subject: subject
      })
    }).catch(function(err) {
      console.error('Error sending timer event:', err);
    });
  }
  
  sendCompletedSession() {
    const subjectSelect = document.getElementById('timer-subject');
    const subject = subjectSelect ? subjectSelect.value : null;
    
    fetch('/pomodoro/complete', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: subject
      })
    })
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      if (data.success) {
        const todayCountElement = document.getElementById('today-count');
        if (todayCountElement) {
          todayCountElement.textContent = data.sessions_today;
        }
      }
    })
    .catch(function(err) {
      console.error('Error logging Pomodoro:', err);
    });
  }
}

// Initialize timer when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Request notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  
  // Initialize Pomodoro timer if elements exist on page
  if (document.getElementById('timer-display')) {
    window.pomodoroTimer = new PomodoroTimer();
  }
});
