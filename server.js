const http = require('http');
const fs = require('fs');
const WebSocket = require('ws');
//const mysql = require('mysql2');
let clients = [];
// Tạo kết nối với database
// const connection = mysql.createConnection({
//   host: 'localhost',      // Địa chỉ server database
//   user: 'root',           // Tên đăng nhập MySQL
//   password: '1234', // Mật khẩu MySQL
//   database: 'data' // Tên database bạn muốn kết nối
// });

// Mở kết nối
// connection.connect((err) => {
//   if (err) {
//     console.error('Error connecting to the database:', err.stack);
//     return;
//   }
//   console.log('Connected to the database as id', connection.threadId);
// });

// Tạo HTTP server để phục vụ file HTML
const server = http.createServer((req, res) => {
  fs.readFile('index.html', (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('File not found');
    } else {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(data);
    }
  });
});

// Tạo WebSocket server chạy cùng HTTP server
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
  console.log('Client đã kết nối');
  clients.push(ws);
//   connection.query('SELECT * FROM data.data_1', (err, results) => {
//     if (err) throw err;
//     ws.send(JSON.stringify(results)); // Gửi dữ liệu thiết bị hiện tại
  
//   });
  ws.on('message', (message) => {
    console.log('Nhận được từ client:', message.toString());
    //{'name':' light','status':'on'}
    const {name,status} = JSON.parse(message.toString());
    //nhận được message từ client sau đó cập nhật database
    // connection.query('update data.data_1 set status = ? where name =?',[status,name],(err,results) => {
    //   if(err){
    //     console.error('lỗi cập nhật trạng thái',err);
    //     return;
    //   }
    //   console.log(`Cập nhật trạng thái thiết bị ${name} thành ${status}`);
    // })
   // ws.send(message.toString());
    clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN){
      client.send(JSON.stringify({name,status}));
      }
    })
  });

  ws.on('close', () => {
    console.log('Client đã ngắt kết nối');
    const index = clients.indexOf(ws);
    if (index !== -1) {
      clients.splice(index, 1);
    }
  });
});

// Lắng nghe trên cổng 8080 (hoặc một cổng khác nếu bạn muốn)
server.listen(8080, () => {
  console.log('Server đang chạy tại http://<IP-nội-bộ>:8080');
});

