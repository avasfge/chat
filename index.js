const fs = require('fs');
const geoip = require('geoip-lite'); // Нужно установить эту библиотеку через npm
const app = require('express')();
const server = require('http').createServer(app);
const io = require('socket.io')(server);
const PORT = process.env.PORT || 3000;

const users = [];
const logFilePath = 'chat.log';

app.get('/', (req, res) => {
   res.sendFile(__dirname + '/chat.html');
});

server.listen(PORT, () => {
   console.log('Server is running on port: ' + PORT);
   logToFile(`\n=== Server started on port: ${PORT} ===`);
});

function logToFile(message) {
   const timestamp = new Date().toISOString();
   const logMessage = `[${timestamp}] ${message}`;
   fs.appendFile(logFilePath, logMessage + '\n', (err) => {
       if (err) {
           console.error('Error writing to log file:', err);
       }
   });
}

function formatLog(action, details) {
   const separator = '='.repeat(60);
   return `${separator}\nAction: ${action}\n${details}\n${separator}`;
}

io.on('connection', (socket) => {
   const userIP = socket.request.connection.remoteAddress;
   const geo = geoip.lookup(userIP); // Получение геолокации по IP

   socket.on('new user', (usr, userAgent) => {
       socket.username = usr;
       users.push(usr);
       io.emit('send message', { message: `${socket.username} В сети!`, user: "Пользователь" });

       // Логирование подключения
       const location = geo ? `${geo.city}, ${geo.country}` : 'Unknown location';
       const details = `Username: ${socket.username}\nSession ID: ${socket.id}\nIP Address: ${userIP}\nLocation: ${location}\nDevice: ${userAgent}`;
       const logMessage = formatLog('New User Connected', details);
       console.log(logMessage);
       logToFile(logMessage);
   });

   socket.on('new message', (msg) => {
       const messageData = { message: msg, user: socket.username };
       io.emit('send message', messageData);

       // Логирование сообщения
       const details = `Username: ${socket.username}\nSession ID: ${socket.id}\nMessage: ${msg}`;
       const logMessage = formatLog('New Message', details);
       console.log(logMessage);
       logToFile(logMessage);
   });

   socket.on('disconnect', () => {
       if (socket.username) {
           io.emit('send message', { message: `${socket.username} покинул чат`, user: "Пользователь" });
           users.splice(users.indexOf(socket.username), 1);

           // Логирование отключения
           const details = `Username: ${socket.username}\nSession ID: ${socket.id}\nIP Address: ${userIP}`;
           const logMessage = formatLog('Пользователь покинул чат', details);
           console.log(logMessage);
           logToFile(logMessage);
       }
   });

   socket.on('refresh users', () => {
       io.emit('send message', { message: `Текущие пользователи: ${users.join(', ')}`, user: "Система" });

       // Логирование текущего количества пользователей
       const details = `Active Users: ${users.length}\nUser List: ${users.join(', ')}`;
       const logMessage = formatLog('Refresh Users', details);
       console.log(logMessage);
       logToFile(logMessage);
   });
});
