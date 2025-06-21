// Main application JavaScript
document.addEventListener('DOMContentLoaded', () => {
  // DOM elements
  const startBtn = document.getElementById('start-btn');
  const stopBtn = document.getElementById('stop-btn');
  const statusLight = document.getElementById('status-light');
  const statusText = document.getElementById('status-text');
  const conversation = document.getElementById('conversation');
  
  // WebSocket connection
  let socket = null;
  let sessionId = null;
  
  // Update status UI
  function updateStatus(status) {
    statusLight.className = 'status-light';
    
    switch(status) {
      case 'ready':
        statusLight.classList.add('active');
        statusText.textContent = 'Ready';
        break;
      case 'connecting':
        statusLight.classList.add('processing');
        statusText.textContent = 'Connecting...';
        break;
      case 'connected':
        statusLight.classList.add('active');
        statusText.textContent = 'Connected';
        break;
      case 'listening':
        statusLight.classList.add('listening');
        statusText.textContent = 'Listening...';
        break;
      case 'processing':
        statusLight.classList.add('processing');
        statusText.textContent = 'Processing...';
        break;
      case 'speaking':
        statusLight.classList.add('active');
        statusText.textContent = 'Speaking...';
        break;
      case 'error':
        statusLight.classList.add('error');
        statusText.textContent = 'Error';
        break;
      case 'disconnected':
        statusLight.classList.remove('active', 'listening', 'processing', 'error');
        statusText.textContent = 'Disconnected';
        break;
      default:
        statusLight.classList.remove('active', 'listening', 'processing', 'error');
        statusText.textContent = 'Ready';
    }
  }
  
  // Add message to conversation
  function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    messageDiv.textContent = text;
    conversation.appendChild(messageDiv);
    conversation.scrollTop = conversation.scrollHeight;
  }
  
  // Create a new session
  async function createSession() {
    try {
      const response = await fetch('/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const data = await response.json();
      return data.session_id;
    } catch (error) {
      console.error('Error creating session:', error);
      updateStatus('error');
      return null;
    }
  }
  
  // Connect WebSocket
  function connectWebSocket(sessionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      console.log('WebSocket connected');
      updateStatus('connected');
      startBtn.disabled = true;
      stopBtn.disabled = false;
      
      // Welcome message
      setTimeout(() => {
        addMessage('Hello! I am your AI assistant. How can I help you today?');
      }, 1000);
    };
    
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch(message.type) {
        case 'status':
          updateStatus(message.status);
          break;
        case 'transcript':
          addMessage(message.text, true);
          break;
        case 'response':
          addMessage(message.text);
          break;
        case 'error':
          console.error('Error from server:', message.error);
          addMessage(`Error: ${message.error}`);
          updateStatus('error');
          break;
      }
    };
    
    socket.onclose = () => {
      console.log('WebSocket disconnected');
      updateStatus('disconnected');
      startBtn.disabled = false;
      stopBtn.disabled = true;
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      updateStatus('error');
    };
  }
  
  // Start conversation
  async function startConversation() {
    updateStatus('connecting');
    
    // Create a new session
    sessionId = await createSession();
    
    if (sessionId) {
      // Connect WebSocket
      connectWebSocket(sessionId);
    }
  }
  
  // End conversation
  function endConversation() {
    if (socket) {
      socket.close();
    }
  }
  
  // Event listeners
  startBtn.addEventListener('click', startConversation);
  stopBtn.addEventListener('click', endConversation);
  
  // Initialize
  updateStatus('ready');
});