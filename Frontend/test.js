const WebSocket = require('ws');

// Replace with your token
const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTFlNDE5MTAtYTc3Yy00ODE4LWIwNzMtMjgwMTliMGZiYzkyIiwiZW1haWwiOiJhaG1lZEBnbWFpbC5jb20iLCJyb2xlcyI6WyJ1c2VyIl0sIm9yZ19pZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsInBlcm1pc3Npb25zIjpbInRhc2tzOnVwZGF0ZSIsInRhc2tzOmNyZWF0ZSIsInRhc2tzOnJlYWQiLCJwcm9qZWN0czpyZWFkIiwib3JnYW5pemF0aW9uczpyZWFkIl0sImV4cCI6MTc0NzY5OTA4MCwibmJmIjoxNzQ3NjEyNjgwLCJpYXQiOjE3NDc2MTI2ODB9.RnwkifD5zxVD3u5gHgeslhAij7W5pnUwgEiZMiLW-3Q';
const ws = new WebSocket(`ws://localhost:8000/api/notifications/ws`,{
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

ws.on('open', function open() {
  console.log('Connected to notification WebSocket');
});

ws.on('message', function incoming(data) {
  console.log('Received notification:', JSON.parse(data));
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
});