const WebSocket = require('ws');

const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTFlNDE5MTAtYTc3Yy00ODE4LWIwNzMtMjgwMTliMGZiYzkyIiwiZW1haWwiOiJhaG1lZEBnbWFpbC5jb20iLCJyb2xlcyI6WyJ1c2VyIl0sIm9yZ19pZCI6IjAwMDAwMDAwLTAwMDAtMDAwMC0wMDAwLTAwMDAwMDAwMDAwMCIsInBlcm1pc3Npb25zIjpbInRhc2tzOnVwZGF0ZSIsInRhc2tzOmNyZWF0ZSIsInRhc2tzOnJlYWQiLCJwcm9qZWN0czpyZWFkIiwib3JnYW5pemF0aW9uczpyZWFkIl0sImV4cCI6MTc0NzQ2MDAzNCwibmJmIjoxNzQ3MzczNjM0LCJpYXQiOjE3NDczNzM2MzR9.ZPEc95Op431gPL5-nItyD1LWs3nfpUkIFK_47hIOL2I';

const ws = new WebSocket('ws://localhost:8000/api/notifications/ws', {
  headers: {
    Authorization: `Bearer ${token}`,
  }
});

ws.on('open', function open() {
  console.log('WebSocket connection established');
});

ws.on('message', function incoming(data) {
  console.log('Notification received:', data.toString());
});

ws.on('close', function close() {
  console.log('WebSocket connection closed');
});

ws.on('error', function error(err) {
  console.error('WebSocket error:', err);
});