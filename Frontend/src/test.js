const WebSocket = require('ws');

const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTFlNDE5MTAtYTc3Yy00ODE4LWIwNzMtMjgwMTliMGZiYzkyIiwiZW1haWwiOiJhaG1lZEBnbWFpbC5jb20iLCJyb2xlcyI6WyJ1c2VyIl0sIm9yZ19pZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsInBlcm1pc3Npb25zIjpbInRhc2tzOnVwZGF0ZSIsInRhc2tzOmNyZWF0ZSIsInRhc2tzOnJlYWQiLCJwcm9qZWN0czpyZWFkIiwib3JnYW5pemF0aW9uczpyZWFkIl0sImV4cCI6MTc0NzcwNDI3NiwibmJmIjoxNzQ3NjE3ODc2LCJpYXQiOjE3NDc2MTc4NzZ9.LQg6ueeOKynMXzSOqFA3KfzgJ7XN-vbBPeN2PXXUZYE';

// Pass token as a query parameter instead of a header
const ws = new WebSocket(`ws://localhost:8000/api/notifications/ws?token=${token}`);

console.log('Listening for notifications. Press Ctrl+C to exit.');

// Store received notifications
const notifications = [];

ws.on('open', function open() {
  console.log('WebSocket connection established');
  
  // Set up command input from console
  process.stdin.on('data', (data) => {
    const input = data.toString().trim();
    
    if (input === 'exit' || input === 'quit') {
      console.log('Closing connection...');
      ws.close();
      process.exit(0);
    } else if (input === 'mark-all-read') {
      // Send command to mark all notifications as read
      ws.send(JSON.stringify({
        command: 'mark_all_read'
      }));
      console.log('Sent command: mark all as read');
    } else if (input.startsWith('mark-read ')) {
      // Extract notification ID and send mark-read command
      const id = input.substring('mark-read '.length).trim();
      ws.send(JSON.stringify({
        command: 'mark_read',
        id: id
      }));
      console.log(`Sent command: mark notification ${id} as read`);
    } else if (input === 'list') {
      // List all received notifications
      console.log('Received notifications:');
      notifications.forEach((notif, index) => {
        console.log(`[${index}] ID: ${notif.id} - ${notif.title}: ${notif.content}`);
      });
    } else if (input === 'help') {
      console.log('\nAvailable commands:');
      console.log('  help - Show this help message');
      console.log('  list - List all received notifications');
      console.log('  mark-read <id> - Mark specific notification as read');
      console.log('  mark-all-read - Mark all notifications as read');
      console.log('  exit/quit - Close the connection and exit\n');
    } else {
      console.log('Unknown command. Type "help" for available commands.');
    }
  });
  
  console.log('\nType "help" for available commands\n');
});

ws.on('message', function incoming(data) {
  try {
    const notification = JSON.parse(data.toString());
    
    // Check if it's a notification or a count message
    if (notification.type === 'count') {
      console.log(`You have ${notification.count} unread notifications`);
    } else if (notification.id) {
      // It's a notification
      console.log('Notification received:');
      console.log(`ID: ${notification.id}`);
      console.log(`Title: ${notification.title}`);
      console.log(`Content: ${notification.content}`);
      console.log(`Type: ${notification.type}`);
      console.log(`Status: ${notification.status}`);
      console.log('-----------------------------------');
      
      // Store the notification
      notifications.push(notification);
    }
  } catch (err) {
    console.error('Error parsing notification:', data.toString());
  }
});

ws.on('close', function close() {
  console.log('WebSocket connection closed');
  process.exit(0);
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
  process.exit(1);
});